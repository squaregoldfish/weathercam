# Screen control
import signal
import os
import threading
import time
import pygame
from gpiozero import Button
from cam_status import cam_status

FONT = '/root/TerminusTTF-4.47.0.ttf'

KEEP_RUNNING = True

def screen_thread():
  global KEEP_RUNNING
  while KEEP_RUNNING:
    if door_button.is_active:
      backlight(0)
      screen.fill((0,0,0))
      pygame.display.flip()
    else:
      backlight(1)
      draw_screen()

    time.sleep(0.75)

  # Make sure the screen is on
  backlight(1)

def draw_screen():
  screen.fill((0,0,0))

  # Current Time
  timesurface = font.render(cam_status.time_string(False), True, (255,255,255))
  screen.blit(timesurface, (0, 0))

  # Uptime
  uptimesurface = font.render(cam_status.sys_uptime(), True, (0, 255, 255))
  screen.blit(uptime_icon, (0, 33))
  screen.blit(uptimesurface, (33, 29))

  # Load Average
  load = cam_status.load_avg()
  load1_surface = font.render(f'{load[0]:5.2f}', True, (255, 255, 0))
  load5_surface = font.render(f'{load[1]:5.2f}', True, (180, 180, 0))
  load15_surface = font.render(f'{load[2]:5.2f}', True, (140, 140, 0))

  screen.blit(heartbeat_icon, (0, 72))
  screen.blit(load1_surface, (33, 68))
  screen.blit(load5_surface, (136, 68))
  screen.blit(load15_surface, (238, 68))

  # CPU Usage
  cpu_usage_surface = font.render(f'{cam_status.cpu():>3}%', True, (74, 200, 46))
  screen.blit(speedometer_icon, (0, 109))
  screen.blit(cpu_usage_surface, (33, 105))

  # RAM
  ram_surface = font.render(f'{cam_status.ram_used():>3}/{cam_status.ram_free():>3}Mb', True, (39, 93, 163))
  screen.blit(ram_icon, (136, 109))
  screen.blit(ram_surface, (170, 105))

  # Case temp
  casetemp = cam_status.case_temp()
  casetempstr = ' ??.?°C' if casetemp == -999 else f'{casetemp:5.1f}°C'
  case_temp_surface = font.render(casetempstr, True, (255, 128, 0))
  screen.blit(case_temp_icon, (0, 145))
  screen.blit(case_temp_surface, (33, 141))

  # Humidity
  humidity = cam_status.case_humidity()
  humiditystr = ' ??.?°C' if humidity == -999 else f'{humidity:5.1f}°C'
  humidity_surface = font.render(humiditystr, True, (83, 164, 202))
  screen.blit(humidity_icon, (0, 181))
  screen.blit(humidity_surface, (33, 177))

  # CPU Temp
  cpu_temp_surface = font.render(f'{cam_status.cpu_temp():5.1f}°C', True, (255, 0, 0))
  screen.blit(cpu_temp_icon, (170, 145))
  screen.blit(cpu_temp_surface, (203, 141))

  # Wifi
  wifi = cam_status.wifi()
  wifistr = f'{wifi[0]:>3}% {wifi[1]}dBm'
  wifi_surface = font.render(wifistr, True, (153, 51, 255))
  screen.blit(wifi_icon, (0, 214))
  screen.blit(wifi_surface, (33, 210))

  # Camera icon
  if (cam_status.camera_active()):
    screen.blit(camera_icon, (250, 181))
  else:
    screen.blit(disabled_camera_icon, (250, 181))

  pygame.display.flip()

def backlight(val):
  with open('/sys/class/backlight/soc:backlight/brightness', 'w') as b:
    b.write(str(val))

# Unix signal handler
def receiveSignal(signalNumber, frame):
  global KEEP_RUNNING
  KEEP_RUNNING = False

############################################
##
## Here we go
signal.signal(signal.SIGTERM, receiveSignal)

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

door_button = Button(22)

screenthread = threading.Thread(target=screen_thread)
screenthread.start()
