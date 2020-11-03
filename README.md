# bacteria-networks

## Dependencies:

python3, make, gcc, matplotlib, pyqt5, scikit-image, networkx

## Installation instructions:

Clone this repository. You should probably use `--depth 1` so the download doesn't take 1000 years.

Go into `darknet_orig` and run `make`.

Download `model_3.weights` from [here](https://drive.google.com/drive/folders/1oHpzVVqVL67unqOnrObX49XkeUii3Jg4?usp=sharing), and stick it in `darknet_orig/backup`.

Run `python3 run.py`.

### Using YOLO:

File->Open->Image, then choose an image.

Run->YOLO

Run->Process Image

Run->Contour
