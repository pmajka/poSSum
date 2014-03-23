Stack sections into volume and/or reorient volumes.
===========================================================================

A script for stacking slices and reorienting volumes
****************************************************

Usage summary
-------------

.. highlight:: bash

All supported features in one invocation (an example) ::

    $pos_stack_reorient.py -i input_file.nii.gz \
        RAS code           --orientationCode ras \
      string, see -h       --interpolation NearestNeighbor \
   [float float float]     --resample 0.5 0.5 0.5 \
   permutation of 0 1 2    --permutation 2 1 0 \
      [0-1 0-1 0-1]        --flipAxes 1 0 1 \
          bool             --flipAroundOrigin \
   [float float float]     --setSpacing 0.05 0.05 0.05 \
   [float float float]     --setOrigin 0 0 0 \
                           --setType uchar

Details - volume stacking
-------------------------

Some precise examples of using the volume stacking and reorienting script.  In
order to stack a series of slices onto a volume, the following command has to
be invoked::

    $pos_stack_reorient.py -i prefix_%04d.png \
                           --stackingOptions 0 100 1 \
                           -o output.nii.gz

And that's it. The command above will stack a series of images (assuming that
they are compatibile with the script) from `prefix_0001.png` to
`prefix_0100.png` with a step of a single slice. The resulting stack will be
saved as a `output.nii.gz`. The type of output volumetric file will be the same
as the input filetype.

.. note::

    When stacking a multichannel stack of images you are only allowed to use
    **24bpp** rgb files, no alpha channel. Providing a different type of
    multichannel images will cause an error. However, you are fully allowed to
    use any usual type (uchar, ushort, float) of a single channel images.

A swiss army knife for stacking slices and reorienting the volumes in
various ways!. It's a really nice tool, believe me.

The purpose of this class is to:
    * Stack individual 2D slices into volumes
        (either single- or multichannel)
    or
    * Load volumes (again: either single- or multichannel)

    and then:

    * Permute axes of the volumes or flip the volumes
    * Rescale the images (an)isotropically
    * Assign various anatomical orientation
    * And save them as volumes of various types

Assumptions for the input images:

    * Grayscale images: any reasonable type and format
    * RGB images: **ONLY** 24bpp RGB images.
            * Indexed colors does not work,
            * Alpha channel does not work,
            * Two channel images does not work
            * Really, check what you are putting in.

If stacking options are provided, the script works in
stacking mode - a stack of slices is red instead of a volume.
Then the stack is stacked (!) into a volume and processed as a typical
volume.

.. note::
    The following options: `--workDir`, `--cleanup` `--disableSharedMemory`
    `--dryRun` `--cpuNo` have no use in this script. So please don't use
    them.
