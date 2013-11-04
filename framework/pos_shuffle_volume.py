#!/usr/bin/python
# -*- coding: utf-8 -*

"""
.. module:: pos_reorder_volume
    :platform: Ubuntu
    :synopsis: A script for reordering slices

.. moduleauthor:: Piotr Majka <pmajka@nencki.gov.pl>
"""

import random
import csv
import itk
import pos_itk_core
import pos_wrapper_skel


class reorder_volume_workflow(pos_wrapper_skel.enclosed_workflow):
    """
    A class which purpose is to load a volume and then reorder slices along
    given axis according to the provided settings.
    # TODO: Provide more documentation below:
    # TODO: Allowed grayscale image type
    # TODO: Allowed multichannel image type.
    # TODO: Mapping file format.
    """

    # This is the the one and only multichannel output image type supported by
    # this script
    _rgb_out_type = itk.Image.RGBUC3

    # This attrubute define the internal image type of each grayscale channel
    # of the multichannel volume.
    _rgb_out_component_type = itk.Image.UC3

    def _validate_options(self):
        super(self.__class__, self)._initializeOptions()

        # Well, that's simple: the script only accepts 0,1,2 as image slicing
        # plane.
        assert self.options.sliceAxisIndex in [0, 1, 2],\
            self._logger.error("The slicing plane has to be either 0, 1 or 2.")

        # And we DO require an input image.
        assert self.options.inputImage is not None,\
            self._logger.error("No input provided (-i ....). Plese supply input filename and try again.")

        # Print a warning if no mapping file is provided.
        if not self.options.mapping:
            self._logger.warning("No mapping file has been provided! Slices will be reordered according to the randomly generated permutation.")

    def _read_input_image(self):
        """
        Reads the input image and sets some auxiliary variables like image type
        and dimensionality.
        """
        input_filename = self.options.inputImage

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
        self._image_shape =\
            self._original_image.GetLargestPossibleRegion().GetSize()

        # Checking if the provided file is a volume -- it has to be exactly
        # three dimensional, no more, no less!
        assert len(self._image_shape) == 3, \
            self._logger.error("The provided image is not three dimensional one. A three dimensional image is required.")

    def _random_slices_permutation(self):
        """
        """
        self._reorder_mapping =\
            range(self._image_shape[self.options.sliceAxisIndex])
        random.shuffle(self._reorder_mapping)

    def _get_mapping_from_file(self):
        """
        Here I use pretty neat code snipper for determining the
        dialect of teh csv file. Found at:
        http://docs.python.org/2/library/csv.html#csv.Sniffer
        # TODO make this function in the way that we start from one!
        # Yes!, we assume that the mapping starts from one
        # TODO: Another important remark:
        # The form of the mapping is the following:
        # map[new_slice_idx] = source_slice_idx!!!, not the reverse!
        """
        with open(self.options.mapping, 'rb') as mapping_file:
            dialect = csv.Sniffer().sniff(mapping_file.read(1024))
            mapping_file.seek(0)
            reader = csv.reader(mapping_file, dialect)
            self._reorder_mapping =\
                dict(map(lambda (x, y): (int(x), int(y)), list(reader)))

    def _check_mapping_structure(self):
        """
        Checks if the provided mapping is a correct one. The criteria are following:
        #TODO: Put the criteria here.
        """
        pass

    def _get_reorder_mapping(self):
        """
        Generates mapping of the slices from one image to another.

        If a slice-to-slice mapping is provided, if has to satisfy the
        following conditions:
            1. asdf
            2. sdf #TODO Fill it up.

        If there is no mapping provided, a random permutation of the slices is
        generated and applied.

        The mapping file should be a typical CSV file wich either comma, space
        or tab as a delimiter. No header lines and no comments are allowed.
        """

        if not self.options.mapping:
            self._random_slices_permutation()
        else:
            try:
                self._get_mapping_from_file()
            except:
                self._logger.error("The mapping file cannot be parsed for some reason. Please check it.")

        # Whatever is the source of the mapping, it is better to check if the
        # mapping itself is a correct one. In the future there may be more
        # ways to provide the mapping. Let's then assume that we check the
        # mapping whatever the source is.
        #for slice_idx in range(self._numbers_of_components):

        # quick alias:
        mapping = self._reorder_mapping
        if len(mapping.keys()) != len(set(mapping.keys())):
            print "PROBLEM, keys has to be unique!"


    def _process_multichannel_image(self):
        """
        Multichannel workflow.
        """
        self._logger.debug("Entering multichannel workflow.")

        # This is gonna be a container for collecting all processed
        # channels of a multichannel image.
        processed_components = []

        # Extract the component `channel_idx` from the composite image,
        # process it and store:
        for channel_idx in range(self._numbers_of_components):
            self._logger.debug("Processing channel %d of %d.",
                channel_idx, self._numbers_of_components)

            extract_filter = \
                itk.VectorIndexSelectionCastImageFilter[
                self._input_image_type, self._rgb_out_component_type].New()
            extract_filter.SetInput(self._image_reader.GetOutput()),
            extract_filter.SetIndex(channel_idx)
            extract_filter.Update()

            processed_channel = pos_itk_core.reorder_volume(
                extract_filter.GetOutput(),
                self._reorder_mapping, self.options.sliceAxisIndex)
            processed_components.append(processed_channel)

            self._logger.debug("Finished processing %d.", channel_idx)

        # After iterating over all channels, compose the individual
        # components back into multichannel image.
        self._logger.info("Composing back the processed channels.")
        compose = itk.ComposeImageFilter[
            self._rgb_out_component_type, self._input_image_type].New()
        compose.SetInput1(processed_components[0])
        compose.SetInput2(processed_components[1])
        compose.SetInput3(processed_components[2])
        compose.Update()

        # At the end, save the image.
        itk.write(compose.GetOutput(), self.options.outputImage)

    def _process_grayscale_image(self):
        """
        This method handles the grayscale image processing workflow.
        It's extremely simple - just an invocation of reordering function.
        """
        # Yeap. Just use the external reordering function and then save the
        # result.
        self._logger.debug("Entering grayscale workflow.")

        processed_channel = pos_itk_core.reorder_volume(
            self._image_reader.GetOutput(),
            self._reorder_mapping, self.options.sliceAxisIndex)
        self._logger.debug("Exiting grayscale workflow.")

        # At the end, save the image.
        self._logger.info("Writing the processed file to: %s.",
                          self.options.outputImage)
        itk.write(processed_channel, self.options.outputImage)

    def launch(self):

        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Read the input image and extract the images' metadata
        self._read_input_image()

        # Generate the reorder mapping.
        self._get_reorder_mapping()

        # If it happened that the provided images is multichannel, we iterate
        # over all channels process it one by one.  If the image is fortunately
        # a regular, grayscale image then a grayscale image workflow is
        # invoked, which is faster and more reliable.
        if self._numbers_of_components > 1:
            self._process_multichannel_image()
        else:
            self._process_grayscale_image()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    @staticmethod
    def parseArgs():
        usage_string = "python pos_slice_volume.py  -i <input_filename> -o <output_filename> --reorderMapping <reorder_mapping_file>"
        parser = pos_wrapper_skel.enclosed_workflow._getCommandLineParser()

        parser.add_option('--inputImage', '-i', dest='inputImage',
                type='str', default=None,
                help='File that is going to be sliced.')
        parser.add_option('--outputImage', '-o', dest='outputImage',
                type='str', default=None,
                help='Filename format for the the output images.')
        parser.add_option('--mapping', dest='mapping',
                type='str', default=None,
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
