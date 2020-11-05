from skimage.color import rgb2gray
from PyQt5.QtWidgets import QFileDialog
from PIL import Image
import numpy as np
import random
import matplotlib.pyplot as plt
import subprocess
import os
import networkx as nx
import pickle
import collections

from bio_object import BioObject, compute_all_cell_bbox_overlaps, compute_nanowire_to_cell_bbox_overlaps, compute_cell_center
from crop_processing import Tile, make_tiles, IMAGE_EXTENSIONS, reunify_tiles
from yolo import parse_yolo_input, parse_yolo_output, run_yolo_on_images
from edge_detection import compute_cell_contact, compute_nanowire_edges

TILE_SIZE = 416
CROP_DIR = ".crops"

class ProgramManager:
    def __init__(self):
        self.image = np.array([])
        self.original_image = np.array([])
        self.cells = []

        self.made_crops = False

        self.image_path = ""
        self.label_path = ""
        self.filename = None

    def open_image_file_and_crop_if_necessary(self):
        path, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif)")
        if not path:
            return

        print("using image {}".format(path))
        self.image_path = path
        self.image = rgb2gray(plt.imread(self.image_path))
        self.original_image = plt.imread(self.image_path)
        for i in range(len(self.image)):
            count = 0
            for item in self.image[i]:
                if 0 < item < 255:
                    count += 1
                    if count > 10:
                        break
            else:
                self.image = self.image[:i]
                break

        self.cells.append(BioObject(0, 0, len(self.image[0]), len(self.image), 0, "surface"))

        if self.image.shape[0] > TILE_SIZE or self.image.shape[1] > TILE_SIZE:
            self.crop()

    def open_label_file(self):
        path, _ = QFileDialog.getOpenFileName(None, "Select label", "", "Label Files (*.txt)")
        if not path:
            return
        classes_file_path = "{}classes.txt".format(path[:len(path) - path[::-1].find("/")])
        print("using label {}".format(path))
        classes_ofile = None
        if os.path.isfile(classes_file_path):
            classes_ofile = open(classes_file_path)
            print("using classifications {}".format(classes_file_path))
        self.label_path = path
        label_ofile = open(self.label_path)
        self.cells += parse_yolo_input(label_ofile, classes_ofile, self.original_image)

    def get_save_loc(self, ext):
        path, _ = QFileDialog.getSaveFileName(None, 'Save File', "", ext)
        if not path:
            return
        return path

    def compute_bounding_boxes(self):
        if not self.made_crops:
            image_filename = self.image_path
            slash_index = -1
            if "/" in image_filename:
                slash_index = image_filename.rfind("/")
            elif "\\" in image_filename:
                slash_index = image_filename.rfind("\\")
            image_filename = image_filename[slash_index + 1:]

            filenames = [image_filename]
            paths = [self.image_path]
            top_left_corners = [(0, 0)]
        else:
            filenames = list(filter(lambda s: any(s.lower().endswith(ext) for ext in IMAGE_EXTENSIONS), os.listdir(CROP_DIR)))
            paths = list(map(lambda filename: f"{CROP_DIR}/{filename}", filenames))
            top_left_corners = list(map(int, path[:path.rfind(".")].split("_")[-2:]) for path in paths)

        # This is a list of lists of cells, each list corresponding to a crop.
        yolo_output = run_yolo_on_images(paths)
        cell_lists = parse_yolo_output(yolo_output)

        if len(cell_lists) > 1:
            tiles = []
            for i in range(len(filenames)):
                xmin, ymin = top_left_corners[i]
                tile = Tile(Image.open(paths[i]), xmin, ymin, xmin + TILE_SIZE, ymin + TILE_SIZE, filenames[i])
                tile.cells = cell_lists[i]
                tiles.append(tile)
            full_tile = reunify_tiles(tiles, full_image=Image.fromarray(self.image))
            self.cells += full_tile.cells
        elif cell_lists == []:
            self.cells += []
        else:
            self.cells += cell_lists[0]

    def compute_bbox_overlaps_and_cell_centers(self):
        compute_all_cell_bbox_overlaps(self.cells)
        compute_nanowire_to_cell_bbox_overlaps(self.cells)
        for obj in self.cells:
            if obj.is_cell():
                compute_cell_center(obj, self.image)

    def crop(self):
        # Make the crops directory
        directory = self.image_path[:self.image_path.rfind("/")]
        self.made_crops = True

        os.makedirs(CROP_DIR, exist_ok=True)

        # Remove any clutter in the crop directory
        for file in os.listdir(CROP_DIR):
            os.remove(f"{CROP_DIR}/{file}")

        # Get a list of all the image files we're going to crop
        input_images = [self.image_path[self.image_path.rfind("/") + 1:]]

        # Crop each image, and save all the crops in CROP_DIR
        for filename in input_images:
            for tile in make_tiles(Image.open(f"{directory}/{filename}"), filename[:filename.rfind(".")]):
                tile.save(directory=CROP_DIR)

    def compute_cell_network_edges(self, canvas):
        compute_cell_contact(self.cells, self.image)
        compute_nanowire_edges(self.cells, canvas, self.image)
