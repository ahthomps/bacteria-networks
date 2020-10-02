import sys
from PIL import Image
from copy import deepcopy
from os import listdir
from classes import *

TILE_OVERLAP = 2 # 2 -> 50% overlap, 3 -> 33% overlap, etc.
TILE_SIZE = 416
IMAGE_EXTENSIONS = (".tiff", ".tif", ".png", ".jpg", ".jpeg", ".gif")

def make_tiles(img, filename):
    """ img: A PIL.Image to be tiled.
        filename: A filename, usually the filename of img without its extension. """
    tiles = []
    for r in range(0, img.height, TILE_SIZE // TILE_OVERLAP):
        for c in range(0, img.width, TILE_SIZE // TILE_OVERLAP):
            x1, y1, x2, y2 = (r, c, r + TILE_SIZE, c + TILE_SIZE)
            tiles.append(Tile(img.crop((x1, y1, x2, y2)), x1, y1, x2, y2, filename))

    return tiles


def make_labeled_tiles(input_dir):
    """ input_dir:  Directory containing uncropped images and associated labels.
        Returns Tile objects representing CROP_SIZE x CROP_SIZE crops of each image in input_dir
        that has an associated label file. Each of these Tiles has the appropriate labels. """
    files = listdir(input_dir)
    for filename in files:
        if any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
            # The filename of the image
            image_filename = f"{input_dir}/{filename}"

            # The filename of the image without an extension
            filename = filename[:filename.rfind(".")]

            # Ignore images with no label files
            if f"{filename}.txt" not in files:
                continue

            # The filename of the label file
            label_filename = f"{input_dir}/{filename}.txt"

            # Open the files
            img = Image.open(image_filename)
            labels = open(label_filename)

            # Make the BoundingBox objects
            bounding_boxes = parse_yolo_input(labels)

            # Convert them to px
            for box in bounding_boxes:
                box.to_px(img.width, img.height)

            # Tile the image
            tiles = make_tiles(img, filename)

            # Convert the bounding boxes to fit the tiles.
            for tile in tiles:
                for box in bounding_boxes:
                    if box.overlaps(tile):
                        tile.add_bounding_box(box)

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

def reunify_tiles(tiles, output_dir="."):
    """ Takes all the tiles in tiles, and returns a new Tile object representing the untiled image. """

    full_image = rebuild_original_image(tiles)

    full_tile = Tile(full_image, 0, 0, *full_image.size, "full_image")
    # This is not really a tile per se, but I want to use Tile's methods.

    # i.e. if TILE_OVERLAP = 2, the confidence_region is 1/4, 1/4, 3/4, 3/4 (proportions of TILE_SIZE)
    confidence_region = Box(TILE_SIZE // (2 * TILE_OVERLAP),
                            TILE_SIZE // (2 * TILE_OVERLAP),
                            ((2 * TILE_OVERLAP - 1) * TILE_SIZE) // (2 * TILE_OVERLAP),
                            ((2 * TILE_OVERLAP - 1) * TILE_SIZE) // (2 * TILE_OVERLAP))
    for tile in tiles:
        for bounding_box in tile.bounding_boxes:
            # If the center of the bounding box is in the confidence region of this tile
            if confidence_region.contains_point(bounding_box.center()):
                # Then we add the bounding box to the big image
                new_bbox = deepcopy(bounding_box)
                new_bbox.x1 += tile.x1
                new_bbox.x2 += tile.x1
                new_bbox.y1 += tile.y1
                new_bbox.y2 += tile.y1
                full_tile.add_bounding_box(new_bbox)

    return full_tile


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("USAGE: python3 make_labeled_crops.py <input_directory> <output_directory>", file=sys.stderr)
        sys.exit(1)

    input_dir, output_dir = sys.argv[1:]
    tiles = make_labeled_tiles(input_dir)
    save_tiles(tiles, output_dir)
