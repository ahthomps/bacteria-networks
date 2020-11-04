# bacteria-networks

## Dependencies:

Download these from their websites or through your package manager:
- `python3`
- `pip3`
- `make`
- `gcc`

Download these with `pip3`:
- `matplotlib`
- `pyqt5`
- `scikit-image`
- `networkx`

Optional dependencies:
- `cuda` (For better performance if you have a modern Nvidia GPU)
- `cudnn` (Also for better performance if you have a modern Nvidia GPU)
- `openmp` (For better performance if you don't have a GPU)

## Installation instructions:

### Download the application

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

### Configure the makefile and compile Darknet

You can greatly improve the performance of this application by tweaking Darknet's makefile. If you have a CUDA-enabled GPU, and you have CUDA installed, set `GPU=1`. If you also have cuDNN installed, set `CUDNN=1`. If you aren't using a GPU, and your CPU was manufactured after 2011, you should set `AVX=1`. Installing OpenMP and setting `OPENMP=1` will massively improve performance for those of you without GPUs.

`cd` into the `darknet` directory, then run `make`.

### Download the model

Download `model_4.weights` from [here](https://drive.google.com/drive/folders/1oHpzVVqVL67unqOnrObX49XkeUii3Jg4?usp=sharing), and stick it in `models/model_4`.

## Using this application:

Run `python3 run.py`.

File->Open->Image, then choose an image.

Run->YOLO

Run->Process Image

Run->Contour
