import sys
import os
import tempfile
import contextlib
import shutil
from ffmpy import FFmpeg
import toml
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from multiprocessing import Pool
from itertools import repeat
"""
Main function
"""
def main(config, image_dir):

  # Work with a temporary directory
  with make_temp_directory() as tmpdir:

    # Get all the jpg files in the folder
    start_image = f'{os.path.basename(image_dir)}{config["range"]["start"]}00.jpg'
    end_image = f'{os.path.basename(image_dir)}{config["range"]["end"]}59.jpg'

    image_list = list(f for f in sorted(os.listdir(image_dir)) \
      if f >= start_image and f <= end_image)

    image_indices = range(0, len(image_list))

    pool = Pool()
    pool.starmap(process_image, \
      zip(repeat(config), repeat(image_dir), repeat(tmpdir), image_list, image_indices))

    pool.close()

    ff = FFmpeg(
      global_options='-y',
      inputs={f'{os.path.join(tmpdir, "%5d.jpg")}': None},
      outputs={f'{image_dir}.mp4': '-c:v libx264 -profile:v high -pix_fmt yuv420p -g 25 -r 25'}
    )

    ff.run()

def process_image(config, indir, outdir, file, index):

  try:
    img = Image.open(os.path.join(indir, file))
    id = ImageDraw.Draw(img)

    if config['commandline']['timestamp']:
      fillFont = ImageFont.truetype(config['main']['timestamp_font'], 30)
      shadowFont = ImageFont.truetype(config['main']['timestamp_font'], 30)

      timeText=f'{file[8:10]}:{file[10:12]}'

      xpos = img.size[0] - 117
      ypos = img.size[1] - 40

      id.text((xpos + 3, ypos + 3), timeText, font=shadowFont, fill=(0, 0, 0))
      id.text((xpos, ypos), timeText, font=fillFont, fill=(255, 255, 255))

    if config['commandline']['small']:
      img = img.resize((1280,720))

    img.save(os.path.join(outdir, f'{index:05d}.jpg'))
  except:
    pass


@contextlib.contextmanager
def make_temp_directory():
  temp_dir = tempfile.mkdtemp()
  try:
    yield temp_dir
  finally:
    shutil.rmtree(temp_dir)

# Print usage message and quits
def usage():
  print('Usage: make_video [-small] [-timestamp] [-start hhmm] [-end hhmm] <image_dir>')
  exit()

def check_time(hhmm):

  ok = True

  if len(hhmm) != 4:
    ok = False

  if ok:
    hours = int(hhmm[0:2])
    if hours < 0 or hours > 23:
      ok = False


  if ok:
    minutes = int(hhmm[2:4])
    if minutes < 0 or minutes > 59:
      ok = False

  if not ok:
    print(f'Invalid time \'{hhmm}\'')
  return ok

# Script run
if __name__ == '__main__':
  if len(sys.argv) < 2:
    usage()

  image_dir = sys.argv[-1]
  if not os.path.isdir(image_dir):
    print(f'{image_dir} is not a directory')
    exit()

  config = toml.load('config.toml')
  config['commandline'] = {
    'small': False,
    'timestamp': False
  }
  config['range'] =  {
    'start': '0000',
    'end': '2359'
  }

  argindex = 1
  while argindex < len(sys.argv) - 1:
    arg = sys.argv[argindex]

    if arg == '-small':
      config['commandline']['small'] = True
      argindex += 1
    elif arg == '-timestamp':
      config['commandline']['timestamp'] = True
      argindex += 1
    elif arg == '-start':
      time = sys.argv[argindex + 1]
      if check_time(time):
        config['range']['start'] = time
      else:
        usage()
      argindex += 2
    elif arg == '-end':
      time = sys.argv[argindex + 1]
      if check_time(time):
        config['range']['end'] = time
      else:
        usage()
      argindex += 2
    else:
      usage()

  if config['range']['start'] >= config['range']['end']:
    print(f'Start must be before end')
    exit()

  main(config, os.path.dirname(f'{image_dir}/'))