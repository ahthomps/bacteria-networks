from skimage.color import rgb2gray
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os

from bio_object import BioObject, compute_all_cell_bbox_overlaps, compute_nanowire_to_cell_bbox_overlaps, compute_cell_center
from crop_processing import Tile, make_tiles, IMAGE_EXTENSIONS, reunify_tiles
from yolo import parse_yolo_output, run_yolo_on_images
from edge_detection import compute_cell_contact, compute_nanowire_edges

TILE_SIZE = 416
CROP_DIR = ".crops"

class ProgramManager:
    def __init__(self):
        self.image = np.array([])
        self.original_image = np.array([])
        self.bio_objs = []
        self.made_crops = False
        self.image_path = ""

    def open_image_file(self, image_path):
        self.image_path = image_path
        self.image = rgb2gray(plt.imread(self.image_path)) # In the future, this will be incompatible with greyscale input images.
        self.original_image = plt.imread(self.image_path)

        self.bio_objs.append(BioObject(0, 0, len(self.image[0]), len(self.image), 0, "surface"))

        if self.image.shape[0] > TILE_SIZE or self.image.shape[1] > TILE_SIZE:
            self.crop()

    def compute_bounding_boxes(self, update_progress_bar=None):
        if not self.made_crops:
            image_filename = self.image_path
            slash_index = -1
            if "/" in image_filename:
                slash_index = image_filename.rfind("/")
            image_filename = image_filename[slash_index + 1:]

            filenames = [image_filename]
            paths = [self.image_path]
            top_left_corners = [(0, 0)]
        else:
            filenames = list(filter(lambda s: any(s.lower().endswith(ext) for ext in IMAGE_EXTENSIONS), os.listdir(CROP_DIR)))
            paths = list(map(lambda filename: f"{CROP_DIR}/{filename}", filenames))
            top_left_corners = list(map(int, path[:path.rfind(".")].split("_")[-2:]) for path in paths)

        # This is a list of lists of cells, each list corresponding to a crop.
        yolo_output = run_yolo_on_images(paths, update_progress_bar)
        cell_lists = parse_yolo_output(yolo_output)

        if len(cell_lists) > 1:
            tiles = []
            for i in range(len(filenames)):
                xmin, ymin = top_left_corners[i]
                tile = Tile(Image.open(paths[i]), xmin, ymin, xmin + TILE_SIZE, ymin + TILE_SIZE, filenames[i])
                tile.bio_objs = cell_lists[i]
                tiles.append(tile)
            full_tile = reunify_tiles(tiles, full_image=Image.fromarray(self.image))
            self.bio_objs += full_tile.bio_objs
        elif cell_lists == []:
            self.bio_objs += []
        else:
            self.bio_objs += cell_lists[0]

    def compute_bbox_overlaps_and_cell_centers(self):
        compute_all_cell_bbox_overlaps(self.bio_objs)
        compute_nanowire_to_cell_bbox_overlaps(self.bio_objs)
        for obj in self.bio_objs:
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

        # The image file we're going to crop
        filename = self.image_path[self.image_path.rfind("/") + 1:]

        # This assumes the image has the information bar on the bottom
        image = Image.open(f"{directory}/{filename}")
        min_row = image.height
        for row in reversed(range(image.height)):
            if all(image.getpixel((col, row)) in (0, 255) for col in range(0, image.width, image.width // 10)):
                min_row = row

        image = image.crop((0, 0, image.width, min_row))
        image.save("out.jpg")

        # Crop the image, and save all the crops in CROP_DIR
        for tile in make_tiles(image, filename[:filename.rfind(".")]):
            tile.save(directory=CROP_DIR)

    def compute_cell_network_edges(self, update_progress_bar=None):
        compute_cell_contact(self.bio_objs, self.image, update_progress_bar)
        compute_nanowire_edges(self.bio_objs, self.image, update_progress_bar)
