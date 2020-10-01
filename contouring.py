import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy
from skimage import morphology, filters, exposure, segmentation, restoration, color, util, measure
from skimage.viewer import ImageViewer
from scipy import ndimage as ndi
import sys
import math
from classes import *

def erode_and_dilate(image, erode, dilate):
    """ Performs erosions and dialations on an image and returns processed
        image."""
    image_open = image
    for _ in range(erode):
        image_open = morphology.erosion(image_open)
    for _ in range(dilate):
        image_open = morphology.dilation(image_open)

    return image_open

def process_image(image, threshold=None, openings=None, initial_dilations=None):
    """ Takes original image (np.array) and option of numbers for threshold and
        number of openings. Returns an binary image (np.array type np.int8)"""

    # converts from RBG to grayscale image
    image_gray = color.rgb2gray(image)

    # creates binary image
    if threshold is None:
        # finds threshold using Yen technique
        threshold = filters.threshold_yen(deepcopy(image_gray))
    image_binary = image_gray > threshold

    if openings is None:
        # default number of openings
        openings = 7
    if initial_dilations is None:
        # default number of inital dilations
        initial_dilations = 4

    # filling any in the cells -- seems to work better than the fill_holes method
    image_binary = erode_and_dilate(image_binary, 0, initial_dilations)
    image_binary = erode_and_dilate(image_binary, initial_dilations, 0)

    # performs opening to reduce noise around cells
    image_binary = erode_and_dilate(image_binary, openings, openings)

    return image_binary.astype(np.int8)

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

            # A.overlaps(B) finds the number of corners of A that are in B
            points_in_box2 = box1.overlaps(box2)
            points_in_box1 = box2.overlaps(box1)
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
        ils = np.zeros(image.shape, dtype=np.int8)
        ils[box.y1 + y - 1:box.y1 + y + 1, box.x1 + x - 1:box.x1 + x + 1] = 1
        initial_level_sets.append(ils)

    return initial_level_sets

def contour(image_binary, bounding_boxes):
    """ Takes a binary image and corresponding bounding boxes and returns a list of
        cell contours, [np.array]"""
    contours = []
    # finds areas inside cells to start ballooning
    initial_level_sets = find_balloon_ils(image_binary, bounding_boxes)
    image_binary = util.img_as_float(image_binary)

    for i in range(len(bounding_boxes)):
        box = bounding_boxes[i]
        ils = initial_level_sets[i]
        # computes the number of iterations for the contour method to grow --
        # based on the size of the diagonal of the bounding box multiplied by a scalar
        iterations = int(math.sqrt(box.width() ** 2 + box.height() ** 2) // 2.5)
        # finds the contour and stores them
        contours.append(segmentation.morphological_geodesic_active_contour(image_binary, iterations, init_level_set=ils, smoothing=1, balloon=1))

    return contours
