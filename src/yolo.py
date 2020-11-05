import subprocess
from bio_object import BioObject

DARKNET_BINARY_PATH = "darknet/darknet"
DATA_PATH = "models/model_4/obj.data"
CFG_PATH = "models/model_4/test.cfg"
WEIGHTS_PATH = "models/model_4/model_4.weights"
YOLO_OPTIONS = ["-ext_output", "-dont_show"]

def run_yolo_on_images(filenames):
    return subprocess.run([DARKNET_BINARY_PATH, "detector", "test", DATA_PATH, CFG_PATH, WEIGHTS_PATH, *YOLO_OPTIONS],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL,
                          encoding="UTF-8",
                          input="\n".join(filenames)).stdout

def parse_yolo_input(label_file, classes_file, image):
    """ Reads from a yolo training file and returns a list of BoundingBox objects.
        Also takes the labels' image so we can convert from relative to px. """
    cells = []
    classifications = []
    obj_id = 1
    if classes_file is not None:
        for line in classes_file.readlines():
            classifications.append(line.rstrip())
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
        if classifications != []:
            classification = classifications[int(classification)]
        else:
            classification = "cell"
        cells.append(BioObject(int(x - width / 2), int(y - height / 2), int(x + width / 2), int(y + height / 2), obj_id, classification))
        obj_id += 1

    return cells

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
            xmin = int(tokens[3])
            ymin = int(tokens[5])
            width = int(tokens[7])
            height = int(tokens[9][:-1]) # Slice because this will have a ')' stuck on the end
            bio_objs[-1].append(BioObject(xmin, ymin, xmin + width, ymin + height, bio_obj_id, classification))
            bio_obj_id += 1

    if len(bio_objs) > 0 and bio_objs[-1] == []:
        bio_objs.pop()

    return bio_objs
