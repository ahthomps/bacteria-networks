# bacteria-networks

## Dependencies:

python3, make, gcc, pyqt5, matplotlib 

## Installation instructions:

Clone this repository.

Run `make`.

Download [one of these models](https://drive.google.com/drive/folders/1oHpzVVqVL67unqOnrObX49XkeUii3Jg4?usp=sharing), and stick it in `backup`.

Change the constants in `make_labeled_crops.py` to reflect the model you chose.

Run `python3 run.py`.

### Using YOLO:

File->Open->Image, then choose a 416x416 jpg image.

Run->YOLO

Run->Contour

### Using other bounding boxes:

File->Open->Image, then choose an image file.

File->Open->Label, then choose a YOLO-formatted label file.

Run->Contour
