# This script takes an image and associated yolo labels, then crops the image into 416x416 tiles with 50% vertical and horizontal overlap, preserving the labels.

import sys
from PIL import Image
from copy import deepcopy

TILE_OVERLAP = 2 # 2 -> 50% overlap, 3 -> 33% overlap, etc.
TILE_SIZE = 416

class Box:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

class Tile(Box):
    def __init__(self, crop, x1, y1, x2, y2):
        """ crop:           The cropped PIL Image object.
            x1, y1, x2, y2: The position of this tile in the larger image. """
        super().__init__(x1, y1, x2, y2)
        self.crop = crop

        # This will store all the (potentially partial) bounding boxes that overlap this tile.
        # Their coordinates are relative to this tile.
        # (i.e. if a bounding box starts on the left edge of this tile, its x1 is 0)
        self.bounding_boxes = []

        # This will be used as a unique identifier for this crop.
        self.filename = f"{self.x1}_{self.y1}"

    def add_bounding_box(self, box):
        box = deepcopy(box)
        box.x1 = max(box.x1, self.x1) - self.x1
        box.y1 = max(box.y1, self.y1) - self.y1
        box.x2 = min(box.x2, self.x2) - self.x1
        box.y2 = min(box.y2, self.y2) - self.y1
        self.bounding_boxes.append(box)

    def to_relative_bounding_boxes(self):
        for box in self.bounding_boxes:
            box.to_relative(TILE_SIZE, TILE_SIZE)

    def save(self, directory="."):
        self.crop.save(f"{directory}/{self.filename}.jpg", "JPEG", subsampling=0, quality=100)
        ofile = open(f"{directory}/{self.filename}.txt", "w")
        for box in self.bounding_boxes:
            ofile.write(f"{box.classification} {box.x1} {box.y1} {box.x2} {box.y2}\n")
        ofile.close()



class BoundingBox(Box):
    def __init__(self, classification, x1, y1, x2, y2):
        """ classification: A number representing a YOLO classification
            x1, y1, x2, y2: Floats between 0 and 1 representing a relative position. """
        super().__init__(x1, y1, x2, y2)
        self.classification = int(classification)
        self.in_px = False

    def to_px(self, width, height):
        self.x1 *= width
        self.x2 *= width
        self.y1 *= height
        self.y2 *= height
        self.in_px = True

    def to_relative(self, width, height):
        self.x1 /= width
        self.x2 /= width
        self.y1 /= height
        self.y2 /= height
        self.in_px = False

    def overlaps(self, box):
        assert self.in_px
        return any(box.x1 < x < box.x2 and box.y1 < y < box.y2 \
           for (x,y) in [(self.x1,self.y1), (self.x1,self.y2), (self.x2,self.y1), (self.x2,self.y2)])
        


def parse_yolo_input(label_file):
    """ Reads from a yolo training file and returns a list of BoundingBox objects.
        Also takes the labels' image so we can convert from relative to px. """
    bounding_boxes = []
    for line in label_file.readlines():
        # Ignore comments
        if "#" in line:
            line = line[:line.index("#")]
        if line.split() == []:
            continue

        bounding_boxes.append(BoundingBox(*map(float, line.split())))

    return bounding_boxes

def main(image_filename, label_filename, output_dir):
    im = Image.open(image_filename)
    labels = open(label_filename)
    
    # Make the BoundingBox objects
    bounding_boxes = parse_yolo_input(labels)

    # Convert them to px
    for box in bounding_boxes:
        box.to_px(im.width, im.height)

    tiles = []
    for r in range(0, im.height, TILE_SIZE // TILE_OVERLAP):
        for c in range(0, im.width, TILE_SIZE // TILE_OVERLAP):
            x1, y1, x2, y2 = (r, c, r + TILE_SIZE, c + TILE_SIZE)
            tile = Tile(im.crop((x1, y1, x2, y2)), x1, y1, x2, y2)
            for box in bounding_boxes:
                if box.overlaps(tile):
                    tile.add_bounding_box(box)
            tiles.append(tile)

    for tile in tiles:
        tile.to_relative_bounding_boxes()
        tile.save(output_dir)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("USAGE: python3 parse_yolo_file.py <image_file> <label_file> <output_directory>", file=sys.stderr)
        sys.exit(1)

    main(*sys.argv[1:])

# TO DO:
# Batch processing
# Cropping of bottom (maybe not even necessary...)