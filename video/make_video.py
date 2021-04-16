import sys
import os
import tempfile
import contextlib
import shutil
from ffmpy import FFmpeg

"""
Main function
"""
def main(image_dir):

  # Work with a temporary directory
  with make_temp_directory() as tmpdir:

    # Get all the jpg files in the folder
    image_list = (f for f in sorted(os.listdir(image_dir)) if f.endswith('.jpg'))

    last_image = None
    image_count = 0
    for img_file in image_list:
      image_count += 1
      last_image = img_file
      shutil.copy(os.path.join(image_dir, img_file), \
        os.path.join(tmpdir, f'{image_count:05d}.jpg'))

    ff = FFmpeg(
      inputs={f'{os.path.join(tmpdir, "%5d.jpg")}': None},
      outputs={f'{image_dir}.mp4': None}
    )

    ff.run()

@contextlib.contextmanager
def make_temp_directory():
  temp_dir = tempfile.mkdtemp()
  try:
    yield temp_dir
  finally:
    pass
    #shutil.rmtree(temp_dir)

# Print usage message and quits
def usage():
  print('Usage: make_video <image_dir>')
  exit()

# Script run
if __name__ == '__main__':
  if len(sys.argv) < 2:
    usage()

  image_dir = sys.argv[-1]
  if not os.path.isdir(image_dir):
    print(f'{image_dir} is not a directory')
    exit()

  main(os.path.dirname(image_dir))