# bacteria-networks

## Installation instructions:

### Mac

Install `homebrew` by following the instructions [here](https://brew.sh/).

`brew install` these packages:
- `python3`
- `make`
- `gcc`
- `git` (duh)
- `libomp` (optional; improves performance)

`pip3 install` these packages:
- `matplotlib`
- `pyqt5`
- `scikit-image`
- `networkx`

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

You can greatly improve the performance of this application by tweaking Darknet's makefile. If your CPU was manufactured after 2011, you should set `AVX=1`. If you installed `libomp`, set `OPENMP=1`.

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

`pip3 install` these packages:
- `matplotlib`
- `pyqt5`
- `scikit-image`
- `networkx`

Clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`.

You can greatly improve the performance of this application by tweaking Darknet's makefile. If you installed CUDA, set `GPU=1`. If you installed cuDNN, set `CUDNN=1`. If you aren't using a GPU, and your CPU was manufactured after 2011, you should set `AVX=1`. If you installed OpenMP (`libomp`), set `OPENMP=1`.

`cd` into the `darknet` directory, then run `make`.

### Windows

(This is copied almost verbatim from [here](https://github.com/AlexeyAB/darknet/blob/master/README.md).)

0. Install git.

1. Install Visual Studio 2017 or 2019. In case you need to download it, please go here: [Visual Studio Community](http://visualstudio.com)

2. Install CUDA (at least v10.0) enabling VS Integration during installation.

3. Open Powershell (Start -> All programs -> Windows Powershell) and type these commands:

```PowerShell
git clone https://github.com/microsoft/vcpkg
cd vcpkg
$env:VCPKG_ROOT=$PWD
.\bootstrap-vcpkg.bat
.\vcpkg install darknet[full]:x64-windows
```

That last command might take a long time to finish. Once it's done, clone this repository by running `git clone --recurse-submodules --depth 1 https://github.com/ahthomps/bacteria-networks.git`. Then, `cd` into the repository, and run 

```PowerShell
.\build.ps1
```

## Downloading the model:

Download `model_4.weights` from [here](https://drive.google.com/drive/folders/1oHpzVVqVL67unqOnrObX49XkeUii3Jg4?usp=sharing), and stick it in `models/model_4`. If the program never finds any bounding boxes, there's a good chance you forgot this step.

## Using this application:

Run `python3 run.py`.

File -> Open -> Image, then choose an image.

Run -> YOLO

Run -> Process Image

Run -> Contour
