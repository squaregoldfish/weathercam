import socket
import logging
import shlex
import subprocess
import os
import signal
import time

LOG_FILE='/var/log/cam_control.log'
PORT=10570
MJPG_STREAMER_CMD = 'mjpg_streamer -b -i "input_uvc.so -f 5 -r 1920x1080 -q 98" -o "output_http.so -w /usr/local/share/mjpg-streamer/www"'

def process_command(command):
  result = None

  try:
    if command == 'startcam':
      result = start_cam()
    elif command == 'stopcam':
      result = stop_cam()
    elif command == 'status':
      result = cam_status()
    else:
      result = 'Command not recognised'
  except Exception as e:
    logging.error(e, exc_info=True)
    result = 'Internal error'


  return f'{result}\n'

def start_cam():
  result = None
  existing_pid = get_cam_pid()
  if existing_pid is not None:
    logging.info(f'Camera already running with PID {existing_pid}')
    result = "Camera already running"
  else:
    process = subprocess.Popen(shlex.split(MJPG_STREAMER_CMD),
      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logging.info(f'Camera started with process {process.pid}')
    result = "Camera started"

  return result

def stop_cam():
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

def cam_status():
  result = 'Not running'
  pid = get_cam_pid()
  if pid is not None:
    result = 'Running'

  return result

def get_cam_pid():
  pid = None
  pgrep = subprocess.run(['pgrep', 'mjpg_streamer'], capture_output=True)
  if len(pgrep.stdout.decode()) > 0:
    pid = int(pgrep.stdout.decode())

  return pid

  int(x.stdout.decode())

################################
#
# Start up the server

logging.basicConfig(filename=LOG_FILE, format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG)
logging.debug('Weathercam control server')
logging.debug(f'Starting server on port {PORT}')

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', PORT))

s.listen(5)
logging.debug('Server listening')
while True:
  conn, addr = s.accept()
  try:
    command = conn.recv(512).decode("utf-8").strip()
    logging.info(f'{addr}: {command}')
    result = process_command(command)
    logging.info(f'Sending result: {result}')
    conn.send(result.encode(encoding='utf_8', errors='strict'))
  except Exception as e:
    logging.error(e)
  finally:
    conn.close()
