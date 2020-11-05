import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy
from skimage import morphology, filters, segmentation, restoration, color, util, measure
from math import sqrt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider, QLCDNumber, QLabel, QPushButton
from PyQt5.QtCore import Qt

def compute_all_cell_bbox_overlaps(cells):
    """ Computes the overlaps of the bounding boxes containing cells. """
    for i in range(len(cells) - 1):
        cell1 = cells[i]
        for j in range(i + 1, len(cells)):
            cell2 = cells[j]

            if cell1.bbox_overlaps_with_other_bbox(cell2):
                cell1.overlapping_bboxes.append(cell2)
            if cell2.bbox_overlaps_with_other_bbox(cell1):
                cell2.overlapping_bboxes.append(cell1)


def compute_cell_contours(binary_image, bio_objects, image):
    """ Takes a binary image and corresponding bounding boxes and returns a list of
        cell contours, [np.array]"""

    # filter out nanowires
    cells = []
    for obj in bio_objects:
        if obj.is_cell():
            cells.append(obj)

    # finds areas inside cells to start ballooning
    compute_all_cell_bbox_overlaps(cells)
    for cell in cells:
        cell.get_cell_center(image)

    for cell in cells:
        if cell.overlapping_bboxes == []:
            continue
        cell.compute_cell_contour(image)

    return

    # old way

    binary_image = util.img_as_float(binary_image)

    for i, cell in enumerate(cells):
        if cell.overlapping_bboxes == []:
            continue
        print("contouring cell #{} of {}".format(i, len(cells)))
        # computes the number of iterations for the contour method to grow --
        # based on the size of the diagonal of the bounding box multiplied by a scalar
        iterations = int(sqrt(cell.width() ** 2 + cell.height() ** 2) / 2.5)
        ils = np.zeros(binary_image.shape, dtype=np.uint8)
        (x, y) = cell.cell_center
        ils[y - 1:y + 1, x - 1:x + 1] = 1
        # finds the contour and stores them
        cell.contour = segmentation.morphological_geodesic_active_contour(binary_image, iterations, init_level_set=ils, smoothing=1, balloon=1)
