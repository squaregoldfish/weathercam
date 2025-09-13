# Screen control
import signal
import os
import threading
import time
import pygame
from cam_status import cam_status
from pitft_touchscreen import pitft_touchscreen
import io
import requests
from gpiozero import MotionSensor
from datetime import datetime

FONT = '/root/TerminusTTF-4.47.0.ttf'
CAPTURE_URL = 'http://localhost:8080?action=snapshot'

KEEP_RUNNING = True
IMAGE_MODE = False
SHOW_SCREEN = True
SHOW_SCREEN_TIME = datetime.now()
SCREEN_TIMEOUT = 10

def screen_thread(touch_screen):
  global KEEP_RUNNING
  while KEEP_RUNNING:
    if SHOW_SCREEN:
      # See if we have been touched
      if touch_screen.has_event():
        show_image(screen)
        touch_screen.clear_event()
      else:
        if not IMAGE_MODE:
          draw_screen()

    time.sleep(0.9)

def show_image(screen):
  global IMAGE_MODE

  if IMAGE_MODE:
    IMAGE_MODE = False
  else:
    IMAGE_MODE = True

    if not cam_status.camera_active():
      screen.fill((0,0,0))
      surface = font.render("Camera not running", True, (255,0,0))
      screen.blit(surface, (7, 100))
    else:
      with requests.get(CAPTURE_URL) as r:
        img_file = io.BytesIO(r.content)
        img = pygame.image.load(img_file)
        img = pygame.transform.scale(img, (320, 240))
        screen.blit(img, (0,0))

    pygame.display.flip()
  
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
  #load5_surface = font.render(f'{load[1]:5.2f}', True, (180, 180, 0))
  #load15_surface = font.render(f'{load[2]:5.2f}', True, (140, 140, 0))

  screen.blit(heartbeat_icon, (0, 72))
  screen.blit(load1_surface, (33, 68))
  #screen.blit(load5_surface, (136, 68))
  #screen.blit(load15_surface, (238, 68))

  # Disk space
  space = cam_status.disk_space()
  diskspace_surface = font.render(f'{space:7.2f}Gb', True, (0, 128, 0))

  screen.blit(sd_icon, (136, 72))
  screen.blit(diskspace_surface, (170, 72))

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
  humiditystr = ' ??.?%' if humidity == -999 else f'{humidity:5.1f}%'
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

# Screen on/off thread
def screen_off_thread():
  global SHOW_SCREEN
  global SHOW_SCREEN_TIME
  global SCREEN_TIMEOUT

  while True:
    if SHOW_SCREEN:
      diff = (datetime.now() - SHOW_SCREEN_TIME).seconds
      if diff > SCREEN_TIMEOUT:
        SHOW_SCREEN = False
        screen.fill((0,0,0))
        pygame.display.flip()
        backlight(0)
  
    time.sleep(10)


def motion_trigger():
  global SHOW_SCREEN
  global SHOW_SCREEN_TIME
  global IMAGE_MODE

  IMAGE_MODE = False
  SHOW_SCREEN = True
  SHOW_SCREEN_TIME = datetime.now()  
  backlight(1)

############################################
##
## Here we go

# Handle signals
signal.signal(signal.SIGTERM, receiveSignal)

# Init screen
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
sd_icon = pygame.image.load('sd.png')

divider = pygame.Surface((320, 2))
pygame.draw.line(divider, (30, 102, 96), (0, 0), (320, 0), 2)

touch_screen = pitft_touchscreen()
touch_screen.start()

screenthread = threading.Thread(target=screen_thread, args=[touch_screen])
screenthread.start()

#scroffthread = threading.Thread(target=screen_off_thread)
#scroffthread.start()

# Motion Sensor
#pir = MotionSensor(14)
#pir.when_motion = motion_trigger

motion_trigger()

