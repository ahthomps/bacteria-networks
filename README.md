# bacteria-networks

## Dependencies:

Download these from their websites or through your package manager: `python3`, `pip3`, `make`, `gcc`

Download these with `pip3`: `matplotlib`, `pyqt5`, `scikit-image`, `networkx`

## Installation instructions:

### Download the application

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

### Configure the makefile and compile Darknet

You can greatly improve the performance of this application by tweaking Darknet's makefile. You probably want to set `GPU=1`, and `CUDNN=1`. If you aren't using a GPU, you will get better performance by seting `AVX=1` (speeds up vector math) and `OPENMP=1` (enables parallel processing). In order to use OpenMP, you'll need to install OpenMP.

Run `cd darknet; make`.

### Download the model

Download `model_4.weights` from [here](https://drive.google.com/drive/folders/1oHpzVVqVL67unqOnrObX49XkeUii3Jg4?usp=sharing), and stick it in `models/model_4`.

### That's it!

## Using this application:

Run `python3 run.py`.

File->Open->Image, then choose an image.

Run->YOLO

Run->Process Image

Run->Contour
