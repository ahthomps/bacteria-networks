import os
import random
import sys

if len(sys.argv) != 2:
    print("USAGE: python3 train_test_split.py <model_directory>", file=sys.stderr)
    sys.exit(1)

model_directory = sys.argv[1]

train_txt = open(f"{model_directory}/train.txt", "w")
test_txt = open(f"{model_directory}/test.txt", "w")

for image_filename in os.listdir(f"{model_directory}/images"):
    if random.randint(0,9):
        train_txt.write(image_filename + "\n")
    else:
        test_txt.write(image_filename + "\n")

