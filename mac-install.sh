#!/bin/bash

# This script installs the project on a Mac. It has been tested on macOS 10.13, 10.14, and 10.15.
# It also has no error handling, so if you feel like it, add some.

# If homebrew isn't installed, then install it.
which -s brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew upgrade

# Install our brew dependencies
brew install gcc libomp
# Installing brew installs the developer tools, which include python3 (on Catalina and later) and make, so we don't need to get those.

# If this is being run from within this repo, then great! Otherwise, we should go clone the repo.
# Maybe we should come up with a better way of checking whether we're in the repo than whether there's a directory called "darknet".
ls darknet ||
	curl -L https://github.com/ahthomps/bacteria-networks/archive/master.zip -o bacteria-networks.zip &&
	unzip bacteria-networks.zip &&
	rm bacteria-networks.zip &&
	mv bacteria-networks-master bacteria-networks &&
	cd bacteria-networks

# Grab darknet if we need it.
if [ -z "$(ls darknet)" ]; then
    rmdir darknet
    curl -L https://github.com/AlexeyAB/darknet/archive/master.zip -o darknet.zip
    unzip darknet.zip
    rm darknet.zip
    mv darknet-master darknet
fi

# Because Apple sucks, they symlink gcc to clang. So the version of gcc brew installs has to be installed as gcc-10.
# When gcc 11 comes out, this will have to be updated.
sed -i "" "s/gcc/gcc-10/" darknet/Makefile
sed -i "" "s/g++/g++-10/" darknet/Makefile
sed -i "" "s/OPENMP=0/OPENMP=1/" darknet/Makefile # Enables multicore support for running the neural network.
sed -i "" "s/AVX=0/AVX=1/" darknet/Makefile # Enables vector instructions for running the neural network.

cd darknet &&
	make clean &&
	make &&
	cd ..

# On macOS <10.15, python3 isn't part of the Xcode tools, so we need to install it with brew.
which -s python3 ||
	brew install python@3.8 &&
	/usr/local/opt/python@3.8/bin/pip3 install --user numpy matplotlib scipy scikit-image networkx pyqt5 Pillow &&
	sed -i "" "1 s/^.*$/#\!\/usr\/local\/opt\/python@3.8\/bin\/python3/" run.py

# Install our pip dependencies, if we didn't already just install them with brew's pip3
which -s pip3 && pip3 install --user numpy matplotlib scipy scikit-image networkx pyqt5 Pillow

# Grab the model
curl -L https://github.com/kenballus/bacteria-networks-model/archive/master.zip -o bacteria-networks-model.zip &&
unzip bacteria-networks-model.zip &&
rm bacteria-networks-model.zip &&
cd bacteria-networks-model-master &&
cat *.part > model_5.weights &&
mv model_5.weights ../models/model_5 &&
rm -rf bacteria-networks-model-master &&
cd ..
