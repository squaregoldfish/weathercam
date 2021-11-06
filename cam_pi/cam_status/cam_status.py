# Status functions used by both cam_pi_screen and cam_control
from cam_status import cputemp
from cam_status import temp_sensor
import time
from datetime import timedelta
from uptime import uptime
import os
import psutil
import subprocess
import re
import shutil

def time_string(include_timezone):
  if include_timezone:
    return time.strftime('%Y-%m-%d %H:%M:%S %Z')
  else:
    return time.strftime('%Y-%m-%d %H:%M:%S')

def sys_uptime():
  current_uptime = timedelta(seconds=round(uptime()))

  result = ''
  if current_uptime.days > 0:
    result = f'{current_uptime.days}d '

  hours, remainder = divmod(current_uptime.seconds, 3600)
  minutes, seconds = divmod(remainder, 60)

  result += f'{hours:02}:{minutes:02}:{seconds:02}'

  return result

def load_avg():
  return os.getloadavg()

def cpu():
  return round(psutil.cpu_percent())

def ram_used():
  meminfo = psutil.virtual_memory()
  return round(meminfo.used / (1024 * 1024))

def ram_free():
  meminfo = psutil.virtual_memory()
  free = round(meminfo.free / (1024 * 1024))
  cached = round(meminfo.cached / (1024 * 1024))
  return free + cached

def cpu_temp():
  return cputemp.temperature

def case_temp():
  result = -999

  try:
    result = temp_sensor.temperature
  except:
    pass

  return result

def case_humidity():
  result = -999

  try:
    result = temp_sensor.relative_humidity
  except:
    pass

  return result

def wifi():
  quality = 0
  max_quality = 100
  signal = 0

  iwconfig = subprocess.run(['iwconfig', 'wlan0'], stdout=subprocess.PIPE).stdout.decode('utf-8')
  pattern = re.compile('Link Quality=([0-9]*)/([0-9]*).*Signal level=([-0-9]*)')
  values = pattern.search(iwconfig)
  if values is not None:
    quality = int(values.group(1))
    max_quality = int(values.group(2))
    signal = int(values.group(3))

  quality_percent = (quality / max_quality) * 100
  return (round(quality_percent), signal)

def camera_active():
  streamer = subprocess.run(['pgrep', 'mjpg_streamer'], stdout=subprocess.PIPE).stdout.decode('utf-8')
  return True if len(streamer) > 0 else False

def disk_space():
  return shutil.disk_usage('/').free / 1073742000
