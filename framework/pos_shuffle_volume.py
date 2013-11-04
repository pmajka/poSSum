#!/usr/bin/python
# -*- coding: utf-8 -*

"""
.. module:: pos_reorder_volume
    :platform: Ubuntu
    :synopsis: A script for reordering slices

.. moduleauthor:: Piotr Majka <pmajka@nencki.gov.pl>
"""

import random
import itk
import pos_itk_core
import pos_wrapper_skel


class reorder_volume_workflow(pos_wrapper_skel.enclosed_workflow):
    """
    A class which purpose is to load a volume and then reorder slices along
    given axis according to the provided settings.
    # TODO: Provide more documentation below.
    """

    #TODO: Document these attributes.
    _rgb_out_type = itk.Image.RGBUC3
    _rgb_out_component_type = itk.Image.UC3

    def _validate_options(self):
        super(self.__class__, self)._initializeOptions()

        assert self.options.sliceAxisIndex in [0, 1, 2],\
            self._logger.error("The slicing plane has to be either 0, 1 or 2.")

        assert self.options.inputFileName is not None,\
            self._logger.error("No input provided (-i ....). Plese supply input filename and try again.")


    def _read_input_image(self):
        """
        Reads the input image and sets some auxiliary variables like image type
        and dimensionality.
        """

        input_filename = self.options.inputFileName

        # Determine the input image type (data type and dimensionality)
        self._input_image_type =\
            pos_itk_core.autodetect_file_type(input_filename)
        self._logger.info("Determined input image type: %s",
                          self._input_image_type)

        # Load the provided image,
        self._logger.debug("Reading volume file %s", input_filename)
        self._image_reader = itk.ImageFileReader[self._input_image_type].New()
        self._image_reader.SetFileName(input_filename)
        self._image_reader.Update()

        # Read number of the components of the image.
        self._numbers_of_components =\
            self._image_reader.GetOutput().GetNumberOfComponentsPerPixel()
        self._original_image = self._image_reader.GetOutput()
        self._image_shape = self._original_image.GetLargestPossibleRegion().GetSize()

        # Checking if the provided file IS a volume -- it has to be exactly
        # three dimensional, no more, no less!
        assert len(self._image_shape) == 3, \
            self._logger.error("The provided image is not three dimensional one. A three dimensional image is required.")

    def _get_reorder_mapping(self):
        """
        Generates mapping of the slices from one image to another.

        If a slice-to-slice mapping is provided, if has to satisfy the
        following conditions:
            1. asdf
            2. sdf #TODO Fill it up.

        If there is no mapping provided, a random permutation of the slices is
        generated and applied.
        """
        self._reorder_mapping = range(self._image_shape[self.options.sliceAxisIndex])
        random.shuffle(self._reorder_mapping)

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Read the input image and extract the images' metadata
        self._read_input_image()

        # Generate the reorder mapping.
        self._get_reorder_mapping()

        # BEGIN reorder volume -------------
        if self._numbers_of_components > 1:
            processed_components = []

            for i in range(self._numbers_of_components):
                extract_filter = \
                    itk.VectorIndexSelectionCastImageFilter[
                    self._input_image_type, self._rgb_out_component_type].New()
                extract_filter.SetInput(self._image_reader.GetOutput()),
                extract_filter.SetIndex(i)
                extract_filter.Update()

                processed_channel = pos_itk_core.reorder_volume(
                    extract_filter.GetOutput(),
                    self._reorder_mapping, self.options.sliceAxisIndex)
                processed_components.append(processed_channel)

            compose = itk.ComposeImageFilter[
                self._rgb_out_component_type, self._input_image_type].New()
            compose.SetInput1(processed_components[0])
            compose.SetInput2(processed_components[1])
            compose.SetInput3(processed_components[2])
            compose.Update()

            itk.write(compose.GetOutput(), self.options.outputImage)
        else:
            processed_channel = pos_itk_core.reorder_volume(
                self._image_reader.GetOutput(),
                self._reorder_mapping, self.options.sliceAxisIndex)
            itk.write(processed_channel, self.options.outputImage)
        # END reorder volume -----------------

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _check_mapping_structure(self):
        pass

    @staticmethod
    def parseArgs():
        usage_string = "python pos_slice_volume.py  -i <input_filename> -o <output_filename> --reorderMapping <reorder_mapping_file>"
        parser = pos_wrapper_skel.enclosed_workflow._getCommandLineParser()

        parser.add_option('--inputFileName', '-i', dest='inputFileName',
                type='str', default=None,
                help='File that is going to be sliced.')
        parser.add_option('--outputImage', '-o', dest='outputImage',
                type='str', default=None,
                help='Filename format for the the output images.')
        parser.add_option('--reorderMappingFile', dest='sliceRange',
                type='int', nargs=3, default=None,
                help='Reorder mapping file.')
        parser.add_option('--sliceAxisIndex', '-s', dest='sliceAxisIndex',
                type='int', default=0,
                help='Index of the slicing axis.')

        (options, args) = parser.parse_args()
        return (options, args)

if __name__ == '__main__':
    options, args = reorder_volume_workflow.parseArgs()
    workflow = reorder_volume_workflow(options, args)
    workflow.launch()
#python pos_shuffle_volume.py ~/Dropbox/Photos/oposy_skrawki/02_02_NN2/myelin.nii.gz ~/app.nii.gz
