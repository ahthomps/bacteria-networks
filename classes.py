""" classes.py
    Here, we define the Cell and Tile classes.
"""

from copy import deepcopy
import numpy as np
from skimage import measure

class Cell:
    def __init__(self, x1, y1, x2, y2, classification="cell"):
        """ Represents a cell found by YOLO.
            x1, y1, x2, y2: px coordinates of xmin xmax ymin ymax of bounding box.
            classification: the classification of this cell. This will eventually have to change. """
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self._contour = None
        self._classification = classification
        self._cell_center = (0, 0)
        # list of the INDICES adjacent cells in the cells list
        self._adj_list = []

    def width(self):
        """ Returns the width of this cell. """
        return self.x2 - self.x1

    def height(self):
        """ Returns the height of this cell. """
        return self.y2 - self.y1

    def center(self):
        """ Returns the center of this cell. """
        return self.x1 + self.width() / 2, self.y1 + self.height() / 2

    # On the chopping block
    def corners(self):
        """ Returns the corners of this cell. """
        return (self.x1, self.y1), (self.x2, self.y1), (self.x2, self.y2), (self.x1, self.y2)

    # Also on the chopping block
    def corners_contained_in(self, box):
        """ Returns the number of this Cell's corners that are contained in box. """
        overlapped_corners = 0
        for x, y in self.corners():
            if box.x1 <= x <= box.x2 and box.y1 <= y <= box.y2:
                overlapped_corners += 1
        return overlapped_corners

    def contains_point(self, pt):
        """ Returns whether pt is in the bounding box. """
        x, y = pt
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def overlaps(self, other):
        """ Returns True if overlaps, False otherwise"""
        return int(self.x1) < int(other.x2) and int(other.x1) < int(self.x2) \
           and int(self.y1) < int(other.y2) and int(other.y1) < int(self.y2)

    def get_cell_center(self, binary_image, overlaps):
        """ adapted code from contouring.py, finds some point in a cell """
        image_working = deepcopy(binary_image)
        # removes all other cells so only bright spots are cell in question
        for overlap_box in overlaps:
            image_working[overlap_box.y1:overlap_box.y2 + 1, overlap_box.x1:overlap_box.x2 + 1] = 0

        # creates an np.array image of just the current bbox
        subimage = np.asarray(image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])
        # finds connected bright regions (foreground)
        labels_mask = measure.label(subimage, connectivity=2)
        # determines quantitative properties of each region of brightness
        regions = measure.regionprops(labels_mask)
        # sorts the regions, largest area to smallest
        regions.sort(key=lambda x: x.area, reverse=True)
        # take the region with largest area and find its center
        y, x = map(int, regions[0].centroid) # subimage ils bbox
        # find cell center in original image
        self._cell_center = (self.x1 + x, self.y1 + y)

    # This might also be on the chopping block.
    def subimage(self, image):
        """ Returns the subset of the image within the bounding box as an np.array """
        return np.asarray(image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])

    # This is useful for cropping training data. Should be in a separate script
    def to_relative(self, width, height):
        """ Converts pixel data to data relative to size of the image"""
        self.x1 /= width
        self.x2 /= width
        self.y1 /= height
        self.y2 /= height

class Tile:
    def __init__(self, img, x1, y1, x2, y2, filename):
        """ img:            The cropped PIL Image object.
            x1, y1, x2, y2: The position of this tile in the larger image.
            filename:       A unique identifier for this tile. (No file extension) """

        self.img = img
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        # This will store all the (potentially partial) bounding boxes that overlap this tile.
        # Their coordinates are relative to this tile.
        # (i.e. if a bounding box starts on the left edge of this tile, its x1 is 0)
        self.cells = []

        # This will be used as a unique identifier for this crop.
        self.filename = f"{filename}_{self.x1}_{self.y1}"

    def width(self):
        """ Returns width of bounding box"""
        return self.x2 - self.x1

    def height(self):
        """ Returns height of bounding box"""
        return self.y2 - self.y1

    def center(self):
        """ Returns center of bounding box"""
        return self.x1 + self.width() / 2, self.y1 + self.height() / 2

    def add_bounding_box(self, box):
        """ box: A bounding box with coordinates relative to the untiled image. """
        box = deepcopy(box)
        box.x1 = max(box.x1, self.x1) - self.x1
        box.y1 = max(box.y1, self.y1) - self.y1
        box.x2 = min(box.x2, self.x2) - self.x1
        box.y2 = min(box.y2, self.y2) - self.y1
        self.cells.append(box)

    # This is useful for cropping training data. Should be in a separate script
    def to_relative(self):
        """ Converts bounding boxes to image relative values. """
        for box in self.cells:
            box.to_relative(self.width(), self.height())

    # This is useful for cropping training data. Should be in a separate script
    def save(self, directory="."):
        """ Saves this tile as a cropped image and an associated label file.
            Note: This will convert bounding boxes to relative, because that's how YOLO likes it. """
        self.img.save(f"{directory}/{self.filename}.jpg", "JPEG", subsampling=0, quality=100)

        if self.cells != []:
            self.to_relative()
            ofile = open(f"{directory}/{self.filename}.txt", "w")
            for cell in self.cells:
                ofile.write(f"{cell.classification} {cell.center()[0]} {cell.center()[1]} {cell.width()} {cell.height()}\n")
            ofile.close()
