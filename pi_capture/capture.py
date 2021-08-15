import traceback
from threading import Thread
import time
import socket
import json
#from datetime import date
#from datetime import datetime
#from datetime import timedelta
#from astral import LocationInfo
#from astral.sun import sun
#from dateutil.tz import *
import toml
import os
import requests
import re
import subprocess

MIN_QUALITY = 90

LONGITUDE = None
LATITUDE = None
TIMEZONE = None
STREAM_SERVER = None
STREAM_SERVER_CONTROL_PORT = None

ERROR = None

SUNRISE_COLOR = 1
SUNSET_COLOR = 2
TIME_COLOR = 3
CAM_RUNNING_COLOR = 4
CAM_NOT_RUNNING_COLOR = 5
PI_HEADER_COLOR = 6

SUNRISE = None
SUNSET = None

CAMERA_RUNNING = False
CAPTURE_URL = None
IMAGE_DIR = None

def camera_control_thread():
  global ERROR
  global CAMERA_RUNNING

  try:
    while True:
      status = camera_command('status')
      if status is not None:
        if not status['active']:
          camera_command('startcam')

        # if status is not None:
        #   if SUNRISE is not None:
        #     now = datetime.now(tzlocal())
        #     hour = timedelta(hours=1)

        #     day_start = SUNRISE - hour
        #     day_end = SUNSET + hour

        #     if now >= day_start and now < day_end:
        #       if not status['active']:
        #         camera_command('startcam')
        #     elif status['active']:
        #       camera_command('stopcam')

      if status is not None:
        if status['active']:
          CAMERA_RUNNING = True
        else:
          CAMERA_RUNNING = False

      time.sleep(calc_sleep_time(5))

  except:
    ERROR = traceback.format_exc()


def capture_thread():
  global ERROR

  while True:
    time.sleep(0.5)
    if int(time.time() % 10) == 0 and CAMERA_RUNNING:
      try:
        capture_dir = os.path.join(IMAGE_DIR, time.strftime('%Y%m%d'))
        if (not os.path.exists(capture_dir)):
          os.mkdir(capture_dir)

        filename = f'{time.strftime("%Y%m%d%H%M%S")}.jpg'
        capture_file = os.path.join(capture_dir, filename)
        with requests.get(CAPTURE_URL) as r:
          open(capture_file, 'wb').write(r.content)

          # Make sure the captured image is OK
          check_image(capture_file)

      except:
        ERROR = traceback.format_exc()

# Check a captured image and restart the camera if it's of poor quality
  irint(filename)
def check_image(filename):
  quality = 100

  try:
    identify = subprocess.Popen(('identify', '-verbose', filename),
      stdout=subprocess.PIPE)

    quality_line = subprocess.run(('grep', 'Quality'),
      stdin=identify.stdout, stdout=subprocess.PIPE).stdout.decode('utf-8')

    quality_re = re.compile('.*Quality: ([0-9]+)')
    quality_match = quality_re.match(quality_line)

    if quality_match:
      quality = int(quality_match.group(1))
  except:
    global ERROR
    ERROR = traceback.format_exc()

  if quality < MIN_QUALITY:
    camera_command('stopcam')
    time.sleep(5)
    camera_command('startcam')

def calc_sleep_time(target):
  current_seconds_digit = int(time.strftime('%S')) % 10
  if current_seconds_digit < target:
    return target - current_seconds_digit
  else:
    return 10 - current_seconds_digit + target

def camera_command(command):
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.connect((STREAM_SERVER, STREAM_SERVER_CONTROL_PORT))
      s.sendall(bytes(command, 'utf-8'))
      return json.loads(s.recv(1024)) if command == 'status' else None
  except:
    print(traceback.format_exc())

def load_config():
  global LONGITUDE
  global LATITUDE
  global TIMEZONE
  global STREAM_SERVER
  global STREAM_SERVER_CONTROL_PORT
  global CAPTURE_URL
  global IMAGE_DIR

  with open('config.toml', 'r') as f:
    config = toml.load(f)

  LONGITUDE = config['location']['lon']
  LATITUDE = config['location']['lat']
  TIMEZONE = config['location']['timezone']
  STREAM_SERVER = config['pi']['server']
  STREAM_SERVER_CONTROL_PORT = config['pi']['port']
  CAPTURE_URL = config['capture']['url']
  IMAGE_DIR = config['capture']['dir']

# Main function
def main():
  global ERROR
  keep_running = True

  load_config()

  camcontrolthread = Thread(target=camera_control_thread, args=[], daemon=True)
  camcontrolthread.start()

  capturethread = Thread(target=capture_thread, args=[], daemon=True)
  capturethread.start()

  while keep_running:
    time.sleep(1)
    if ERROR is not None:
      keep_running = False

if __name__ == '__main__':
  main()
  if ERROR is not None:
    print(f'{ERROR}')

