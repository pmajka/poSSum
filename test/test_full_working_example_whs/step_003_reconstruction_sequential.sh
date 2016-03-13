#!/bin/bash
set -x

source header.sh


# ---------------------------------------------------------
# Clean up the obsolete calculations.
# ---------------------------------------------------------

rm -rvf ${DIR_SECTIONS_TO_SHAPE_PRIOR} \
      ${DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS}/ \

mkdir -p ${DIR_SECTIONS_TO_SHAPE_PRIOR} \
      ${DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS}/ \


# ---------------------------------------------------------
# Below a data for the sequential alignment is prepared.
# The red channel of the image is extracted and a negative
# image is calculated. This is due to the fact that the
# registration routines handles better images which have
# 0 as a background and nonzero values as content.
# ---------------------------------------------------------

c3d rgb_after_pairwise.nii.gz \
    -scale -1 -shift 255 \
    -o gray_after_pairwise.nii.gz

pos_slice_volume \
    -s ${SLICING_PLANE_INDEX} \
    -i gray_after_pairwise.nii.gz \
    -o ${DIR_SECTIONS_TO_SHAPE_PRIOR}/%04d.nii.gz


# ---------------------------------------------------------
# Perform seqential alignment
# ---------------------------------------------------------

pos_sequential_alignment \
 --enable-sources-slices-generation \
 --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
 --inputImageDir ${DIR_SECTIONS_TO_SHAPE_PRIOR}/ \
 --registrationColor red \
 --enable-sources-slices-generation \
 --enable-transformations \
     --enable-moments \
     --useRigidAffine \
     --antsImageMetric MI \
     --resliceBackgorund ${RESLICE_BACKGROUND} \
     --transformationsDirectory ${DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS}/ \
     --graphEdgeLambda 0.000 \
     --graphEdgeEpsilon 5 \
 --outputVolumesDirectory . \
     ${OV_SETTINGS} \
 --multichannel-volume-filename sequential_alignment.nii.gz \
 --work-dir ${DIR_SEQUENTIAL_ALIGNMENT} \
 --loglevel DEBUG \
 --cleanup

# ---------------------------------------------------------
# Yeap, that's it. 
# ---------------------------------------------------------
