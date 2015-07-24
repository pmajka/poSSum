#!/bin/bash -xe

source header.sh

## Preparing direcotory tree

mkdir -p 001_phantom\
  002_distorted_data/distorted_sections/ \
  002_distorted_data/section_transformations \
  002_distorted_data/undistorted_sections/ \

# ---------------------------------------------------------
# Process the raw MR image into something on which we will
# be working on
# ---------------------------------------------------------

#thresholding segmentation file to extract 1 banana
c3d ${SEGMENTATION_FILE} \
    -thresh ${NO_OF_BANANA} ${NO_OF_BANANA} 1 0 \
    -type uchar \
    -o ${PHANTOM_MASK}

c3d ${INPUT_FILE} ${PHANTOM_MASK} -times \
    -clip 0 255 \
    -region ${ROIS[${NO_OF_BANANA}-1]} \
    -type uchar -o ${PHANTOM_MASKED}
    
#cutting mask
c3d ${PHANTOM_MASK} \
    -clip 0 255 \
    -region ${ROIS[${NO_OF_BANANA}-1]} \
    -type uchar \
    -o ${PHANTOM_MASK}

#cutting phantom
c3d ${INPUT_FILE} \
    -clip 0 255 \
    -region ${ROIS[${NO_OF_BANANA}-1]} \
    -type uchar \
    -o ${PHANTOM_FILE}
    
#reorientig phantom, mask and masked phantom    
pos_stack_reorient \
    -i ${PHANTOM_MASKED} \
    -o ${PHANTOM_MASKED} \
    --permutation 1 2 0 \
    --orientation RAS \
    --flipAxes 0 1 0 \
    --setOrigin 0 0 0
    
pos_stack_reorient \
    -i ${PHANTOM_FILE} \
    -o ${PHANTOM_FILE} \
    --permutation 1 2 0 \
    --orientation RAS \
    --flipAxes 0 1 0 \
    --setOrigin 0 0 0
    
pos_stack_reorient \
    -i ${PHANTOM_MASK} \
    -o ${PHANTOM_MASK} \
    --permutation 1 2 0 \
    --orientation RAS \
    --flipAxes 0 1 0 \
    --setOrigin 0 0 0



#--------------------------------------------------------------------
# Generate a random series of rigid transformations it order to distort
# the volume and then apply the transformation to the reference,
# undistorted data
#--------------------------------------------------------------------

## Generate the distortions
python step_001_distort_reference_image.py \
       step_001_distort_reference_image.cfg

# Extract the 2d sections from the 3d image
pos_slice_volume \
    -i 002_distorted_data/deformed_reference.nii.gz \
    -o "002_distorted_data/undistorted_sections/%04d.nii.gz" \
    -s ${SLICING_PLANE_INDEX}

# Apply the transformations to the individual sections.
for i in `seq ${IDX_FIRST_SLICE} 1 ${IDX_LAST_SLICE}`
do
    ii=`printf %04d $i`

    echo "antsApplyTransforms -d 2 \
    --input 002_distorted_data/undistorted_sections/${ii}.nii.gz \
    --reference-image 002_distorted_data/undistorted_sections/${ii}.nii.gz \
    --output 002_distorted_data/distorted_sections/${ii}.nii.gz \
    --transform 002_distorted_data/section_transformations/${ii}.txt \
    --default-value ${RESLICE_BACKGROUND}" >> 002_distorted_data/tempfile.txt
done

parallel -j 8 -k < 002_distorted_data/tempfile.txt

#------------------------------------------------------------------
#~ # Stack the distorted slices into the volume and scale and orient
#~ # the new volume in the same way as the reference volume is scaled
#~ # and oriented.

pos_stack_reorient \
    -i "002_distorted_data/distorted_sections/%04d.nii.gz" \
    -o distorted_stack.nii.gz \
    --stacking-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} 1 \
    ${OV_SETTINGS_SHORT}

rm -rfv 002_distorted_data  
