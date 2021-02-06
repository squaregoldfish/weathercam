#!/bin/bash

# Start mjpg_streamer
mjpg_streamer -i "input_uvc.so -f 5 -r 1920x1080 -q 98" -o "output_http.so -w /usr/local/share/mjpg-streamer/www" &

# Detach mjpg_streamer so it keeps running after our session is shut down
disown -h `pgrep mjpg_streamer`
