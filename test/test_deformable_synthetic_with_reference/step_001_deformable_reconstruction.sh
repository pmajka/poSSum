#!/bin/bash -xe

# -------------------------------------------------------------------
# At this stage the only step that left is the deformbale reconstruction
# which is carried out below.

# This particular test utilizes a reference volume '--referenceVolume'
# which is used as an additional metric to drive the registration.
# The reference volume remains constant all the time (the reference 
# section does not change over the course of the iteration).
#
# The number next to the reference volume filename is the weight
# of this particular metric.
#
# For the purpose of the registration the CC metric is used throghout
# the reconstruction process. Bear that in mind when choosing the
# reference volume.
#  
# Note that the image which is an input for the reconstruction has
# a sampling of 1x1x1mm which is required for the deformable registration
# routines. Spacing of a different order of magnitude (e.g. 0.01 or 10)
# would cause faulire of the ANTS registration.
# -------------------------------------------------------------------

DIR_DEFORMABLE_RECONSTRUCTION=${HOME}/deformable_test/
SLICING_PLANE_INDEX=2
SOURCE_SPACING=1
IDX_FIRST_SLICE=0
IDX_LAST_SLICE=99

c3d deformed_stack.nii.gz \
    -spacing 1x1x1mm \
    -o input_for_deformable_reconstruction.nii.gz

pos_deformable_histology_reconstruction \
    --inputVolume 1 input_for_deformable_reconstruction.nii.gz \
    --referenceVolume 1 initial_stack.nii.gz \
    --slicingPlane ${SLICING_PLANE_INDEX} \
    --planeSpacing ${SOURCE_SPACING} \
    --startSlice ${IDX_FIRST_SLICE} \
    --endSlice ${IDX_LAST_SLICE} \
    --iterations 12 \
    --neighbourhood 1 \
    --outputNaming output_ \
    --ants-image-metric CC \
    --ants-image-metric-opt 4 \
    --antsTransformation 0.01 \
    --antsRegularization 2.0 1.0 \
    --antsIterations 1000x1000x1000x1000 \
    --loglevel DEBUG \
    --stackFinalDeformation \
    --work-dir ${DIR_DEFORMABLE_RECONSTRUCTION} 
    
cp -v ${DIR_DEFORMABLE_RECONSTRUCTION}/08_intermediate_results/intermediate_output__0007.nii.gz \
      deformable_reconstruction_result.nii.gz

rm -rfv input_for_deformable_reconstruction.nii.gz
rm -rf ${DIR_DEFORMABLE_RECONSTRUCTION}
