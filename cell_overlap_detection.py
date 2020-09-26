import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy
from skimage import morphology, filters, exposure, segmentation, restoration, color, util
from skimage.viewer import ImageViewer
from scipy import ndimage as ndi
import sys
import math

def import_image_and_labels(image_filename, bbox_filename):
    image = plt.imread(image_filename)
    # labels = open("labels/{}.txt".format(image_name[image_name.find("/") + 1:image_name.find(".")]))
    labels = open(bbox_filename)

    return image, labels

def show(image, bounding_boxes, yolo_bounding_boxes, snakes):
    fix, ax = plt.subplots(1, 1, figsize=(14, 14))
    ax.imshow(image, cmap='gray')
    ax.axis('off')
    for box in bounding_boxes:
        ax.plot(box[:, 0], box[:, 1], '--b', lw=3)

    for i in range(len(yolo_bounding_boxes)):
        box = yolo_bounding_boxes[i]
        ax.text(box[0], box[1], str(i))

    colors = ['b', 'g', 'r']
    count = 0
    for snake in snakes:
        ax.contour(snake, [0.75], colors=colors[count % len(colors)])
        count += 1

    plt.show()

def get_corners(box_range):
    x_interval = box_range[0]
    y_interval = box_range[1]

    return [(x_interval[0], y_interval[0]), (x_interval[1], y_interval[0]),
            (x_interval[1], y_interval[1]), (x_interval[0], y_interval[1])]

def get_box(resolution, center, width, height):

    top_point = center[1] - (height // 2)
    bottom_point = center[1] + (height // 2)
    left_point = center[0] - (width // 2)
    right_point = center[0] + (width // 2)

    box_range = ((left_point, right_point), (top_point, bottom_point))

    top_p = np.linspace(left_point, right_point, resolution)
    bottom_p = np.linspace(right_point, left_point, resolution)
    left_p = np.linspace(bottom_point, top_point, resolution)
    right_p = np.linspace(top_point, bottom_point, resolution)

    top_points = []
    bottom_points = []
    for _ in range(top_p.size):
        top_points.append(top_point)
        bottom_points.append(bottom_point)
    top_points = np.array(top_points)
    bottom_points = np.array(bottom_points)

    left_points = []
    right_points = []
    for _ in range(left_p.size):
        left_points.append(left_point)
        right_points.append(right_point)
    left_points = np.array(left_points)
    right_points = np.array(right_points)

    top = np.array([top_p, top_points]).T
    bottom = np.array([bottom_p, bottom_points]).T
    left = np.array([left_points, left_p]).T
    right = np.array([right_points, right_p]).T

    return np.concatenate([top, right, bottom, left])[:-1], box_range

def get_bounding_boxes(image, labels):

    bounding_boxes = []
    yolo_bounding_boxes = []
    range_bounding_boxes = []

    # x_max = len(image[0])
    # y_max = len(image)
    # scalars = [x_max, y_max, x_max, y_max]

    # line = labels.readline()
    # while line:
    #     data = line.split()[1:]
    #     for i in range(4):
    #         data[i] = int(float(data[i]) * scalars[i])
    #     yolo_bounding_boxes.append(data)
    #     box, box_range = get_box(50, (data[0], data[1]), data[2], data[3])
    #     bounding_boxes.append(box)
    #     range_bounding_boxes.append(box_range)
    #     line = labels.readline()

    line = labels.readline()
    while line:
        # takes data in the form "% x1 y1 x2 y2"
        data = line.split()[1:]

        width = data[2] - data[0]
        height = data[3] - data[1]
        center = (data[0] + width \\ 2, data[1] + height \\ 2)

        yolo_bounding_boxes.append([center[0], center[1], width, height])
        box, box_range = get_box(50, center, width, height)
        bounding_boxes.append(box)
        range_bounding_boxes.append(box_range)
        line = labels.readline()

    return bounding_boxes, yolo_bounding_boxes, range_bounding_boxes

def erode_and_dialate(image, erode, dialate):
    image_open = image

    for _ in range(erode):
        image_open = morphology.erosion(image_open)
    for _ in range(dialate):
        image_open = morphology.dilation(image_open)

    return image_open

def process_image(image):
    image_gray = color.rgb2gray(image)
    # create a binary image
    thresh_yen = filters.threshold_yen(deepcopy(image_gray))
    image_yen = image_gray > thresh_yen
    # another way to "fill holes", works better than the method
    image_yen = erode_and_dialate(image_yen, 0, 4)
    image_yen = erode_and_dialate(image_yen, 4, 0)
    image_yen = erode_and_dialate(image_yen, 10, 10)
    image_yen = image_yen.astype(np.int8)

    return image_yen

def num_points_in_region(points, region):
    # region in the form ((x1, x2), (y1, y2))

    x_interval = region[0]
    y_interval = region[1]
    counter = 0

    for point in points:
        x = point[0]
        y = point[1]
        if ((x_interval[0] <= x <= x_interval[1]) and
             (y_interval[0] <= y <= y_interval[1])):
            counter += 1

    return counter

def find_overlapping_bounding_boxes(box_ranges):

    overlaps = [[] for _ in range(len(box_ranges))]

    for i in range(len(box_ranges)):
        box1 = box_ranges[i]
        for j in range(i + 1, len(box_ranges)):
            box2 = box_ranges[j]

            # note: if there exists some box1 that is totally inside a box2,
            #       overlaps[box1] does NOT include box2 -- I chose to do this
            #       because when looking for balloon start I don't want to
            #       subtract all of box1 (what I'm looking for)
            points_in_region = num_points_in_region(get_corners(box2), box1)
            if points_in_region == 4:
                overlaps[i].append(j)
                continue
            elif points_in_region:
                overlaps[i].append(j)
                overlaps[j].append(i)
                continue

            points_in_region = num_points_in_region(get_corners(box1), box2)
            if points_in_region == 4:
                overlaps[j].append(i)
                continue
            elif points_in_region:
                overlaps[i].append(j)
                overlaps[j].append(i)
                continue

    return overlaps

def find_ils(image_working, box_center, box_range, axis):
    # axis == 0 is y-axis, axis == 1 is x_axis

    ils = np.zeros(image_working.shape, dtype=np.int8)

    if not axis:
        fixed = box_center[0]
        current = box_center[1]
        height = box_range[1][1] - box_range[1][0]
        interval = (box_center[1] - height // 4, box_center[1] + height // 4)
    else:
        fixed = box_center[1]
        current = box_center[0]
        width = box_range[0][1] - box_range[0][0]
        interval = (box_center[0] - width // 4, box_center[0] + width // 4)

    for direction in [-1, 1]:
        while interval[0] <= current <= interval[1]:
            if not axis:
                if image_working[current - 5:current + 5, fixed - 5:fixed + 5].all():
                    ils[current - 3:current + 3, fixed - 3:fixed + 3] = 1
                    return ils
                elif image_working[current - 5:current + 5, fixed - 5:fixed + 5].any():
                    current += direction
                else:
                    current += 5 * direction
            else:
                if image_working[fixed - 5:fixed + 5, current - 5:current + 5].all():
                    ils[current - 3:current + 3, fixed - 3:fixed + 3] = 1
                    return ils
                elif image_working[fixed - 5:fixed + 5, current - 5:current + 5].any():
                    current += direction
                else:
                    current += 5 * direction

    return ils

def find_balloon_starts(image_binary, yolo_bounding_boxes, box_ranges, overlaps):

    image_working = deepcopy(image_binary)
    box_ilss = []

    for i in range(len(box_ranges)):
        for j in overlaps[i]:
            overlap_box = box_ranges[j]
            x_interval = overlap_box[0]
            y_interval = overlap_box[1]
            image_working[y_interval[0]:y_interval[1] + 1, x_interval[0]:x_interval[1] + 1] = 0

        # start in the middle (center-point and work down?) -- use .all()
        # to test if a whole subset is white
        box_center = (yolo_bounding_boxes[i][0], yolo_bounding_boxes[i][1])
        ils = find_ils(image_working, box_center, box_ranges[i], 0)
        if not ils.any():
            ils = find_ils(image_working, box_center, box_ranges[i], 1)
        if not ils.any():
            ils[box_center[1] - 3:box_center[1] + 3, box_center[0] - 3:box_center[0] + 3] = 1

        box_ilss.append(ils)

        for j in overlaps[i]:
            overlap_box = box_ranges[j]
            x_interval = overlap_box[0]
            y_interval = overlap_box[1]
            image_working[y_interval[0]:y_interval[1] + 1, x_interval[0]:x_interval[1] + 1] = image_binary[y_interval[0]:y_interval[1] + 1, x_interval[0]:x_interval[1] + 1]

    return box_ilss

def find_balloon_iterations(box_range):
    x_interval = box_range[0]
    y_interval = box_range[1]
    width = x_interval[1] - x_interval[0]
    height = y_interval[1] - y_interval[0]
    diagonal = math.sqrt(width ** 2 + height ** 2)

    return int(diagonal // 2.5)

def balloon(binary_image, box_ranges, box_ilss):

    snakes = []
    binary_image = binary_image.astype(np.int8)
    binary_image = util.img_as_float(binary_image)

    for i in range(len(box_ilss)):
        ils = box_ilss[i]
        box_range = box_ranges[i]
        snake = segmentation.morphological_geodesic_active_contour(binary_image, find_balloon_iterations(box_range), init_level_set=ils, smoothing=1, balloon=1)
        snakes.append(snake)

    return snakes

def get_contours(image, labels):

    bounding_boxes, yolo_bounding_boxes, box_ranges = get_bounding_boxes(image, labels)
    image_binary = process_image(image)
    overlaps = find_overlapping_bounding_boxes(box_ranges)
    box_ilss = find_balloon_starts(image_binary, yolo_bounding_boxes, box_ranges, overlaps)
    snakes = balloon(image_binary, box_ranges, box_ilss)

    # show(image, bounding_boxes, yolo_bounding_boxes, snakes)

    return image_binary, snakes


def main():
    if len(sys.argv) == 1:
        exit(0)

    image, labels = import_image_and_labels(sys.argv[1])
    bounding_boxes, yolo_bounding_boxes, box_ranges = get_bounding_boxes(image, labels)
    image_binary = process_image(image)
    overlaps = find_overlapping_bounding_boxes(box_ranges)
    box_ilss = find_balloon_starts(image_binary, yolo_bounding_boxes, box_ranges, overlaps)
    snakes = balloon(image_binary, box_ranges, box_ilss)

    show(image, bounding_boxes, yolo_bounding_boxes, snakes)
