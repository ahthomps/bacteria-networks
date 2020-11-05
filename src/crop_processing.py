""" crop_processing.py
    Here, we define some functions for dealing with Tiles. This will probably get merged into something else as the project grows.
"""

import sys
from PIL import Image
from copy import deepcopy
from os import listdir

TILE_OVERLAP = 3 # 2 -> 50% overlap, 3 -> 33% overlap, etc.
TILE_SIZE = 416
IMAGE_EXTENSIONS = (".tiff", ".tif", ".png", ".jpg", ".jpeg", ".gif", ".bmp")

class Tile:
    def __init__(self, img, x1, y1, x2, y2, filename_no_ext):
        """ img:            The cropped PIL Image object.
            x1, y1, x2, y2: The position of this tile in the larger image.
            filename:       A unique identifier for this tile. (No file extension) """

        self.img = img
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        # This will store all the (potentially partial) bounding boxes that overlap this tile.
        # Their coordinates are relative to this tile.
        # (i.e. if a bounding box starts on the left edge of this tile, its x1 is 0)
        self.bio_objs = []

        # This will be used as a unique identifier for this crop.
        self.filename_no_ext = f"{filename_no_ext}_{self.x1}_{self.y1}"

    def width(self):
        """ Returns width of bounding box"""
        return self.x2 - self.x1

    def height(self):
        """ Returns height of bounding box"""
        return self.y2 - self.y1

    def center(self):
        """ Returns center of bounding box"""
        return self.x1 + self.width() / 2, self.y1 + self.height() / 2

    def add_cell(self, cell):
        """ box: A bounding box with coordinates relative to the untiled image. """
        cell = deepcopy(cell)
        cell.x1 = max(cell.x1, self.x1) - self.x1
        cell.y1 = max(cell.y1, self.y1) - self.y1
        cell.x2 = min(cell.x2, self.x2) - self.x1
        cell.y2 = min(cell.y2, self.y2) - self.y1
        self.bio_objs.append(cell)

    def save(self, directory="."):
        """ Saves this tile as a cropped image and (potentially) an associated label file.
            Note: This will convert bounding boxes to relative, because that's how YOLO likes it. """
        self.img.save(f"{directory}/{self.filename_no_ext}.jpg", "JPEG", subsampling=0, quality=100)


def make_tiles(img, filename):
    """ img: A PIL.Image to be tiled.
        filename: A filename, usually the filename of img without its extension. """
    tiles = []
    for r in range(0, img.height, ((TILE_OVERLAP - 1) * TILE_SIZE) // TILE_OVERLAP):
        for c in range(0, img.width, ((TILE_OVERLAP - 1) * TILE_SIZE) // TILE_OVERLAP):
            x1, y1, x2, y2 = (r, c, r + TILE_SIZE, c + TILE_SIZE)
            tiles.append(Tile(img.crop((x1, y1, x2, y2)), x1, y1, x2, y2, filename))

    return tiles

def save_tiles(tiles, output_dir):
    """ tiles: A list of Tile objects. """
    for tile in tiles:
        tile.save(output_dir)

def rebuild_original_image(tiles):
    full_height = max(tiles, key=lambda tile: tile.y2).y2
    full_width = max(tiles, key=lambda tile: tile.x2).x2

    return Image.new(mode="L", size=(full_width, full_height)) # mode "L" is for 8-bit greyscale

def in_confidence_region(pt):
    return TILE_SIZE // (2 * TILE_OVERLAP) <= pt[0] <= (2 * TILE_OVERLAP - 1) * TILE_SIZE // (2 * TILE_OVERLAP) \
       and TILE_SIZE // (2 * TILE_OVERLAP) <= pt[1] <= (2 * TILE_OVERLAP - 1) * TILE_SIZE // (2 * TILE_OVERLAP)

def reunify_tiles(tiles, full_image):
    """ Takes all the tiles in tiles, and returns a new Tile object representing the untiled image. """

    # This is not really a tile, but I want to use Tile's methods.
    full_tile = Tile(full_image, 0, 0, *full_image.size, "full_image")

    for tile in tiles:
        for cell in tile.bio_objs:
            # If the center of the bounding box is in the confidence region of this tile
            if in_confidence_region(cell.center()):
                # Then we add the bounding box to the big image
                new_cell = deepcopy(cell)
                new_cell.x1 += tile.x1
                new_cell.x2 += tile.x1
                new_cell.y1 += tile.y1
                new_cell.y2 += tile.y1
                full_tile.add_cell(new_cell)

    return full_tile
