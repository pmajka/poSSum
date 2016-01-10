Preprocess slices for registration 
===========================================================================

.. highlight:: bash


Usage summary
-------------

.. todo::

   Provide a graph showing how the input image is processed.

.. graphviz::

   digraph foo {
         "bar" -> "baz";
            }

All supported features in one invocation (an example) ::

    pos_slice_preprocess.py
        [required]      --inputFilename <filename>
                        --grayscaleOutputImage <filename>
                        --colorOutputImage <filename>
     [ox, oy, sx, sy]   --registrationROI 10 20 30 30
                        --registrationResize 0.5
     [red, green, blue] --color-channel red
                        --median-filter-radius 2 2
                        --invert-source-image
                        --invert-rgb-image


Desctiption
-----------

This script performs several operations on the 2d image in order to
prepare it to a coregistration or reconstruction process.


Input image requirements
________________________

The script requires only one input parameter - the slice image to process
(provided via ``--inputFilename`` command line option). It has to be in one of
the formats from the list below:

    1) Three channel, 8-bit per channel RGB image. A 24-bit PNG (no transparency)
       image is a good example here.
    2) Single channel 8-bit (0-255) image, for instance a 8-bit grayscale TIFF
       file.
    3) When a grayscale image in Nifti format is provided, it can be of any
       data type recognized by the itk.

Providing images not matching the specification above will surely lead to a **lot
of errors end even more confusion**. So please be carefull and examine type of
your image before supplying it to the script.


Output image type
-----------------

Depending on the provided output settings, the script produces:

    1) RGB: three channel `uchar` images in niftii format.
    2) Grayscale: single channel `float` image in niftii format.

The output images carry information about their spacing and origin thus are
fully suitable for registration procedures.


Simple usage example
--------------------

The folloving invocation takes an rgb input image and produces two output
files: grayscale (by default, the blue channel is extracted) and rgb image,
both in nifti format. No additional processing is performed ::

    pos_slice_preprocess
        [required]      --inputFilename <filename>
                        --grayscaleOutputImage <filename>
                        --colorOutputImage <filename>


Trim and rescale and image
--------------------------

The example below the script takes an image scales it down and extracts a
square from the whole image and outputs only color image::

    pos_slice_preprocess
        [required]      --inputFilename <filename>
                        --grayscaleOutputImage <filename>
                        --color-channel blue
                        --registrationResize 0.5
                        --registrationROI 200 200 100 100


Smooth and invert images
------------------------

Now some more complicated processing example. The code below takes an rgb image
for input, extracts default color channel and applies smoothing and inverts the
images. Both grayscale and rgb images are outputes. Note, however, that only
grayscale image is smoothed by the median workflow::

    pos_slice_preprocess
        [required]      --inputFilename <filename>
                        --grayscaleOutputImage <filename>
                        --colorOutputImage <filename>
                        --median-filter-radius 2 2
                        --invert-source-image
                        --invert-rgb-image

Examples
--------

Please see the examples in the `tests/test_slice_preprocess` directory which
contains several examples on using the `pos_slice_preprocess` script.
