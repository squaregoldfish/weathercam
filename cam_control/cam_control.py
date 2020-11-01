import socket
import logging

LOG_FILE='/var/log/cam_control.log'
PORT=10570
MJPG_STREAMER_CMD = 'mjpg_streamer -i "input_uvc.so -f 5 -r 1920x1080 -q 98"  -o "output_http.so -w /usr/local/share/mjpg-streamer/www"'

def process_command(command):
  return 'jfdsklfjsdkl'

################################
#
# Start up the server

logging.basicConfig(filename=LOG_FILE, format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.debug('Weathercam control server')
logging.debug('Starting server on port {:d}'.format(PORT))

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', PORT))

s.listen(5)
logging.debug('Server listening')
while True:
  conn, addr = s.accept()
  try:
    command = conn.recv(512).decode("utf-8").strip()
    result = process_command(command)
    logging.info('{:s}: {:s} -> {:s}'.format(str(addr), command, result))
    conn.send(result.encode(encoding='utf_8', errors='strict'))
  except Exception as e:
    logging.error(e)
  finally:
    conn.close()
