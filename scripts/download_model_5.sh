#!/bin/bash

# Grab the model
curl -L https://github.com/kenballus/bacteria-networks-model/archive/master.zip -o bacteria-networks-model.zip
unzip bacteria-networks-model.zip
rm bacteria-networks-model.zip
cd bacteria-networks-model-master
cat *.part > model_5.weights
mv model_5.weights ../../models/model_5
cd ..
rm -rf bacteria-networks-model-master