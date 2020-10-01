# This script takes an image and associated yolo labels, then crops the image into 416x416 tiles
# with 50% vertical and horizontal overlap, preserving the labels.

import sys
from PIL import Image
from copy import deepcopy
from os import listdir
from classes import *

TILE_OVERLAP = 2 # 2 -> 50% overlap, 3 -> 33% overlap, etc.
TILE_SIZE = 416
IMAGE_EXTENSIONS = (".tiff", ".tif", ".png", ".jpg", ".jpeg", ".gif")

def make_crops(img, filename):
    tiles = []
    for r in range(0, img.height, TILE_SIZE // TILE_OVERLAP):
        for c in range(0, img.width, TILE_SIZE // TILE_OVERLAP):
            x1, y1, x2, y2 = (r, c, r + TILE_SIZE, c + TILE_SIZE)
            tiles.append(Tile(img.crop((x1, y1, x2, y2)), x1, y1, x2, y2, filename))

    return tiles


def make_labeled_crops(input_dir, output_dir):
    """ input_dir:  Directory containing uncropped images and associated labels
        output_dir: Directory in which we will dump all the crops and their labels. """
    files = listdir(input_dir)
    for filename in files:
        if any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
            # The filename of the image
            image_filename = f"{input_dir}/{filename}"

            # The filename of the image without an extension
            filename = filename[:filename.rfind(".")]

            # Ignore images with no label files
            if f"{filename}.txt" not in files:
                continue

            # The filename of the label file
            label_filename = f"{input_dir}/{filename}.txt"

            # Open the files
            img = Image.open(image_filename)
            labels = open(label_filename)

            # Make the BoundingBox objects
            bounding_boxes = parse_yolo_input(labels)

            # Convert them to px
            for box in bounding_boxes:
                box.to_px(img.width, img.height)

            # Tile the image
            tiles = make_crops(img, filename)

            # Convert the bounding boxes to fit the tiles.
            for tile in tiles:
                for box in bounding_boxes:
                    if box.overlaps(tile):
                        tile.add_bounding_box(box)

            # Save the tiles and their bounding boxes
            for tile in tiles:
                tile.to_relative_bounding_boxes()
                tile.save(output_dir)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("USAGE: python3 parse_yolo_file.py <input_directory> <output_directory>", file=sys.stderr)
        sys.exit(1)

    make_labeled_crops(*sys.argv[1:])
