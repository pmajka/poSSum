#!/bin/bash -xe

# ---------------------------------------------------------
# This script downloads the tutorial on reconstruction
# 3D brain images based on serial sections including
# all intermediate reconstruction steps.
# 
# The file is downloaded from the 3D Bar Service website
# ---------------------------------------------------------

DATASET_FILENAME=reconstruction_of_the_waxholm_space_nissl_image_tutorial.tgz
DATASET_URL=http://doc.3dbar.org/possum/reconstruction_of_the_waxholm_space_nissl_image_tutorial.tgz

if [ -e ${DATASET_FILENAME} ]
then
    sleep 1
else
    wget ${DATASET_URL} -O ${DATASET_FILENAME}
fi

md5sum -c ${DATASET_FILENAME}.md5 && tar -xvvzf ${DATASET_FILENAME} 
