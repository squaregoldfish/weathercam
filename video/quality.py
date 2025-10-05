import argparse
import glob
import subprocess
import re
from multiprocessing import Pool
import tqdm
import numpy as np
from matplotlib import pyplot as plt

def get_quality(filename):
    quality = 0

    try:
        # Run ImageMagick identify and get the Quality line if it's there
        identify = subprocess.Popen(('identify', '-verbose', filename),
            stdout=subprocess.PIPE)

        quality_line = subprocess.run(('grep', 'Quality'),
        stdin=identify.stdout, stdout=subprocess.PIPE).stdout.decode('utf-8')

        quality_re = re.compile('.*Quality: ([0-9]+)')
        quality_match = quality_re.match(quality_line)

        if quality_match:
            quality = int(quality_match.group(1))
    except Exception as e:
        print(e)
        pass # Quality remains zero so the camera gets restarted

    return quality

parser = argparse.ArgumentParser(description='Show the quality of captured images')
parser.add_argument('img_dir')
args = parser.parse_args()

images = glob.glob(f'{args.img_dir}/*.jpg', recursive=False)
qualities = [0] * len(images)
image_indices = range(0, len(images))

pool = Pool()
qualities = list(tqdm.tqdm(pool.imap(get_quality, images), total=len(images)))
pool.close()

counts, bins = np.histogram(qualities, bins=100)
plt.stairs(counts, bins)
plt.show()