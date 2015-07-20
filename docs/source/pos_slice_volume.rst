Extract slices from a volume
===========================================================================

``pos_slice_volume`` - a volume slicing script.

.. highlight:: bash


Usage summary
--------------

All supported features in one invocation::

    pos_slice_vol.py  -i filename.nii.gz
                       -s 1
    [start, end, step] -r 20 50 1
                       -o /some/path/prefix_%04d_suffix.ext
                       --shiftIndexes 1
    [ox, oy, sx, sy]   --extract-roi 20 30 50 50


Simple usage example
--------------------

A script for extracting slices from given input volume in a flexible way.
Check the examples below.
The script requires only one input parameter - the image to slice:
``inputFileName`` which is supposed to be a valid three dimensional image
supported by the itk. The simplest invocation is::

    pos_slice_vol.py -i filename.nii.gz


Slicing along particular axis
-----------------------------

The code sample above will slice the ``filename.nii.gz`` according to the default
settings. In order to select a particular slicing plane use ``--sliceAxisIndex``
or ``-s`` switch::

    pos_slice_vol.py -i filename.nii.gz -s <slicing_plane=0,1,2>


Extracting certain range
------------------------

One can also select a particular range of slices to extract. Note the range has
to be within image's limit - it cannot exceed the actual number of slices in
given plane, otherwise, an error will occur. The slicing range works like
python :py:func:`range` function. Use either ``--sliceRange`` or ``-r`` switch to
set slices to extract, e.g. ::

    pos_slice_vol.py -i filename.nii.gz -s 1 --sliceRange 0 20 1

Will extract the first twenty slices of the Y (second) axis.


Imposing naming scheme for the extracted slices
-----------------------------------------------

So far, the extracted slices were saved using default output naming scheme
which is ``%04d.png``. One can use any valid naming scheme which should
include output path as well as output filename scheme. E.g. to save the
extracted slices in home directory, using ``slice_`` prefix, pad the output number
to three digits and save slices as jpegs, the ``--file-series-format`` or ``-o``
parameter should be the following (**remember - use** ``%d`` **format!**)::

    pos_slice_vol.py -i filename.nii.gz --file-series-format /home/user/slice_%03d.jpg

Note that the output format has to support the input image type. For instance,
if the input file has a ``float`` data type, saving extracted slices as PNGs will
cause a type error. Please make sure that your input and output types are
compatible.


Altering the output sections' indexes
-------------------------------------

Sometimes, one will need to shift the indexes of the output slices, for
instance, save slice 0 as file 5, slice 5 as slice 10 and so on (e.g. to match
some other series). This effect may be achieved by issuing ``--shiftIndexes
<int>`` switch which shifts the output naming by provided number (either
positive or negative). As you may guess the default value is zero which means
that this parameter has no influence::

    pos_slice_vol.py -i filename.nii.gz --sliceAxisIndex 5


Extracting particular region
----------------------------

Another possibility of manipulation of the slices is extraction of the
subregion from the whole slice. This may be achieved by using ``--extract-roi``
switch. The switch accepts four integer parameters, the first two values
denotes the origin of the extraction (in pixels) while the other two -- the
size of the extracted region. E.g.::

    pos_slice_vol.py -i filename.nii.gz --extract-roi 40 100 50 50

Will extract the square slice of 50x50 pixel that originates in pixel (40,100).
