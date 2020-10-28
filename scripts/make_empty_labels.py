import os
import sys

if len(sys.argv) != 3:
    print("USAGE: python3 make_empty_labels.py <image_directory> <label_directory>", file=sys.stderr)
    sys.exit(1)

image_dir = sys.argv[1]
label_dir = sys.argv[2]

preexisting_labels = set(os.listdir(label_dir))

for file in os.listdir(image_dir):
    file = file[:file.index(".")]
    if file + ".txt" not in preexisting_labels:
        label_file = open(label_dir + "/" + file + ".txt", "w")
        label_file.write("\n")
        label_file.close()