import socket
import logging
from logging.handlers import RotatingFileHandler
import shlex
import subprocess
import os
import signal
import time
import json
from cam_status import cam_status

LOG_FILE='/var/log/cam_control.log'
PORT=10570
MJPG_STREAMER_CMD = 'mjpg_streamer -b -i "input_uvc.so -f 5 -r 1920x1080 -q 98" -o "output_http.so -w /usr/local/share/mjpg-streamer/www"'

def process_command(command, logger):
  result = None

  try:
    if command == 'startcam':
      result = start_cam(logger)
    elif command == 'stopcam':
      result = stop_cam(logger)
    elif command == 'status':
      result = status(logger)
    else:
      result = 'Command not recognised'
  except Exception as e:
    logger.error(e, exc_info=True)
    result = 'Internal error'


  return f'{result}\n'

def start_cam(logger):
  result = None
  existing_pid = get_cam_pid()
  if existing_pid is not None:
    logger.info(f'Camera already running with PID {existing_pid}')
    result = "Camera already running"
  else:
    process = subprocess.Popen(shlex.split(MJPG_STREAMER_CMD),
      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f'Camera started with process {process.pid}')
    result = "Camera started"

  return result

def stop_cam(logger):
  result = None

  pid = get_cam_pid()
  if pid is None:
    result = "Camera not running"
  else:
    os.kill(pid, signal.SIGTERM)
    time.sleep(2)
    if get_cam_pid() is not None:
      result = "Failed to shut down camera"
    else:
      result = "Camera shut down"

  return result

def status(logger):
  status = {}
  status['time'] = cam_status.time_string(True)
  status['uptime'] = cam_status.sys_uptime()
  status['load'] = cam_status.load_avg()
  status['cpu'] = cam_status.cpu()
  status['ram_used'] = cam_status.ram_used()
  status['ram_free'] = cam_status.ram_free()
  status['cpu_temp'] = cam_status.cpu_temp()
  status['case_temp'] = cam_status.case_temp()
  status['case_humidity'] = cam_status.case_humidity()
  status['wifi'] = cam_status.wifi()
  status['active'] = cam_status.camera_active()

  return json.dumps(status)

def get_cam_pid():
  pid = None
  pgrep = subprocess.run(['pgrep', 'mjpg_streamer'], capture_output=True)
  if len(pgrep.stdout.decode()) > 0:
    pid = int(pgrep.stdout.decode())

  return pid

  int(x.stdout.decode())

# Unix signal handler
def receiveSignal(signalNumber, frame):
  global KEEP_RUNNING
  global SOCKET
  SOCKET.shutdown(socket.SHUT_RDWR)
  KEEP_RUNNING = False

################################
#
# Start up the server

KEEP_RUNNING = True
signal.signal(signal.SIGTERM, receiveSignal)

logger = logging.getLogger('CamControl')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(LOG_FILE, maxBytes=10000000, backupCount=5)
logger.addHandler(handler)

logger.debug('Weathercam control server')
logger.debug(f'Starting server on port {PORT}')

SOCKET = socket.socket()
SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SOCKET.bind(('', PORT))

SOCKET.listen(5)
logger.debug('Server listening')
while KEEP_RUNNING:
  conn = None
  try:
    conn, addr = SOCKET.accept()
    command = conn.recv(512).decode("utf-8").strip()
    logger.info(f'{addr}: {command}')
    result = process_command(command, logger)
    conn.send(result.encode(encoding='utf_8', errors='strict'))
  except Exception as e:
    # Only log an error if we haven't been told to shut down
    if KEEP_RUNNING:
      logger.error(e)
  finally:
    if conn is not None:
      conn.close()

logger.info('Shutting down')
