#!/bin/bash
# Changes permissions recursively at folder and files level from a provided path
# ARGS:
# 1 - The target path


set -e

export MERGIN_DIR=$1
sudo mkdir -p $MERGIN_DIR
sudo find $MERGIN_DIR -type f -exec sudo chmod 640 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod 750 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod g+s {} \;
sudo chown -R 901:999 $MERGIN_DIR
