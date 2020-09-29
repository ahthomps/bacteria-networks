from PIL import Image
from sys import argv
import os

files = os.listdir(os.getcwd())

cooridinates = [(0,0,416,416),(334,0,750,416),
                (0,334,416,750),(334,334,750,750)]

i = 0
for filename in files:
    if filename != "imageprocessing.py":
        i += 1
        img = Image.open(filename)
        width, height = img.size
        height = 1767 / 1886 * height # this cuts off the bottom bar
        img = img.resize(size=(750,750), box=(0,0,width,height))
        j = 0
        for box in cooridinates:
            j += 1
            new = img.crop(box)
            new.save('im' + str(i) + '-' + str(j) + '.jpg')

