# Screen control
import os, time
from datetime import datetime
import threading
import pygame
from pygame.locals import *

class Screen(object):
  def __init__(self, config, info, camera):

    self._WHITE = (255, 255, 255)
    self._CYAN = (0, 255, 255)
    self._PURPLE = (153, 51, 255)
    self._RED = (255, 0, 0)
    self._BLUE = (39, 93, 163)
    self._YELLOW = (255, 255, 0)
    self._ORANGE = (255, 128, 0)
    self._GREY = (128, 128, 128)

    self._TEXT = 0
    self._IMAGE = 1

    self._config = config
    self._info = info
    self._camera = camera

    self._lcdsize = (320, 240)
    self._textsurface = None
    self._imagesurface = None
    self._currentpage = self._TEXT

    self._currentimage = None


    os.putenv('SDF_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

    pygame.init()
    pygame.font.init()
    self._font = pygame.font.Font(self._config['screen']['font'], 33)
    self._smallfont = pygame.font.Font(self._config['screen']['font'], 18)
    pygame.mouse.set_visible(False)
    self._screen = pygame.display.set_mode(self._lcdsize)

    # Initialise fixed UI components
    self._uptime_icon = pygame.image.load('uptime.png')
    self._cputemp_icon = pygame.image.load('cpu.png')
    self._microsd_icon = pygame.image.load('microsd.png')
    self._nas_icon = pygame.image.load('nas.png')
    self._temp_icon = pygame.image.load('temperature.png')
    self._rain_icon = pygame.image.load('rain.png')
    self._clock_icon = pygame.image.load('clock.png')
    self._hourglass_icon = pygame.image.load('hourglass.png')
    self._reload_icon = pygame.image.load('reload.png')
    self._dawn_icon = pygame.image.load('sunrise.png')
    self._dusk_icon = pygame.image.load('sunset.png')
    self._capture_icon = pygame.image.load('capture.png')
    self._upload_icon = pygame.image.load('upload.png')
    self._sleep_icon = pygame.image.load('sleep.png')

    self._divider = pygame.Surface((320, 2))
    pygame.draw.line(self._divider, (30, 102, 96), (0, 0), (320, 0), 2)


    self._imagesurface = self._font.render('Image', True, (255,0,0))

    self.__eventthread = threading.Thread(target=self._event_thread)
    self.__eventthread.start()

    self.__screenthread = threading.Thread(target=self._screen_thread)
    self.__screenthread.start()

  def _switch_page(self):
    if self._currentpage == self._TEXT:
      self._currentpage = self._IMAGE
    else:
      self._currentpage = self._TEXT

  def _event_thread(self):
    while True:
      event = pygame.event.wait()
      if event.type is MOUSEBUTTONUP:
        self._switch_page()
        time.sleep(0.1)
        pygame.event.clear()
      time.sleep(0.1)

  def _screen_thread(self):
    while True:
      if self._currentpage == self._TEXT:
        self._draw_text()
      else:
        self._draw_image()

      pygame.display.flip()
      time.sleep(1)

  def _draw_text(self):
    self._screen.fill((0,0,0))

    # Current Time
    timesurface = self._font.render(self._format_date(self._info.time()), True, (255,255,255))
    self._screen.blit(timesurface, (0, 0))

    # Uptime
    uptimesurface = self._font.render(self._format_delta(self._info.uptime()), True, (0, 255, 255))
    self._screen.blit(self._uptime_icon, (0, 33))
    self._screen.blit(uptimesurface, (33, 29))

    # CPU temp & disk space
    self._screen.blit(self._cputemp_icon, (0, 66))
    cputempsurface = self._font.render("{:6.1f}°C".format(self._info.cputemp()), True, self._PURPLE)
    self._screen.blit(cputempsurface, (33, 62))

    self._screen.blit(self._microsd_icon, (188, 66))
    localspacesurface = self._font.render("{:4.1f}Gb".format(self._info.localspace() / 1073741824), True, self._PURPLE)
    self._screen.blit(localspacesurface, (221, 62))

    # Divider
    self._screen.blit(self._divider, (0, 100))

    # Weather
    self._screen.blit(self._temp_icon, (0, 108))
    tempsurface = self._font.render('{:6.1f}°C'.format(self._info.outdoortemp()), True, self._RED)
    self._screen.blit(tempsurface, (33, 104))

    self._screen.blit(self._rain_icon, (188, 108))
    rainsurface = self._font.render('{:4.1f}mm'.format(self._info.rain()), True, self._BLUE)
    self._screen.blit(rainsurface, (221, 104))

    self._screen.blit(self._clock_icon, (0, 142))
    weathertimesurface = self._font.render('{}'.format(self._format_time(self._info.outdoortemptime())), True, self._GREY)
    self._screen.blit(weathertimesurface, (33, 138))

    weatherupdateicon = self._reload_icon if self._info.weatherupdating() else self._hourglass_icon
    self._screen.blit(weatherupdateicon, (188, 142))
    tempupdatesurface = self._font.render('{}'.format(self._min_sec(self._info.outdoortempnextupdatedelta())), True, self._GREY)
    self._screen.blit(tempupdatesurface, (238, 138))

    # Divider
    self._screen.blit(self._divider, (0, 176))

    # Dawn/Dusk
    self._screen.blit(self._dawn_icon, (154, 181))
    dawnsurface = self._font.render(self._format_time(self._info.dawn()), True, self._YELLOW)
    self._screen.blit(dawnsurface, (187, 177))

    self._screen.blit(self._dusk_icon, (154, 214))
    dusksurface = self._font.render(self._format_time(self._info.dusk()), True, self._ORANGE)
    self._screen.blit(dusksurface, (187, 210))

    if self._camera.mode == self._camera.SLEEP:
      self._screen.blit(self._sleep_icon, (45, 181))
    elif self._camera.mode == self._camera.CAPTURE:
      self._screen.blit(self._capture_icon, (45, 181))
    elif self._camera.mode == self._camera.PROCESS:
      self._screen.blit(self._upload_icon, (45, 181))


  def _draw_image(self):
    #self._screen.fill((0,0,0))
    #imagesurface = self._smallfont.render('Image preview disabled', True, (255,255,0))
    #self._screen.blit(imagesurface, (5, 215))
    today_images = os.listdir(self._info.get_today_dir())
    today_images.sort()
    image_name = today_images[-2]
    image_file = os.path.join(self._info.get_today_dir(), image_name)
    if image_file != self._currentimage:
      image = pygame.image.load(image_file)
      image = pygame.transform.scale(image, (320, 240))
      self._screen.blit(image, (0,0))
      self._currentimage = image_file
      self._imagesurface = self._smallfont.render(image_name, True, (255,255,0))
      self._screen.blit(self._imagesurface, (5, 215))

  def _format_date(self, date):
    return date.strftime('%Y-%m-%d %H:%M:%S')

  def _format_time(self, date):
    return date.strftime('%H:%M:%S')

  def _min_sec(self, delta):
    return datetime.utcfromtimestamp(delta.total_seconds()).strftime('%M:%S')

  def _format_delta(self, delta):
    result = ''
    if delta.days > 0:
      result = '{}d '.format(delta.days)

    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    result += '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

    return result