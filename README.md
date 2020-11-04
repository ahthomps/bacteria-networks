# bacteria-networks

This program employs a neural network to identify nanowire network structure in images of Shewanella oneidensis.

## Installation instructions:

### Mac

Install `homebrew` by following the instructions [here](https://brew.sh/).

`brew install` these packages:
- `python3`
- `make`
- `gcc`
- `git` (duh)
- `libomp` (optional; improves performance)

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

You'll need to edit `Makefile` in the `darknet` directory of this repository. If your CPU was manufactured after 2011, you should set `AVX=1`. If you installed `libomp`, set `OPENMP=1`. Now, do a find and replace across the file replacing all instance of `gcc` with `gcc-10` and all instance of `g++` with `g++-10`.

`cd` into the `darknet` directory, then run `make`.

### Linux

Use your package manager to install the following packages:
- `python3`
- `pip3`
- `make`
- `gcc`
- `git` (duh)
- `cuda` (optional; improves performance if you have a modern Nvidia GPU)
- `cudnn` (optional; improves performance if you have a modern Nvidia GPU; requires `cuda`)
- `openmp` (optional; improves performance if you're not using `cuda`)

(Note: Some of these packages will have different names in different repositories. These are their names in the Arch repositories.)

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

You can greatly improve the performance of this application by tweaking Darknet's makefile. If you installed `cuda`, set `GPU=1`. If you installed `cudnn`, set `CUDNN=1`. If you aren't using a GPU, and your CPU was manufactured after 2011, you should set `AVX=1`. If you installed `openmp` (`libomp`), set `OPENMP=1`.

`cd` into the `darknet` directory, then run `make`.

### Windows

(This is copied almost verbatim from [here](https://github.com/AlexeyAB/darknet/blob/master/README.md).)

0. Install `git`, `python3`, and `pip3`.

1. Install Visual Studio 2017 or 2019. You can download it [here](http://visualstudio.com). Be sure to install all of the optional C++ extensions.

2. If you have a modern Nvidia GPU, install CUDA (at least v10.0) enabling VS Integration during installation. You can download it [here](https://developer.nvidia.com/cuda-downloads).

3. Open Powershell (Start -> All programs -> Windows Powershell) and run these commands:

```PowerShell
git clone https://github.com/microsoft/vcpkg
cd vcpkg
$env:VCPKG_ROOT=$PWD
.\bootstrap-vcpkg.bat
.\vcpkg install darknet[full]:x64-windows
cd ..
```

Once that's done, run these commands:

```PowerShell
git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git
cd bacteria-networks\darknet
.\build.ps1
```

## Installing `pip` dependencies:

`pip3 install` these packages:
- `matplotlib`
- `pyqt5`
- `scikit-image`
- `networkx`

(Note: If you're on Mac or Linux, these packages may be available from your package manager. Feel free to use those versions instead of the `pip` ones.)

## Downloading the model:

Download `model_4.weights` from [here](https://drive.google.com/drive/folders/1oHpzVVqVL67unqOnrObX49XkeUii3Jg4?usp=sharing), and stick it in `models/model_4`.

If the program never finds any bounding boxes, there's a good chance you forgot this step.

## Using this application:

Run `python3 run.py`.

File -> Open -> Image, then choose an image.

Run -> YOLO

Run -> Process Image

Run -> Contour
