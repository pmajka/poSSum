This workflow executes the sequential alignment procedure.
#TODO: Put something more about the sequrntial alignment procedure.


Sequential alignment workflow
=======================================

.. highlight:: bash

Usage summary
-------------

A minimum working example of the sequential alignment script ::

    python pos_sequential_alignment.py \
    [start stop ref] --sliceRange 50 70 60 \
    [directory]      --inputImageDir <directory_name>


Assumptions of the input images
--------------------------------------

All the input images are expected to be in one of the formats described below :

1. Three channel, 8-bit per channel RGB image in NIfTI format.
2. Single channel 8-bit (0-255) image, for instance a 8-bit grayscale image
   in NIfTI format.

No other input image type is supported, trying to apply any other image
specification will surely cause errors. Obviously, the spacing as well as the
image origin and directions does matter. All transformations are generated based
on the input images reference system thus, the best way is to supply NIfTI files
as the input images.


Input images naming scheme
--------------------------

TODO: Describe the parameters for the workflow.
Images in order Continous naming, Reference slice ::

    python pos_sequential_alignment.py \
            --inputImageDir dir_with_the_niftii_images/ \
            --sliceRange 10 120 60
            --loglevel DEBUG \
            --registrationColor blue \
            --median-filter-radius 4 4 \
            --reslice-backgorund 255 \
            --disable-source-slices-generation \
            --use-rigid-affine \
            --enableTransformations \
            --enableReslice \
            --output-volume-spacing 0.02 0.02 0.06


Description of the output files
-------------------------------

As an output of the sequential alignment script many output files are produced
apart from the aligned volumes. Below contents and meaning of the individual
files are explained:

    1. Transformation report: Contains transformation parameteres calculated
    for individual slices. The file contains only parameters related to the
    rigid transformation: translation vector as well as rotation angle.

    2. Graph edges file. A file holding a graph in which the vertices are the
    images and the edges weights are based on the image similarity.

    3. Similarity measure between individual images.
