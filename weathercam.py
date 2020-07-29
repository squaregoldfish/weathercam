#!/usr/bin/python3
import os
import time, datetime
import toml
from Info import Info

def format_date(date):
  return date.strftime('%Y-%m-%d %H:%M:%S %Z')





#### Here we go

with open('config.toml', 'r') as f:
  config = toml.loads(f.read())

info = Info(config)

while True:
  os.system('clear')
  print("Time:                     {}".format(format_date(info.time())))
  print("Uptime:                   {}".format(info.uptime()))
  print("Dawn:                     {}".format(format_date(info.dawn())))
  print("Dusk:                     {}".format(format_date(info.dusk())))
  print("CPU Temp:                 {:.1f}°C".format(info.cputemp()))
  print("Outdoor Temp:             {:.1f}°C".format(info.outdoortemp()))
  print("Outdoor Temp Time:        {}".format(format_date(info.outdoortemptime())))
  print("Outdoor Temp Last Update: {}".format(format_date(info.outdoortemplastupdate())))
  print("Outdoor Temp Next Update: {}".format(format_date(info.outdoortempnextupdate())))
  print("Outdoor Temp Next Update: {}".format(info.outdoortempnextupdatedelta()))
  print("Outdoor Temp Updating:    {}".format(info.outdoortempupdating()))
  time.sleep(0.9)
