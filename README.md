# bacteria-networks

## Dependencies:

python3, make, gcc, matplotlib, pyqt5, scikit-image, networkx

## Installation instructions:

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

If you have an Nvidia GPU with CUDA installed, and you want to use it, configure `darknet/Makefile` to your liking. You probably want to set `GPU=1`, and `CUDNN=1`. Otherwise, just use the default makefile.

Run `cd darknet; make`.

Download `model_4.weights` from [here](https://drive.google.com/drive/folders/1oHpzVVqVL67unqOnrObX49XkeUii3Jg4?usp=sharing), and stick it in `models/model_4`.

Run `python3 run.py`.

### Using YOLO:

File->Open->Image, then choose an image.

Run->YOLO

Run->Process Image

Run->Contour
