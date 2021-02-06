import traceback
import threading
import curses
import time
import socket
import json
from datetime import date
from astral import LocationInfo
from astral.sun import sun

LONGITUDE=5.417278
LATITUDE=60.554981
STREAM_SERVER='weathercam'
STREAM_SERVER_CONTROL_PORT=10570

ERROR = None

SUNRISE_COLOR = 1
SUNSET_COLOR = 2
TIME_COLOR = 3
CAM_RUNNING_COLOR = 4
CAM_NOT_RUNNING_COLOR = 5
PI_HEADER_COLOR = 5

SUNRISE = None
SUNSET = None

def time_thread(stdscr):
  try:
    while True:
      last_sun_update = None
      loc = LocationInfo(latitude=LATITUDE, longitude=LONGITUDE, timezone=time.strftime('%Z'))

      if last_sun_update is not date.today():
        # Calculate sunrise/sunset
        s = sun(loc.observer, date=date.today(), tzinfo=loc.timezone)
        SUNRISE = s['sunrise']
        SUNSET = s['sunset']
        last_sun_update = date.today()

        # Update screen
        stdscr.addstr(1, 28, SUNRISE.strftime('%H:%M:%S %Z'), curses.color_pair(SUNRISE_COLOR))
        stdscr.addstr(2, 28, SUNSET.strftime('%H:%M:%S %Z'), curses.color_pair(SUNSET_COLOR))

      stdscr.addstr(0, 17, time.strftime('%Y-%m-%d %H:%M:%S %Z'), curses.color_pair(TIME_COLOR))
      stdscr.refresh()
      time.sleep(1)
  except:
    global ERROR
    ERROR = traceback.format_exc()

def camera_control_thread(stdscr):
  global ERROR
  try:
    while True:
      cam_status = camera_command('status')
      if cam_status['active']:
        stdscr.addstr(3, 33, 'Running', curses.color_pair(CAM_RUNNING_COLOR))
      else:
        stdscr.addstr(3, 29, 'Not Running', curses.color_pair(CAM_NOT_RUNNING_COLOR))

      stdscr.addstr(6, 17, cam_status['time'])
      stdscr.addstr(7, 40 - len(cam_status['uptime']), cam_status['uptime'])
      stdscr.addstr(8, 34, f'{cam_status["load"][0]:6.2f}')
      stdscr.addstr(9, 36, f'{cam_status["cpu"]:>3}%')
      
      memstr = f'{cam_status["ram_used"]}/{cam_status["ram_free"]}Mb'
      stdscr.addstr(10, 40 - len(memstr), memstr)

      cputempstr = f'{cam_status["cpu_temp"]:5.1f}°C'
      stdscr.addstr(11, 40 - len(cputempstr), cputempstr)

      casetempstr = '??.?°C'
      if cam_status['case_temp'] != -999:
        casetempstr = f'{cam_status["case_temp"]:8.1f}°C'

      stdscr.addstr(12, 40 - len(casetempstr), casetempstr)

      casehumidstr = '??.?%'
      if cam_status['case_humidity'] != -999:
        casehumidstr = f'{cam_status["case_humidity"]:>8.1f}%'

      stdscr.addstr(13, 40 - len(casehumidstr), casehumidstr)

      wifistr = f'{cam_status["wifi"][0]}%, {cam_status["wifi"][1]}dBm'
      stdscr.addstr(14, 40 - len(wifistr), wifistr)

      stdscr.refresh()
      time.sleep(5)

  except:
    ERROR = traceback.format_exc()

def camera_command(command):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((STREAM_SERVER, STREAM_SERVER_CONTROL_PORT))
    s.sendall(b'status')
    return json.loads(s.recv(1024))


# Set up the screen
def setup_screen(stdscr):
  # Hide the cursor
  curses.curs_set(0)

  stdscr.addstr(0, 0, 'Current time:', curses.color_pair(TIME_COLOR))
  stdscr.addstr(1, 0, 'Sunrise:', curses.color_pair(SUNRISE_COLOR))
  stdscr.addstr(2, 0, 'Sunset:', curses.color_pair(SUNSET_COLOR))
  stdscr.addstr(3, 0, 'Camera status:', curses.color_pair(CAM_RUNNING_COLOR))
  stdscr.addstr(5, 0, '                PI INFO                 ', curses.color_pair(PI_HEADER_COLOR))
  stdscr.addstr(6, 0, 'Time:')
  stdscr.addstr(7, 0, 'Uptime:')
  stdscr.addstr(8, 0, 'Load:')
  stdscr.addstr(9, 0, 'CPU Usage:')
  stdscr.addstr(10, 0, 'RAM Used/Free:')
  stdscr.addstr(11, 0, 'CPU Temp:')
  stdscr.addstr(12, 0, 'Case Temp:')
  stdscr.addstr(13, 0, 'Case Humidity:')
  stdscr.addstr(14, 0, 'Wifi:')

# Main function
def main(stdscr):
  global ERROR
  keep_running = True

  # Initialise colors
  curses.init_pair(TIME_COLOR, 81, curses.COLOR_BLACK)
  curses.init_pair(SUNRISE_COLOR, 226, curses.COLOR_BLACK)
  curses.init_pair(SUNSET_COLOR, 172, curses.COLOR_BLACK)
  curses.init_pair(CAM_RUNNING_COLOR, 82, curses.COLOR_BLACK)
  curses.init_pair(CAM_NOT_RUNNING_COLOR, 249, curses.COLOR_BLACK)
  curses.init_pair(PI_HEADER_COLOR, curses.COLOR_BLACK, curses.COLOR_WHITE)

  # Clear screen
  stdscr.nodelay(1)
  stdscr.clear()

  setup_screen(stdscr)
  stdscr.refresh()

  timethread = threading.Thread(target=time_thread, args=[stdscr], daemon=True)
  timethread.start()

  camcontrolthread = threading.Thread(target=camera_control_thread, args=[stdscr], daemon=True)
  camcontrolthread.start()

  while keep_running:
    time.sleep(0.1)
    char = ''
    try:
      char = stdscr.getkey()
    except:
      pass

    if char == 'q' or  ERROR is not None:
      keep_running = False


curses.wrapper(main)
if ERROR is not None:
  print(f'{ERROR}')
