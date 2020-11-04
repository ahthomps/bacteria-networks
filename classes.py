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
        self.classification = classification
        self.cell_center = (0, 0)
        self.contour = None
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

    def compute_subimage_labels_and_region_data(self, image):
        # creates an np.array image of just the current bbox
        subimage = np.asarray(image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])
        # makes the image binary using li thresholding method
        threshold = filters.threshold_li(subimage)
        subimage = subimage > threshold
        if self.is_cell():
            subimage = morphology.erosion(subimage)
            subimage = morphology.dilation(subimage)
        self.subimage_labels = measure.label(subimage, connectivity=2)
        self.subimage_regions = measure.regionprops(self.subimage_labels)

    def get_cell_center(self, image):
        """ finds some point in the cell"""
        placeholder_image = np.zeros(image.shape, dtype=np.uint8)

        subimage = np.asarray(image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])

        threshold = filters.threshold_li(subimage)
        subimage = subimage > threshold

        placeholder_image[self.y1:self.y2 + 1, self.x1:self.x2 + 1] = subimage

        for overlap_box in self.overlapping_bboxes:
            placeholder_image[overlap_box.y1:overlap_box.y2 + 1, overlap_box.x1:overlap_box.x2 + 1] = 0

        if np.any(placeholder_image[self.y1:self.y2 + 1, self.x1:self.x2 + 1]):
            subimage = placeholder_image[self.y1:self.y2 + 1, self.x1:self.x2 + 1]

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


    def compute_cell_contour(self, image):
        assert(self.is_cell() and self.subimage_labels is not None)
        # subimage = np.asarray(image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])
        # subimage_binary_plot = plt.imshow(subimage, cmap='gray')
        # plt.show()
        # fig, ax = filters.try_all_threshold(subimage, figsize=(10, 8), verbose=False)
        # plt.show()

        # subimage = np.asarray(image[self.y1:self.y2 + 1, self.x1:self.x2 + 1])
        # threshold = filters.threshold_li(subimage)
        # subimage = subimage > threshold
        # subimage = morphology.erosion(subimage)
        # subimage = morphology.dilation(subimage)
        # subimage_binary_plot = plt.imshow(subimage, cmap='gray')
        # plt.show()
        #
        # labels_mask = measure.label(subimage, connectivity=2)
        # image_labels_plt = plt.imshow(labels_mask, cmap='gray')
        # plt.show()
        # regions = measure.regionprops(labels_mask)
        self.subimage_regions.sort(key=lambda x: x.area, reverse=True)
        largest_region_label = self.subimage_regions[0].label
        subimage_contour = self.subimage_labels == largest_region_label
        # largest_region_plt = plt.imshow(largest_region, cmap='gray')
        # plt.show()
        contour = np.zeros(image.shape, dtype=np.uint8)

        # contour[self.y1:self.y1 + len(largest_region), self.x1:self.x1 + len(largest_region[0])] = regions[0].image
        contour[self.y1:self.y2 + 1, self.x1:self.x2 + 1] = subimage_contour
        self.contour = contour

    def compute_nanowire_contour(self, image):
        assert(self.is_nanowire() and self.subimage_labels is not None)
        self.subimage_regions.sort(key=lambda x: x.bbox_area, reverse=True)
        nanowire_label = self.subimage_regions[0].label
        subimage_contour = self.subimage_labels == nanowire_label
        contour = np.zeros(image.shape, dtype=np.uint8)
        contour[self.y1:self.y2 + 1, self.x1:self.x2 + 1] = subimage_contour
        self.contour = contour



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
