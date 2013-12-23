#!/usr/bin/python
# -*- coding: utf-8 -*

"""
Slice preprocessing script
**************************

:author: Piotr Majka <pmajka@nencki.gov.pl>
:revision: $Rev$
:date: $LastChangedDate$

`pos_stack_warp_image_multi_transform`, a workflow for warping a whole stack of idmages.

This file is part of Multimodal Atlas of Monodelphis Domestica.
(c) Piotr Majka 2011-2014. Restricted, damnit!
"""

import os, sys
from optparse import OptionGroup
import copy

from pos_wrapper_skel import output_volume_workflow
import pos_parameters
import pos_wrappers


class stack_warp_image_multi_transform(output_volume_workflow):
    """
    """
    _f = {
        'moving_raw': pos_parameters.filename('moving_raw', work_dir='00_override_this', str_template='{idx:04d}.nii.gz'),
        'fixed_raw': pos_parameters.filename('fixed_raw', work_dir='00_override_this', str_template='{idx:04d}.nii.gz'),
        'output_transforms': pos_parameters.filename('output_transforms', work_dir='02_transforms', str_template='{idx:04d}_Affine.txt'),
        'resliced_gray': pos_parameters.filename('resliced_gray', work_dir='04_gray_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_gray_mask': pos_parameters.filename('resliced_gray_mask', work_dir='04_gray_resliced', str_template='%04d.nii.gz'),
        'resliced_color': pos_parameters.filename('resliced_color', work_dir='05_color_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_color_mask': pos_parameters.filename('resliced_color_mask', work_dir='05_color_resliced', str_template='%04d.nii.gz'),
        'out_volume_gray': pos_parameters.filename('out_volume_gray', work_dir='06_output_volumes', str_template='{fname}_gray.nii.gz'),
        'out_volume_color': pos_parameters.filename('out_volume_color', work_dir='06_output_volumes', str_template='{fname}_color.nii.gz'),
        }

    _usage = ""

    # Define the magic numbers:
    __IMAGE_DIMENSION = 2
    __VOL_STACK_SLICE_SPACING = 1

    def _initializeOptions(self):
        super(self.__class__, self)._initializeOptions()

        # Assert if the image stack is defined.
        assert self.options.sliceRange is not None,\
            "The input image slice is not provided. Please supply the input image range: --sliceRange."

        # Range of images to register
        self._logger.debug("Setting the slice range.")
        self.options.sliceRange = \
            range(self.options.sliceRange[0],
                  self.options.sliceRange[1] + 1)

        # Assert if the transformation stack is defined.
        assert self.options.transformSpec is not None, \
            "At least one transformation is required in the transformation chain. Please supply at least one --appendTransformationFilenameTemplate option"

        # Since, in some, rare cases, the transformation indexing is different
        # than the actual slice indexing there is a possibility to specify a
        # separate set of indexes for the transformation files.
        # However, if such custom index set is not provided, both ranges will
        # be defined to be the same.
        self._logger.debug("Setting the transformations range.")
        if self.options.transformationsRange is not None:
            self._logger.debug("Using the custom transformation range.")
            self.options.transformRange = \
                range(self.options.transformationsRange[0],
                    self.options.transformationsRange[1] + 1)
        else:
            self._logger.debug("Using the same set of indexes as the slices.")
            self.options.transformRange = self.options.sliceRange

        # In both cases, the lists of indices has to have the same length.
        assert len(self.options.transformRange) == \
            len(self.options.sliceRange), \
            self._logger.error("Indexes for the slices and for the transformations does not have equal lenght.")
        # This condition is required since below we create slice to
        # transformation mapping:

        # Here, we create a slice to transformation index mapping.
        # This means that for each slice to be reslices we assign corresponding
        # transformation file index.
        self._slice_transform_map = \
            dict(zip(self.options.sliceRange, self.options.transformRange))
        self._logger.debug("Slice to transformation index mapping: %s."
            % str(self._slice_transform_map))

        # Check for the fixed images directory
        assert self.options.fixedImageInputDirectory is not None,\
            self._logger.error("Fixed images directory is a obligatory parameters. Please supply the 'fixedImageInputDirectory' parameter.")

        # And for the moving images directory
        assert self.options.movingImageInputDirectory is not None,\
            self._logger.error("Fixed images directory is a obligatory parameters. Please supply the 'movingImageInputDirectory' parameter.")

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # Override default output volumes directory if custom directory is
        # provided (We check before if proper parameter values are provided).
        self.f['moving_raw'].override_dir = \
            self.options.movingImageInputDirectory
        self.f['fixed_raw'].override_dir = \
            self.options.fixedImageInputDirectory

        # Transformation directory is not obligaroty. When no custom output
        # transformation directory is provided, the default dir is used.
        # Pretty obvious.
        if self.options.transformationsDirectory is not False:
            self.f['output_transforms'].override_dir = \
                self.options.transformationsDirectory

        # Apart from just setting the custom output volumes directory, one can
        # also customize even the output filename of both, grayscale and
        # multichannel volumes! That a variety of options!
        if self.options.outputVolumesDirectory is not False:
            self.f['out_volume_gray'].override_dir = \
                self.options.outputVolumesDirectory
            self.f['out_volume_color'].override_dir = \
                self.options.outputVolumesDirectory

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        self._load_transformations_chain()

        if self.options.dryRun is False:
            self._inspect_input_data()

        self._compose_transforms()
        self._reslice()

        if self.options.skipOutputVolumes is True:
            self._stack_output_images()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _load_transformations_chain(self):
        """
        Load the specification of the individual transformation.

        As this script is designed to deal with itk affine transfomations in
        form of the text files only these are widely supported. In theory, the
        script should work fine for the deformation fields but this has not
        been tested at all.
        """

        # Initialize workflow-wide transformation array.
        self.transformations = []

        # Iterate over all provided transformation and then put it into the
        # transformation array. The provided transformation is used in
        # "forward" mode when the "0" is used in the paramters specification.
        # When the transformation specification is "1" used in the transform
        # specification, the inversion of the transformation is used.
        for transfSpec in self.options.transformSpec:

            if int(transfSpec[0]) == 1:
                invert = " -i "
            else:
                invert = " "

            # Add forward or inverse tranfromation for the transformation
            # chain. Note that the array stores only the transformation
            # templates. This means that each template has to be exeluated in
            # order to get a particular fiename.
            self.transformations.append(invert + transfSpec[1])

    def _compose_transforms(self):
        """
        Creates a composite transformation based for whole image stack.
        """

        commands = []
        for slice_index, transform_index in self._slice_transform_map.items():
            commands.append(
                self._compose_transformation_chain(transform_index))
        self.execute(commands)

    def _compose_transformation_chain(self, transform_index):
        """
        Composes a single composite transformation based on a provided chain of
        transformations.

        :param transform_index: iindex of the transformation chain to merge
        :type transform_index: int

        :rtype: `pos_wrappers.ants_compose_multi_transform`
        :return: Transformation composition wrapper.
        """
        # Define the output transformation string.
        out_transform_filename = self.f['output_transforms'](idx=transform_index)

        # Create a list of all the input transformations.
        transformations_list = \
            map(lambda x: x % transform_index, self.transformations)

        # Create and return a transformation composition wrapper.
        command = pos_wrappers.ants_compose_multi_transform(
            dimension=self.__IMAGE_DIMENSION,
            output_image=out_transform_filename,
            deformable_list=[],
            affine_list=transformations_list)
        return copy.deepcopy(command)

    def _inspect_input_data(self):
        """
        Verify if all the files are availabe: All images have to be ailable. If
        the case is different, the workflow will not proceed and the user will
        be asked to supply the missing images.
        """
        self._logger.debug("Inspecting all the input slices and transformations.")

        # Below we iterate over all indexes of the input slices. For each
        # index, the existance if the images is assesed. Then the
        # transformation index related for the given slice index is extracted
        # and all transformations related with given slice are validated.
        for slice_index, transform_index in self._slice_transform_map.items():
            slice_filename = self.f['moving_raw'](idx=slice_index)
            self.__is_filename_available(slice_filename)
            # Done with the slice image.

            # Iteate over all transformations related with the given slice
            # index.
            for chain_item in self.options.transformSpec:
                transform_filename = self.options.transformSpec[chain_item] \
                    % transform_index
                self.__is_filename_available(transform_filename)

    def __is_filename_available(self, filename):
        """
        A helper function which queries for the given filename. Checks if the
        file is available. If the file is not valid
        or not accesible, outputs the error and exits
        the script.

        :param filename: Path to validate
        :type filename: str
        """

        self._logger.debug("Checking for file: %s.", filename)
        if not os.path.isfile(filename):
            self._logger.error("File does not exist: %s. Exiting", filename)
            sys.exit(1)

    def _reslice(self):
        """
        Reslice input images according to composed transformations. Both,
        grayscale and multichannel images are resliced.
        """

        # Reslicing grayscale images.  Reslicing multichannel images. Collect
        # all reslicing commands into an array and then execute the batch.
        if self.options.skipColorReslice is False:
            self._logger.info("Reslicing grayscale images.")
            commands = []
            for slice_index in self._slice_transform_map.keys():
                commands.append(self._reslice_grayscale(slice_index))
            self.execute(commands)

        # Reslicing multichannel images. Again, collect all reslicing commands
        # into an array and then execute the batch.
        if self.options.skipGrayReslice is False:
            self._logger.info("Reslicing multichannel images.")
            commands = []
            for slice_index in self._slice_transform_map.keys():
                commands.append(self._reslice_color(slice_index))
            self.execute(commands)

        # Yeap, it's done.
        self._logger.info("Finished reslicing.")

    def _reslice_grayscale(self, slice_number):
        """
        Reslice grayscale images.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        # Define all the filenames required by the reslice command
        moving_image_filename = self.f['moving_raw'](idx=slice_number)
        resliced_image_filename = self.f['resliced_gray'](idx=slice_number)
        reference_image_filename = self.f['fixed_raw'](idx=slice_number)

        # Get the transformation file index:
        transform_index = self._slice_transform_map[slice_number]
        transformation_file = self.f['output_transforms'](idx=transform_index)

        # And finally initialize and customize reslice command.
        command = pos_wrappers.command_warp_grayscale_image(
            reference_image=reference_image_filename,
            moving_image=moving_image_filename,
            transformation=transformation_file,
            output_image=resliced_image_filename,
            background=self.options.resliceBackgorund,
            interpolation=self.options.resliceInterpolation)

        return copy.deepcopy(command)

    def _reslice_color(self, slice_number):
        """
        Reslice multichannel image. The reslicing process is conducted via the
        `pos_wrappers.command_warp_rgb_slice` class. More information on the
        actual configuration of the reslicing process is available in the
        documentation of the `pos_wrappers.command_warp_rgb_slice` class.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        # Define all the filenames required by the reslice command
        moving_image_filename = self.f['moving_raw'](idx=slice_number)
        resliced_image_filename = self.f['resliced_color'](idx=slice_number)
        reference_image_filename = self.f['fixed_raw'](idx=slice_number)

        # Get the transformation file index:
        transform_index = self._slice_transform_map[slice_number]
        transformation_file = self.f['output_transforms'](idx=transform_index)

        # And finally initialize and customize reslice command.
        command = pos_wrappers.command_warp_rgb_slice(
            reference_image=reference_image_filename,
            moving_image=moving_image_filename,
            transformation=transformation_file,
            output_image=resliced_image_filename,
            background=self.options.resliceBackgorund,
            interpolation=self.options.resliceInterpolation)

        # Return the created command line parser.
        return copy.deepcopy(command)

    def _get_generic_stack_slice_wrapper(self, mask_type, ouput_filename_type):
        """
        Return generic command wrapper suitable either for stacking grayscale
        images or multichannel images. Aproperiate command line wrapper is returned
        depending on provided `mask_type` and `output_filename_type`.
        The command line wrapper is prepared mostly based on the command line
        parameters which are common between both images stacks thus so there is
        no need to parametrize them individually.

        :param mask_type: mask type determining which images stack will be
                          converted into a volume.
        :type mask_type: str

        :param ouput_filename_type: output filename naming scheme.
        :type ouput_filename_type: str
        """

        # Assign some usefull aliases.
        start, stop, reference = self.options.sliceRange

        # Define the output volume filename. If no custom colume name is
        # provided, the filename is based on the provided processing
        # parameters. In the other case the provided custom filename is used.
        filename_prefix = self._get_parameter_based_output_prefix()
        output_filename = self.f[ouput_filename_type](fname=filename_prefix)

        # Define the warpper according to the provided settings.
        command = pos_wrappers.stack_and_reorient_wrapper(
            stack_mask=self.f[mask_type](),
            slice_start=start,
            slice_end=stop,
            slice_step=self.__VOL_STACK_SLICE_SPACING,
            output_volume_fn=output_filename,
            permutation_order=self.options.outputVolumePermutationOrder,
            orientation_code=self.options.outputVolumeOrientationCode,
            output_type=self.options.outputVolumeScalarType,
            spacing=self.options.outputVolumeSpacing,
            origin=self.options.outputVolumeOrigin,
            interpolation=self.options.setInterpolation,
            resample=self.options.outputVolumeResample)

        # Return the created parser.
        return copy.deepcopy(command)

    def _stack_output_images(self):
        """
        Execute stacking images based on grayscale and multichannel images.
        Both resliced image stacks are turned into volumetric files by this
        method.
        """

        self._logger.info("Stacking the grayscale image stack.")
        command = self._get_generic_stack_slice_wrapper(
                    'resliced_gray_mask', 'out_volume_gray')
        self.execute(command)

        self._logger.info("Stacking the multichannel image stack.")
        command = self._get_generic_stack_slice_wrapper(
                    'resliced_color_mask', 'out_volume_color')
        self.execute(command)

        self._logger.info("Reslicing is done.")

    @classmethod
    def _getCommandLineParser(cls):
        """
        #TODO: _getCommandLineParser -> _get_command_line_parser
        """
        parser = output_volume_workflow._getCommandLineParser()

        obligatory_options = \
            OptionGroup(parser, 'Obligatory options')

        obligatory_options.add_option('--sliceRange', default=None,
            type='int', dest='sliceRange', nargs=2,
            help='Index of the first slice of the stack')
        obligatory_options.add_option('--transformationsRange', default=None,
            type='int', dest='transformationsRange', nargs=2,
            help='Indexed of the transformations.')
        obligatory_options.add_option('--transformationsDirectory', default=None,
            dest='transformationsDirectory', action='store',
            help='Store transformations in given directory instead of using default one.')
        obligatory_options.add_option('--fixedImageInputDirectory', default=None,
            type='str', dest='fixedImageInputDirectory', help='')
        obligatory_options.add_option('--movingImageInputDirectory', default=None,
            type='str', dest='movingImageInputDirectory', help='')
        obligatory_options.add_option('--appendTransformationFilenameTemplate', default=None,
            type='str', action='append',  nargs=2,
            dest='transformSpec', help='')

        workflow_settings = \
            OptionGroup(parser, 'Workflow execution settings')

        workflow_settings.add_option('--skipGrayReslice', default=False,
            dest='skipGrayReslice', action='store_const', const=True,
            help='Supress generating grayscale volume')
        workflow_settings.add_option('--skipColorReslice', default=False,
            dest='skipColorReslice', action='store_const', const=True,
            help='Supress generating RGB volume.')
        workflow_settings.add_option('--skipOutputVolumes', default=False,
            dest='skipOutputVolumes', action='store_const', const=True,
            help='Supress generating color volume')
        workflow_settings.add_option('--outputVolumesDirectory', default=None,
            dest='outputVolumesDirectory', action='store',
            help='Store output volumes in given directory instead of using default one.')

        image_processing_options = \
            OptionGroup(parser, "Image processing options")

        image_processing_options.add_option('--resliceInterpolation',
            dest='resliceInterpolation', default=None, type='str',
            help='Cubic Gaussian Linear Nearest Sinc cubic gaussian linear nearest sinc')
        image_processing_options.add_option('--resliceBackgorund', default=None,
            type='float', dest='resliceBackgorund',
            help='Background color')
        image_processing_options.add_option('--outputVolumeROI', default=None,
            type='int', dest='outputVolumeROI',  nargs=4,
            help='ROI of the output volume - in respect to registration ROI.')

        parser.add_option_group(workflow_settings)
        parser.add_option_group(obligatory_options)
        parser.add_option_group(image_processing_options)

        return parser


if __name__ == '__main__':
    options, args = stack_warp_image_multi_transform.parseArgs()
    process = stack_warp_image_multi_transform(options, args)
    process.launch()
