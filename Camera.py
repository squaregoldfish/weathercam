
import time
from datetime import datetime
import threading

class Camera(object):
  def __init__(self, config, info):

    self.SLEEP = 0
    self.CAPTURE = 1
    self.PROCESS = 2

    self._config = config
    self._info = info

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
    print("Image")

  def _process_images(self):
    print("Process")