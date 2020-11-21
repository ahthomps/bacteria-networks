#!/bin/bash

# This script installs the project on a Mac. It has been tested on macOS 10.13, 10.14, and 10.15.
# It also has no error handling, so if you feel like it, add some.

# The pip dependencies. If you get a pip error, you might want to add version numbers to these.
PIP_DEPENDENCIES="scikit-image numpy matplotlib scipy networkx pyqt5 Pillow"
SHORTCUT_PATH="~/Desktop/Start JAB Labeler.sh"

# If homebrew isn't installed, then install it.
which -s brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew upgrade

# Install our brew dependencies
brew install gcc libomp
# Installing brew installs the developer tools, which include python3 (on Catalina and later) and make, so we don't need to get those.

# If this is being run from within this repo, then great! Otherwise, we should go clone the repo.
# Maybe we should come up with a better way of checking whether we're in the repo than whether there's a directory called "darknet".
ls darknet 2>/dev/null ||
	curl -L https://github.com/ahthomps/bacteria-networks/archive/master.zip -o bacteria-networks.zip &&
	unzip bacteria-networks.zip > /dev/null &&
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

# Try to install the pip dependencies. If that doesn't work, then go install python3.8 from brew and use
# that instead.
pip3 install --user $PIP_DEPENDENCIES 2>/dev/null ||
	brew install python@3.8 &&
	/usr/local/opt/python@3.8/bin/pip3 install --user $PIP_DEPENDENCIES &&
	sed -i "" "1 s/^.*$/#\!\/usr\/local\/opt\/python@3.8\/bin\/python3/" run.py

# Grab the model
curl -L https://github.com/kenballus/bacteria-networks-model/archive/master.zip -o bacteria-networks-model.zip &&
unzip bacteria-networks-model.zip > /dev/null &&
rm bacteria-networks-model.zip &&
cd bacteria-networks-model-master &&
cat *.part > model_5.weights &&
mv model_5.weights ../models/model_5 &&
cd .. &&
rm -rf bacteria-networks-model-master

touch $SHORTCUT_PATH
echo -e "#!/bin/bash\nchmod +x ~/bacteria-networks/run.py\n~bacteria-networks/run.py" > $SHORTCUT_PATH
chmod +x $SHORTCUT_PATH