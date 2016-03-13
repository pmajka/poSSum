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
    --median-filter-radius 2 2 \
    --ants-image-metric MI \
    --movingSlicesRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedSlicesRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --reslice-backgorund 0 \
    --fixedImagesDir 003_shape_prior_sections/ \
    --movingImagesDir 004_distorted_sections/ \
    --output-volumes-directory . \
    --transformations-directory 005_pairwise_alignment/ \
    --grayscale-volume-filename sections_to_shape_prior.nii.gz \
    --skipColorReslice \
        ${OV_SETTINGS} \
    --affineGradientDescent 0.5 0.95 0.0001 0.0001 \
    --use-rigid-affine \
    --disable-moments \
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
    --registration-color-channel red \
    --enable-transformations \
        --use-rigid-affine \
        --ants-image-metric MI \
        --reslice-backgorund 0 \
        --transformations-directory 007_sequential_alignment/ \
    --output-volumes-directory . \
        ${OV_SETTINGS} \
    --multichannel-volume-filename sequential_alignment.nii.gz \
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
    --sections-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --smoothing-simga-rotation 5 \
    --smoothing-simga-offset 5 \
    --smoothing-simga-fixed 5 \
    --reports-directory 008_coarse_to_fine/ \
    --loglevel DEBUG \
    --cleanup

pos_stack_warp_image_multi_transform  \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedImageInputDirectory 006_sections_to_shape_prior/ \
    --movingImageInputDirectory 006_sections_to_shape_prior/ \
    --appendTransformation 0 007_sequential_alignment/ct_m%04d_f0110_Affine.txt \
    --appendTransformation 1 008_coarse_to_fine/01_smooth/%04d.txt \
        ${OV_SETTINGS} \
    --output-volumes-directory . \
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
# At the very end prove that coarse-to-fine reconstruction
# gave better results than just the pairwise alignment
# ---------------------------------------------------------
# Cleaning up

rm -rv   002_distorted_data\
         003_shape_prior_sections \
         004_distorted_sections \
         005_pairwise_alignment \
         006_sections_to_shape_prior \
         007_sequential_alignment/ \
         008_coarse_to_fine \
         sequential_alignment_s-0_e-199_r-110_ROI-None_Resize-None_Color-red_Median-None_Metric-MI_MetricOpt-32_Affine-True_eps-1_lam0.00outROI-None_gray.nii.gz
         
c3d reference_image.nii.gz sections_to_shape_prior.nii.gz -msq > discrepancy_measurements.txt
# Should give MSQ = 55.3536

c3d coarse_to_fine.nii.gz reference_image.nii.gz -msq >> discrepancy_measurements.txt
# Should give: MSQ = 38.7323

# ---------------------------------------------------------
# Validate md5 sums of the obtained files
# ---------------------------------------------------------
md5sum -c test_banana_effect.md5
