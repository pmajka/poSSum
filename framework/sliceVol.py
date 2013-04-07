#!/usr/bin/python
# -*- coding: utf-8 -*
###############################################################################
#                                                                             #
#    This file is part of Multimodal Atlas of Monodelphis Domestica           #
#                                                                             #
#    Copyright (C) 2011-2012 Piotr Majka                                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is free software: you can redistribute      #
#    it and/or modify it under the terms of the GNU General Public License    #
#    as published by the Free Software Foundation, either version 3 of        #
#    the License, or (at your option) any later version.                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is distributed in the hope that it          #
#    will be useful, but WITHOUT ANY WARRANTY; without even the implied       #
#    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.         #
#    See the GNU General Public License for more details.                     #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along  with  3d  Brain  Atlas  Reconstructor.   If  not,  see            #
#    http://www.gnu.org/licenses/.                                            #
#                                                                             #
###############################################################################

import sys, os
import datetime, logging
from optparse import OptionParser, OptionGroup
import itk

# Dictionary below copied from (Sun Apr  7 14:04:28 CEST 2013)
# http://code.google.com/p/medipy/source/browse/lib/medipy/itk/types.py?name=default&r=0da35e1099e5947151dee239f7a09f405f4e105c
io_component_type_to_type = {
        itk.ImageIOBase.UCHAR : itk.UC,
        itk.ImageIOBase.CHAR : itk.SC,
        itk.ImageIOBase.USHORT : itk.US,
        itk.ImageIOBase.SHORT : itk.SS,
        itk.ImageIOBase.UINT : itk.UI,
        itk.ImageIOBase.INT : itk.SI,
        itk.ImageIOBase.ULONG : itk.UL,
        itk.ImageIOBase.LONG : itk.SL,
        itk.ImageIOBase.FLOAT : itk.F,
        itk.ImageIOBase.DOUBLE : itk.D,
        }

# And this is my own invention: a dictionary that converts tuple of specific
# image parameters into itk image type. We all love ITK heavy templated code
# style!
io_component_string_name_to_image_type = {
        ('scalar', 'short', 3) : itk.Image.SS3,
        ('scalar', 'unsigned_short', 3) : itk.Image.US3,
        ('scalar', 'unsigned_char', 3) : itk.Image.UC3,
        ('vector', 'unsigned_char', 3) : itk.Image.RGBUC3,
        ('scalar', 'short', 2) : itk.Image.SS2,
        ('scalar', 'unsigned_short', 2) : itk.Image.US2,
        ('vector', 'unsigned_char', 2) : itk.Image.RGBUC2,
        ('scalar', 'unsigned_char', 2) : itk.Image.UC2
        }

# Another quite clever dictionary. This one converts given image type to the
# same type but with number of dimensions reduced by one (e.g. 3->2).
types_reduced_dimensions = {
        itk.Image.SS3 : itk.Image.SS2,
        itk.Image.US3 : itk.Image.US2,
        itk.Image.UC3 : itk.Image.UC2,
        itk.Image.RGBUC3 : itk.Image.RGBUC2
    }

def autodetect_file_type(image_path):
    """
    Autodetects image dimensions and size as well as pixel type and component size.

    :param image_path: filename to be investigated
    :type image_path: str
    """

    logging.info("Autodetecting file type: %s",  image_path)

    # Initialize itk imageIO factory which allows to do some strange thing
    # (this function a pythonized code of an itk example from
    # http://www.itk.org/Wiki/ITK/Examples/IO/ReadUnknownImageType
    # Cheers!
    image_io = itk.ImageIOFactory.CreateImageIO(image_path, itk.ImageIOFactory.ReadMode)
    image_io.SetFileName(image_path)
    image_io.ReadImageInformation()

    # Extracting information for determining image type
    image_size = map(image_io.GetDimensions, range(image_io.GetNumberOfDimensions()))
    component_type = image_io.GetComponentTypeAsString(image_io.GetComponentType())
    pixel_type = image_io.GetPixelTypeAsString(image_io.GetPixelType())
    number_of_dimensions = image_io.GetNumberOfDimensions()

    logging.debug("Finished extracting header information.")

    logging.info("   Number of dimensions: %d", number_of_dimensions)
    logging.info("   Image size: %s", str(image_size))
    logging.info("   Component type: %s", component_type)
    logging.info("   Pixel type: %s", pixel_type)
    logging.debug(image_io)
    logging.info("Matching image type...")

    # Matching corresponding image type
    image_type = io_component_string_name_to_image_type[
        (pixel_type, component_type, number_of_dimensions)]

    logging.info("Matched ITK image type: %s", image_type)

    # Hurrayy!!
    return image_type


def setup_logging(log_filename = None, log_level = 'WARNING'):
    """
    Initialize the logging subsystem. The logging is handled (suprisingly!)
    by the logging module. Depending on the command line options the log may
    be streamed to a specified file or printed directly to the stderr.
    """

    # Intialize the logging module.
    logging.basicConfig(\
            level = getattr(logging, log_level),
            filename = log_filename,
            format = '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s',
            datefmt = '%m/%d/%Y %H:%M:%S')


class extract_slices_from_volume(object):
    def __init__(self, optionsDict, args):
        """
        """

        # Store filter configuration withing the class instance
        if type(optionsDict) != type({}):
            self.options = eval(str(optionsDict))
        else:
            self.options = optionsDict

        self._args = args

        self._initializeLogging()
        self._validate_options()

    def _validate_options(self):
        pass

    def _initializeLogging(self):
        setup_logging(self.options['logFilename'],
                      self.options['loglevel'])

        logging.debug("Logging module initialized. Saving to: %s, Loglevel: %s",
                      self.options['logFilename'], self.options['loglevel'])

    def launchFilter(self):

        # At the very beginnig, determine input image type to configure the
        # reader.
        input_filename = self.options['inputFilename']
        self._input_image_type = autodetect_file_type(input_filename)
        self._output_image_type = types_reduced_dimensions[self._input_image_type]

        logging.info("Determined input image type: %s", self._input_image_type)
        logging.info("Determined slices' image type: %s", self._output_image_type)

        logging.debug("Reading volume file %s", input_filename)
        self.image_reader = itk.ImageFileReader[self._input_image_type].New()
        self.image_reader.SetFileName(input_filename)
        self.image_reader.Update()

        initial_full_region = self.image_reader.GetOutput().GetLargestPossibleRegion()
        logging.info("Largest possible region: %s.", initial_full_region)

        logging.debug("Setting slice region.")
        new_region = itk.ImageRegion[3]()
        slice_size = itk.Size[3]()

        # Clone the size of the old region to the new region. Why I can't just
        # assign the whole array? It's very simple - I would copy by reference
        # so both sizes would be binded. Inevitable catastrophy!
        for i in range(3):
            slice_size[i] = initial_full_region.GetSize().GetElement(i)

        # And now I reset the dimension in the slicing axis. So simple in
        # comparision with numpy:
        slice_size[self.options['sliceAxisIndex']] = 0

        # Finally I can put the size into region object.
        new_region.SetSize(slice_size)
        logging.info("Computed slice region: %s.", new_region)

        # Define filter for extracting slices
        logging.debug("Setting slice region.")
        self.extract_slice = itk.ExtractImageFilter[self._input_image_type, self._output_image_type].New()
        self.extract_slice.SetExtractionRegion(new_region)
        self.extract_slice.SetInput(self.image_reader.GetOutput())
        self.extract_slice.SetDirectionCollapseToIdentity()
        self.extract_slice.Update()

        logging.debug("Setting image writer.")
        self.image_writer = itk.ImageFileWriter[self._output_image_type].New()
        self.image_writer.SetInput(self.extract_slice.GetOutput())

        logging.debug("Getting indexed of slices to extract.")
        self.get_slicing_range()

        logging.debug("Extracting slices...")
        for i in self._slicingRange:
            logging.debug("Extracing slice: %d", i)

            slice_index = [0,0,0]
            slice_index[self.options['sliceAxisIndex']] = i
            new_region.SetIndex(slice_index)
            logging.debug("Region to extract: %s", new_region)

            # Now, get the output filename. Filename depends on the slice
            # index :)
            slice_filename = self.get_output_filename(i)
            logging.info("Saving slice %d to: %s", i, slice_filename)
            self.extract_slice.SetExtractionRegion(new_region)
            self.image_writer.SetFileName(slice_filename)
            self.image_writer.Update()

    def get_slicing_range(self):
        """
        """
        logging.debug("Determinig set of slices to extract.")

        # The default slide range is a full slide range (all slices in given
        # plane. When non-empty slide range is provided set of slices to

        if self.options['sliceRange'] is None:
            logging.debug("No custom slice range provided. Extracting all slices in given plane.")
            initial_full_region = self.image_reader.GetOutput().GetLargestPossibleRegion()

            logging.debug("Selecting slices from LargestPossibleRegion: %s", initial_full_region)
            slice_number = initial_full_region.GetSize().GetElement(self.options['sliceAxisIndex'])
            self._slicingRange = range(0, slice_number)

        else:
            self._slicingRange = range(*self.options['sliceRange'])

        logging.info("Selected slices: %s", " ".join(map(str, self._slicingRange)))

    def get_output_filename(self, slice_index):
        """
        """
        outputFilename = \
                self.options['outputImagesFormat'] % (slice_index + self.options['shiftIndexes'], )
        return outputFilename

    @staticmethod
    def parseArgs():
        usage = "python sliceVol.py  -r <range> -s <axis> -o <input filename> [options]"
        parser = OptionParser(usage = usage)

        parser.add_option('--outputImagesFormat', '-o',
                        dest='outputImagesFormat', type='str',
                        default='%04d.png',
                        help='Format of the output images.')
        parser.add_option('--sliceRange', '-r',
                        dest='sliceRange', type='int',  nargs=3,
                        default=None,
                        help='Range of the slice extraction.')
        parser.add_option('--sliceAxisIndex', '-s',
                        dest='sliceAxisIndex', type='int',
                        default=0,
                        help='Index of the slice axis.')
        parser.add_option('--inputFilename', '-i', dest='inputFilename', type='str',
                default=None, help='Input file.')
        parser.add_option('--shiftIndexes', dest='shiftIndexes', type='int',
                default=0, help='Shift output file numbers.')

        logging_settings = OptionGroup(parser, 'General workflow settings')
        logging_settings.add_option('--loglevel', dest='loglevel', type='str',
                default='WARNING', help='Loglevel: CRITICAL | ERROR | WARNING | INFO | DEBUG')
        logging_settings.add_option('--logFilename', dest='logFilename',
                default=None, action='store', type='str',
                help='Sets printing log to stderr instead to a file')
        parser.add_option_group(logging_settings)

        (options, args) = parser.parse_args()

        if not options.inputFilename:
            parser.print_help()
            exit(1)
        return (options, args)

if __name__ == '__main__':
    options, args = extract_slices_from_volume.parseArgs()
    filter = extract_slices_from_volume(options, args)
    filter.launchFilter()
