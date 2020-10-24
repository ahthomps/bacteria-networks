# This script takes an image and associated yolo labels, then crops the image into 416x416 tiles
# with 50% vertical and horizontal overlap, preserving the labels.

import sys
from PIL import Image
from copy import deepcopy
from os import listdir

TILE_OVERLAP = 2 # 2 -> 50% overlap, 3 -> 33% overlap, etc.
TILE_SIZE = 416
IMAGE_EXTENSIONS = (".tiff", ".tif", ".png", ".jpg", ".jpeg", ".gif", ".bmp")

class Box:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def width(self):
        return self.x2 - self.x1

    def height(self):
        return self.y2 - self.y1

    def center(self):
        return self.x1 + self.width() / 2, self.y1 + self.height() / 2


class Tile(Box):
    def __init__(self, crop, x1, y1, x2, y2, filename):
        """ crop:           The cropped PIL Image object.
            x1, y1, x2, y2: The position of this tile in the larger image. """
        super().__init__(x1, y1, x2, y2)
        self.crop = crop

        # This will store all the (potentially partial) bounding boxes that overlap this tile.
        # Their coordinates are relative to this tile.
        # (i.e. if a bounding box starts on the left edge of this tile, its x1 is 0)
        self.bounding_boxes = []

        # This will be used as a unique identifier for this crop.
        self.filename = f"{filename}_{self.x1}_{self.y1}"

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
        """ Saves this tile as a cropped image and an associated label file.
            Note: self.bounding_boxes must all be in relative coords for YOLO to like the label output. """
        self.crop.save(f"{directory}/{self.filename}.jpg", "JPEG", subsampling=0, quality=100)
        
        if self.bounding_boxes != []:
            ofile = open(f"{directory}/{self.filename}.txt", "w")
            for box in self.bounding_boxes:
                ofile.write(f"{box.classification} {box.center()[0]} {box.center()[1]} {box.width()} {box.height()}\n")
            ofile.close()


class BoundingBox(Box):
    def __init__(self, classification, x, y, width, height):
        """ classification: A number representing a YOLO classification
            x, y:           Floats between 0 and 1 representing the relative position of this box's center.
            width, height:  Floats representing the relative dimensions of this box. """
        super().__init__(x - width / 2, y - height / 2, x + width / 2, y + height / 2)
        self.classification = int(classification)
        self.in_px = False

    def to_px(self, width, height):
        assert not self.in_px
        self.x1 *= width
        self.x2 *= width
        self.y1 *= height
        self.y2 *= height
        self.in_px = True

    def to_relative(self, width, height):
        assert self.in_px
        self.x1 /= width
        self.x2 /= width
        self.y1 /= height
        self.y2 /= height
        self.in_px = False

    def overlaps(self, box):
        assert self.in_px

        return int(self.x1) < int(box.x2) and int(box.x1) < int(self.x2) \
           and int(self.y1) < int(box.y2) and int(box.y1) < int(self.y2)

        
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
