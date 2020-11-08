from copy import deepcopy
import numpy as np
from skimage import measure, filters, morphology, color
import matplotlib.pyplot as plt

# This is the allowable distance betwen objects to count them as overlapping
# Having it as a hardcoded value is really just asking for trouble, but we're doing it for now.
OVERLAP_TOLERANCE = 10

def compute_all_cell_bbox_overlaps(bio_objects):
    """ Computes the overlaps of the bounding boxes containing cells. """
    for i in range(len(bio_objects) - 1):
        cell1 = bio_objects[i]
        if not cell1.is_cell():
            continue

        for j in range(i + 1, len(bio_objects)):
            cell2 = bio_objects[j]
            if not cell2.is_cell():
                continue

            if cell1.bbox_overlaps_with_other_bbox(cell2):
                cell1.overlapping_bboxes.append(cell2)
            if cell2.bbox_overlaps_with_other_bbox(cell1):
                cell2.overlapping_bboxes.append(cell1)


def compute_nanowire_to_cell_bbox_overlaps(bio_objects):
    """ Computes the overlaps between nanowires and cells. Stores the overlaps in the nanowire
        objects only. """
    for nanowire in bio_objects:
        if not nanowire.is_nanowire():
            continue
        for cell in bio_objects:
            # only looking at nanowire to cell overlaps, skip nanowires
            if not cell.is_cell():
                continue

            # want overlaps where nanowire and cell partially overlap or cell completely overlaps nanowire
            if nanowire.bbox_overlaps_with_other_bbox(cell) or nanowire.bbox_is_contained_in_other_bbox(cell):
                nanowire.overlapping_bboxes.append(cell)


def compute_cell_center(bio_obj, image):
    """ finds some point in the cell"""
    placeholder_image = np.zeros(image.shape, dtype=np.uint8)

    subimage = np.asarray(image[bio_obj.y1:bio_obj.y2 + 1, bio_obj.x1:bio_obj.x2 + 1])

    threshold = filters.threshold_li(subimage)
    subimage = subimage > threshold

    placeholder_image[bio_obj.y1:bio_obj.y2 + 1, bio_obj.x1:bio_obj.x2 + 1] = subimage

    for overlap_box in bio_obj.overlapping_bboxes:
        placeholder_image[overlap_box.y1:overlap_box.y2 + 1, overlap_box.x1:overlap_box.x2 + 1] = 0

    if np.any(placeholder_image[bio_obj.y1:bio_obj.y2 + 1, bio_obj.x1:bio_obj.x2 + 1]):
        subimage = placeholder_image[bio_obj.y1:bio_obj.y2 + 1, bio_obj.x1:bio_obj.x2 + 1]

    # finds connected bright regions (foreground)
    labels_mask = measure.label(subimage, connectivity=2)
    # determines quantitative properties of each region of brightness
    regions = measure.regionprops(labels_mask)
    # sorts the regions, largest area to smallest
    regions.sort(key=lambda x: x.area, reverse=True)
    # take the region with largest area and find its center
    y, x = map(int, regions[0].centroid) # subimage ils bbox
    # find cell center in original image
    bio_obj.cell_center = (bio_obj.x1 + x, bio_obj.y1 + y)


def compute_subimage_labels_and_region_data(bio_obj, image):
    # creates an np.array image of just the current bbox
    subimage = np.asarray(image[bio_obj.y1:bio_obj.y2 + 1, bio_obj.x1:bio_obj.x2 + 1])
    plt.imshow(subimage, cmap='gray')
    # makes the image binary using li thresholding method
    threshold = filters.threshold_li(subimage) # we should test if li is actually the best method in all lighting environments
    subimage = subimage > threshold
    if bio_obj.is_cell():
        subimage = morphology.erosion(subimage)
        subimage = morphology.dilation(subimage)
    subimage_labels = measure.label(subimage, connectivity=2)
    subimage_regions = measure.regionprops(subimage_labels)

    return subimage_labels, subimage_regions


def compute_contour(bio_obj, image):
    assert not bio_obj.is_surface()

    subimage_labels, subimage_regions = compute_subimage_labels_and_region_data(bio_obj, image)

    if bio_obj.is_cell():
        bio_obj_region_label = max(subimage_regions, key=lambda x: x.area).label
    elif bio_obj.is_nanowire():
        bio_obj_region_label = max(subimage_regions, key=lambda x: x.bbox_area).label
    else:
        raise ValueError("What is this BioObject?")
    subimage_contour = subimage_labels == bio_obj_region_label
    contour = np.zeros(image.shape, dtype=np.uint8)
    contour[bio_obj.y1:bio_obj.y2 + 1, bio_obj.x1:bio_obj.x2 + 1] = subimage_contour
    bio_obj.contour = contour


class BioObject:
    def __init__(self, x1, y1, x2, y2, id_no, classification="cell"):
        """ Represents an object found by YOLO. (and also the electrode)
            x1, y1, x2, y2: px coordinates of xmin xmax ymin ymax of bounding box.
            classification: the classification of this object. This will eventually have to change. """
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

    def bbox_is_contained_in_other_bbox(self, other):
        """ Returns True if bbox is in given other bbox, False otherwise"""
        return int(self.x1) < int(other.x2) and int(other.x1) < int(self.x2) \
           and int(self.y1) < int(other.y2) and int(other.y1) < int(self.y2)

    def bbox_overlaps_with_other_bbox(self, other):
        """ Returns True if the bboxes of self and other overlap, False otherwise """

        x1 = self.x1 - OVERLAP_TOLERANCE
        x2 = self.x2 + OVERLAP_TOLERANCE
        y1 = self.y1 - OVERLAP_TOLERANCE
        y2 = self.y2 + OVERLAP_TOLERANCE

        for point in other.compute_corners():
            x, y = point
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True

        # other intersects through top and/or bottom of self
        if (x1 <= other.x1 <= x2 or x1 <= other.x2 <= x2) and other.y1 <= y1 <= y2 <= other.y2:
            return True
        # other intersects through right and/or
        elif (y1 <= other.y1 <= y2 or y1 <= other.y2 <= y2) and other.x1 <= x1 <= x2 <= other.x2:
            return True
        elif x1 <= other.x1 <= other.x2 <= x2 and y1 <= other.y1 <= other.y2 <= y2:
            return True

        return False

    def __str__(self):
        return f"{self.classification}: {self.x1} {self.y1} {self.x2} {self.y2}"
