#!/bin/bash -xe

IDX_FIRST_SLICE=1
IDX_LAST_SLICE=10
REFERENCE_SLICE=5

DIR_SEQUENTIAL_ALIGNMENT=input_images

# The set of sequential alignment below demonstrated the variety of output
# volume options (options specific to sequential alignment, the examples do not
# cover common output volume options like spacing, origin, orientation,
# permutation and flipping. Again: these are not covered here. Check other
# examples for examples using common output volume options.

# So what options are covered here?  Well, some specific options related to
# postprocessing images after reslicing but before stacking as well as some
# options applied during stacking but, as mentioned none of the common output
# postprocessing options.

# This tutorial goes as follows.
#   1) We will conduct a single reconstruction and store the
#      produced transformations in a directory (a fairly advanced feature).
#      Because of that, it will be possible to produce the output stack using
#      various postprocessing options (another advanced applications) without
#      actual need of redoing the registration every time (definitely something
#      advancedi).
#   2) We will produce a numerous output volumes using some advanced
#      postprocessing options. I will try to descripe why and where individual
#      options may come in handy.

# Define the output transformations directory:
DIR_OUTPUT_TRANSFORMATIONS=10_sequential_alignment_transformations
mkdir -p ${DIR_OUTPUT_TRANSFORMATIONS}

# Step one:
# Calculating transformations without generating the output volume(s). 
# What is gonna happen here is that we will run the registration and store the
# produced volume but, in this run either reslicing of the images nor producing
# ouput volumes will be conducted. This will come later on

# To disable the application of the caluclated transformations to the images
# based on which the transformations have been calculated use the
# `--disable-reslice` switch. To prevent the output volumes from being
# generated, use `--disable-output-volumes` switch. Note that the
# `--disable-output-volumes` parameter does not automatically invoked the
# `--disable-reslice` switch. Have in mind that you cannot generate output
# volumes if the images have not been resliced.

pos_sequential_alignment \
    --enable-sources-slices-generation \
    --slices-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
    --input-images-directory ${DIR_SEQUENTIAL_ALIGNMENT}/ \
    --registration-color-channel red \
    --enable-transformations \
        --disable-moments \
        --median-filter-radius 1 1 \
        --use-rigid-affine \
        --ants-image-metric CC \
        --reslice-backgorund 0 \
        --graph-edge-lambda 0.0 \
        --graph-edge-epsilon 1 \
    --transformations-directory ${DIR_OUTPUT_TRANSFORMATIONS}/ \
    --disable-reslice \
    --disable-output-volumes \
    --loglevel DEBUG \
    --cleanup

# Now we have the transformations calculated and it is time to apply those
# transformations to the actual images. This will be the simplest example of
# applying the transformations to images without having to conduct the actual
# coregistration. The example below is equivalent to providing 
# `--enable-reslice` switch in the example below instead of the 
# `--disable-reslice`

pos_sequential_alignment \
    --enable-sources-slices-generation \
    --slices-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
    --input-images-directory ${DIR_SEQUENTIAL_ALIGNMENT}/ \
    --disable-transformations \
    --transformations-directory ${DIR_OUTPUT_TRANSFORMATIONS}/ \
    --enable-reslice \
    --enable-output-volumes \
        --output-volumes-directory . \
        --multichannel-volume-filename rgb_volume_ver_1.nii.gz \
        --grayscale-volume-filename grayscale_volume_ver_1.nii.gz \
    --loglevel DEBUG \
    --cleanup


# Here we crop the reconstructed stack of images fter they have been resliced.
# This is done by issuing the `--output-volume-roi` switch. First, you provide
# the origin of the region to crop (ox oy) and then the size of the cropping
# (sx, sy). Alltoheather: (ox, oy, sx sy).

# This feature is usefull when one wants to extract a region
# of interest from the larger image. In this example we cropped
# the object of interest from the larger image.

pos_sequential_alignment \
    --enable-sources-slices-generation \
    --slices-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
    --input-images-directory ${DIR_SEQUENTIAL_ALIGNMENT}/ \
    --disable-transformations \
    --transformations-directory ${DIR_OUTPUT_TRANSFORMATIONS}/ \
    --enable-reslice \
    --enable-output-volumes \
        --output-volumes-directory . \
        --multichannel-volume-filename rgb_volume_ver_2.nii.gz \
        --grayscale-volume-filename grayscale_volume_ver_2.nii.gz \
        --output-volume-roi 80 40 150 150 \
    --loglevel DEBUG \
    --cleanup


# Another fairly advanced option is to resample (upsample or downsample)
# the 2D image immediately after resampling and cropping but before stacking.
# Note the order: first there is reslicing, they you have cropping and
# only after that you have the resampling.
# The resampling is issued with the `--reslice-resampling` switch. Two numbers
# are required which are interpreted as what is the size of the resized images
# with respect to the original image expressed in percents.
# In other words, when you put 50, the image will be downsampled twice.
# If you put 200, the image will be upsampled twice. Of course, you can put
# two different numbers.


pos_sequential_alignment \
    --enable-sources-slices-generation \
    --slices-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
    --input-images-directory ${DIR_SEQUENTIAL_ALIGNMENT}/ \
    --disable-transformations \
    --transformations-directory ${DIR_OUTPUT_TRANSFORMATIONS}/ \
    --enable-reslice \
    --enable-output-volumes \
        --output-volumes-directory . \
        --multichannel-volume-filename rgb_volume_ver_3.nii.gz \
        --grayscale-volume-filename grayscale_volume_ver_3.nii.gz \
        --output-volume-roi 80 40 150 150 \
        --reslice-resampling 50 50 \
    --loglevel DEBUG \
    --cleanup


# Note that that upon resampling the information about the spacing is
# scrambled and you have to apply spacing on your own:

pos_sequential_alignment \
    --enable-sources-slices-generation \
    --slices-range ${IDX_FIRST_SLICE} ${IDX_LAST_SLICE} ${REFERENCE_SLICE}\
    --input-images-directory ${DIR_SEQUENTIAL_ALIGNMENT}/ \
    --disable-transformations \
    --transformations-directory ${DIR_OUTPUT_TRANSFORMATIONS}/ \
    --enable-reslice \
    --enable-output-volumes \
        --output-volumes-directory . \
        --multichannel-volume-filename rgb_volume_ver_4.nii.gz \
        --grayscale-volume-filename grayscale_volume_ver_4.nii.gz \
        --output-volume-roi 80 40 150 150 \
        --reslice-resampling 300 50 \
        --output-volume-spacing 0.5 3 1 \
    --loglevel DEBUG \
    --cleanup

#TODO some time in the future: Provide an example for the 
# --reslice-interpolation NearestNeighbor \ 
# option.

# ---------------------------------------------------------
# At the end of the day we would like to know if our test
# results match the reference images, in order to do that
# we compare md5 sums of the generated files.
# Please not that it it likely to happen that the md5 sums
# will not match. This is very unfortunate, but the
# images will be generated properly. If you know
# how to nicely handle such kind of porblem, please let
# me know
# ---------------------------------------------------------
md5sum -c sequential_alignment_advanced.md5
