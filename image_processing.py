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


class SliderWidget(QWidget):
    """ Sliders are used for user-interactive image processing. The binary image
    that's created by default is normally quite good, but this allows for tweaking"""
    def __init__(self, parent=None, mgr=None, dmgr=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle('Image Processing Options')

        # This is a hack
        if parent is not None:
            return

        self.prgmmgr = mgr
        self.dmgr = dmgr

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
        self.prgmmgr.compute_binary_image()
        self.dmgr.MplWidget.draw_image(self.prgmmgr.binary_image)

    def update_dilations(self, event):
        """ Responds to changes of the dilations slider """
        self.dilationsLCD.display(event)
        self.prgmmgr.dilations = event
        self.prgmmgr.compute_binary_image()
        self.dmgr.MplWidget.draw_image(self.prgmmgr.binary_image)

    def update_threshold(self, event):
        """ Responds to changes of the threshold slider """
        self.thresholdLCD.display(event / 100)
        self.prgmmgr.threshold = event / 100
        self.prgmmgr.compute_binary_image()
        self.dmgr.MplWidget.draw_image(self.prgmmgr.binary_image)

    def restore_defaults(self, event):
        """ This is a hack and should be fixed. """
        self.update_dilations(DEFAULT_DILATIONS)
        self.update_openings(DEFAULT_OPENINGS)
        self.prgmmgr.threshold = None
        self.prgmmgr.compute_binary_image()
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
