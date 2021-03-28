import sys
import time
import os.path
import datetime
import socket
import json
import requests

CAM_URL = 'http://weathercam:8080?action=snapshot'
CAM_CONTROL_SERVER='weathercam'
CAM_CONTROL_PORT=10570

def get_sleep_time():
  seconds = int(time.strftime('%S'))
  return 10 - (seconds % 10)

def camera_running():
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((CAM_CONTROL_SERVER, CAM_CONTROL_PORT))
    s.sendall(bytes('status', 'utf-8'))
    return json.loads(s.recv(1024))['active']

def capture(basedir):
  if camera_running():
    capture_dir = os.path.join(basedir, time.strftime('%Y%m%d'))
    if (not os.path.exists(capture_dir)):
      os.mkdir(capture_dir)

    capture_file = os.path.join(capture_dir, f'{time.strftime("%Y%m%d%H%M%S")}.jpg')
    with requests.get(CAM_URL) as r:
      open(capture_file, 'wb').write(r.content)
      print(f'Captured {os.path.basename(capture_file)}')



#####################################
basedir = sys.argv[1]
if (not os.path.exists(basedir)):
  os.mkdir(basedir)

while True:
  time.sleep(get_sleep_time())
  capture(basedir)