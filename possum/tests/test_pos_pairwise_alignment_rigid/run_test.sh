set -x

WORK_DIR=/dev/shm/mdt_test_circle/

mu=128
sigma=16
n=10
image_size=256
image_center=128

function generate_fixed_images {
python << END
import numpy as np

mu, sigma, n = $mu, $sigma, $n
samples1 = np.random.normal(mu, sigma, size=n)
samples2 = np.random.normal(mu, sigma, size=n)

for i in range(n):
    cx=samples1[i]
    cy=samples2[i]
    print "convert -size ${image_size}x${image_size} xc:black -fill white -draw \'circle %d,%d %d, %d\' fimg_%03d.png; c2d fimg_%03d.png -o fixed/%04d.nii.gz" %(${image_center}, ${image_center}, ${image_center}+48, ${image_center}+48, i, i, i)
END
}

function generate_moving_images {
python << END
import numpy as np

mu, sigma, n = $mu, $sigma, $n
samples1 = np.random.normal(mu, sigma, size=n)
samples2 = np.random.normal(mu, sigma, size=n)

for i in range(n):
    cx=samples1[i]
    cy=samples2[i]
    print "convert -size ${image_size}x${image_size} xc:black -fill white -draw \'circle %d,%d %d, %d\' mimg_%03d.png; c2d mimg_%03d.png -o moving/%04d.nii.gz" %(cx, cy, cx+48, cy+48, i, i, i)
END
}

# ---------------------------------------------------------
# Generate the source data - images to align
# ---------------------------------------------------------
# mkdir -p fixed
# mkdir -p moving
# generate_moving_images | bash -x
# generate_fixed_images | bash -x
# rm -vf *.png

python ../../pos_pairwise_registration.py \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --useRigidAffine \
    --outputVolumesDirectory . \
    --loglevel DEBUG  \
    --grayscaleVolumeFilename test_1_gray.nii.gz\
    --multichannelVolumeFilename test_1_color.nii.gz\
    -d /dev/shm/x/

python ../../pos_pairwise_registration.py \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --useRigidAffine \
    --outputVolumesDirectory . \
    --loglevel DEBUG  \
    --skipPreprocessing \
    --skipTransformGeneration \
    --resliceBackgorund 255 \
    --grayscaleVolumeFilename test_2_gray.nii.gz\
    --multichannelVolumeFilename test_2_color.nii.gz\
    -d /dev/shm/x/

python ../../pos_pairwise_registration.py \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --outputVolumesDirectory . \
    --useRigidAffine \
    --loglevel DEBUG  \
    --skipPreprocessing \
    --skipTransformGeneration \
    --outputVolumeROI 64 64 64 64 \
    --grayscaleVolumeFilename test_3_gray.nii.gz\
    --multichannelVolumeFilename test_3_color.nii.gz\
    -d /dev/shm/x/

python ../../pos_pairwise_registration.py \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --outputVolumesDirectory . \
    --useRigidAffine \
    --loglevel DEBUG  \
    --skipPreprocessing \
    --skipTransformGeneration \
    --outputVolumeROI 0 0 64 64 \
    --grayscaleVolumeFilename test_4_gray.nii.gz\
    --multichannelVolumeFilename test_4_color.nii.gz\
    -d /dev/shm/x/

python ../../pos_pairwise_registration.py \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --outputVolumesDirectory . \
    --useRigidAffine \
    --loglevel DEBUG  \
    --fixedImageResize 2.0 \
    --movingImageResize 2.0 \
    --registrationColorChannelMovingImage red \
    --registrationColorChannelFixedImage red \
    --grayscaleVolumeFilename test_5_gray.nii.gz\
    --multichannelVolumeFilename test_5_color.nii.gz\
    -d /dev/shm/x/

python ../../pos_pairwise_registration.py \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --outputVolumesDirectory . \
    --useRigidAffine \
    --loglevel DEBUG  \
    --fixedImageResize 2.0 \
    --movingImageResize 2.0 \
    --medianFilterRadius 2 2 \
    --grayscaleVolumeFilename test_6_gray.nii.gz\
    --multichannelVolumeFilename test_6_color.nii.gz\
    -d /dev/shm/x/
