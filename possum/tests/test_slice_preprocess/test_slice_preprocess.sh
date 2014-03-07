#!/bin/bash
set -xe 

# Image downloaded from the BrainMaps.org website: 
# http://brainmaps.org/ajax-viewer.php?datid=42&sname=459

INPUT_IMAGE=test_input
rm -rfv ${INPUT_IMAGE}_*.*

pos_slice_preprocess \
    -i ${INPUT_IMAGE}.nii.gz \
    -g ${INPUT_IMAGE}_g_1.nii.gz \
    -r ${INPUT_IMAGE}_r_1.nii.gz 

pos_slice_preprocess \
    -i ${INPUT_IMAGE}.nii.gz \
    -g ${INPUT_IMAGE}_g_3.nii.gz \
    -r ${INPUT_IMAGE}_r_3.nii.gz \
    --registrationColorChannel red

pos_slice_preprocess \
    -i ${INPUT_IMAGE}.nii.gz \
    -g ${INPUT_IMAGE}_g_4.nii.gz \
    -r ${INPUT_IMAGE}_r_4.nii.gz \
    --registrationColorChannel red \
    --invertSourceImage \
    --invertMultichannelImage

pos_slice_preprocess \
    -i ${INPUT_IMAGE}.nii.gz \
    -g ${INPUT_IMAGE}_g_5.nii.gz \
    -r ${INPUT_IMAGE}_r_5.nii.gz \
    --registrationColorChannel red \
    --invertSourceImage \
    --medianFilterRadius 3 3 \
    --invertMultichannelImage

pos_slice_preprocess \
    -i ${INPUT_IMAGE}.nii.gz \
    -g ${INPUT_IMAGE}_g_6.nii.gz \
    -r ${INPUT_IMAGE}_r_6.nii.gz \
    --registrationROI 200 200 250 250 \
    --registrationResize 0.5

pos_slice_preprocess \
    -i ${INPUT_IMAGE}.nii.gz \
    -g ${INPUT_IMAGE}_g_8.nii.gz \
    -r ${INPUT_IMAGE}_r_8.nii.gz \
    --registrationROI 100 100 350 350 \
    --registrationResize 0.5

pos_slice_preprocess \
    -i ${INPUT_IMAGE}.nii.gz \
    -g ${INPUT_IMAGE}_g_7.nii.gz \
    -r ${INPUT_IMAGE}_r_7.nii.gz \
    --registrationROI 100 100 350 350 \
    --registrationResize 0.5 \
    --medianFilterRadius 4 4 \
    --invertMultichannelImage
