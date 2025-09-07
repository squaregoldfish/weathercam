import argparse
from datetime import datetime, timedelta
import os
import cv2
import numpy as np

parser = argparse.ArgumentParser(description='Check the image coverage for a day')
parser.add_argument('expected_timestep', help='The expected interval between images', type=int)
parser.add_argument('folder', help='The folder of images. Assumed to be YYYYMMDD.')

args = parser.parse_args()

image_count = int(86400 / args.expected_timestep)

start_time = datetime.strptime(f'{args.folder}000000', '%Y%m%d%H%M%S')
end_time = datetime.strptime(f'{args.folder}235959', '%Y%m%d%H%M%S')
step = timedelta(seconds=args.expected_timestep)


frames = [False] * image_count

current_frame = 0
current_time = start_time
while current_time <= end_time:
    if os.path.exists(f'{args.folder}/{args.folder}{current_time.strftime("%H%M%S")}.jpg'):
        frames[current_frame] = True

    current_time += step
    current_frame += 1

present = sum(frames)
missing = image_count - present

print(f'Present {present} ({present / image_count * 100:.1f} %)')
print(f'Missing {missing} ({missing / image_count * 100:.1f} %)')

# Now make an image
pixels = np.zeros((1, image_count, 3), np.uint8)
for i in range(image_count):
    pixels[:, i, :] = [0, 255, 0] if frames[i] else [0, 0, 255]

image = cv2.resize(pixels, (image_count, 720), interpolation=cv2.INTER_LINEAR)
cv2.imwrite(f'{args.folder}.png', image)
