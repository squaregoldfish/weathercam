# Holds data for the info screen and image overlays
import time
from datetime import datetime
from datetime import timedelta
import threading
import shutil
from astral import LocationInfo
from astral.sun import sun
from gpiozero import CPUTemperature
import pytz
from uptime import uptime
import netatmo

class Info(object):
  def __init__(self, config):

    self._config = config

    # Reference objects
    self._timezone = config['location']['timezone']
    self._tz = pytz.timezone(config['location']['timezone'])
    self._cpu_temp = CPUTemperature()
    self._location = LocationInfo('Weathercam', 'Weathercam', config['location']['timezone'], config['location']['latitude'], config['location']['longitude'])

    # Dawn/Dusk
    self._dawn = datetime.fromtimestamp(0, tz=self._tz)
    self._dusk = datetime.fromtimestamp(0, tz=self._tz)
    self.calctimerange()

    # Netatmo retrieval
    self._weather = {
      'temp': -99,
      'rain': 0,
      'data_time': datetime.fromtimestamp(0, tz=self._tz),
      'last_update': datetime.fromtimestamp(0, tz=self._tz),
      'next_update': datetime.now(tz=self._tz),
      'updating': True
    }
    self.__weather_thread = threading.Thread(target=self._weather_thread, args=(config,))
    self.__weather_thread.start()

  def time(self):
    return datetime.now(tz=self._tz)

  def uptime(self):
    return timedelta(seconds=round(uptime()))

  def cputemp(self):
    return self._cpu_temp.temperature

  def localspace(self):
    dummy, dummy2, space = shutil.disk_usage(self._config['images']['local'])
    return space

  def dawn(self):
    return self._dawn

  def dusk(self):
    return self._dusk

  def calctimerange(self):
    suninfo = sun(self._location.observer, date=datetime.now(), tzinfo=self._location.timezone)
    self._dawn = suninfo['dawn']
    self._dusk = suninfo['dusk']

  def outdoortemp(self):
    return self._weather['temp']

  def rain(self):
    return self._weather['rain']

  def outdoortemptime(self):
    return self._weather['data_time']

  def outdoortemplastupdate(self):
    return self._weather['last_update']

  def outdoortempnextupdate(self):
    return self._weather['next_update']

  def outdoortempnextupdatedelta(self):
    diff = self._weather['next_update'] - datetime.now(tz=self._tz)
    if self._weather['updating'] or diff < timedelta(seconds=0):
      diff = timedelta(seconds=0)

    return diff

  def weatherupdating(self):
    return self._weather['updating']

  def _weather_thread(self, config):
    while True:

      self._weather['updating'] = True

      ws = netatmo.WeatherStation({
        'client_id': config['netatmo']['client_id'],
        'client_secret': config['netatmo']['client_secret'],
        'username': config['netatmo']['username'],
        'password': config['netatmo']['password'],

      })

      ws.get_data()

      for dev in ws.devices:
        if dev['_id'] == config['netatmo']['device']:
          for module in dev['modules']:
            if module['_id'] == config['netatmo']['temp_module']:
              self._weather['temp'] = module['dashboard_data']['Temperature']
              data_time = module['dashboard_data']['time_utc']
              self._weather['data_time'] = datetime.fromtimestamp(data_time, tz=self._tz)
              self._weather['last_update'] = datetime.now(tz=self._tz)
              self._weather['next_update'] = self._weather['data_time'] + timedelta(minutes=11, seconds=30)
              if self._weather['next_update'] < self._weather['last_update']:
                self._weather['next_update'] = datetime.now(tz=self._tz) + timedelta(seconds=15)

            elif module['_id'] == config['netatmo']['rain_module']:
              self._weather['rain'] = module['dashboard_data']['sum_rain_24']


      self._weather['updating'] = False

      while datetime.now(tz=self._tz) < self._weather['next_update']:
        time.sleep(1)
