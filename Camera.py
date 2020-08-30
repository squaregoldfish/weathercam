import os, shutil
import time
from datetime import datetime
from datetime import timedelta
import threading
from picamera import PiCamera
import requests
import pysftp

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
    self.mode = None
    self._set_mode()

    self.__camerathread = threading.Thread(target=self._camera_thread)
    self.__camerathread.start()

  def _set_mode(self):
    dawn = self._info.dawn()
    dusk = self._info.dusk()
    now = self._info.time()

    old_mode = self.mode
    mode_message = None

    if now >= dawn and now <= dusk:
      self.mode = self.CAPTURE
      mode_message = 'Start Capture'
    else:
      if self.mode == self.CAPTURE:
        self.mode = self.PROCESS
        mode_message = 'Uploading files'
      else:
        self.mode = self.SLEEP
        mode_message = 'Sleeping'

    if old_mode != self.mode:
      self._send_message(mode_message)

  def _camera_thread(self):

    while True:
      if self.mode == self.SLEEP:
        time.sleep(60)
      elif self.mode == self.CAPTURE:
        self._capture_image()
        time.sleep(10)
      else:
        self._process_images()

        # Calculate the time range for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=1)
        self._info.calctimerange(tomorrow)

      self._set_mode()

  def _capture_image(self):
    filename = self._get_filename()
    self._camera.capture(filename)
    self._last_image = filename

  def _process_images(self):
    remote = self._config['remote']
    src_dir = self._info.get_today_dir()
    dest_dir = os.path.join(remote['dir'], os.path.split(self._info.get_today_dir())[1])

    try:
      with pysftp.Connection(remote['server'], username=remote['user'], password=remote['password']) as sftp:
        with sftp.cd(remote['dir']):
          if not sftp.exists(os.path.split(dest_dir)[1]):
            sftp.mkdir(os.path.split(dest_dir[1]))

          sftp.put_d(src_dir, dest_dir, preserve_mtime=True)

        # Delete the local folder only if the upload succeeded
        shutil.rmtree(src_dir)
    except Exception as e:
      self._send_message('PROCESSING ERROR: {}'.format(e))

  def _get_filename(self):
    image_dir = self._info.get_today_dir()
    if not os.path.exists(image_dir):
      os.makedirs(image_dir)

    return os.path.join(image_dir, "{}.jpg".format(datetime.now().strftime('%Y%m%d-%H%M%S')))

  def _send_message(self, message):
    print("Message {}".format(message))
    requests.post(self._config['remote']['message_url'], data={'value1': message})