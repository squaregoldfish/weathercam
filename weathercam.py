#!/usr/bin/python3
import os
import time, datetime
import toml
from Info import Info
from Camera import Camera
from Screen import Screen

#### Here we go

with open('config.toml', 'r') as f:
  config = toml.loads(f.read())

info = Info(config)
camera = Camera(config, info)
screen = Screen(config, info, camera)
