#!/bin/sh

# Images downloaded from the brainmaps.org website:
# http://brainmaps.org/index.php?action=viewslides&datid=94
# http://brainmaps.org/index.php?action=viewslides&datid=148
# http://brainmaps.org/index.php?action=viewslides&datid=60

list_of_files="mouse_immuno.nii.gz mouse_myelin.nii.gz mouse_nissl_1.nii.gz mouse_nissl_2.nii.gz"

for fixed_image in ${list_of_files}
do
    for moving_image in ${list_of_files}
    do
        prefix_fixed=`basename ${fixed_image} .nii.gz`
        prefix_moving=`basename ${moving_image} .nii.gz`

        pos_align_by_moments \
            -f ${fixed_image} \
            -m ${moving_image} \
            -o resliced_${prefix_moving}-to-${prefix_fixed}.nii.gz \
            -t transformation-${prefix_moving}-to-${prefix_fixed}.txt

        ImageMath 2 \
            comparison-${prefix_moving}-to-${prefix_fixed}.nii.gz \
            TileImages 3 \
            ${moving_image} \
            ${fixed_image} \
            resliced_${prefix_moving}-to-${prefix_fixed}.nii.gz

        rm -rf resliced_${prefix_moving}-to-${prefix_fixed}.nii.gz
    done
done
