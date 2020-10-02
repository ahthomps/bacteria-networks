from copy import deepcopy
import numpy as np
import sys

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

    def corners(self):
        return (self.x1, self.y1), (self.x2, self.y1), (self.x2, self.y2), (self.x1, self.y2)

    def contains_point(self, pt):
        x, y = pt
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def corners_contained_in(self, box):
        """ Returns the number of this Box's corners that are contained in box. """
        overlapped_corners = 0
        for x, y in self.corners():
            if box.x1 <= x <= box.x2 and box.y1 <= y <= box.y2:
                overlapped_corners += 1
        return overlapped_corners

    def subimage(self, image):
        """ returns the subset of the image within the bounding box as an np.array """
        return np.asarray(image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])


class Tile(Box):
    def __init__(self, img, x1, y1, x2, y2, filename):
        """ img:           The cropped PIL Image object.
            x1, y1, x2, y2: The position of this tile in the larger image. """
        super().__init__(x1, y1, x2, y2)
        self.img = img

        # This will store all the (potentially partial) bounding boxes that overlap this tile.
        # Their coordinates are relative to this tile.
        # (i.e. if a bounding box starts on the left edge of this tile, its x1 is 0)
        self.bounding_boxes = []

        # This will be used as a unique identifier for this crop.
        self.filename = f"{filename}_{self.x1}_{self.y1}"

    def add_bounding_box(self, box):
        """ box: A bounding box with coordinates relative to the untiled image. """
        box = deepcopy(box)
        box.x1 = max(box.x1, self.x1) - self.x1
        box.y1 = max(box.y1, self.y1) - self.y1
        box.x2 = min(box.x2, self.x2) - self.x1
        box.y2 = min(box.y2, self.y2) - self.y1
        self.bounding_boxes.append(box)

    def to_relative_bounding_boxes(self):
        for box in self.bounding_boxes:
            if isinstance(box, BoundingBox):
                box.to_relative(self.width(), self.height())

    def save(self, directory="."):
        """ Saves this tile as a cropped image and an associated label file.
            Note: This will convert bounding boxes to relative, because that's how YOLO likes it. """
        self.img.save(f"{directory}/{self.filename}.jpg", "JPEG", subsampling=0, quality=100)

        if self.bounding_boxes != []:
            self.to_relative_bounding_boxes()
            ofile = open(f"{directory}/{self.filename}.txt", "w")
            for box in self.bounding_boxes:
                ofile.write(f"{box.classification} {box.center()[0]} {box.center()[1]} {box.width()} {box.height()}\n")
            ofile.close()

    def to_relative(self, width, height):
        self.x1 /= width
        self.x2 /= width
        self.y1 /= height
        self.y2 /= height

class BoundingBox(Box):
    def __init__(self, classification, x, y, width, height):
        """ classification: A number representing a YOLO classification
            x, y:           Floats between 0 and 1 representing the relative position of this box's center.
            width, height:  Floats representing the relative dimensions of this box. """
        super().__init__(x - width / 2, y - height / 2, x + width / 2, y + height / 2)
        self.classification = int(classification)
        self.in_px = False

    def to_px(self, width, height):
        if self.in_px:
            print("WARNING: BoundingBox already in px.", file=sys.stderr)
            return

        self.x1 = int(self.x1 * width)
        self.x2 = int(self.x2 * width)
        self.y1 = int(self.y1 * height)
        self.y2 = int(self.y2 * height)
        self.in_px = True

    def to_relative(self, width, height):
        if not self.in_px:
            print("WARNING: BoundingBox already in relative.", file=sys.stderr)
            return

        super().to_relative(width, height)
        self.in_px = False

    def overlaps(self, box):
        assert self.in_px
    
        # The reason I int here is to remove the possibility of 0-width overlaps.
        return int(self.x1) < int(box.x2) and int(box.x1) < int(self.x2) \
           and int(self.y1) < int(box.y2) and int(box.y1) < int(self.y2)

def parse_yolo_input(label_file):
    """ Reads from a yolo training file and returns a list of BoundingBox objects.
        Also takes the labels' image so we can convert from relative to px. """
    bounding_boxes = []
    for line in label_file.readlines():
        # Treat #s as comments
        if "#" in line:
            line = line[:line.index("#")]
        if line.split() == []:
            continue

        bounding_boxes.append(BoundingBox(*map(float, line.split())))

    return bounding_boxes

def parse_yolo_output(yolo_output):
    """ Takes a string of stdout from running yolo and returns a list of Box objects."""
    bounding_boxes = []
    for line in yolo_output.splitlines():
        if line.startswith("    BBOX:"):
            line = line[len("    BBOX:"):]
            bounding_boxes.append(Box(*map(int, line.split())))

    return bounding_boxes
