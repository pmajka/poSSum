#!/bin/bash -xe

NO_OF_BANANA=3
# Master banana = 1

# Define some important filenames         
INPUT_FILE=000_raw_data/20140612_142959t2tsevflisos006a1001.nii.gz
PHANTOM_FILE=001_phantom_master/phantom.nii.gz
PHANTOM_MASK=001_phantom_master/phantom_mask.nii.gz
PHANTOM_MASKED=001_phantom_master/phantom_masked.nii.gz
SEGMENTATION_FILE=000_raw_data/raw_segmentation.nii.gz
FILE_REFERENCE_MASK=001_phantom_master/phantom_masked.nii.gz
MASK_FILE=001_phantom_master/mask.nii.gz

# Indexing in arrays -> [NO_OF_BANANA - 1]

# Variables used to select ROIs of corresponding bananas
ROIS=()
ROIS[1]="70x40x0vox 130x120x200vox"
ROIS[2]="31x49x0vox 130x120x200vox"
ROIS[3]="80x40x0vox 130x120x210vox"
ROIS[4]="120x10x0vox 130x120x200vox"



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

OV_SETTINGS_SHORT="--permutation ${OV_PERMUTATION} --flipAxes ${OV_FLIP} --setSpacing ${OV_SPACING}  --setOrigin ${OV_ORIGIN} --setType ${OV_TYPE} --orientation ${OV_ORIENTATION_CODE}"
OV_SETTINGS=" --outputVolumeSpacing ${OV_SPACING} --outputVolumeOrigin ${OV_ORIGIN} --outputVolumeOrientationCode ${OV_ORIENTATION_CODE}  --outputVolumePermutationOrder ${OV_PERMUTATION} --outputVolumeScalarType ${OV_TYPE} --setFlip ${OV_FLIP}"
