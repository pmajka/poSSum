#!/bin/bash -xe

# Setup some basic information about the processed volume
IDX_FIRST_SLICE=0
IDX_LAST_SLICE=199
REFERENCE_SLICE=100
RESLICE_BACKGROUND=0
SLICING_PLANE_INDEX=1

# Define short and long output volume settings:
OV_PERMUTATION='0 2 1'
OV_ORIENTATION_CODE='RAS'
OV_TYPE='uchar'
OV_ORIGIN='0 0 0'
OV_SPACING='1 1 1'
OV_FLIP='0 1 1'

OV_SETTINGS_SHORT="--permutation ${OV_PERMUTATION} --flip ${OV_FLIP} --setSpacing ${OV_SPACING}  --setOrigin ${OV_ORIGIN} --setType ${OV_TYPE} --orientation ${OV_ORIENTATION_CODE}"
OV_SETTINGS=" --outputVolumeSpacing ${OV_SPACING} --outputVolumeOrigin ${OV_ORIGIN} --outputVolumeOrientationCode ${OV_ORIENTATION_CODE}  --outputVolumePermutationOrder ${OV_PERMUTATION} --outputVolumeScalarType ${OV_TYPE} --flip ${OV_FLIP}"
