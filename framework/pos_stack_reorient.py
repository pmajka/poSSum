#!/usr/bin/python
# -*- coding: utf-8 -*

"""
.. module:: pos_stack_reorient
    :platform: Ubuntu
    :synopsis: A volume stacking and reorienting script.

.. moduleauthor:: Piotr Majka <pmajka@nencki.gov.pl>

A script for stacking slices and reorienting volumes
****************************************************

This file is part of Multimodal Atlas of Monodelphis Domestica.
(c) Piotr Majka 2011-2013. Restricted, damnit!

Syntax
======

.. highlight:: bash

Summary
-------

All supported features in one invocation (an example) ::

    $pos_stack_reorient.py -i input_file.nii.gz
        RAS code           --orientationCode ras
      string, see -h       --interpolation NearestNeighbor
   [float float float]     --resample 0.5 0.5 0.5
   permutation of 0 1 2    --permutation 2 1 0
      [0-1 0-1 0-1]        --flipAxes 1 0 1
          bool             --flipAroundOrigin
   [float float float]     --setSpacing 0.05 0.05 0.05
   [float float float]     --setOrigin 0 0 0
                           --setType uchar

Details - volume stacking
-------------------------

Some precise examples of using the volume stacking and reorienting script.  In
order to stack a series of slices onto a volume, the following command has to
be invoked::

    $pos_stack_reorient.py -i prefix_%04d.png
                           --stackingOptions 0 100 1
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

"""
import itk

import pos_wrapper_skel
import pos_itk_core

class reorient_image_wrokflow(pos_wrapper_skel.enclosed_workflow):
    """
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
    """

    rgb_out_component_type = itk.Image.UC3

    def _validate_options(self):
        assert self.options.inputFile,\
            self._logger.error("No input provided (-i ....). Plese supply input filename and try again.")

    def launch(self):
        # Ok, if the image stacking is enabled, create the input volume
        # by stacking the input image stack. Otherwise just load the
        # input volume in the regular manner.
        if self.options.stackingOptions:
            self._logger.info("Input volume will be generated from the image stack.")
            self._stack_input_slices()
        else:
            self._logger.info("Input volume will be loaded from the volume file.")
            self._load_input_volume()

        # After executing the code above, the input volume is loaded and ready
        # to use.

        # First, determine the number of input image components to select
        # aproperiate workflow: either single- or multichannel.
        numbers_of_components = \
            self._reader.GetOutput().GetNumberOfComponentsPerPixel()
        self._logger.info("Number of components of the input volume: %d.",
                          numbers_of_components)

        # The multichannel workflow i a bit more complicated
        if numbers_of_components > 1:
            self._logger.debug("Entering multichannel workflow.")

            # We will collect the consecutive processed components
            # into this array
            processed_components = []

            # Extract the component `i` from the composite image,
            # process it and store:
            for i in range(numbers_of_components):
                self._logger.debug("Processing channel %d of %d.",
                             i, numbers_of_components)

                extract_filter =\
                    itk.VectorIndexSelectionCastImageFilter[
                    self._input_type, self.rgb_out_component_type].New()
                extract_filter.SetIndex(i)
                extract_filter.SetInput(self._reader.GetOutput())

                processed_channel =\
                    self.process_single_channel(extract_filter.GetOutput())
                processed_components.append(processed_channel)
                self._logger.debug("Finished processing %d.", i)

            # After iterating over all channels, compose the individual
            # components back into multichannel image.
            self._logger.info("Composing back the processed channels.")
            compose = itk.ComposeImageFilter[
                self.rgb_out_component_type,
                self._input_type].New(
                    Input1 = processed_components[0],
                    Input2 = processed_components[1],
                    Input3 = processed_components[2])
            processed_image = compose.GetOutput()

        else:
            # If we're processing a single channel image, the whole procedure
            # is much much easier. Just process the single component.
            self._logger.debug("Entering grayscale workflow.")
            processed_image =\
                self.process_single_channel(self._reader.GetOutput())
            self._logger.debug("Exiting grayscale workflow.")

        # After processing the input volume, save it.
        self._logger.info("Writing the processed file to: %s.",\
                          self.options.outputFile)
        self._writer=itk.ImageFileWriter[processed_image].New()
        self._writer.SetFileName(self.options.outputFile)
        self._writer.SetInput(processed_image)
        self._writer.Update()

    def process_single_channel(self, input_image):
        """
        Routine for processing a single channel image.

        :param input_image: Image to process
        :type input_image: `itk.Image`
        """

        # Permuting the input image, if required
        permute = itk.PermuteAxesImageFilter[input_image].New()
        permute.SetInput(input_image)
        permute.SetOrder(self.options.permutation)
        self._logger.debug("Setting the axes permutation to: %s.",
                           str(self.options.permutation))

        # Flipping the permuted volume
        flip = itk.FlipImageFilter[permute.GetOutput()].New()
        flip.SetInput(permute.GetOutput())
        flip.SetFlipAxes(self.options.flipAxes)
        self._logger.debug("Applying the flip axis settings: %s.",
                           str(self.options.flipAxes))

        # Do we flip the axes around the origin?:
        if self.options.flipAroundOrigin:
            flip.FlipAboutOriginOn()
        else:
            flip.FlipAboutOriginOff()
        self._logger.debug("Flip around origin? %s",
                           str(self.options.flipAroundOrigin))

        # Changing the image information, if required
        change_information = \
            itk.ChangeInformationImageFilter[flip.GetOutput()].New()
        change_information.SetInput(flip.GetOutput())

        if self.options.setOrigin:
            change_information.ChangeOriginOn()
            change_information.SetOutputOrigin(self.options.setOrigin)
            self._logger.debug("Changing the origin to: %s.",
                               str(self.options.setOrigin))

        if self.options.setSpacing:
            change_information.ChangeSpacingOn()
            change_information.SetOutputSpacing(self.options.setSpacing)
            self._logger.debug("Changing the spacing to: %s.",
                               str(self.options.setOrigin))

        if self.options.orientationCode:
            ras_code = self.options.orientationCode.upper()
            change_information.ChangeDirectionOn()
            code_matrix = pos_itk_core.get_itk_direction_matrix(ras_code)
            change_information.SetOutputDirection(code_matrix)
            self._logger.debug("Setting the anatomical direction to %s.",
                               ras_code)

        # Latch the changes - we need to have a computed image
        # before resampling
        change_information.Update()
        last_image = change_information.GetOutput()

        # Resample the image, if required
        if self.options.resample:
            last_image = pos_itk_core.resample_image_filter(\
                change_information.GetOutput(),
                self.options.resample,
                interpolation=self.options.interpolation)

        # Assign anatomical orientation to the image.
        if self.options.setType:
            self._logger.debug("Casting the ouput image to: %s.",
                               self.options.setType)

            cast_to_type = pos_itk_core.get_cast_image_type_from_string(self.options.setType)
            cast_image = itk.CastImageFilter[last_image, cast_to_type].New()
            cast_image.SetInput(last_image)
            cast_image.Update()
            last_image = cast_image.GetOutput()

        return last_image

    def _stack_input_slices(self):
        """
        Stack 2D images into 3D volume.
        """
        # This is a bit tricky. Few words of explanation are required.
        # First, assign the slices' indexes. Simple.
        start, stop, step = tuple(self.options.stackingOptions)

        # Then, determine the filename for the first slice
        first_slice = self.options.inputFile % (start,)

        # Autodetect the type of the slice. Note that the rest of the slices
        # has to have the same image type as the first file.
        slice_type = pos_itk_core.autodetect_file_type(first_slice)
        self._input_type = pos_itk_core.types_increased_dimensions[slice_type]
        self._logger.info("Detrmined input image type: %s",\
                          self._input_type)

        # As the image type of the first slice is determined, the proper
        # numeric series reader can be defined and utilized.
        nameGenerator = itk.NumericSeriesFileNames.New()
        nameGenerator.SetSeriesFormat(self.options.inputFile)
        nameGenerator.SetStartIndex(start)
        nameGenerator.SetEndIndex(stop)
        nameGenerator.SetIncrementIndex(step)

        # Then just read the slices.
        self._reader = itk.ImageSeriesReader[self._input_type].New()
        self._reader.SetFileNames(nameGenerator.GetFileNames())
        self._reader.Update()

    def _load_input_volume(self):
        """
        Load the input volume.
        """
        # Autodetect image type
        self._input_type = \
            pos_itk_core.autodetect_file_type(self.options.inputFile)

        # And then just load the volume. Simple as it is.
        self._reader = itk.ImageFileReader[self._input_type].New()
        self._reader.SetFileName(self.options.inputFile)
        self._reader.Update()

    @classmethod
    def _getCommandLineParser(cls):
        parser = pos_wrapper_skel.enclosed_workflow._getCommandLineParser()

        parser.add_option('--outputFile', '-o', dest='outputFile', type='str',
                default=None, help='Output volume filename.')
        parser.add_option('--inputFile', '-i', dest='inputFile', type='str',
                default=None, help='Input volume filename (if no stackingOptions are provided) or input naming scheme (stackingOptions) are provided.')
        parser.add_option('--orientationCode', dest='orientationCode', type='str',
                default=None, help='Anatomical orientation code in RAS mode.')
        parser.add_option('--stackingOptions', dest='stackingOptions', type='int',
                default=None, help='Image stacking options: first slice, last slice, slice increment. Three integers are required.', nargs=3)

        parser.add_option('--interpolation', default='linear',
            type='str', dest='interpolation',
            help='Resampling interpolation method. Allowed options: NearestNeighbor|Linear. Default: linear')
        parser.add_option('--resample', default=None,
            type='float', nargs=3, dest='resample',
            help='Resampling vector. Provide three floats from 0 to 1.')
        parser.add_option('--permutation', default=[0,1,2],
            type='int', nargs=3, dest='permutation',
            help='Apply axes permutation. Permutation has to be provided as sequence of 3 integers separated by space. Identity (0,1,2) permutation is a default one.')
        parser.add_option('--flipAxes', default=[0,0,0],
            type='int', nargs=3, dest='flipAxes',
            help='Select axes to flip. Selection has to be provided as sequence of three numbers. E.g. \'0 0 1\' will flip the z axis.')
        parser.add_option('--flipAroundOrigin', default=False,
            dest='flipAroundOrigin', action='store_const', const=True,
            help='Flip around origin.')
        parser.add_option('--setSpacing',
            dest='setSpacing', type='float', nargs=3, default=None,
            help='Set spacing values. The dpacing has to be provided as three floats.')
        parser.add_option('--setOrigin', dest='setOrigin', type='float',
            nargs=3, default=None,
            help='Set origin values instead of voxel location. Origin has to be provided as three floats.')
        parser.add_option('--setType', dest='setType', type='str', default=None,
            help='Allowed values: uchar | ushort |float | double')

        return parser

if __name__ == '__main__':
    options, args = reorient_image_wrokflow.parseArgs()
    d = reorient_image_wrokflow(options, args)
    d.launch()
