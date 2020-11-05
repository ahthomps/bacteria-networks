""" classes.py
    Here, we define the BioObject and Tile classes.
"""

from copy import deepcopy
import numpy as np
from skimage import measure, filters, morphology, color
import matplotlib.pyplot as plt

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
