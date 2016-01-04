#!/bin/bash
set -xe

# Generation date: 04_01_2016_13-35-50

SPECIMEN_NAME=test_case

STACK_SIZE=14
IDX_FIRST_SLICE=1
IDX_LAST_SLICE=14
IDX_FIRST_SLICE_ZERO=0
IDX_LAST_SLICE_ZERO=13

SOURCE_FULLRES_SPACING=0.500000
SOURCE_NOMINAL_SPACING=0.500000
SOURCE_SPACING=0.500000
SOURCE_THICKNESS=2.000000

FULLSIZE_CANVAS_SIZE="300 300"

ATLAS_PLATE_SPACING=0.100000
ATLAS_PLATE_EXTENT="1000 1000"

SLICING_PLANE_INDEX=1
SLICING_PLANE_VERBAL="coronal"

OUTPUT_VOLUME_SPACING="0.5 2.0 0.5"
OUTPUT_VOLUME_ORIGIN="0.0 0 0.0"
OUTPUT_VOLUME_PERMUTATION="0 2 1"
OUTPUT_VOLUME_FLIPPING="0 0 0"
OUTPUT_VOLUME_ORIENTATION="RAS"

OUTPUT_VOLUME_PROPERTIES=" --output-volume-permute-axes ${OUTPUT_VOLUME_PERMUTATION} --output-volume-orientation ${OUTPUT_VOLUME_ORIENTATION} --output-volume-spacing ${OUTPUT_VOLUME_SPACING} --output-volume-origin ${OUTPUT_VOLUME_ORIGIN} --output-volume-filp-axes ${OUTPUT_VOLUME_FLIPPING}"


VOL_MASK=10_processed_sections/08_source_stacks/mask_stack.nii.gz
VOL_RGB_MASKED=10_processed_sections/08_source_stacks/rgb_masked_stack.nii.gz
VOL_RGB_SLICE_TO_REF_MASKED=10_processed_sections/08_source_stacks/rgb_slice_to_reference_masked_stack.nii.gz
VOL_RGB_SLICE_TO_SLICE_MASKED=10_processed_sections/08_source_stacks/rgb_slice_to_slice_masked_stack.nii.gz
VOL_RGB=10_processed_sections/08_source_stacks/rgb_stack.nii.gz
VOL_SLICE_TO_REF_MASK=10_processed_sections/08_source_stacks/slice_to_reference_mask_stack.nii.gz
VOL_SLICE_TO_SLICE_MASK=10_processed_sections/08_source_stacks/slice_to_slice_mask_stack.nii.gz
VOL_ATLAS_TO_SLICE_MASK=10_processed_sections/08_source_stacks/atlas_mask_stack.nii.gz
VOL_ATLAS_RGB=10_processed_sections/08_source_stacks/atlas_rgb_stack.nii.gz
VOL_ATLAS_TO_SLICE_MASKED=10_processed_sections/08_source_stacks/atlas_masked_stack.nii.gz

DIR_IMAGES=10_processed_sections/10_seqential_input_images/
DIR_MASKS=10_processed_sections/11_seqential_input_masks/
DIR_SLICE_TO_SLICE_MASKED=10_processed_sections/12_slice_to_slice/
DIR_SLICE_TO_SLICE_MASKS=10_processed_sections/13_slice_to_slice_masks/
DIR_SLICE_TO_REF=10_processed_sections/14_slice_to_ref/
DIR_SLICE_TO_REF_MASK=10_processed_sections/15_slice_to_ref_masks/
DIR_REF_TO_SLICE=10_processed_sections/16_ref_to_slice/
DIR_REF_TO_SLICE_MASK=10_processed_sections/17_ref_to_slice_mask/


# Functions for slicing input stack into sections and 
# stacking back into 3D image. Useful in all intermediate
# stacking back into volumetric form.

hd_split_volume ()
{
    VOLUME=$1
    OUTPUT_DIR=`mktemp -d`

    pos_slice_volume \
        -i ${VOLUME} \
        -o ${OUTPUT_DIR}/%04d.nii.gz \
        --output-filenames-offset ${IDX_FIRST_SLICE} \
        -s ${SLICING_PLANE_INDEX} > /dev/null 2>&1 
    
    echo ${OUTPUT_DIR}
}

hd_stack_sections ()
{
    INPUT_DIR=$1
    OUTPUT_VOLUME=$2

    pos_stack_sections \
        -i ${INPUT_DIR}/%04d.nii.gz \
        -o ${OUTPUT_VOLUME} \
        --stacking-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} 1 \
        ${OUTPUT_VOLUME_PROPERTIES}  > /dev/null 2>&1 
     rm -rfv ${INPUT_DIR} 
}
