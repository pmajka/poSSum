set -x

WORK_DIR=/dev/shm/mdt_test_circle/

mu=64
sigma=16
n=10
image_size=128
image_center=64

function generate_moving_images {
python << END
import numpy as np

mu, sigma, n = $mu, $sigma, $n
samples = np.random.normal(mu, sigma, size=n)

for i in range(n):
    v=samples[i]
    print "convert -size ${image_size}x${image_size} xc:black -draw \"fill none stroke white stroke-linecap round stroke-width %0d line ${image_center},${image_center} ${image_center},${image_center}.0001\" img_%03d.png; c2d img_%03d.png -o moving/%04d.nii.gz" %(v, i, i, i)
END
}

function generate_fixed_images {
python << END
import numpy as np

mu, sigma, n = $mu, $sigma, $n
samples = np.random.normal(mu, sigma, size=n)

for i in range(n):
    v=samples[i]
    print "convert -size ${image_size}x${image_size} xc:black -draw \"fill none stroke white stroke-linecap round stroke-width ${mu} line ${image_center},${image_center} ${image_center},${image_center}.0001\" img_%03d.png; c2d img_%03d.png -o fixed/%04d.nii.gz" %(i, i, i)
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

# ---------------------------------------------------------
# Remove the results from the previous iterations
rm -rfv *.nii.gz

# ---------------------------------------------------------
# Start the calculations

pos_pairwise_registration \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --output-volumes-directory . \
    --loglevel DEBUG  \
    --grayscale-volume-filename test_1_gray.nii.gz\
    --multichannel-volume-filename test_1_color.nii.gz\
    -d /dev/shm/x/

pos_pairwise_registration \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --output-volumes-directory . \
    --loglevel DEBUG  \
    --skipPreprocessing \
    --skipTransformGeneration \
    --resliceBackgorund 255 \
    --grayscale-volume-filename test_2_gray.nii.gz\
    --multichannel-volume-filename test_2_color.nii.gz\
    -d /dev/shm/x/

pos_pairwise_registration \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --output-volumes-directory . \
    --loglevel DEBUG  \
    --skipPreprocessing \
    --skipTransformGeneration \
    --outputVolumeROI 64 64 64 64 \
    --grayscale-volume-filename test_3_gray.nii.gz\
    --multichannel-volume-filename test_3_color.nii.gz\
    -d /dev/shm/x/

pos_pairwise_registration \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --output-volumes-directory . \
    --loglevel DEBUG  \
    --skipPreprocessing \
    --skipTransformGeneration \
    --outputVolumeROI 0 0 64 64 \
    --grayscale-volume-filename test_4_gray.nii.gz\
    --multichannel-volume-filename test_4_color.nii.gz\
    -d /dev/shm/x/

pos_pairwise_registration \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --output-volumes-directory . \
    --loglevel DEBUG  \
    --fixedImageResize 2.0 \
    --movingImageResize 2.0 \
    --registrationColorChannelMovingImage red \
    --registrationColorChannelFixedImage red \
    --grayscale-volume-filename test_5_gray.nii.gz\
    --multichannel-volume-filename test_5_color.nii.gz\
    -d /dev/shm/x/

pos_pairwise_registration \
    --fixedImagesDir fixed/ \
    --movingImagesDir moving/ \
    --movingSlicesRange 0 9 \
    --fixedSlicesRange 0 9  \
    --output-volumes-directory . \
    --loglevel DEBUG  \
    --fixedImageResize 2.0 \
    --movingImageResize 2.0 \
    --medianFilterRadius 2 2 \
    --grayscale-volume-filename test_6_gray.nii.gz\
    --multichannel-volume-filename test_6_color.nii.gz\
    -d /dev/shm/x/

# -------------------------------------------------------------------
# Validate the md5 sums
# -------------------------------------------------------------------
md5sum -c test_pos_pairwise_alignment_ellipses.md5
