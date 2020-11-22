# bacteria-networks

This program employs a neural network to identify nanowire network structure in images of Shewanella oneidensis.

## Installation instructions:

### Mac

Open Terminal (it's in Utilities) and run the following command:

`/bin/bash -c "$(curl -L https://raw.githubusercontent.com/ahthomps/bacteria-networks/master/mac-install.sh)"`

This will install the program to your home directory and leave a shortcut on your desktop called JAB.
Double click it to run the program.

### Linux

Use your package manager to install the following packages:
- `python3`
- `pip3`
- `make`
- `gcc`
- `git`
- `cuda` (optional; improves performance if you have a modern Nvidia GPU)
- `cudnn` (optional; improves performance if you have a modern Nvidia GPU; requires `cuda`)
- `openmp` (optional; improves performance if you're not using `cuda`)

(Note: Some of these packages will have different names in different package repositories. For example, `openmp` is called `libomp` in Ubuntu's package repositories. The names given match the names in the default Arch Linux package repositories. )

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

You can greatly improve the performance of this application by tweaking Darknet's makefile. If you installed `cuda`, set `GPU=1`. If you installed `cudnn`, set `CUDNN=1`. If you aren't using a GPU, and your CPU was manufactured after 2011, you should set `AVX=1`. If you installed `openmp`, set `OPENMP=1`.

`cd` into the `darknet` directory, then run `make`.

`pip3 install` these packages:
- `matplotlib`
- `pyqt5`
- `scikit-image`
- `networkx`
- `scipy`
- `Pillow`

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

`pip3 install` these packages:
- `matplotlib`
- `pyqt5`
- `scikit-image`
- `networkx`
- `numpy`
- `scipy`
- `Pillow`

## Downloading the model:

TO DO

If the program never finds any bounding boxes, there's a good chance you forgot this step.

## Using this application:

Run the program with `python3 run.py` (or double click on the shortcut if you're on a Mac).

File -> Open -> Image, then choose an image.

Run -> YOLO

Run -> Process Image

Run -> Contour
