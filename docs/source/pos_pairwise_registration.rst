Align sections pairwisely
=========================


.. highlight:: bash

.. contents::
   :local:
   :depth: 2


Usage summary
-------------


Providing information on slices to process
------------------------------------------

There are two ways of defining the moving slice image. Either:

    1. It can go from the source moving slices that were used
       for the registration purposes.

       or

    2. The moving images can go from the additional images stack.
       This is solved by passing the whole ``filename`` parameter.

Ok, what is going on here? In the workflow there are two types of ranges: the
moving slices range and the fixed slices range. In general they do not
necessarily overlap thus in general they are two different ranges. The
corespondence between ranges is established according to the
``imagePairsAssignmentFile`` file supplied via the command line. If neither
moving slices range nor fixes slices range are provided, the approperiate
ranges are copied from the general slice range. When provided, the custom
slices ranges override the default slice range value.


How to process additional image stacks
+++++++++++++++++++++++++++++++++++++++++++++

.. note ::
    First of all: additional stack settings are optional while the primary image
    stacks are obligatory.

    Second of all: The additional image stack should comprise only **three channel,
    8bit per pixel RGB** images. The workflow will not work for any other type of images.
    provided as a additional images.

This workflow supports a very nice functionality of handling more than one
image stack to process. While the transformations are caluclated based on a
single image stack (let's call it a `primary image stack`), the transformation
may be applied to other image stacks (reffered as the `additional image stacks`).


Providing additional image stacks
+++++++++++++++++++++++++++++++++++++++++++++

Information on additional image stacks is provided using several command line
arguments, namely: ``--additionalMovingImagesDirectory``,
``--additionalInvertMultichannel``, ``--additionalMultichannelVolume``,
``--additionalInterpolation``, ``--additionalInterpolationBackground``. For every
additional image stacks all of the command arguments have to be provided.
Skipping any of the parametrers will cause the workflow to collapse.

The parameters have the following meaning:

    1. ``--additionalInvertMultichannel``: directory containing the input images
    comprising the image stack. The input images have to provided as three
    channel, 8bit per channel RGB images. The names should comply the
    ``%04d.nii.gz`` format and the indexes of the slices have to be the same as
    the indexed of the primary moving stack.

    2. ``--additionalInvertMultichannel``: Determines of the input images are
    inverted ofr the purpose of reslicing. Only two values are allowed: Either
    ``1`` or ``0``.

    3. ``--additionalMultichannelVolume``: Filename of the output rgb volume. The
    parameters is no less obligatory than all the other parameters. Output
    volumes of additional image stacks are created in the same directory as the
    volumes of the regular image stacks.

    4. ``--additionalInterpolation``: Determines the interpolation method to
    apply during reslicing of the given stack. The allowed values are the same
    as those for interpolation of the primary image stacks.

    5. ``--additionalInterpolationBackground``: Default background color to be
    used during reslicing of the image stack (a value for the individual
    channels).

Only when all the parameters describing single additional image stack are
provided, the setting of the another stack could be specified. On other words:
one have to specify a block of parameteter for the one image stack before
specifying description of the another one.



Setting the properties of the resliced images
---------------------------------------------

Define output images stack origin and and size according to the
providing command line arguments. If provided, the resliced images are
cropped before stacking into volumes. Note that when the slices are
cropped their origin is preserved. That should be taken into
consideration when origin of the stacked volume if provided.

When the output ROI is not defined, nothing special will happen.
Resliced images will not be cropped in any way.


An example of an advanced usage
--------------------------------------

Here is a pretty comprehensive example of a pairwise registration script.
Utilizes typical options::

    pos_pairwise_registration.py \
            --fixedImagesDir fixed_images_directory/ \
            --movingImagesDir moving_images_directory/ \
            --movingSlicesRange 10 20  \
            --fixedSlicesRange 10 20   \
            --registrationColorChannelMovingImage blue  \
            --registrationColorChannelFixedImage green  \
            --resliceBackgorund 255  \
            --medianFilterRadius 4 4 \
            --outputVolumesDirectory output_volumes_directory/ \
            --useRigidAffine \
            --loglevel DEBUG \
            --output-volume-spacing 0.02 0.02 0.06 \
            --dry-run

