""" make_labeled_crops.py
    Here, we define some functions for dealing with Tiles. This will probably get merged into something else as the project grows.
"""

import sys
from PIL import Image
from copy import deepcopy
from os import listdir
import subprocess
from classes import *

TILE_OVERLAP = 3 # 2 -> 50% overlap, 3 -> 33% overlap, etc.
TILE_SIZE = 416
IMAGE_EXTENSIONS = (".tiff", ".tif", ".png", ".jpg", ".jpeg", ".gif")

DATA_PATH = "model_3/obj.data"
CFG_PATH = "model_3/test.cfg"
WEIGHTS_PATH = "backup/model_3.weights"

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

    # Rebuild the original image
    full_image = Image.new(mode="L", size=(full_width, full_height)) # mode "L" is for 8-bit greyscale
    for tile in tiles:
        full_image.paste(tile.img, box=(tile.x1, tile.y1, tile.x2, tile.y2))

    return full_image

def in_confidence_region(pt):
    return TILE_SIZE // (2 * TILE_OVERLAP) <= pt[0] <= (2 * TILE_OVERLAP - 1) * TILE_SIZE // (2 * TILE_OVERLAP) \
       and TILE_SIZE // (2 * TILE_OVERLAP) <= pt[1] <= (2 * TILE_OVERLAP - 1) * TILE_SIZE // (2 * TILE_OVERLAP)

def reunify_tiles(tiles):
    """ Takes all the tiles in tiles, and returns a new Tile object representing the untiled image. """

    full_image = rebuild_original_image(tiles)

    # This is not really a tile per se, but I want to use Tile's methods.
    full_tile = Tile(full_image, 0, 0, *full_image.size, "full_image")
                            
    for tile in tiles:
        for cell in tile.cells:
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

def run_yolo_on_images(filenames):
    output = subprocess.run(["./darknet", "detector", "test", DATA_PATH, CFG_PATH, WEIGHTS_PATH],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            input="\n".join(filenames).encode("UTF-8")).stdout
    return str(output, "UTF-8")

def parse_yolo_input(label_file, image):
    """ Reads from a yolo training file and returns a list of BoundingBox objects.
        Also takes the labels' image so we can convert from relative to px. """
    cells = []
    id = 0
    for line in label_file.readlines():
        # Treat #s as comments
        if "#" in line:
            line = line[:line.index("#")]
        if line.split() == []:
            continue

        classification, x, y, width, height = map(float, line.split())
        x *= len(image[0])
        width *= len(image[0])
        y *= len(image)
        height *= len(image)
        cells.append(Cell(int(x - width / 2), int(y - height / 2), int(x + width / 2), int(y + height / 2), id, classification))
        id += 1

    return cells

def parse_yolo_output(yolo_output):
    """ Takes a string (probably stdout from running yolo) and returns a list of lists of Cell objects.
        Each sublist corresponds to one input file."""
    print(yolo_output)
    cells = []
    cell_id = 0
    for line in yolo_output.splitlines():
        if line.startswith("Enter Image Path:"):
            cells.append([])
        else:
            tokens = line.split()
            classification = tokens[0]
            confidence = int(tokens[1]) # Not used yet
            xmin = int(tokens[2])
            ymin = int(tokens[3])
            xmax = int(tokens[4])
            ymax = int(tokens[5])
            cells[-1].append(Cell(xmin, ymin, xmax, ymax, cell_id, classification))
            cell_id += 1

    if len(cells) > 0 and cells[-1] == []:
        cells.pop()
    return cells
