#!/bin/bash

# Grab the model
curl -L https://github.com/kenballus/bacteria-networks-model/archive/master.zip -o bacteria-networks-model.zip
unzip bacteria-networks-model.zip
rm bacteria-networks-model.zip
cd bacteria-networks-model-master
cat *.part > model_6.weights
mv model_6.weights ../../models/model_6
cd ..
rm -rf bacteria-networks-model-master
