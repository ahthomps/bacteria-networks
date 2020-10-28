""" classes.py
    Here, we define the BioObject and Tile classes.
"""

from copy import deepcopy
import numpy as np
from skimage import measure

class NetworkEdge:
    def __init__(self, tail, head, nanowire=None):
        self.tail = tail
        self.head = head
        self.type = ""
        self.nanowire = nanowire

    def set_type_as_cell_contact(self):
        self.type = "cell_contact"

    def set_type_as_cell_to_cell(self):
        self.type = "cell_to_cell"

    def set_type_as_cell_to_surface(self):
        self.type = "cell_to_surface"

    def type_is_cell_contact(self):
        return self.type == "cell_contact"

    def type_is_cell_to_cell(self):
        return self.type == "cell_to_cell"

    def type_is_cell_to_surface(self):
        return self.type == "cell_to_surface"

    def __str__(self):
        return f"{self.type}: {self.tail.id} {self.head.id}"


class BioObject:
    def __init__(self, x1, y1, x2, y2, id_no, classification="cell"):
        """ Represents a cell found by YOLO.
            x1, y1, x2, y2: px coordinates of xmin xmax ymin ymax of bounding box.
            classification: the classification of this cell. This will eventually have to change. """
        self.id = id_no
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.contour = None
        self.classification = classification
        self.cell_center = (0, 0)
        # list of the adjacent cells in the cells list
        self.adj_list = []
        # list of the edges this cell participates in
        self.edge_list = []
        self.overlapping_bboxes = []

    def is_cell(self):
        return self.classification == "cell"

    def is_nanowire(self):
        return self.classification == "nanowire"

    def is_surface(self):
        return self.classification == "surface"

    def has_contour(self):
        return self.contour is not None

    def width(self):
        """ Returns the width of this cell. """
        return self.x2 - self.x1

    def height(self):
        """ Returns the height of this cell. """
        return self.y2 - self.y1

    def center(self):
        """ Returns the center of this cell. """
        return self.x1 + self.width() / 2, self.y1 + self.height() / 2

    def compute_corners(self):
        """ Returns a list the corner coordinates of the bounding box containing this cell. """
        return [(self.x1, self.y1), (self.x2, self.y1), (self.x2, self.y2), (self.x1, self.y2)]

    def bbox_is_contained_in_tile(self, tile):
        """ Returns True if bbox is in given Tile, False otherwise"""
        return int(self.x1) < int(tile.x2) and int(tile.x1) < int(self.x2) \
           and int(self.y1) < int(tile.y2) and int(tile.y1) < int(self.y2)

    def bbox_overlaps_with_other_bbox(self, other):
        """ Returns True if the bboxes of self and other overlap, False otherwise """
        if (other.x1 <= self.x1 <= self.x2 <= other.x2 and other.y1 <= self.y1 <= self.y2 <= other.y2):
            return False, True
        for point in other.compute_corners():
            x, y = point
            if self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2:
                return True, False

        # other intersects through top and/or bottom of self
        if (self.x1 <= other.x1 <= self.x2 or self.x1 <= other.x2 <= self.x2) and other.y1 <= self.y1 <= self.y2 <= other.y2:
            return True, False
        # other intersects through right and/or
        elif (self.y1 <= other.y1 <= self.y2 or self.y1 <= other.y2 <= self.y2) and other.x1 <= self.x1 <= self.x2 <= other.x2:
            return True, False
        elif self.x1 <= other.x1 <= other.x2 <= self.x2 and self.y1 <= other.y1 <= other.y2 <= self.y2:
            return True, False

        return False, False

    def get_cell_center(self, binary_image):
        """ adapted code from contouring.py, finds some point in a cell """
        image_working = deepcopy(binary_image)
        # removes all other cells so only bright spots are cell in question
        for overlap_box in self.overlapping_bboxes:
            image_working[overlap_box.y1:overlap_box.y2 + 1, overlap_box.x1:overlap_box.x2 + 1] = 0

        # creates an np.array image of just the current bbox
        subimage = np.asarray(image_working[self.y1:self.y2 + 1, self.x1:self.x2 + 1])
        # if cell completely overlapped by other bboxes, use binary_image
        if not subimage.any():
            subimage = np.asarray(binary_image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])
        # finds connected bright regions (foreground)
        labels_mask = measure.label(subimage, connectivity=2)
        # determines quantitative properties of each region of brightness
        regions = measure.regionprops(labels_mask)
        # sorts the regions, largest area to smallest
        regions.sort(key=lambda x: x.area, reverse=True)
        # take the region with largest area and find its center
        y, x = map(int, regions[0].centroid) # subimage ils bbox
        # find cell center in original image
        self.cell_center = (self.x1 + x, self.y1 + y)

    def __str__(self):
        return f"{self.classification}: {self.x1} {self.y1} {self.x2} {self.y2}"

class Tile:
    def __init__(self, img, x1, y1, x2, y2, filename_no_ext):
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
        self.filename_no_ext = f"{filename_no_ext}_{self.x1}_{self.y1}"

    def width(self):
        """ Returns width of bounding box"""
        return self.x2 - self.x1

    def height(self):
        """ Returns height of bounding box"""
        return self.y2 - self.y1

    def center(self):
        """ Returns center of bounding box"""
        return self.x1 + self.width() / 2, self.y1 + self.height() / 2

    def add_cell(self, cell):
        """ box: A bounding box with coordinates relative to the untiled image. """
        cell = deepcopy(cell)
        cell.x1 = max(cell.x1, self.x1) - self.x1
        cell.y1 = max(cell.y1, self.y1) - self.y1
        cell.x2 = min(cell.x2, self.x2) - self.x1
        cell.y2 = min(cell.y2, self.y2) - self.y1
        self.cells.append(cell)

    def save(self, directory="."):
        """ Saves this tile as a cropped image and (potentially) an associated label file.
            Note: This will convert bounding boxes to relative, because that's how YOLO likes it. """
        self.img.save(f"{directory}/{self.filename_no_ext}.jpg", "JPEG", subsampling=0, quality=100)
