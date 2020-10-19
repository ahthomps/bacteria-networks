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
