""" contouring.py
    Here we define the function for image processing, the QtWidget to manually process the image,
    and methods to contour the cells.
"""
import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy
from skimage import morphology, filters, segmentation, restoration, color, util, measure
from math import sqrt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider, QLCDNumber, QLabel, QPushButton
from PyQt5.QtCore import Qt

MIN_OPENINGS = 0
MAX_OPENINGS = 20
DEFAULT_OPENINGS = 7

MIN_DILATIONS = 0
MAX_DILATIONS = 20
DEFAULT_DILATIONS = 4

MIN_THRESHOLD = 0
MAX_THRESHOLD = 100
DEFAULT_THRESHOLD = 50

def erode_and_dilate(image, erode, dilate):
    """ Performs erosions and dilations on an image and returns processed
        image."""
    image_open = image
    for _ in range(erode):
        image_open = morphology.erosion(image_open)
    for _ in range(dilate):
        image_open = morphology.dilation(image_open)

    return image_open

def process_image(image, openings=DEFAULT_OPENINGS, initial_dilations=DEFAULT_DILATIONS, threshold=None):
    """ Takes original image (np.array) and option of numbers for threshold and
        number of openings. Returns an binary image (np.array type np.uint8) and the binary threshold. """

    # converts from RBG to grayscale image
    image_gray = color.rgb2gray(image)

    # creates binary image
    if threshold is None:
        # finds threshold using Yen technique
        threshold = filters.threshold_yen(deepcopy(image_gray))

    binary_image = image_gray > threshold

    # filling any holes in the cells -- seems to work better than the fill_holes method
    binary_image = erode_and_dilate(binary_image, 0, initial_dilations)
    binary_image = erode_and_dilate(binary_image, initial_dilations, 0)

    # performs opening to reduce noise around cells
    binary_image = erode_and_dilate(binary_image, openings, openings)

    return binary_image.astype(np.uint8), threshold

def get_bbox_overlaps(bounding_boxes):
    """ Takes a list of Box objects and returns a list of the overlaps of each
        box. The overlaps of bounding_boxes[i] are in overlaps[i]. """
    overlaps = [[] for _ in range(len(bounding_boxes))]

    for i in range(len(bounding_boxes) - 1):
        box1 = bounding_boxes[i]
        for j in range(i + 1, len(bounding_boxes)):
            box2 = bounding_boxes[j]

            # note: if there exists some box1 that is totally inside a box2,
            #       overlaps[box1] does NOT include box2 -- I chose to do this
            #       because when looking for balloon start I don't want to
            #       subtract all of box1 (what I'm looking for)

            # A.corners_contained_in(B) returns the number of corners of A that are in B
            points_in_box2 = box1.corners_contained_in(box2)
            points_in_box1 = box2.corners_contained_in(box1)
            # if Box1 is completely inside Box2, only add Box1 as overlap of Box2 --
            # don't add Box2 to Box1 because when subtracting overlapping boxes this would make all of Box1 black
            if points_in_box2 == 4:
                overlaps[j].append(box1)
            # similar to above
            elif points_in_box1 == 4:
                overlaps[i].append(box2)
            # add as overlapping each other if not completely overlapping
            elif points_in_box1 or points_in_box2:
                overlaps[i].append(box2)
                overlaps[j].append(box1)

    return overlaps

def find_balloon_ils(image, bounding_boxes):
    """ Takes the binary image and the bounding_boxes to find some set in the middle
        of cells to start ballooning. Returns a list of these initial level sets."""

    initial_level_sets = []
    # find overlaps of bboxes
    overlaps = get_bbox_overlaps(bounding_boxes)

    for i in range(len(bounding_boxes)):
        image_working = deepcopy(image)
        box = bounding_boxes[i]

        # removes all other cells so only bright spots are cell in question
        for overlap_box in overlaps[i]:
            image_working[overlap_box.y1:overlap_box.y2 + 1, overlap_box.x1:overlap_box.x2 + 1] = 0

        # creates an np.array image of just the current bbox
        subimage = box.subimage(image_working)
        # finds connected bright regions (foreground)
        labels_mask = measure.label(subimage, connectivity=2)
        # determines quantitative properties of each region of brightness
        regions = measure.regionprops(labels_mask)
        # sorts the regions, largest area to smallest
        regions.sort(key=lambda x: x.area, reverse=True)
        # take the region with largest area and find its center
        y, x = map(int, regions[0].centroid) # subimage ils bbox

        # create a 2x2 ils in the center of the largest region (map back to original image size)
        ils = np.zeros(image.shape, dtype=np.uint8)
        ils[box.y1 + y - 1:box.y1 + y + 1, box.x1 + x - 1:box.x1 + x + 1] = 1
        initial_level_sets.append(ils)

    return initial_level_sets

def contour(binary_image, bounding_boxes):
    """ Takes a binary image and corresponding bounding boxes and returns a list of
        cell contours, [np.array]"""
    contours = []
    # finds areas inside cells to start ballooning
    initial_level_sets = find_balloon_ils(binary_image, bounding_boxes)
    binary_image = util.img_as_float(binary_image)

    for i in range(len(bounding_boxes)):
        box = bounding_boxes[i]
        ils = initial_level_sets[i]
        # computes the number of iterations for the contour method to grow --
        # based on the size of the diagonal of the bounding box multiplied by a scalar
        iterations = int(sqrt(box.width() ** 2 + box.height() ** 2) / 2.5)
        # finds the contour and stores them
        contours.append(segmentation.morphological_geodesic_active_contour(binary_image, iterations, init_level_set=ils, smoothing=1, balloon=1))

    return contours

class SliderWidget(QWidget):
    """ Sliders are used for user-interactive image processing. The binary image
    that's created by default is normally quite good, but this allows for tweaking"""
    def __init__(self, parent=None, mgr=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle('Image Processing Options')

        if parent is not None:
            return

        self.prgmmgr = mgr

        self.layout = QVBoxLayout()

        # Initialize Openings Slider
        make_centered_label(self.layout, "Openings")
        self.openingsLCD = QLCDNumber()
        self.layout.addWidget(self.openingsLCD)
        make_slider(self.update_openings, self.layout, MIN_OPENINGS, MAX_OPENINGS, self.prgmmgr.openings)

        # Initialize Dilations Slider
        make_centered_label(self.layout, "Dilations")
        self.dilationsLCD = QLCDNumber()
        self.layout.addWidget(self.dilationsLCD)
        make_slider(self.update_dilations, self.layout, MIN_DILATIONS, MAX_DILATIONS, self.prgmmgr.dilations)

        # Initialize Threshold Slider
        make_centered_label(self.layout, "Binary threshold")
        self.thresholdLCD = QLCDNumber()
        self.layout.addWidget(self.thresholdLCD)
        make_slider(self.update_threshold, self.layout, MIN_THRESHOLD, MAX_THRESHOLD, self.prgmmgr.threshold * 100)

        # Save New Image Processing Options
        b1 = QPushButton("Restore Defaults")
        b1.clicked.connect(self.restore_defaults)
        self.layout.addWidget(b1)

    def update_openings(self, event):
        """ Responds to changes of the opening slider """
        self.openingsLCD.display(event)
        self.prgmmgr.openings = event
        self.prgmmgr.get_processed_image()

    def update_dilations(self, event):
        """ Responds to changes of the dilations slider """
        self.dilationsLCD.display(event)
        self.prgmmgr.dilations = event
        self.prgmmgr.get_processed_image()

    def update_threshold(self, event):
        """ Responds to changes of the threshold slider """
        self.thresholdLCD.display(event / 100)
        self.prgmmgr.threshold = event / 100
        self.prgmmgr.get_processed_image()

    def restore_defaults(self, event):
        """ This is a hack and should be fixed. """
        self.update_dilations(DEFAULT_DILATIONS)
        self.update_openings(DEFAULT_OPENINGS)
        self.prgmmgr.threshold = None
        self.prgmmgr.get_processed_image()
        self.update_threshold(self.prgmmgr.threshold * 100)


def make_slider(action, layout, minn, maxx, default):
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(minn)
    slider.setMaximum(maxx)
    slider.setTickPosition(QSlider.TicksBelow)
    slider.valueChanged.connect(action)
    slider.setValue(default)

    layout.addWidget(slider)

def make_centered_label(layout, text):
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)

    layout.addWidget(label)
