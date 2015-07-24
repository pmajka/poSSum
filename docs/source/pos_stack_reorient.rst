Stack 2d images into 3d image and/or reorient
==================================================

Usage summary
-------------

.. highlight:: bash

All supported features in one invocation ::

   pos_stack_reorient.py -i input_file.nii.gz \
        RAS code           --orientation ras \
      string, see -h       --interpolation NearestNeighbor \
   [float float float]     --resample 0.5 0.5 0.5 \
   permutation of 0 1 2    --permutation 2 1 0 \
      [0-1 0-1 0-1]        --flip 1 0 1 \
          bool             --flip-around-origin \
   [float float float]     --spacing 0.05 0.05 0.05 \
   [float float float]     --setOrigin 0 0 0 \
                           --setType uchar


Introduction
------------

A swiss army knife for stacking slices and reorienting the volumes in
various ways!. It's a really nice tool, believe me.


The purpose of this class is to:
    * Stack individual 2D slices into volumes (either single- or multichannel)

    or

    * Load volumes (again: either single- or multichannel)

    and then:

    * Permute axes of the volumes or flip the volumes
    * Rescale the images (an)isotropically
    * Assign various anatomical orientation
    * And save them as volumes of various types

If stacking options are provided, the script works in
stacking mode - a stack of slices is red instead of a volume.
Then the stack is stacked (!) into a volume and processed as a typical
volume.


Requirements for the input images
_________________________________

The input image (images) have to comply with the specification below:

    * Grayscale images: any reasonable type and format:
        * types: uchar, ushort, float
        * formats: niftii (preffered), tiff, png, jpeg
          (if you use jpegs, your're not taking your job seriously :).

    * RGB images: **only** 24bpp RGB images.
        * Indexed colors does not work,
        * Alpha channel does not work,
        * Two channel images does not work
        * Seriously, check what you are putting in.


.. note::

    When stacking a multichannel stack of images you are only allowed to use
    **24bpp** rgb files, **no alpha channel**. Providing a different type of
    multichannel images will cause an error. However, you are fully allowed to
    use any usual type (uchar, ushort, float) of a single channel images.


.. note::
    The following options: ``--workDir``, ``--cleanup`` ``--disableSharedMemory``
    ``--dryRun`` and ``--cpuNo`` have no use in this script. Please don't use
    them.


The simplest example
--------------------

A few detailed examples of the volume stacking and reorienting script.

In order to stack a series of slices onto a volume, the following command
has to be invoked::

    pos_stack_reorient.py -i prefix_%04d.png \
                           --stacking-range 0 100 1 \
                           -o output.nii.gz

And that's it. The command above will stack a series of images (assuming that
they are compatibile with the script) from ``prefix_0001.png`` to
``prefix_0100.png`` with a step of a single slice. The resulting stack will be
saved as a ``output.nii.gz``. The data type of output volumetric file will be the same
as the input filetype.

