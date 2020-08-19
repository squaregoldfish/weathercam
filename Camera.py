
import os
import time
from datetime import datetime
import threading
from picamera import PiCamera

class Camera(object):
  def __init__(self, config, info):

    self.SLEEP = 0
    self.CAPTURE = 1
    self.PROCESS = 2

    self._config = config
    self._info = info

    # Initialise camera
    self._camera = PiCamera()
    self._camera.resolution = (4000, 3000)

    self._last_image = None
    self._set_mode()

    self.__camerathread = threading.Thread(target=self._camera_thread)
    self.__camerathread.start()


  def _set_mode(self):
    dawn = self._info.dawn()
    dusk = self._info.dusk()
    now = self._info.time()

    if now >= dawn and now <= dusk:
      self.mode = self.CAPTURE
    else:
      if self.mode == self.CAPTURE:
        self.mode = self.PROCESS
      else:
        self.mode = self.SLEEP

  def _camera_thread(self):

    while True:
      if self.mode == self.SLEEP:
        time.sleep(60)
      elif self.mode == self.CAPTURE:
        self._capture_image()
        time.sleep(10)
      else:
        self._process_images()
        self._info.calctimerange()

      self._set_mode()

  def _capture_image(self):
    filename = self._get_filename()
    self._camera.capture(filename)
    self._last_image = filename

  def _process_images(self):
    print("Process")

  def _get_filename(self):
    image_dir = self._get_today_dir()
    if not os.path.exists(image_dir):
      os.makedirs(image_dir)

    return os.path.join(image_dir, "{}.jpg".format(datetime.now().strftime('%Y%m%d%H%M%S')))

  def _get_today_dir(self):
    return os.path.join(self._config['images']['local'], "{}".format(datetime.now().strftime('%Y%m%d')))
