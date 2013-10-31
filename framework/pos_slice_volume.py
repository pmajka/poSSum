#!/usr/bin/python
# -*- coding: utf-8 -*

"""
.. module:: pos_slice_volume
    :platform: Ubuntu
    :synopsis: A volume slicing module.

.. moduleauthor:: Piotr Majka <pmajka@nencki.gov.pl>

Volume slicing script
*********************

This file is part of Multimodal Atlas of Monodelphis Domestica.
(c) Piotr Majka 2011-2013. Restricted, damnit!

Syntax
======

.. highlight:: bash

Summary
-------

All supported features in one invocation (an example) ::

    $pos_slice_vol.py  -i filename.nii.gz
                       -s 1
    [start, end, step] -r 20 50 1
                       -o /some/path/prefix_%04d_suffix.ext
                       --shiftIndexes 1
    [ox, oy, sx, sy]   --extractionROI 20 30 50 50

Details
-------

This module provide a script for extracting slices from given input volume in a
flexible way. Check the examples below.


The script requires only one input parameter - the image to slice:
`inputFileName` which is supposed to be a valid three dimensional image
supported by itk. The simplest invocation is::

    $pos_slice_vol.py -i filename.nii.gz

It will slice the provided file `filename.nii.gz` according to the default
settings. In order to select a particular slicing plane use `--sliceAxisIndex`
or `-s` switch::

    $pos_slice_vol.py -i filename.nii.gz -s <slicing_plane=0,1,2>

One can also select a particular range of slices to extract. Note the range has
to be within image's limit - it cannot exceed the actual number of slices in
given plane, otherwise, an error will occur. The slicing range works like
python :py:func:`range` function. Use either `--sliceRange` or `-r` switch to
set slices to extract, e.g. ::

    $pos_slice_vol.py -i filename.nii.gz -s 1 --sliceRange 0 20 1

Will extract the first twenty slices slicing the image through Y (second) axis.

So far, the extracted slices were saved using default output naming scheme
which is `%04d.png`. One can use any valid naming scheme which should
include output path as well as output filename scheme. E.g. to save the
extracted slices in home directory, using `slice_` prefix, pad the output up to
three digits and save slices as jpegs, the `--outputImagesFormat` or `-o`
parameter should be the following (**remember to use `%d` format!**)::

    $pos_slice_vol.py -i filename.nii.gz --outputImagesFormat /home/user/slice_%03d.jpg

Note that the output format has to support the input image type. For instance,
if the input file has a float data type, saving extracted slices as PNGs will
cause a type error. Please make sure that your input and output types are
compatible.

Sometimes, one will need to shift the indexes of the output slices, for
instance, save slice 0 as file 5, slice 5 as slice 10 and so on (e.g. to match
some other series). This effect may be achieved by issuing `--shiftIndexes
<int>` switch which shifts the output naming by provided number (either
positive or negative). As you may guess the default value is zero which means
that this parameter has no influence::

    $pos_slice_vol.py -i filename.nii.gz --sliceAxisIndex 5

Another possibility of manipulation of the slices is extraction of the
subregion from the whole slice. This may be achieved by using `--extractionROI`
switch. The switch accepts four integer parameters, the first two values
denotes the origin of the extraction (in pixels) while the other two -- the
size of the extracted region. E.g.::

    $pos_slice_vol.py -i filename.nii.gz --extractionROI 40 100 50 50

Will extract the square slice of 50x50 pixel that originates in pixel (40,100).

Reference
=========
"""

import sys, os
import logging
from optparse import OptionParser, OptionGroup
import pos_wrapper_skel

import itk
import pos_itk_core


class extract_slices_from_volume(pos_wrapper_skel.enclosed_workflow):
    """
    Class which purpose is to extract a slice(s) from 3d volume. So much buzzz
    about so simple thing... yeap, that's itk.
    """

    def _validate_options(self):
        super(self.__class__, self)._initializeOptions()

        assert self.options.sliceAxisIndex in [0, 1, 2],\
            self._logger.error("The slicing plane has to be either 0, 1 or 2.")

        assert self.options.inputFileName is not None,\
            self._logger.error("No input provided (-i ....). Plese supply input filename and try again.")

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # At the very beginning, determine input image type to configure the
        # reader.
        input_filename = self.options.inputFileName
        self._input_image_type =\
            pos_itk_core.autodetect_file_type(input_filename)
        self._output_image_type =\
            pos_itk_core.types_reduced_dimensions[self._input_image_type]

        self._logger.info("Determined input image type: %s", self._input_image_type)
        self._logger.info("Determined slices' image type: %s", self._output_image_type)

        self._logger.debug("Reading volume file %s", input_filename)
        self._image_reader = itk.ImageFileReader[self._input_image_type].New()
        self._image_reader.SetFileName(input_filename)
        self._image_reader.Update()

        self._source_largest_region = self._image_reader.GetOutput().GetLargestPossibleRegion()
        self._logger.info("Largest possible region: %s.", self._source_largest_region)

        # Checking if the provided file IS a volume -- it has to be exactly
        # three dimensional, no more, no less!
        assert len(self._source_largest_region.GetSize()) == 3, \
            self._logger.error("The provided file is not three dimensional. Plase provide a 3D one.")

        # Define slicing region (in its initial form)
        self._define_slicing_region()

        # Define filter for extracting slices
        self._logger.debug("Setting slice region.")
        self._extract_slice = itk.ExtractImageFilter[
            self._input_image_type, self._output_image_type].New()
        self._extract_slice.SetExtractionRegion(self._new_region)
        self._extract_slice.SetInput(self._image_reader.GetOutput())
        self._extract_slice.SetDirectionCollapseToIdentity()
        self._extract_slice.Update()

        self._logger.debug("Setting image writer.")
        self._image_writer = itk.ImageFileWriter[self._output_image_type].New()
        self._image_writer.SetInput(self._extract_slice.GetOutput())

        self._logger.debug("Getting indexed of slices to extract.")
        self._define_slicing_range()

        self._logger.debug("Extracting slices.")
        for i in self._slicingRange:
            self._extract_single_slice(i)

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _define_slicing_region(self):
        """
        Create slicing region - a region that will be used for slicing.
        This method only creates the region (initializes).

        The properties of the slicing region are updated in the loop
        that is actually extracting the slices.
        """

        # Well, we assume that volume that we slice is three dimensional
        # otherwise the script is gonna crush.
        self._logger.debug("Setting slice region.")
        self._new_region = itk.ImageRegion[3]()
        slice_size = itk.Size[3]()

        # Clone the size of the old region to the new region. Why I can't just
        # assign the whole array? It's very simple - I would copy by reference
        # so both sizes would be binded. Inevitable catastrophy!
        for i in range(3):
            slice_size[i] = self._source_largest_region.GetSize()[i]

        # The code below is responsible for selecting a subregion of a
        # extracted slide. The definition of the subregion comes from the
        # --extractionROI command line parameter. If the parameters is not
        # provided the subregion is equal to the full region.
        if self.options.extractionROI:

            # Remove the index of the slicing plane and use the remaining
            # indexes to define region to extract.

            reg_definition = self.options.extractionROI
            self._logger.debug("Extracting subregion: %s.",
                    " ".join(map(str, reg_definition)))

            indexes_left = range(3)
            indexes_left.pop(self.options.sliceAxisIndex)
            slice_size[indexes_left[0]] = reg_definition[2]
            slice_size[indexes_left[1]] = reg_definition[3]

            self._new_region.SetIndex(indexes_left[0], reg_definition[0])
            self._new_region.SetIndex(indexes_left[1], reg_definition[1])

        # And now I reset the dimension in the slicing axis. So simple in
        # comparision with numpy:
        slice_size[self.options.sliceAxisIndex] = 0

        # Finally I can put the size into region object.
        self._new_region.SetSize(slice_size)
        self._logger.info("Computed slice region: %s.", self._new_region)

    def _define_slicing_range(self):
        """
        Defines indexes of slices that are to be extracted from the volume.
        The default set of slices to extract are all the sliced in the slicing
        plane.
        """
        self._logger.debug("Defining set of slices to extract.")

        # The default slide range is a full slide range (all slices in given
        # plane). When non-empty slide range is provided, the slices to extract
        # are defined according to provided settings.

        # First, we extract the number of slices in the volume in the provided
        # slicing plane.
        max_slice_number = self._source_largest_region.GetSize()\
                                [self.options.sliceAxisIndex]

        if self.options.sliceRange is None:
            self._logger.debug("No custom slice range provided. Extracting all slices in given plane.")
            self._logger.debug("Selecting slices from LargestPossibleRegion: %s",
                          self._source_largest_region)

            # Grab indexes of all slices in slicing plane
            self._slicingRange = range(0, max_slice_number)

        else:
            # Check if the requested slices are within the volume size:
            assert self.options.sliceRange[1] <= max_slice_number,\
                self._logger.error("Index of the last slice (%d)\
                                   is higher that maximum number of slices within\
                                   given slicing plane (%d).",\
                        self.options.sliceRange[1], max_slice_number)

            # Get only those sliced that user wants to.
            self._slicingRange = range(*self.options.sliceRange)

        self._logger.info("Selected slices: %s",
                          " ".join(map(str, self._slicingRange)))

    def _extract_single_slice(self, slice_index):
        """
        Extract single slice from the volume.

        :type slice_index: int
        :param slice_index: index of the slice to be extracted.
        """
        self._logger.debug("Extracing slice: %d", slice_index)
        self._new_region.SetIndex(self.options.sliceAxisIndex, slice_index)
        self._logger.debug("Region to extract: %s", self._new_region)

        # Now, get the output filename. Filename depends on the slice
        # region_index :)
        # Ok, this is a bit dirty hack. If we want the output image which name
        # does not depend on the slice index, we need to handle type error:
        try:
            filename = \
                self.options.outputImagesFormat \
                % (slice_index + self.options.shiftIndexes, )
        except TypeError:
            filename = self.options.outputImagesFormat

        self._logger.info("Saving slice %d to: %s", slice_index, filename)
        self._extract_slice.SetExtractionRegion(self._new_region)
        self._image_writer.SetFileName(filename)
        self._image_writer.Update()

    @staticmethod
    def parseArgs():
        usage_string = "python pos_slice_volume.py  -i <input_filename> [options]"
        parser = pos_wrapper_skel.enclosed_workflow._getCommandLineParser()

        parser.add_option('--outputImagesFormat', '-o',
                        dest='outputImagesFormat', type='str',
                        default='%04d.png',
                        help='Filename format for the the output images.')
        parser.add_option('--sliceRange', '-r',
                        dest='sliceRange', type='int',  nargs=3,
                        default=None,
                        help='Indexes of the slices to extract defined as parameters of the python range function.')
        parser.add_option('--sliceAxisIndex', '-s',
                        dest='sliceAxisIndex', type='int',
                        default=0,
                        help='Index of the slicing axis.')
        parser.add_option('--inputFileName', '-i', dest='inputFileName', type='str',
                default=None, help='File that is going to be sliced.')
        parser.add_option('--shiftIndexes', dest='shiftIndexes', type='int',
                default=0, help='Shift output file numbers by given value (has to be integer).')
        parser.add_option('--extractionROI', default=None,
                            type='int', dest='extractionROI',  nargs=4,
                            help='ROI of the input image used for registration (ox, oy, sx, sy).')

        (options, args) = parser.parse_args()

        return (options, args)

if __name__ == '__main__':
    options, args = extract_slices_from_volume.parseArgs()
    filter = extract_slices_from_volume(options, args)
    filter.launch()
