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
    image_list = list(f for f in sorted(os.listdir(image_dir)) if f.endswith('.jpg'))
    image_indices = range(0, len(image_list))

    pool = Pool()
    pool.starmap(process_image, \
      zip(repeat(config), repeat(image_dir), repeat(tmpdir), image_list, image_indices))

    pool.close()

    ff = FFmpeg(
      global_options='-y',
      inputs={f'{os.path.join(tmpdir, "%5d.jpg")}': None},
      outputs={f'{image_dir}.mp4': None}
    )

    ff.run()

def process_image(config, indir, outdir, file, index):

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


@contextlib.contextmanager
def make_temp_directory():
  temp_dir = tempfile.mkdtemp()
  try:
    yield temp_dir
  finally:
    shutil.rmtree(temp_dir)

# Print usage message and quits
def usage():
  print('Usage: make_video [-small] [-timestamp] <image_dir>')
  exit()

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

  argindex = 1
  while argindex < len(sys.argv) - 1:
    arg = sys.argv[argindex]

    if arg == '-small':
      config['commandline']['small'] = True
      argindex += 1
    elif arg == '-timestamp':
      config['commandline']['timestamp'] = True
      argindex += 1
    else:
      usage()

  main(config, os.path.dirname(image_dir))