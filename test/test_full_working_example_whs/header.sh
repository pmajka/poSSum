#!/bin/bash -xe

# Setup some basic information about the processed volume
IDX_FIRST_SLICE=0
IDX_LAST_SLICE=311
RESLICE_BACKGROUND=0
SLICING_PLANE_INDEX=2

REFERENCE_SLICE=110
SEQ_REF_LONG=`printf %04d ${REFERENCE_SLICE}`

# This is quite important number which describes
# in-plane resolution of the image.
#SOURCE_SPACING=0.253782
SOURCE_SPACING=0.507564
SECTION_THICKNESS=0.25

# Define short and long output volume settings:
OV_PERMUTATION='0 1 2'
OV_ORIENTATION_CODE='RAS'
OV_TYPE='uchar'
OV_ORIGIN='0 0 0'
OV_SPACING="${SOURCE_SPACING} ${SOURCE_SPACING} ${SECTION_THICKNESS}"
OV_FLIP='0 0 0'

OV_SETTINGS_SHORT="--permutation ${OV_PERMUTATION} --flipAxes ${OV_FLIP} --setSpacing ${OV_SPACING}  --setOrigin ${OV_ORIGIN} --setType ${OV_TYPE} --orientationCode ${OV_ORIENTATION_CODE}"
OV_SETTINGS=" --outputVolumeSpacing ${OV_SPACING} --outputVolumeOrigin ${OV_ORIGIN} --outputVolumeOrientationCode ${OV_ORIENTATION_CODE}  --outputVolumePermutationOrder ${OV_PERMUTATION} --outputVolumeScalarType ${OV_TYPE} --setFlip ${OV_FLIP}"

# Setup input and output filenames
REFERENCE_VOLUME=input_for_reconstruction.nii.gz

# Define number of iterations in pairwise alignment
MAX_PAIRWISE_ITERATIONS=10
MAX_PAIRWISE_LONG=`printf %04d ${MAX_PAIRWISE_ITERATIONS}`

# Define names of a few directories
DIR_REFERENCE=00_reference/
DIR_SOURCE_STACKS=01_input_data/01_source_stacks/
DIR_SLICE_TO_SLICE_MASKED=01_input_data/01_rgb_to_resample/
DIR_SLICE_TO_SLICE_MASK=01_input_data/03_masks_to_resample/
DIR_SECTIONS_TO_SHAPE_PRIOR=01_input_data/02_sections_to_shape_prior/

DIR_COARSE_ALIGNMENT=__calculations__01_iterative_pariwise_alignment/
DIR_FINAL_PAIRWISE=transforms_01_pairwise/

DIR_SEQUENTIAL_ALIGNMENT=__calculations__02_sequential_alignment/
DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS=transforms_02_sequential/

DIR_DEFORMABLE_RECONSTRUCTION=__calculations__03_deformable_reconstruction/

mkdir -p ${DIR_DEFORMABLE_RECONSTRUCTION}
