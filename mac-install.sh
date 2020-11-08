#!/bin/bash

# This script is a work in progress. It will install most (maybe all) of the dependencies for this app,
# but it needs more testing and it needs to be able to get the model.

# If homebrew isn't installed, then install it.
which -s brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# Install our brew dependencies
brew install python3 gcc git libomp pyqt5
# bsd make comes with the xcode tools that get installed alongside homebrew, and darknet doesn't use
# any of the gnu make features, so we don't need to brew install make.

# If this is being run from within this repo, then great! Otherwise, we should go clone the repo.
# Maybe we should come up with a better way of checking whether we're in the repo than the directory name.
if [ "$(basename $(pwd))" != "bacteria-networks" ]; then
    git clone --depth 1 --recurse-submodules https://github.com/ahthomps/bacteria-networks.git
    cd bacteria-networks
fi

# Because Apple sucks, they symlink gcc to clang. So the version of gcc brew installs has to be installed as gcc-10.
# When gcc 11 comes out, this will have to be updated.
sed -i "" "s/gcc/gcc-10" darknet/Makefile
sed -i "" "s/g++/g++-10" darknet/Makefile
sed -i "" "s/OPENMP=0/OPENMP=1/" darknet/Makefile # Enables multicore support for running the neural network.
sed -i "" "s/AVX=0/AVX=1/" darknet/Makefile # Enables vector instructions for running the neural network.

# Install our pip dependencies
pip3 install numpy matplotlib scikit-image networkx

# Now, we need to get the model. We need a place to host it that isn't Google Drive so it can be downloaded from this script.
# Ideally, we'd get a cs server to host it, and we can host this script there too.
# Then, they can install this whole program with one command.