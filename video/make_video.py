import argparse
import contextlib
import os
import shutil
import tempfile
from itertools import repeat
from multiprocessing import Pool

import toml
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from ffmpy import FFmpeg


def main(conf, image_dir):
    """
    Main function
    """

    # Work with a temporary directory
    with make_temp_directory() as tmp_dir:
        # Get all the jpg files in the folder
        start_image = f'{os.path.basename(image_dir)}{conf["range"]["start"]}00.jpg'
        end_image = f'{os.path.basename(image_dir)}{conf["range"]["end"]}59.jpg'

        image_list = list(f for f in sorted(os.listdir(image_dir)) if start_image <= f <= end_image)

        image_indices = range(0, len(image_list))

        pool = Pool()
        pool.starmap(process_image, zip(repeat(conf), repeat(image_dir), repeat(tmp_dir), image_list, image_indices))
        pool.close()

        ff = FFmpeg(
            global_options='-y',
            inputs={f'{os.path.join(tmp_dir, "%5d.jpg")}': None},
            outputs={f'{image_dir}.mp4': '-c:v libx264 -profile:v high -pix_fmt yuv420p -g 25 -r 25'}
        )

        ff.run()


def process_image(conf, in_dir, out_dir, file, index):
    try:
        img = Image.open(os.path.join(in_dir, file))
        img_draw = ImageDraw.Draw(img)

        if conf['commandline']['timestamp']:
            fill_font = ImageFont.truetype(conf['main']['timestamp_font'], 30)
            shadow_font = ImageFont.truetype(conf['main']['timestamp_font'], 30)

            time_text = f'{file[8:10]}:{file[10:12]}'

            x_pos = img.size[0] - 117
            y_pos = img.size[1] - 40

            img_draw.text((x_pos + 3, y_pos + 3), time_text, font=shadow_font, fill=(0, 0, 0))
            img_draw.text((x_pos, y_pos), time_text, font=fill_font, fill=(255, 255, 255))

        if conf['commandline']['small']:
            img = img.resize((1280, 720))

        img.save(os.path.join(out_dir, f'{index:05d}.jpg'))
    except Exception as e:
        print(e)
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
    config = toml.load('config.toml')
    config['commandline'] = {
        'small': False,
        'timestamp': False
    }
    config['range'] = {
        'start': '0000',
        'end': '2359'
    }

    parser = argparse.ArgumentParser(description='Make video from captured images')
    parser.add_argument('-small', action='store_true', help='Generate a 720p video')
    parser.add_argument('-timestamp', action='store_true', help='Add a timestamp to the video')
    parser.add_argument('-start', dest='start', help='Start time (hhmm)')
    parser.add_argument('-end', dest='end', help='End time (hhmm)')
    parser.add_argument('img_dir')

    args = parser.parse_args()
    config['commandline']['small'] = args.small
    config['commandline']['timestamp'] = args.timestamp

    if args.start is not None:
        if check_time(args.start):
            config['range']['start'] = args.start
        else:
            print('Invalid start time')
            exit()

    if args.end is not None:
        if check_time(args.end):
            config['range']['end'] = args.end
        else:
            print('Invalid end time')
            exit()

    if config['range']['start'] >= config['range']['end']:
        print(f'Start must be before end')
        exit()

    main(config, os.path.dirname(f'{args.img_dir}/'))
