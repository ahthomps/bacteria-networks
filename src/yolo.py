import subprocess
from bio_object import BioObject
import os

DARKNET_BINARY_PATH = "darknet/darknet"
DATA_PATH = "models/model_6/obj.data"
CFG_PATH = "models/model_6/test.cfg"
WEIGHTS_PATH = "models/model_6/model_6.weights"
YOLO_OPTIONS = ["-ext_output", "-dont_show"]

def run_yolo_on_images(img_paths, update_progress_bar):
    """ img_paths:           A list of image paths to be run through YOLO. These are probably crops
        update_progress_bar: A function to update the progress bar. """

    for path in [DARKNET_BINARY_PATH, DATA_PATH, CFG_PATH, WEIGHTS_PATH]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Can't open {path}: No such file.")

    proc = subprocess.Popen([DARKNET_BINARY_PATH, "detector", "test", DATA_PATH, CFG_PATH, WEIGHTS_PATH, *YOLO_OPTIONS],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            stdin=subprocess.PIPE,
                            encoding="UTF-8")

    proc.stdin.write("\n".join(img_paths))
    proc.stdin.close()

    total_output = ""
    total_images_processed = 0
    while proc.poll() is None:
        # We have to read it line by line because reading as many as we can amounts to waiting for the process to finish
        current_output = proc.stdout.readline()
        total_output += current_output
        current_images_processed = current_output.count("Enter Image Path:")
        if current_images_processed != 0:
            total_images_processed += current_images_processed
            if update_progress_bar is not None:
                update_progress_bar(min(100, int(total_images_processed / len(img_paths) * 100)))
        # It felt like I should put a sleep in here, but I timed it and it makes no difference.

    total_output += "".join(proc.stdout.readlines())

    # Remove the garbage files that yolo makes
    if os.path.exists("bad.list"):
        os.remove("bad.list")
    if os.path.exists("predictions.jpg"):
        os.remove("predictions.jpg")

    return total_output

def parse_yolo_output(yolo_output):
    """ Takes a string (probably stdout from running yolo) and returns a list of lists of BioObject objects.
        Each sublist corresponds to one input file."""

    bio_objs = []
    bio_obj_id = 1
    in_an_image = False
    for line in yolo_output.splitlines():
        if line.endswith("milli-seconds."): # Starting a new image
            bio_objs.append([])
            in_an_image = True
        elif line.startswith("Enter Image Path:"): # It's asking for another image, so this one is done
            in_an_image = False
        elif in_an_image:
            tokens = line.split()
            classification = tokens[0][:-1] # Slice because this will have a ':' stuck on the end
            confidence = tokens[1] # Not used yet
            # For some reason, yolo sometimes gives negative bounding box dimensions.
            # We've only seen this happen when the images are really busy
            xmin = int(tokens[3]) if int(tokens[3]) >= 0 else 0
            ymin = int(tokens[5]) if int(tokens[5]) >= 0 else 0
            width = int(tokens[7]) if int(tokens[7]) >= 0 else 0
            # Slice because this will have a ')' stuck on the end
            height = int(tokens[9][:-1]) if int(tokens[9][:-1]) >= 0 else 0

            bio_objs[-1].append(BioObject(xmin, ymin, xmin + width, ymin + height, bio_obj_id, classification))
            bio_obj_id += 1

    return bio_objs
