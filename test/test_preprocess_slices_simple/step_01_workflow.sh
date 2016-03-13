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


specimen_id=brainmaps_s40

DIR_RAW_SLICES=00_source_sections
DIR_RAW_REFERENCE=01_raw_reference
DIR_INPUT_DATA=10_input_data

RESLICE_BACKGROUND=255


#--------------------------------------------------------------------
# Prepare the directory structure. It is not complicated this time
#--------------------------------------------------------------------
rm -rf ${DIR_RAW_SLICES} ${DIR_INPUT_DATA}
mkdir -p ${DIR_RAW_SLICES} ${DIR_INPUT_DATA}

#--------------------------------------------------------------------
# Download the image stack to reconstruct. In case it is not already
# downloaded.
#--------------------------------------------------------------------

for section in `cat sections_to_download`
do
    if [ ! -f  ${DIR_RAW_SLICES}/${section}.jpg ]; then
        wget http://brainmaps.org/HBP-JPG/40/${section}.jpg \
            -O ${DIR_RAW_SLICES}/${section}.jpg 
        convert \
            ${DIR_RAW_SLICES}/${section}.jpg -level -10% \
            ${DIR_RAW_SLICES}/${section}.jpg
    fi
done 


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
         --mask-threshold 65.0 \
         --mask-median 4 \
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


#--------------------------------------------------------------------
# Only now we can load the actual header file
#--------------------------------------------------------------------

source header.sh
DIR_SEQUENTIAL_ALIGNMENT=11_sections_sequential_alignment/
mkdir -p ${DIR_SEQUENTIAL_ALIGNMENT}

# ---------------------------------------------------------
# Below a data for the sequential alignment is prepared.
# The red channel of the image is extracted and a negative
# image is calculated. This is due to the fact that the
# registration routines handles better images which have
# 0 as a background and nonzero values as content.
# ---------------------------------------------------------

c3d -mcs ${VOL_RGB_MASKED} \
    -foreach \
        -scale -1 -shift 255 -type uchar \
    -endfor \
    -omc 3 __temp__rgb_stack_inverted.nii.gz

pos_slice_volume \
    -s ${SLICING_PLANE_INDEX} \
    -i __temp__rgb_stack_inverted.nii.gz \
    --output-filenames-offset ${IDX_FIRST_SLICE} \
    -o ${DIR_SEQUENTIAL_ALIGNMENT}/%04d.nii.gz
rm -rfv __temp__rgb_stack_inverted.nii.gz


# ---------------------------------------------------------
# Perform seqential alignment
# ---------------------------------------------------------
REFERENCE_SLICE=25

pos_sequential_alignment \
    --enable-sources-slices-generation \
    --slices-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
    --input-images-directory ${DIR_SEQUENTIAL_ALIGNMENT}/ \
    --registration-color-channel red \
    --enable-transformations \
        --enable-moments \
        --median-filter-radius 4 4 \
        --use-rigid-affine \
        --ants-image-metric CC \
        --affine-gradient-descent 0.5 0.95 0.0001 0.0001 \
        --reslice-backgorund 0 \
        --graph-edge-lambda 0.0 \
        --graph-edge-epsilon 2 \
    --output-volumes-directory . \
    ${OUTPUT_VOLUME_PROPERTIES} \
    --multichannel-volume-filename sequential_alignment.nii.gz \
    --loglevel DEBUG

# ---------------------------------------------------------
# Yeap, that's it. 
# ---------------------------------------------------------
