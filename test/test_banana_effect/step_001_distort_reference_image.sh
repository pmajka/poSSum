#!/bin/bash -xe

source header.sh

# ---------------------------------------------------------
# Process the raw MR image into something on which we will
# be working on
# ---------------------------------------------------------
pos_stack_sections \
    -i ${INPUT_FILE} \
    -o ${PHANTOM_FILE} \
    --permutation 1 2 0 \
    --orientation RAS \
    --flip 0 1 1 \
    --origin 0 0 0 

c3d ${PHANTOM_FILE} ${PHANTOM_FILE} \
        -clip 0 255 \
        -reslice-itk ${TRANSFORMATION} \
        -region 140x0x60vox 60x200x150vox \
        -origin 0x0x0mm \
        -type uchar -o ${PHANTOM_FILE} \

if [ ! -f ${PHANTOM_MASK} ]
then
    c3d ${PHANTOM_FILE}\
        -thresh 20 255 1 0 \
        -type uchar -o ${PHANTOM_MASK}
fi

c3d ${PHANTOM_FILE} ${PHANTOM_MASK} -times \
    -type uchar -o ${PHANTOM_MASKED}


#--------------------------------------------------------------------
# Generate a random series of rigid transformations it order to distort
# the volume and then apply the transformation to the reference,
# undistorted data
#--------------------------------------------------------------------

# Generate the distortions
# python step_001_distort_reference_image.py \
#       step_001_distort_reference_image.cfg

# Extract the 2d sections from the 3d image
pos_slice_volume \
    -i 002_distorted_data/deformed_reference.nii.gz \
    -o "002_distorted_data/undistorted_sections/%04d.nii.gz" \
    -s ${SLICING_PLANE_INDEX}

# Apply the transformations to the individual sections.
for i in `seq ${IDX_FIRST_SLICE} 1 ${IDX_LAST_SLICE}`
do
    ii=`printf %04d $i`

    antsApplyTransforms -d 2 \
	--input 002_distorted_data/undistorted_sections/${ii}.nii.gz \
	--reference-image 002_distorted_data/undistorted_sections/${ii}.nii.gz \
	--output 002_distorted_data/distorted_sections/${ii}.nii.gz \
	--transform 002_distorted_data/section_transformations/${ii}.txt \
	--default-value ${RESLICE_BACKGROUND}
done

#------------------------------------------------------------------
# Stack the distorted slices into the volume and scale and orient
# the new volume in the same way as the reference volume is scaled
# and oreinted.

pos_stack_sections \
    -i "002_distorted_data/distorted_sections/%04d.nii.gz" \
    -o distorted_stack.nii.gz \
    --stacking-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} 1 \
    ${OV_SETTINGS_SHORT}

rm -rfv 002_distorted_data  
