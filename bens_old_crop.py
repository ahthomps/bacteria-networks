from PIL import Image
from sys import argv, stderr, exit
from os import listdir, makedirs
from random import random

WIDTH = HEIGHT = 416

if len(argv) != 2:
    print("USAGE: python3 crop.py <directoryectory>")
    exit(1)

directory = argv[1]
try:
    imgs = listdir(directory)
except:
    print(f"Can't list directory {directory}.", file=stderr)
    exit(1)


makedirs(f"{directory}/train", exist_ok=True)
makedirs(f"{directory}/test", exist_ok=True)

test_txt = open(f"{directory}/test/test.txt", "w")
train_txt = open(f"{directory}/train/train.txt", "w")

count = 0
for img in imgs:
    try:
        im = Image.open(f"{directory}/{img}")
    except:
        print(f"Can't open image {img}", file=stderr)
        continue

    for r in range(0, im.size[1], HEIGHT // 2):
        for c in range(0, im.size[0], WIDTH // 2):
            crop = im.crop((r, c, r + WIDTH, c + HEIGHT))
            seg = "train" if random() > .1 else "test"
            img_name = f"{img[:img.find('.')]}_crop_{r}_{c}.jpg"
            crop.save(f"{directory}/{img_name}", "JPEG", subsampling=0, quality=100)
            if seg == "train":
                train_txt.write(f"{directory}/{img_name}\n")
            else:
                test_txt.write(f"{directory}/{img_name}\n")
            count += 1
            if count > 300:
                exit(0)
