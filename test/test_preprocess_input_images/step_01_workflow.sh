#!/bin/bash -xe

# -------------------------------------------------------------------
# This example shows how to use the image preprocessing script
# which uses an XLS spreadsheet process a set of input sections in
# a typical image format (png, tif, jpg, anything which is well
# supported by the ImageMagick into a 3D stack used by
# the reconstruction workflows.
#
# The XLS spreadsheet contains metadata related to the individual
# images as well as the whole image stack. The individual serctions are
# processed into a 3D stack and all relevant information is embeded into the 3D
# stack (e.g. spacing, origin, anatomical directions, order of the sections,
# replacement, rotation flipping and what not.)
# 
# The script creates also a rudimentary mask based on the median filtering
# followed by a naive thresholding. It works suprisingly well.


specimen_id=test_case

DIR_RAW_SLICES=00_input_sections
DIR_INPUT_DATA=10_processed_sections

RESLICE_BACKGROUND=255


#--------------------------------------------------------------------
# Prepare the directory structure. It is not complicated this time
#--------------------------------------------------------------------
rm -rf  ${DIR_INPUT_DATA}
mkdir -p ${DIR_INPUT_DATA} ${DIR_RAW_SLICES}

# If you want to recreate the input images, use this command:
# bash -x generate_test_images.sh


# ------------------------------------------------------------------
# And now the main part: Starting the image preprocessing script.
# ------------------------------------------------------------------

pos_process_source_images \
     --loglevel=DEBUG \
     -d ${DIR_INPUT_DATA} \
     --input-images-dir ${DIR_RAW_SLICES} \
     --input-workbook ${specimen_id}.xls \
     --output-workbook ${specimen_id}_processed.xls \
     --header-file header.sh \
     \
     --enable-process-source-images \
         --canvas-gravity Center \
         --canvas-background White \
         --mask-threshold 50.0 \
         --mask-median 0 \
         --mask-color-channel red \
         --masking-background ${RESLICE_BACKGROUND} \
     \
     --enable-source-stacking \
         --use-slice-to-slice-mask \
     \
     --enable-remasking \
     \
     --enable-slice-extraction \
     \
     --disable-reference
