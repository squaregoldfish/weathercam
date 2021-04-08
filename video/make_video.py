import sys
import os
import cv2

image_dir = sys.argv[1]

if not os.path.isdir(image_dir):
  print('Must supply a directory')
  exit()

image_list = sorted(os.listdir(image_dir))

# Get image info
frame = cv2.imread(os.path.join(image_dir, image_list[0]))
height, width, layers = frame.shape

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
video = cv2.VideoWriter(f'{image_dir}.mp4', fourcc, 25, (width, height))

for image in image_list:
  video.write(cv2.imread(os.path.join(image_dir, image)))

cv2.destroyAllWindows()
video.release()
