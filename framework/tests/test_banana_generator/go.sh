
FIXED_DIR=f/
MOVING_DIR=m/
SEQUENTIAL_TRANSFORMS=sequential_transforms/
PAIRWISE_TRANSFORMS=pairwise_transforms/
AFTER_PAIRWISE=after_pairwise/

mkdir -p ${FIXED_DIR} ${MOVIG_DIR} \
    ${SEQUENTIAL_TRANSFORMS} \
    ${PAIRWISE_TRANSFORMS} \
    ${AFTER_PAIRWISE}

FIRST_SLICE=0
LAST_SLICE=15
REFERENCE_SLICE=7

python banana_generator.py

pos_stack_reorient.py \
    --stackingOptions ${FIRST_SLICE} ${LAST_SLICE} 1\
    -i ${MOVING_DIR}/%04d.png \
    -o m.nii.gz \
    --setSpacing 0.5 0.5 8
pos_slice_volume.py \
    -i m.nii.gz \
    -s 2 \
    -o ${MOVING_DIR}/%04d.nii.gz

pos_stack_reorient.py \
    --stackingOptions ${FIRST_SLICE} ${LAST_SLICE} 1\
    -i ${FIXED_DIR}/%04d.png \
    -o f.nii.gz \
    --setSpacing 0.5 0.5 8
pos_slice_volume.py \
    -i m.nii.gz \
    -s 2 \
    -o ${FIXED_DIR}/%04d.nii.gz

pos_pairwise_registration.py \
    --fixedSlicesRange  ${FIRST_SLICE} ${LAST_SLICE} \
    --movingSlicesRange  ${FIRST_SLICE} ${LAST_SLICE} \
    --fixedImagesDir ${FIXED_DIR} \
    --movingImagesDir ${MOVING_DIR} \
    --fixedImageResize 2.0 2.0 \
    --movingImageResize 2.0 2.0 \
    --medianFilterRadius 2 2 \
    --transformationsDirectory ${PAIRWISE_TRANSFORMS} \
    --grayscaleVolumeFilename pairwise_gray.nii.gz \
    --multichannelVolumeFilename pairwise_color.nii.gz \
    --outputVolumesDirectory . \
    --outputVolumeSpacing 0.5 0.5 8 \
    --outputVolumeOrientationCode RAS \
    --loglevel DEBUG \
    -d /dev/shm/pairwise/ \
    --antsImageMetric MSQ

#   --useRigidAffine \
pos_slice_volume.py \
    -i pairwise_color.nii.gz \
    -s 2 \
    -o ${AFTER_PAIRWISE}/%04d.nii.gz

pos_sequential_alignment.py \
    --sliceRange ${FIRST_SLICE} ${LAST_SLICE} ${REFERENCE_SLICE} \
    --inputImageDir ${AFTER_PAIRWISE} \
    --registrationColor blue \
    --registrationResize 2.0 2.0 \
    --medianFilterRadius 2 2 \
    --useRigidAffine \
    --outputVolumesDirectory . \
    --grayscaleVolumeFilename sequential_gray.nii.gz \
    --multichannelVolumeFilename sequential_rgb.nii.gz \
    --transformationsDirectory ${SEQUENTIAL_TRANSFORMS} \
    --outputVolumeSpacing 0.5 0.5 8 \
    --outputVolumeOrientationCode RAS \
    --loglevel DEBUG \
    -d /dev/shm/sequential/ \
