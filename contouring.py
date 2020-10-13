import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy
from skimage import morphology, filters, segmentation, restoration, color, util, measure
from math import sqrt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider, QLCDNumber, QLabel, QPushButton
from PyQt5.QtCore import Qt

def compute_all_bbox_overlaps(cells):
    """ Computes the overlaps of the bounding boxes containing cells. """
    for i in range(len(cells) - 1):
        cell1 = cells[i]
        for j in range(i + 1, len(cells)):
            cell2 = cells[j]

            if cell1.bbox_overlaps_with_other_bbox(cell2):
                cell1._overlapping_bboxes.append(cell2)
            if cell2.bbox_overlaps_with_other_bbox(cell1):
                cell2._overlapping_bboxes.append(cell1)


def compute_cell_contours(binary_image, cells):
    """ Takes a binary image and corresponding bounding boxes and returns a list of
        cell contours, [np.array]"""

    # finds areas inside cells to start ballooning
    compute_all_bbox_overlaps(cells)
    for cell in cells:
        cell.get_cell_center(binary_image)
    # initial_level_sets = find_balloon_ils(binary_image, bounding_boxes)
    binary_image = util.img_as_float(binary_image)

    for cell in cells:
        print(cell._overlapping_bboxes)
        # computes the number of iterations for the contour method to grow --
        # based on the size of the diagonal of the bounding box multiplied by a scalar
        iterations = int(sqrt(cell.width() ** 2 + cell.height() ** 2) / 2.5)
        ils = np.zeros(binary_image.shape, dtype=np.uint8)
        (x, y) = cell._cell_center
        ils[y - 1:y + 1, x - 1:x + 1] = 1
        # finds the contour and stores them
        cell._contour = segmentation.morphological_geodesic_active_contour(binary_image, iterations, init_level_set=ils, smoothing=1, balloon=1)
