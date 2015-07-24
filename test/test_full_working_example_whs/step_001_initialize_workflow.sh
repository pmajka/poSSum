#!/bin/bash -xe

source header.sh


# ---------------------------------------------------------
# NOTE: The commented code below is a preprocessing code.
# You do not have to execute the code below if you only
# wish to reproduce the results of this reconstruction.
#
# Multiplying original stack by mask, used to remove nervers,
# tissue or debris which are not present on original MRI scan
# and are typically due to the staining procedures.
# ---------------------------------------------------------

#c3d -verbose \
#    ${DIR_SOURCE_STACKS}/slice_to_slice_mask_stack.nii.gz -popas mask -clear \
#    -mcs ${DIR_SOURCE_STACKS}/rgb_stack.nii.gz \
#    -foreach \
#       -push mask -times -replace 0 255 -type uchar -endfor \
#    -omc 3 ${DIR_SOURCE_STACKS}/rgb_slice_to_slice_masked_stack.nii.gz

####c3d -verbose \
####    ${DIR_SOURCE_STACKS}/slice_to_slice_mask_stack.nii.gz \
####	-spacing ${SOURCE_SPACING}x${SOURCE_SPACING}x${SECTION_THICKNESS}mm \
####	-origin 0x0x0mm \
####	-type uchar \
####    -o ${DIR_SOURCE_STACKS}/slice_to_slice_mask_downsampled.nii.gz

####c3d -verbose \
####   -mcs ${DIR_SOURCE_STACKS}/rgb_slice_to_slice_masked_stack.nii.gz \
####   -foreach \
####       -spacing ${SOURCE_SPACING}x${SOURCE_SPACING}x${SECTION_THICKNESS}mm \
####       -origin 0x0x0mm \
####       -type uchar \
####   -endfor \
####   -omc 3 ${DIR_SOURCE_STACKS}/rgb_slice_to_slice_masked_stack_downsampled.nii.gz
# ---------------------------------------------------------


# -------------------------------------------------------------------
# Split the 3d image into individual horizontal sections.
# -------------------------------------------------------------------

mkdir -p ${DIR_SLICE_TO_SLICE_MASKED} ${DIR_SLICE_TO_SLICE_MASK} 

pos_slice_volume \
      -i ${DIR_SOURCE_STACKS}/rgb_slice_to_slice_masked_stack_downsampled.nii.gz \
      -o ${DIR_SLICE_TO_SLICE_MASKED}/%04d.nii.gz \
      -s ${SLICING_PLANE_INDEX}

pos_slice_volume \
      -i ${DIR_SOURCE_STACKS}/slice_to_slice_mask_downsampled.nii.gz \
      -o ${DIR_SLICE_TO_SLICE_MASK}/%04d.nii.gz \
      -s ${SLICING_PLANE_INDEX}

# Then, get the Red color channel of the image. This channel will be used
# to drive the registration. Additionally, invert the image so that 0 will be
# a background color.

c3d ${DIR_SOURCE_STACKS}/rgb_slice_to_slice_masked_stack_downsampled.nii.gz \
    -scale -1 -shift 255 \
    -o ${DIR_SOURCE_STACKS}/rgb_slice_to_slice_masked_stack_downsampled_gray.nii.gz


# ------------------------------------------------------------------
# Now, prepare the reference dataset - in this case the Waxholm Space
# T1? MR image. To speed up the calculations, the reference image
# is seriously downsampled.
# ------------------------------------------------------------------

c3d ${DIR_REFERENCE}/atlas_fullsize.nii.gz \
    -resample 100%x100%x100% \
    -spacing 0.43x0.43x0.43mm\
    -origin 0x0x0mm \
    -type uchar \
    -o ${DIR_REFERENCE}/atlas.nii.gz

pos_stack_reorient \
    -i ${DIR_REFERENCE}/atlas.nii.gz \
    --orientation RAS \
    -o ${REFERENCE_VOLUME} \
    --flip 1 1 1 \
    --origin 0 0 0 \
    --type uchar

c3d ${REFERENCE_VOLUME} \
    -scale -1 -shift 255 \
    -o ${REFERENCE_VOLUME}
