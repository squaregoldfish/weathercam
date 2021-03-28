import traceback
from threading import Thread, Lock
import curses
import time
import socket
import json
from datetime import date
from datetime import datetime
from astral import LocationInfo
from astral.sun import sun
from dateutil.tz import *

LONGITUDE=5.417278
LATITUDE=60.554981
TIMEZONE='Europe/Oslo'
STREAM_SERVER='weathercam'
STREAM_SERVER_CONTROL_PORT=10570

ERROR = None

SUNRISE_COLOR = 1
SUNSET_COLOR = 2
TIME_COLOR = 3
CAM_RUNNING_COLOR = 4
CAM_NOT_RUNNING_COLOR = 5
PI_HEADER_COLOR = 6

SUNRISE = None
SUNSET = None

mutex = Lock()

def time_thread(stdscr):
  global SUNRISE
  global SUNSET
  try:
    while True:
      last_sun_update = None
      loc = LocationInfo(latitude=LATITUDE, longitude=LONGITUDE, timezone=TIMEZONE)

      if last_sun_update is not date.today():
        # Calculate sunrise/sunset
        s = sun(loc.observer, date=date.today(), tzinfo=loc.timezone)
        SUNRISE = s['sunrise']
        SUNSET = s['sunset']
        last_sun_update = date.today()

      mutex.acquire()
      try:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S %Z')
        sunrise_time = SUNRISE.strftime('%H:%M:%S %Z')
        sunset_time = SUNSET.strftime('%H:%M:%S %Z')

        stdscr.addstr(0, 40 - len(current_time), current_time, curses.color_pair(TIME_COLOR))
        stdscr.addstr(1, 40 - len(sunrise_time), sunrise_time, curses.color_pair(SUNRISE_COLOR))
        stdscr.addstr(2, 40 - len(sunset_time), sunset_time, curses.color_pair(SUNSET_COLOR))

        stdscr.refresh()
      finally:
        mutex.release()

      time.sleep(1)
  except:
    global ERROR
    ERROR = traceback.format_exc()

def camera_control_thread(stdscr):
  global ERROR
  try:
    while True:
      status = camera_command('status')

      if SUNRISE is not None:
        now = datetime.now(tzlocal())
        if now >= SUNRISE and now < SUNSET:
          if not status['active']:
            camera_command('startcam')
        elif status['active']:
          camera_command('stopcam')

      mutex.acquire()

      try:
        if status is None:
          stdscr.addstr(3, 33, 'Unknown')
        elif status['active']:
          stdscr.addstr(3, 29, '    Running', curses.color_pair(CAM_RUNNING_COLOR))
        else:
          stdscr.addstr(3, 29, 'Not Running', curses.color_pair(CAM_NOT_RUNNING_COLOR))


        if status is not None:
          stdscr.addstr(6, 40 - len(status['time']), status['time'])
          stdscr.addstr(7, 40 - len(status['uptime']), status['uptime'])
          stdscr.addstr(8, 20, f'{status["load"][0]:6.2f} {status["load"][1]:6.2f} {status["load"][2]:6.2f}')
          stdscr.addstr(9, 36, f'{status["cpu"]:>3}%')

          memstr = f'{status["ram_used"]}/{status["ram_free"]}Mb'
          stdscr.addstr(10, 40 - len(memstr), memstr)

          cputempstr = f'{status["cpu_temp"]:5.1f}°C'
          stdscr.addstr(11, 40 - len(cputempstr), cputempstr)

          casetempstr = '??.?°C'
          if status['case_temp'] != -999:
            casetempstr = f'{status["case_temp"]:8.1f}°C'

          stdscr.addstr(12, 40 - len(casetempstr), casetempstr)

          casehumidstr = '??.?%'
          if status['case_humidity'] != -999:
            casehumidstr = f'{status["case_humidity"]:>8.1f}%'

          stdscr.addstr(13, 40 - len(casehumidstr), casehumidstr)

          wifistr = f'{status["wifi"][0]}%, {status["wifi"][1]}dBm'
          stdscr.addstr(14, 40 - len(wifistr), wifistr)
      finally:
        mutex.release()

      time.sleep(calc_sleep_time(5))

  except:
    ERROR = traceback.format_exc()

def calc_sleep_time(target):
  current_seconds_digit = int(time.strftime('%S')) % 10
  if current_seconds_digit < target:
    return target - current_seconds_digit
  else:
    return 10 - current_seconds_digit + target

def camera_command(command):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((STREAM_SERVER, STREAM_SERVER_CONTROL_PORT))
    s.sendall(bytes(command, 'utf-8'))
    return json.loads(s.recv(1024)) if command == 'status' else None


# Set up the screen
def setup_screen(stdscr):
  # Initialise colors
  curses.init_pair(TIME_COLOR, 81, curses.COLOR_BLACK)
  curses.init_pair(SUNRISE_COLOR, 226, curses.COLOR_BLACK)
  curses.init_pair(SUNSET_COLOR, 172, curses.COLOR_BLACK)
  curses.init_pair(CAM_RUNNING_COLOR, 82, curses.COLOR_BLACK)
  curses.init_pair(CAM_NOT_RUNNING_COLOR, 197, curses.COLOR_BLACK)
  curses.init_pair(PI_HEADER_COLOR, curses.COLOR_BLACK, curses.COLOR_WHITE)

  # Clear screen
  stdscr.nodelay(1)

  # Hide the cursor
  curses.curs_set(0)

def draw_screen_base(stdscr):
  stdscr.clear()
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

  stdscr.refresh()

# Main function
def main(stdscr):
  global ERROR
  keep_running = True

  stdscr.clear()
  setup_screen(stdscr)
  draw_screen_base(stdscr)

  timethread = Thread(target=time_thread, args=[stdscr], daemon=True)
  timethread.start()

  camcontrolthread = Thread(target=camera_control_thread, args=[stdscr], daemon=True)
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
    elif char == 'r':
      draw_screen_base(stdscr)


curses.wrapper(main)
if ERROR is not None:
  print(f'{ERROR}')
