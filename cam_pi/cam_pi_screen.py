# Screen control
import os, time
from datetime import datetime
from datetime import timedelta
import threading
import pygame
from pygame.locals import *
from uptime import uptime
import psutil
from gpiozero import CPUTemperature
from gpiozero import Button
import subprocess
import re
import board
import busio
import adafruit_am2320

FONT = '/root/TerminusTTF-4.47.0.ttf'

def screen_thread():
  while True:
    if door_button.is_active:
      backlight(0)
      screen.fill((0,0,0))
      pygame.display.flip()
    else:
      backlight(1)
      draw_screen()

    time.sleep(1)

def current_time():
  return '{}'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

def sys_uptime():
  current_uptime = timedelta(seconds=round(uptime()))

  result = ''
  if current_uptime.days > 0:
    result = '{}d '.format(current_uptime.days)

  hours, remainder = divmod(current_uptime.seconds, 3600)
  minutes, seconds = divmod(remainder, 60)

  result += '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

  return result

def load_avg():
  load = os.getloadavg()
  load1 = '{: 5.2f}'.format(load[0])
  load5 = '{: 5.2f}'.format(load[1])
  load15 = '{: 5.2f}'.format(load[2])

  return (load1, load5, load15)

def cpu():
  return '{: 3d}%'.format(round(psutil.cpu_percent()))

def ram():
  meminfo = psutil.virtual_memory()
  return '{:3d}/{:3d}Mb'.format(round(meminfo.used / (1024 * 1024)), round(meminfo.free / (1024 * 1024)))

def cpu_temp():
  return '{:5.1f}°C'.format(cputemp.temperature)

def case_temp():
  return '{:5.1f}°C'.format(temp_sensor.temperature)

def case_humidity():
  return '{:5.1f} %'.format(temp_sensor.relative_humidity)

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
  return '{: 3d}% {}dBm'.format(round(quality_percent), signal)

def camera_active():
  streamer = subprocess.run(['pgrep', 'mjpg_streamer'], stdout=subprocess.PIPE).stdout.decode('utf-8')
  return True if len(streamer) > 0 else False

def draw_screen():
  screen.fill((0,0,0))

  # Current Time
  timesurface = font.render(current_time(), True, (255,255,255))
  screen.blit(timesurface, (0, 0))

  # Uptime
  uptimesurface = font.render(sys_uptime(), True, (0, 255, 255))
  screen.blit(uptime_icon, (0, 33))
  screen.blit(uptimesurface, (33, 29))

  # Load Average
  load = load_avg()
  load1_surface = font.render(load[0], True, (255, 255, 0))
  load5_surface = font.render(load[1], True, (180, 180, 0))
  load15_surface = font.render(load[2], True, (140, 140, 0))

  screen.blit(heartbeat_icon, (0, 72))
  screen.blit(load1_surface, (33, 68))
  screen.blit(load5_surface, (136, 68))
  screen.blit(load15_surface, (238, 68))

  # CPU Usage
  cpu_usage_surface = font.render(cpu(), True, (74, 200, 46))
  screen.blit(speedometer_icon, (0, 109))
  screen.blit(cpu_usage_surface, (33, 105))

  # RAM
  ram_surface = font.render(ram(), True, (39, 93, 163))
  screen.blit(ram_icon, (136, 109))
  screen.blit(ram_surface, (170, 105))

  # Case temp
  case_temp_surface = font.render(case_temp(), True, (255, 128, 0))
  screen.blit(case_temp_icon, (0, 145))
  screen.blit(case_temp_surface, (33, 141))

  # Humidity
  humidity_surface = font.render(case_humidity(), True, (83, 164, 202))
  screen.blit(humidity_icon, (0, 181))
  screen.blit(humidity_surface, (33, 177))

  # CPU Temp
  cpu_temp_surface = font.render(cpu_temp(), True, (255, 0, 0))
  screen.blit(cpu_temp_icon, (170, 145))
  screen.blit(cpu_temp_surface, (203, 141))

  # Wifi
  wifi_surface = font.render(wifi(), True, (153, 51, 255))
  screen.blit(wifi_icon, (0, 214))
  screen.blit(wifi_surface, (33, 210))

  # Camera icon
  if (camera_active()):
    screen.blit(camera_icon, (250, 181))
  else:
    screen.blit(disabled_camera_icon, (250, 181))

  pygame.display.flip()

def backlight(val):
  with open('/sys/class/backlight/soc:backlight/brightness', 'w') as b:
    b.write(str(val))

############################################
##
## Here we go

os.putenv('SDF_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

lcdsize = (320, 240)
textsurface = None
pygame.init()
pygame.font.init()
font = pygame.font.Font(FONT, 33)
screen = pygame.display.set_mode(lcdsize)
pygame.mouse.set_visible(False)

# Initialise fixed UI components
uptime_icon = pygame.image.load('uptime.png')
heartbeat_icon = pygame.image.load('heartbeat.png')
speedometer_icon = pygame.image.load('speedometer.png')
ram_icon = pygame.image.load('ram.png')
cpu_temp_icon = pygame.image.load('cpu_temp.png')
case_temp_icon = pygame.image.load('thermometer.png')
humidity_icon = pygame.image.load('humidity.png')
wifi_icon = pygame.image.load('wifi.png')
camera_icon = pygame.image.load('camera.png')
disabled_camera_icon = pygame.image.load('camera_disabled.png')

divider = pygame.Surface((320, 2))
pygame.draw.line(divider, (30, 102, 96), (0, 0), (320, 0), 2)

cputemp = CPUTemperature()

i2c = busio.I2C(board.SCL, board.SDA)
temp_sensor = adafruit_am2320.AM2320(i2c)

door_button = Button(22)

screenthread = threading.Thread(target=screen_thread)
screenthread.start()
