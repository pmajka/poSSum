#!/bin/bash -xe

mkdir -p 002_distorted_data/distorted_sections/ \
         002_distorted_data/section_transformations \
         002_distorted_data/undistorted_sections/ \
         003_shape_prior_sections \
         004_distorted_sections \
         005_pairwise_alignment \
         006_sections_to_shape_prior \
         007_sequential_alignment/ \
         008_coarse_to_fine/ \

# Define some important filenames         
INPUT_FILE=000_raw_data/20140612_142959t2tsevflisos006a1001.nii.gz
TRANSFORMATION=001_phantom/straighten_the_image.txt
PHANTOM_FILE=001_phantom/phantom.nii.gz
PHANTOM_MASK=001_phantom/phantom_mask.nii.gz
PHANTOM_MASKED=001_phantom/phantom_masked.nii.gz

# Setup some basic information about the processed volume
IDX_FIRST_SLICE=0
IDX_LAST_SLICE=199
RESLICE_BACKGROUND=0
SLICING_PLANE_INDEX=1

# Define short and long output volume settings:
OV_PERMUTATION='0 2 1'
OV_ORIENTATION_CODE='RAS'
OV_TYPE='uchar'
OV_ORIGIN='0 0 0'
OV_SPACING='1 1 1'
OV_FLIP='0 0 0'

OV_SETTINGS_SHORT="--permutation ${OV_PERMUTATION} --flip ${OV_FLIP} --spacing ${OV_SPACING}  --setOrigin ${OV_ORIGIN} --setType ${OV_TYPE} --orientation ${OV_ORIENTATION_CODE}"
OV_SETTINGS=" --outputVolumeSpacing ${OV_SPACING} --outputVolumeOrigin ${OV_ORIGIN} --outputVolumeOrientationCode ${OV_ORIENTATION_CODE}  --outputVolumePermutationOrder ${OV_PERMUTATION} --outputVolumeScalarType ${OV_TYPE} --flip ${OV_FLIP}"
