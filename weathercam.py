#!/usr/bin/python3
import os
import time, datetime
import toml
from Info import Info
from Screen import Screen

def format_date(date):
  return date.strftime('%Y-%m-%d %H:%M:%S %Z')





#### Here we go

with open('config.toml', 'r') as f:
  config = toml.loads(f.read())

info = Info(config)
screen = Screen(config, info)
