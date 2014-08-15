#!/bin/bash -xe

source header.sh


# ---------------------------------------------------------
# Copy the reference images to the main directory, just for
# conveninece.

cp -v ${PHANTOM_MASKED} reference_image.nii.gz
cp -v ${PHANTOM_MASK} shape_prior.nii.gz

# ---------------------------------------------------------
# Slice the distorted image and the shape prior
# ---------------------------------------------------------

pos_slice_volume \
    -s ${SLICING_PLANE_INDEX} \
    -i shape_prior.nii.gz \
    -o 003_shape_prior_sections/%04d.nii.gz

pos_slice_volume \
    -s ${SLICING_PLANE_INDEX} \
    -i distorted_stack.nii.gz \
    -o 004_distorted_sections/%04d.nii.gz


# ---------------------------------------------------------
# Perform section-to-section alignment
# ---------------------------------------------------------

pos_pairwise_registration \
    --medianFilterRadius 2 2 \
    --antsImageMetric MI \
    --movingSlicesRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedSlicesRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --resliceBackgorund 0 \
    --fixedImagesDir 003_shape_prior_sections/ \
    --movingImagesDir 004_distorted_sections/ \
    --outputVolumesDirectory . \
    --transformationsDirectory 005_pairwise_alignment/ \
    --grayscaleVolumeFilename sections_to_shape_prior.nii.gz \
    --skipColorReslice \
        ${OV_SETTINGS} \
    --useRigidAffine \
    --loglevel DEBUG \
    --cleanup

# And then extract the sections:
pos_slice_volume \
    -s ${SLICING_PLANE_INDEX} \
    -i sections_to_shape_prior.nii.gz \
    -o 006_sections_to_shape_prior/%04d.nii.gz


# ---------------------------------------------------------
# Perform seqential alignment
# ---------------------------------------------------------

pos_sequential_alignment \
    --enable-sources-slices-generation \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} 110\
    --inputImageDir 006_sections_to_shape_prior/ \
    --registrationColor red \
    --enable-transformations \
        --useRigidAffine \
        --antsImageMetric MI \
        --resliceBackgorund 0 \
        --transformationsDirectory 007_sequential_alignment/ \
    --outputVolumesDirectory . \
        ${OV_SETTINGS} \
    --multichannelVolumeFilename sequential_alignment.nii.gz \
    --loglevel DEBUG \
    --cleanup


# ---------------------------------------------------------
# Perform coarse-to-fine-transformation merge
# ---------------------------------------------------------

mkdir -p 008_coarse_to_fine/01_smooth \
         008_coarse_to_fine/02_output

pos_coarse_fine \
    -i 007_sequential_alignment/ct_m%04d_f0110_Affine.txt \
    -s 008_coarse_to_fine/01_smooth/%04d.txt \
    -o 008_coarse_to_fine/02_output/%04d.txt \
    --sliceIndex ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --smoothingSimgaRotation 5 \
    --smoothingSimgaOffset 5 \
    --smoothingSimgaFixed 5 \
    --smoothingSimgaFixed 5 \
    --reportsDirectory 008_coarse_to_fine/ \
    --loglevel DEBUG \
    --cleanup

pos_stack_warp_image_multi_transform  \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedImageInputDirectory 006_sections_to_shape_prior/ \
    --movingImageInputDirectory 006_sections_to_shape_prior/ \
    --appendTransformation 0 007_sequential_alignment/ct_m%04d_f0110_Affine.txt \
    --appendTransformation 1 008_coarse_to_fine/01_smooth/%04d.txt \
        ${OV_SETTINGS} \
    --outputVolumesDirectory . \
    --volumeFilename coarse_to_fine.nii.gz \
    --loglevel DEBUG \
    --cleanup


# ---------------------------------------------------------
# Calculate the diference between the reference
# and the reconstructed images
# ---------------------------------------------------------

c3d coarse_to_fine.nii.gz reference_image.nii.gz \
    -scale -1 -add -dup -times -sqrt \
    -o reconstruction_discrepancy.nii.gz

# ---------------------------------------------------------
# Validate md5 sums of the obtained files
# ---------------------------------------------------------
md5sum -c test_banana_effect.md5

# ---------------------------------------------------------
# At the very end prove that coarse-to-fine reconstruction
# gave better results than just the pairwise alignment
# ---------------------------------------------------------

c3d reference_image.nii.gz sections_to_shape_prior.nii.gz -msq
# Should give MSQ = 60.0968

c3d coarse_to_fine.nii.gz reference_image.nii.gz -msq
# Should give:  MSQ = 45.9809
