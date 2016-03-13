#!/bin/bash -xe

source header.sh


# -------------------------------------------------------------------
# At this stage the only step that left is the deformbale reconstruction
# which is carried out below.
# Note that the image which is an input for the reconstruction has
# a sampling of 1x1x1mm which is required for the deformable registration
# routines. Spacing of a different order of magnitude (e.g. 0.01 or 10)
# would cause faulire of the ANTS registration.
# -------------------------------------------------------------------

c3d sequential_alignment.nii.gz \
    -type uchar -spacing 1x1x1mm \
    -o input_for_deformable_reconstruction.nii.gz

pos_deformable_histology_reconstruction \
    --inputVolume 1 input_for_deformable_reconstruction.nii.gz \
    --work-dir ${DIR_DEFORMABLE_RECONSTRUCTION} \
    --slicingPlane ${SLICING_PLANE_INDEX} \
    --planeSpacing ${SOURCE_SPACING} \
    --startSlice ${IDX_FIRST_SLICE} \
    --endSlice ${IDX_LAST_SLICE} \
    --iterations 8 \
    --neighbourhood 1 \
    --outputNaming output_ \
    --ants-image-metric-opt 2 \
    --antsTransformation 0.01 \
    --antsRegularization 2.0 1.0 \
    --antsIterations 1000x1000x1000x1000x1000x1000x1000 \
    ${OV_SETTINGS} \
    --loglevel DEBUG \
    --stackFinalDeformation
rm -rfv input_for_deformable_reconstruction.nii.gz


# -------------------------------------------------------------------
# And the last step of the workflow is to apply all the individual
# transformations to the source images which will produce the final RGB Image
# -------------------------------------------------------------------

pos_stack_warp_image_multi_transform \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedImageInputDirectory ${DIR_SLICE_TO_SLICE_MASKED} \
    --movingImageInputDirectory ${DIR_SLICE_TO_SLICE_MASKED} \
    --appendTransformation 0 ${DIR_DEFORMABLE_RECONSTRUCTION}/10_rescaled_deformation/%04d.nii.gz \
    --appendTransformation 0 ${DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS}/ct_m%04d_f${SEQ_REF_LONG}_Affine.txt \
    --appendTransformation 0 ${DIR_FINAL_PAIRWISE}/%04d.txt \
    ${OV_SETTINGS} \
    --output-volumes-directory . \
    --volumeFilename final_image.nii.gz \
    --loglevel DEBUG \
    --work-dir __stack__final_image \
    --cleanup

pos_stack_warp_image_multi_transform \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedImageInputDirectory ${DIR_SLICE_TO_SLICE_MASK} \
    --movingImageInputDirectory ${DIR_SLICE_TO_SLICE_MASK} \
    --appendTransformation 0 ${DIR_DEFORMABLE_RECONSTRUCTION}/10_rescaled_deformation/%04d.nii.gz \
    --appendTransformation 0 ${DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS}/ct_m%04d_f${SEQ_REF_LONG}_Affine.txt \
    --appendTransformation 0 ${DIR_FINAL_PAIRWISE}/%04d.txt \
    ${OV_SETTINGS} \
    --output-volumes-directory . \
    --volumeFilename final_image_mask.nii.gz \
    --loglevel DEBUG \
    --work-dir __stack__final_mask \
    --cleanup

pos_stack_warp_image_multi_transform \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedImageInputDirectory ${DIR_SLICE_TO_SLICE_MASKED} \
    --movingImageInputDirectory ${DIR_SLICE_TO_SLICE_MASKED} \
    --appendTransformation 0 ${DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS}/ct_m%04d_f${SEQ_REF_LONG}_Affine.txt \
    --appendTransformation 0 ${DIR_FINAL_PAIRWISE}/%04d.txt \
    ${OV_SETTINGS} \
    --output-volumes-directory . \
    --volumeFilename final_image_coarse_to_fine.nii.gz \
    --loglevel DEBUG \
    --work-dir __stack__final_image \
    --cleanup

pos_stack_warp_image_multi_transform \
    --sliceRange ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} \
    --fixedImageInputDirectory ${DIR_SLICE_TO_SLICE_MASK} \
    --movingImageInputDirectory ${DIR_SLICE_TO_SLICE_MASK} \
    --appendTransformation 0 ${DIR_SEQUENTIAL_ALIGNMENT_TRANSFORMS}/ct_m%04d_f${SEQ_REF_LONG}_Affine.txt \
    --appendTransformation 0 ${DIR_FINAL_PAIRWISE}/%04d.txt \
    ${OV_SETTINGS} \
    --output-volumes-directory . \
    --volumeFilename final_image_mask_coarse_to_fine.nii.gz \
    --loglevel DEBUG \
    --work-dir __stack__final_mask \
    --cleanup

# -------------------------------------------------------------------
# Well... and this is actually the end of the calculations
# -------------------------------------------------------------------
