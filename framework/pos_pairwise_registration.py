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

import os, sys, glob
import datetime, logging
import csv
import copy
from optparse import OptionParser, OptionGroup
from pos_wrapper_skel import output_volume_workflow
import pos_wrappers, pos_parameters

class command_warp_rgb_slice(pos_wrappers.generic_wrapper):
    """
    #TODO: Provide provide doctests and eventually move to a separated module
    # dedicated to linear reconstruction workflow.
    A special instance of reslice rgb.
    # TODO: Merge with similar script in pariwise registration script.
    """

    _template = "c{dimension}d -verbose {background}\
       {reference_image} -as ref -clear \
       -mcs {moving_image}\
       -as b \
       -pop -as g \
       -pop -as r \
       -push ref -push r -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rr -clear \
       -push ref -push g -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rg -clear \
       -push ref -push b -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rb -clear \
       -push rr -push rg -push rb -omc 3 {output_image}"
    #TODO: Copy to the other wrapper (sequential alignment)
    #TODO: Implement custom interpolation function.

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'background': pos_parameters.value_parameter('background', None, '-{_name} {_value}'),
        'reference_image': pos_parameters.filename_parameter('reference_image', None),
        'moving_image': pos_parameters.filename_parameter('moving_image', None),
        'transformation': pos_parameters.filename_parameter('transformation', None),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'region_origin' : pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size' : pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
        'inversion_flag' : pos_parameters.boolean_parameter('inversion_flag', False, str_template=' -scale -1 -shift 255 -type uchar'),
    }


class command_warp_grayscale_image(pos_wrappers.generic_wrapper):
    """
    A special instance of reslice grayscale image dedicated for the sequential
    alignment script.
    #TODO: Provide doctests
    # TODO: Merge with similar wrapper in pariwise registration script.
    """

    _template = "c{dimension}d -verbose \
        {reference_image} -as ref -clear \
        {moving_image} -as moving \
        -push ref -push moving -reslice-itk {transformation} \
        {region_origin} {region_size} \
        -type uchar -o {output_image}"

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'reference_image': pos_parameters.filename_parameter('reference_image', None),
        'moving_image': pos_parameters.filename_parameter('moving_image', None),
        'transformation': pos_parameters.filename_parameter('transformation', None),
        'region_origin' : pos_parameters.vector_parameter('region_origin', None, '-region {_list}vox'),
        'region_size' : pos_parameters.vector_parameter('region_size', None, '{_list}vox'),
        'output_image': pos_parameters.filename_parameter('output_image', None),
    }


class pairwiseRegistration(output_volume_workflow):
    """
    Pairwise slice to slice registration script.
    """

    _f = {
        'fixed_raw_image' : pos_parameters.filename('fixed_raw_image', work_dir = '00_override_this', str_template = '{idx:04d}.nii.gz'),
        'moving_raw_image' : pos_parameters.filename('moving_raw_image', work_dir = '00_override_this', str_template = '{idx:04d}.nii.gz'),

        'moving_gray' : pos_parameters.filename('src_gray', work_dir = '00_moving_gray', str_template='{idx:04d}.nii.gz'),
        'moving_color' : pos_parameters.filename('src_color', work_dir = '01_moving_color', str_template='{idx:04d}.nii.gz'),
        'fixed_gray' : pos_parameters.filename('fixed_gray', work_dir = '02_fixed_gray', str_template='{idx:04d}.nii.gz'),
        'fixed_color' : pos_parameters.filename('fixed_color', work_dir = '03_fixed_color', str_template='{idx:04d}.nii.gz'),
        'additional_gray' : pos_parameters.filename('additional_gray', work_dir = '04_additional_gray', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),
        'additional_color' : pos_parameters.filename('additional_color', work_dir = '05_additional_color', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),

        'transf_naming' : pos_parameters.filename('transf_naming', work_dir = '11_transforms', str_template='tr_m{mIdx:04d}_'),
        'transf_file' : pos_parameters.filename('transf_file', work_dir = '12_transforms', str_template='tr_m{mIdx:04d}_Affine.txt'),

        'resliced_gray' : pos_parameters.filename('resliced_gray', work_dir = '21_gray_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_gray_mask' : pos_parameters.filename('resliced_gray_mask', work_dir = '22_gray_resliced', str_template='%04d.nii.gz'),
        'resliced_color' : pos_parameters.filename('resliced_color', work_dir = '23_resliced_color', str_template='{idx:04d}.nii.gz'),
        'resliced_color_mask' : pos_parameters.filename('resliced_color_mask', work_dir = '24_resliced_color_mask', str_template='%04d.nii.gz'),
        'resliced_add_gray' : pos_parameters.filename('resliced_add_gray', work_dir = '25_resliced_add_gray', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),
        'resliced_add_gray_mask' : pos_parameters.filename('resliced_add_gray_mask', work_dir = '26_resliced_add_gray_mask', str_template='stack_{stack_id:02d}_slice_%04d.nii.gz'),
        'resliced_add_color' : pos_parameters.filename('resliced_add_color', work_dir = '27_resliced_add_color', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),
        'resliced_add_color_mask' : pos_parameters.filename('resliced_add_color_mask', work_dir = '28_resliced_add_color_mask', str_template='stack_{stack_id:02d}_slice_%04d.nii.gz'),

        'out_volume_gray' : pos_parameters.filename('out_volume_gray', work_dir = '31_output_volumes', str_template='{fname}_gray.nii.gz'),
        'out_volume_color' : pos_parameters.filename('out_volume_color', work_dir = '32_output_volumes', str_template='{fname}_color.nii.gz'),
        'out_volume_gray_add' : pos_parameters.filename('out_volume_gray_add', work_dir = '33_output_volumes', str_template='additional_stack_{stack_id:02d}_{fname}_gray.nii.gz'),
        'out_volume_color_add' : pos_parameters.filename('out_volume_color_add', work_dir = '34_output_volumes', str_template='additional_stack_{stack_id:02d}_{fname}_color.nii.gz')
         }

    # Define the magic numbers:
    __AFFINE_ITERATIONS = [10000, 10000, 10000, 10000, 10000]
    __DEFORMABLE_ITERATIONS = [0]
    __IMAGE_DIMENSION = 2
    __HISTOGRAM_MATCHING = True
    __MI_SAMPLES = 16000
    __ALIGNMENT_EPSILON = 1
    __VOL_STACK_SLICE_SPACING = 1

    def _validate_options(self):
        super(self.__class__, self)._initializeOptions()

        # Yes, it is extremely important to provide the slicing range.
        assert self.options.sliceRange, \
            self._logger.error("Slice range parameters (`--sliceRange`) are required. Please provide the slice range. ")

        # Validate, if an input images directory is provided,
        # Obviously, we need to load the images in order to process them.
        assert self.options.fixedImagesDir, \
            self._logger.error("No fixed input images directory is provided. Please provide the input images directory (--fixedImagesDir)")
        assert self.options.movingImagesDir, \
            self._logger.error("No moving input images directory is provided. Please provide the input images directory (--movingImagesDir)")

    def _load_slice_assignment(self):
        """
        Load the fixed image index to moving image index assignent. Such an
        assignment is important as it often happens that both series do not
        have a consistent indexing scheme.

        The index assignment is loaded from the provided file. The file is
        obligatory and when not provided interrupts the workflow execution.

        The assignment is a `moving image` to `fixed image` slice index
        mapping. The mapping defines, which fixed image corresponds to given
        moving slice. The best possible option is to define moving slice index
        in a such way that the mapping is a 1:1 image mapping.
        """
        # Just a simple alias
        image_pairs_filename = self.options.imagePairsAssignmentFile

        # Figure out what is the span if the fixes slices as well as the moving
        # slices.
        self._generate_slice_index()

        # If no slice assignment file is provided, then 1:1 moving image to
        # fixed image is automatically generated.
        if not image_pairs_filename :
            self._logger.debug(
            "No slice assignment file was provided. Using pairwise assignment.")
            self._slice_assignment = \
                dict(zip(self.options.movingSlicesRange,
                         self.options.fixedSlicesRange))
        else:
            # Here I use pretty neat code snipper for determining the
            # dialect of teh csv file. Found at:
            # http://docs.python.org/2/library/csv.html#csv.Sniffer
            self._logger.debug(\
               "Loading slice-to-slice assignment from %s.", mapping_file)
            with open(image_pairs_filename, 'rb') as mapping_file:
                dialect = csv.Sniffer().sniff(mapping_file.read(1024))
                mapping_file.seek(0)
                reader = csv.reader(mapping_file, dialect)

                # Then map the list from file into a dictionary.
                self._slice_assignment = \
                    dict(map(lambda (x, y): (int(x), int(y)), list(reader)))

        # At this point we do have: fixed and moving slice ranges and fixed to
        # moving slice assignment. Below, all of these are verified, if they
        # are correct. Iterate over all moving slices and check whether there
        # is a corresponding moving slice assigned.
        for slice_index in self.options.movingSlicesRange:
            fixed_slice_index = self._slice_assignment[slice_index]
            if fixed_slice_index is None:
                self._logger.error("No fixed slice index defined for the moving slice %d.",
                                   slice_index)
                sys.exit(1)

        self._logger.debug("Mappings and slices' ranges passed the validation.")

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # At the very beginning override the default dummy input images
        # directory by the actual images directory.
        self.f['fixed_raw_image'].override_dir = self.options.fixedImagesDir
        self.f['moving_raw_image'].override_dir = self.options.movingImagesDir

    def _inspect_input_images(self):
        """
        Verify if all the files are availabe: All images have to be ailable. If
        the case is different, the workflow will not proceed and the user will
        be asked to supply the missing images.
        """

        # Iterate over all filenames beeing used it the whole workflow
        # and check if all of them exists.
        for slice_index in self.options.fixedSlicesRange + \
                           self.options.movingSlicesRange:
            slice_filename = self.f['moving_raw_image'](idx=slice_index)

            self._logger.debug("Checking for image: %s.", slice_filename)
            if not os.path.isfile(slice_filename):
                self._logger.error("File does not exist: %s. Exiting",
                                   slice_filename)
                sys.exit(1)

    def _generate_slice_index(self):
        """
        Generate moving image to fixed image mappings.
        """

        # Range of images to register. It is a perfect solution to override the
        # command line argument option with some other value, but hey -
        # nobody's perfect.
        self._logger.debug("Defining default slicing range.")
        self.options.sliceRange = \
                range(self.options.sliceRange[0], self.options.sliceRange[1] + 1)

        # Ok, what is going on here? In the workflow there are two types of
        # ranges: the moving slices range and the fixed slices range. In
        # general they do not necessarily overlap thus in general they are two
        # different ranges. The corespondence between ranges is established
        # according to the `imagePairsAssignmentFile` file supplied via the
        # command line. If neither moving slices range nor fixes slices range
        # are provided, the approperiate ranges are copied from the general
        # slice range. When provided, the custom slices ranges override the
        # default slice range value.

        # Check if custom moving slice range is provided.
        # If it's not, use the default slice range.
        if self.options.movingSlicesRange != None:
            self.options.movingSlicesRange = \
                range(self.options.movingSlicesRange[0],
                      self.options.movingSlicesRange[1] + 1)
            self._logger.debug("Using custom moving slice range.")
        else:
            self.options.movingSlicesRange = self.options.sliceRange
            self._logger.debug("Using default slice range as fixed slice range.")

        # Check if custom fixes slice range is provided.
        # If it's not, use the default slice range.
        if self.options.fixedSlicesRange != None:
            self.options.fixedSlicesRange = \
                range(self.options.fixedSlicesRange[0],
                      self.options.fixedSlicesRange[1] + 1)
            self._logger.debug("Using custom fixed slice range.")
        else:
            self.options.fixedSlicesRange = self.options.sliceRange
            self._logger.debug("Using default slice range as moving slice range.")

    def launch(self):
        self._load_slice_assignment()

        # After proving that the mappings are correct, the script verifies if
        # the files to be coregistered do actually exist. However, the
        # verification is performed only when the script is executed in not in
        # `--druRun` mode:
        if self.options.dryRun is False:
            self._inspect_input_images()

        #self._generates_source_slices()
        #self._calculateTransforms()
        self._reslice()
        #self._stack_output_images()
        if self.options.additionalMovingImagesDirectory is not None:
            self._loadAdditionalStacksResliceSettings()

    def _generates_source_slices(self):
        self._generate_fixed_slices()
        self._generate_moving_slices()

    def _get_generic_source_slice_preparation_wrapper(self):
        """
        Get generic slice preparation wrapper for further refinement.
        """
        command = pos_wrappers.alignment_preprocessor_wrapper(
            registration_color = self.options.registrationColor,
            median_filter_radius = self.options.medianFilterRadius,
            invert_grayscale = self.options.invertGrayscale,
            invert_multichannel = self.options.invertMultichannel)
        return copy.deepcopy(command)

    def _generate_fixed_slices(self):
        """
        Generation of fixed as well as moving slices should be implemented in a
        single method as there is not much of a difference between approach to
        both processes. However, taking into account possible further
        extensions, I decided to split both implementations into separate
        methods.
        """

        self._logger.info("Performing fixed slices generation.")
        # The array collecting all the individual command into a commands
        # batch.
        commands = []

        for slice_number in self._slice_assignment.values():

            command = self._get_generic_source_slice_preparation_wrapper()
            command.updateParameters({
                'input_image' :  self.f['fixed_raw_image'](idx=slice_number),
                'grayscele_output_image' : self.f['fixed_gray'](idx=slice_number),
                'color_output_image' : self.f['fixed_color'](idx=slice_number)})
            commands.append(copy.deepcopy(command))

        # Execute the commands in a batch.
        self.execute(commands)
        self._logger.info("Generating fixed slices. Done.")


    def _generate_moving_slices(self):
        """
        Generation of fixed as well as moving slices should be implemented in a
        single method as there is not much of a difference between approach to
        both processes. However, taking into account possible further
        extensions, I decided to split both implementations into separate
        methods.
        """

        self._logger.info("Generating moving slices.")
        # The array collecting all the individual command into a commands
        # batch.
        commands = []

        for slice_number in self._slice_assignment.values():

            command = self._get_generic_source_slice_preparation_wrapper()
            command.updateParameters({
                'input_image' :  self.f['moving_raw_image'](idx=slice_number),
                'grayscele_output_image' : self.f['moving_gray'](idx=slice_number),
                'color_output_image' : self.f['moving_color'](idx=slice_number)})
            commands.append(copy.deepcopy(command))

        # Execute the commands in a batch.
        self.execute(commands)
        self._logger.info("Generating moving slices. Done.")

    def _calculateTransforms(self):
        commands = []
        for moving_slice, fixed_slice in self._slice_assignment.items():
            transform_command = self._calculate_single_transform(moving_slice, fixed_slice)
            commands.append(transform_command)
        self.execute(commands)

    def _calculate_single_transform(self, moving_slice_index, fixed_slice_index):
        """
        #TODO: test out different types of slices' indexes' (the VERY strange one)
        """
        # Define the registration settings: image-to-image metric and its
        # parameter, number of iterations, output naming, type of the affine
        # transformation.
        similarity_metric = self.options.antsImageMetric
        affine_metric_type = self.options.antsImageMetric
        metric_parameter = self.options.antsImageMetricOpt
        affine_iterations = self.__AFFINE_ITERATIONS
        output_naming = self.f['transf_naming'](mIdx=moving_slice_index,
                                                fIdx=fixed_slice_index)
        use_rigid_transformation = str(self.options.useRigidAffine).lower()
        #TODO: Use enchandes ants boolean parameter wrapper

        # Define the image-to-image metric.
        metrics = []
        metric = pos_wrappers.ants_intensity_meric(
            fixed_image=self.f['fixed_gray'](idx=fixed_slice_index),
            moving_image=self.f['moving_gray'](idx=moving_slice_index),
            metric=similarity_metric,
            weight=1.0,
            parameter=metric_parameter)
        metrics.append(copy.deepcopy(metric))

        #TODO: Handle ants boolean switches:
        # 1) Use histogram matching
        # 2) Use rigid affine registration,

        # Define the registration framework for 2D images,
        # without the deformable registration step, etc.
        registration = pos_wrappers.ants_registration(
            dimension = self.__IMAGE_DIMENSION,
            outputNaming = output_naming,
            iterations = self.__DEFORMABLE_ITERATIONS,
            affineIterations = affine_iterations,
            continueAffine = None,
            rigidAffine = use_rigid_transformation,
            imageMetrics = metrics,
            histogramMatching = str(self.__HISTOGRAM_MATCHING).lower(),
            miOption = [metric_parameter, self.__MI_SAMPLES],
            affineMetricType = affine_metric_type)

        # Return the registration command.
        return copy.deepcopy(registration)

    def _reslice(self):

        # Reslicing grayscale images.  Reslicing multichannel images. Collect
        # all reslicing commands into an array and then execute the batch.
        self._logger.info("Reslicing grayscale images.")
        commands = []
        for slice_index in self.options.movingSlicesRange:
            commands.append(self._resliceGrayscale(slice_index))
        self.execute(commands)

        # Reslicing multichannel images. Again, collect all reslicing commands
        # into an array and then execute the batch.
        self._logger.info("Reslicing multichannel images.")
        commands = []
        for slice_index in self.options.movingSlicesRange:
            commands.append(self._resliceColor(slice_index))
        self.execute(commands)

        # Yeap, it's done.
        self._logger.info("Finished reslicing.")

    def _get_output_volume_roi(self):
        """
        Define output images stack origin and and size according to the
        providing command line arguments. If provided, the resliced images are
        cropped before stacking into volumes. Note that when the slices are
        cropped their origin is preserved. That should be taken into
        consideration when origin of the stacked volume if provided.

        When the output ROI is not defined, nothing special will happen.
        Resliced images will not be cropped in any way.
        """

        # Define output ROI based on provided command line arguments, if such
        # arguments are provided.
        if self.options.outputVolumeROI:
            region_origin_roi = self.options.outputVolumeROI[0:2]
            region_size_roi = self.options.outputVolumeROI[2:4]
        else:
            region_origin_roi = None
            region_size_roi = None

        return region_origin_roi, region_size_roi


    def _get_reslice_wrapper(self, wrapper_type, moving_filename_generator,
                             resliced_type, slice_number):
        """
        """
        # Define all the filenames required by the reslice command

        # There are two ways of defining the moving slice image. Either 1) it can
        # go from the source movins slices that were used for the registration
        # purposes or 2) the moving images can go from the additional images
        # stack. This is solved by passing the whole `filename` parameter.
        moving_image_filename = moving_filename_generator(idx=slice_number)
        resliced_image_filename = self.f[resliced_type](idx=slice_number)
        transformation_file = self.f['transf_file'](mIdx=slice_number)

        # Now get the fixed slice number corresponding to given
        # moving slice index (note that the indexing ob both stack is
        # different)
        fixed_slice_index = self._slice_assignment[slice_number]
        reference_image_filename = self.f['fixed_gray'](idx=fixed_slice_index)

        # Get output volume region of interest (if such region is defined)
        region_origin_roi, region_size_roi =\
            self._get_output_volume_roi()

        # And finally initialize and customize reslice command.
        command = wrapper_type(
            reference_image = reference_image_filename,
            moving_image = moving_image_filename,
            transformation = transformation_file,
            output_image = resliced_image_filename,
            region_origin = region_origin_roi,
            region_size = region_size_roi)
        return copy.deepcopy(command)

    def _resliceGrayscale(self, slice_number):
        """
        Reslice grayscale images.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """
        command = self._get_reslice_wrapper(
            wrapper_type=command_warp_grayscale_image,
            moving_filename_generator=self.f['moving_color'],
            resliced_type='resliced_gray',
            slice_number=slice_number)
        return copy.deepcopy(command)

    def _resliceColor(self, slice_number):
        """
        Reslice grayscale images.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """
        command = self._get_reslice_wrapper(
            wrapper_type=command_warp_rgb_slice,
            moving_filename_generator=self.f['moving_color'],
            resliced_type='resliced_color',
            slice_number=slice_number)
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

        #TODO: Enchance the sytax so that for each series slice ranges are
        # separate

        # Assign some usefull aliases.
        start = self.options.movingSlicesRange[0]
        stop = self.options.movingSlicesRange[-1]
        output_filename = self.f[ouput_filename_type](fname='output_volume')

        # Define the warpper according to the provided settings.
        command = pos_wrappers.stack_and_reorient_wrapper(
            stack_mask = self.f[mask_type](),
            slice_start = start,
            slice_end = stop,
            slice_step = self.__VOL_STACK_SLICE_SPACING,
            output_volume_fn = output_filename,
            permutation_order = self.options.outputVolumePermutationOrder,
            orientation_code = self.options.outputVolumeOrientationCode,
            output_type = self.options.outputVolumeScalarType,
            spacing = self.options.outputVolumeSpacing,
            origin = self.options.outputVolumeOrigin,
            interpolation = self.options.setInterpolation,
            resample = self.options.outputVolumeResample)

        # Return the created parser.
        return copy.deepcopy(command)

    def _stack_output_images(self):
        """
        Execute stacking images based on grayscale and multichannel images.
        """

        command = self._get_generic_stack_slice_wrapper(\
                    'resliced_gray_mask','out_volume_gray')
        self.execute(command)

        command = self._get_generic_stack_slice_wrapper(\
                    'resliced_color_mask','out_volume_color')
        self.execute(command)

        #TODO: Put additional slice stacking here
        # iterate over all additional image stacks and stack the output images.

    def _loadAdditionalStacksResliceSettings(self):
        self._additionalStacksSettings = []
        self._add_stacks_inputs = []

        fields = ['additionalMovingImagesDirectory', 'additionalInvertSource', \
                'additionalInvertMultichannel', 'additionalGrayscaleVolume', \
                'additionalMultichannelVolume', 'additionalInterpolation', \
                'additionalInterpolationBackground']

        keys = ['imgDir', 'invertGs', 'invertMc', 'grayVolName', 'rgbVolName',\
                'interpolation', 'background']

        # Number of additional stacks: len(self._additionalStacksSettings)
        for stackIdx in range(len(self.options.additionalMovingImagesDirectory)):
            newStack = {}
            for field, key in zip(fields, keys):
                newStack[key] = self.options[field][stackIdx]
            self._additionalStacksSettings.append(newStack)

        # This is really cool: prepare a decicated file object for each
        # additional stack:
        for stackIdx in range(len(self._additionalStacksSettings)):
            self._add_stacks_inputs.append(pos_parameters.filename(
            'add_stack_%02d' % stackIdx, str_template='{idx:04d}.nii.gz'))
            self._add_stacks_inputs[-1].override_dir = \
                self.options.additionalMovingImagesDirectory[stackIdx]

    def _AdditionalReslice(self):
        for stackIdx in range(len(self._additionalStacksSettings)):
            for sliceNumber in self.options['sliceRange']:
                self._resliceAdditionalGrayscale(sliceNumber, stackIdx)
            self._mergeOutput(stackIdx)

    def _resliceAdditionalGrayscale(self, sliceNumber, stackIdx):
        stackSettings = self._additionalStacksSettings[stackIdx]

        command = self._get_reslice_wrapper(
            wrapper_type=command_warp_grayscale_image,
            moving_filename_generator=self._add_stacks_inputs[stackIdx],
            resliced_type='resliced_color',
            slice_number=slice_number)
        command.updateParameters({
            'inversion_flag' : stackSettings['invertMc'],
            'background' : stackSettings['background'] })

        return copy.deepcopy(command)

    def _resliceAdditionalMultichannel(self, sliceNumber, stackIdx):
        stackSettings = self._additionalStacksSettings[stackIdx]

        command = self._get_reslice_wrapper(
            wrapper_type=command_warp_rgb_slice,
            moving_filename_generator=self._add_stacks_inputs[stackIdx],
            resliced_type='resliced_color',
            slice_number=slice_number)
        command.updateParameters({
            'inversion_flag' : stackSettings['invertGs'],
            'background' : stackSettings['background'] })

        return copy.deepcopy(command)

    @classmethod
    def _getCommandLineParser(cls):
        parser = output_volume_workflow._getCommandLineParser()

        parser.add_option('--fixedImagesDir', default=None,
            type='str', dest='fixedImagesDir', help='')
        parser.add_option('--movingImagesDir', default=None,
            type='str', dest='movingImagesDir', help='')

        parser.add_option('--imagePairsAssignmentFile', default=None,
            type='str', dest='imagePairsAssignmentFile', help='File carrying assignment of a fixed image to corresponding moving image.')
        parser.add_option('--sliceRange', default=None, nargs = 2,
            type='int', dest='sliceRange',
            help='Index of the first and last slice of the stack')
        parser.add_option('--movingSlicesRange', default=None,
            type='int', dest='movingSlicesRange', nargs = 2,
            help='Range of moving slices (for preprocessing). By default the same as fixed slice range.')
        parser.add_option('--fixedSlicesRange', default=None,
            type='int', dest='fixedSlicesRange', nargs = 2,
            help='Range of fixed slices (for preprocessing). By default the same as fixed slice range.')

        parser.add_option('--registrationColor',
            dest='registrationColor', default='blue', type='str',
            help='In rgb images - color channel on which \
            registration will be performed. Has no meaning for \
            grayscale input images. Possible values: r/red, g/green, b/blue.')
        parser.add_option('--medianFilterRadius', dest='medianFilterRadius',
            default=None, type='int', nargs=2,
            help='Median filter radius in voxels e.g. 2 2')
        parser.add_option('--invertGrayscale', dest='invertGrayscale',
            default=None, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
        parser.add_option('--invertMultichannel', dest='invertMultichannel',
            default=None, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
        parser.add_option('--outputVolumeROI', default=None,
            type='int', dest='outputVolumeROI',  nargs=4,
            help='ROI of the output volume - in respect to registration ROI.')

        parser.add_option('--antsImageMetric', default='MI',
                type='str', dest='antsImageMetric',
                help='ANTS image to image metric. See ANTS documentation.')
        parser.add_option('--useRigidAffine', default=False,
                dest='useRigidAffine', action='store_const', const=True,
                help='Use rigid affine transformation. By default affine transformation is used to drive the registration ')
        parser.add_option('--antsImageMetricOpt', default=32,
                type='int', dest='antsImageMetricOpt',
                help='Parameter of ANTS i2i metric.')
        parser.add_option('--additionalAntsParameters', default=None,
                type='str', dest='additionalAntsParameters',  help='Addidtional ANTS command line parameters (provide within double quote: "")')

        additionalStackReslice = OptionGroup(parser, 'Settings for reslicing additional image stacks')
        additionalStackReslice.add_option('--additionalMovingImagesDirectory', default=None,
                dest='additionalMovingImagesDirectory', type='str',
                action='append', help='')
        additionalStackReslice.add_option('--additionalInvertSource', default=None,
                dest='additionalInvertSource', type='str',
                action='append', help='')
        additionalStackReslice.add_option('--additionalInvertMultichannel', default=None,
                dest='additionalInvertMultichannel', type='int',
                action='append', help='')
        additionalStackReslice.add_option('--additionalGrayscaleVolume', default=None,
                dest='additionalGrayscaleVolume', type='str',
                action='append', help='')
        additionalStackReslice.add_option('--additionalMultichannelVolume', default=None,
                dest='additionalMultichannelVolume', type='str',
                action='append', help='')
        additionalStackReslice.add_option('--additionalInterpolation', default=None,
                dest='additionalInterpolation', type='str',
                action='append', help='')
        additionalStackReslice.add_option('--additionalInterpolationBackground', default=None,
                dest='additionalInterpolationBackground', type='float',
                action='append', help='')

        parser.add_option_group(additionalStackReslice)

        return parser

#       def _mergeOutput(self, stackIdx = None):
#           """
#           Merge registered and resliced images into consitent volume with assigned
#           voxel spacing. Grayscale as well as multichannel volumes are created.
#           """

#           # Generate names of the output volume. The names are combination of the
#           # processing options.
#           if stackIdx != None:
#               grayVolumeName = self._getOutputVolumeName(\
#                       volumeType = self.__c.OUT_VOL_GS_A, stackIdx = stackIdx)
#               colorVolumeName= self._getOutputVolumeName(\
#                       volumeType = self.__c.OUT_VOL_RGB_A, stackIdx = stackIdx)
#           else:
#               grayVolumeName = self._getOutputVolumeName(volumeType = self.__c.OUT_VOL_GS)
#               colorVolumeName= self._getOutputVolumeName(volumeType = self.__c.OUT_VOL_RGB)

#           factor = self.options['movingImageResize']
#           outputVolumeSpacing = " ".join(map(str,self.options['outputVolumeSpacing']))
#           volumeTempFn = os.path.join( \
#                   self.options['process_outputVolumes'], '__temp__rgbvol.vtk')
#           volumeOutputMultichannelFn = os.path.join( \
#                   self.options['local_outputVolumes'], colorVolumeName)
#           volumeOutputGrayscale = os.path.join( \
#                   self.options['local_outputVolumes'], grayVolumeName)
#           outputVolumeScalarType = self.options['outputVolumeScalarType']

#           if self.options['outputVolumeResample'] != None:
#               resamplingString = '--resample ' + " ".join(map(str, self.options['outputVolumeResample']))
#           else:
#               resamplingString = ""

#           cmdDict = {}
#           if stackIdx == None:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_RGB_MASK)
#           else:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_RGB_MASK_A)
#           cmdDict['sliceStart']     = self.options['startSliceIndex']
#           cmdDict['sliceEnd']       = self.options['endSliceIndex']
#           cmdDict['spacing']        = outputVolumeSpacing
#           cmdDict['origin']         = " ".join(map(str, self.options['outputVolumeOrigin']))
#           cmdDict['volumeTempFn']   = volumeTempFn
#           cmdDict['volumeOutputFn'] = volumeOutputMultichannelFn
#           cmdDict['outputVolumeScalarType'] = outputVolumeScalarType
#           cmdDict['permutationOrder'] = " ".join(map(str, self.options['outputVolumePermutationOrder']))
#           cmdDict['orientationCode'] = self.options['outputVolumeOrientationCode']
#           cmdDict['resampling']      = resamplingString

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           if stackIdx == None:
#               if not self.options['skipColorReslice']:
#                   command = COMMAND_STACK_SLICES_RGB % cmdDict
#                   self._executeSystem(command, order = "#0009STACK_RGB")
#           else:
#               stackSettings = self._additionalStacksSettings[stackIdx]
#               if stackSettings['rgbVolName'] != 'skip':
#                   order = "%02d" % (10*stackIdx + 17)
#                   command = COMMAND_STACK_SLICES_RGB % cmdDict
#                   self._executeSystem(command, order = "#00" + order + "STACK_ADDITIONAL_RGB")

#           cmdDict = {}
#           if stackIdx == None:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_MASK)
#           else:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_MASK_A)
#           cmdDict['volumeTempFn']   = volumeTempFn
#           cmdDict['volumeOutputFn'] = volumeOutputGrayscale
#           cmdDict['spacing']        = outputVolumeSpacing
#           cmdDict['origin']         = " ".join(map(str, self.options['outputVolumeOrigin']))
#           cmdDict['outputVolumeScalarType'] = outputVolumeScalarType
#           cmdDict['permutationOrder'] = " ".join(map(str, self.options['outputVolumePermutationOrder']))
#           cmdDict['orientationCode'] = self.options['outputVolumeOrientationCode']
#           cmdDict['resampling']      = resamplingString

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '--interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           if stackIdx == None:
#               if not self.options['skipGrayReslice']:
#                   command = COMMAND_STACK_SLICES_GRAY % cmdDict
#                   self._executeSystem(command, order = '#0008STACK_GRAYSCALE')
#           else:
#               stackSettings = self._additionalStacksSettings[stackIdx]
#               if stackSettings['grayVolName'] != 'skip':
#                   order = "%02d" % (10*stackIdx + 16)
#                   command = COMMAND_STACK_SLICES_GRAY % cmdDict
#                   self._executeSystem(command, order = "#00" + order + "STACK_ADDITIONAL_GRAYSCALE")

#       @classmethod
#       def _getCommandLineParser(cls):
#           parser = posProcessingElement._getCommandLineParser()

#           regSettings = \
#                   OptionGroup(parser, 'Registration setttings.')

#           regSettings.add_option('--antsImageMetric', default='MI',
#                   type='str', dest='antsImageMetric',
#                   help='ANTS image to image metric. See ANTS documentation.')
#           regSettings.add_option('--useRigidAffine', default=False,
#                   dest='useRigidAffine', action='store_const', const=True,
#                   help='Use rigid affine transformation. By default affine transformation is used to drive the registration ')
#           regSettings.add_option('--antsImageMetricOpt', default=32,
#                   type='int', dest='antsImageMetricOpt',
#                   help='Parameter of ANTS i2i metric.')
#           regSettings.add_option('--additionalAntsParameters', default=None,
#                   type='str', dest='additionalAntsParameters',  help='Addidtional ANTS command line parameters (provide within double quote: "")')
#           regSettings.add_option('--startSliceIndex', default=0,
#                   type='int', dest='startSliceIndex',
#                   help='Index of the first slice of the stack')
#           regSettings.add_option('--endSliceIndex', default=None,
#                   type='int', dest='endSliceIndex',
#                   help='Index of the last slice of the stack')
#           regSettings.add_option('--movingSlicesRange', default=None,
#                   type='int', dest='movingSlicesRange', nargs = 2,
#                   help='Range of moving slices (for preprocessing). By default the same as fixed slice range.')
#           regSettings.add_option('--fixedSlicesRange', default=None,
#                   type='int', dest='fixedSlicesRange', nargs = 2,
#                   help='Range of fixed slices (for preprocessing). By default the same as fixed slice range.')
#           regSettings.add_option('--imagePairsAssignmentFile', default=None,
#                   type='str', dest='imagePairsAssignmentFile', help='File carrying assignment of a fixed image to corresponding moving image.')
#           regSettings.add_option('--registrationColorChannelMovingImage', default='blue',
#                       type='str', dest='registrationColorChannelMovingImage',
#                       help='In rgb images - color channel on which \
#                       registration will be performed. Has no meaning for \
#                       grayscale input images. Possible values: r/red, g/green, b/blue.')
#           regSettings.add_option('--registrationColorChannelFixedImage', default='red',
#                       type='str', dest='registrationColorChannelFixedImage',
#                       help='In rgb images - color channel on which \
#                       registration will be performed. Has no meaning for \
#                       grayscale input images. Possible values: r/red, g/green, b/blue.')

#           preprocessingSettings = \
#                   OptionGroup(parser, 'Image preprocessing settings')
#           preprocessingSettings.add_option('--fixedImageSpacing', dest='fixedImageSpacing',
#                   default=[1.,1.], action='store', type='float', nargs = 2, help='Spacing of the fixed image in 1:1 scale (before resizing).')
#           preprocessingSettings.add_option('--movingImageSpacing', dest='movingImageSpacing',
#                   default=[1.,1.], action='store', type='float', nargs =2, help='Spacing of the moving image in 1:1 scale (before resizing).')
#           preprocessingSettings.add_option('--fixedImageResize', dest='fixedImageResize',
#                   default=1., action='store', type='float', nargs =1, help='Resampling ratio (optional). Allows to alter registration speed and accuracy. Determines size of the ouput volume.')
#           preprocessingSettings.add_option('--movingImageResize', dest='movingImageResize',
#                   default=1., action='store', type='float', nargs =1, help='Resampling ratio (optional). Allows to alter registration speed and accuracy. Determines size of the ouput volume.')
#           preprocessingSettings.add_option('--fixedImageInputDirectory', default=None,
#                       type='str', dest='fixedImageInputDirectory', help='')
#           preprocessingSettings.add_option('--movingImageInputDirectory', default=None,
#                       type='str', dest='movingImageInputDirectory', help='')

#           workflowSettings = \
#                   OptionGroup(parser, 'Workflow settings')
#           workflowSettings.add_option('--skipGrayReslice', default=False,
#                   dest='skipGrayReslice', action='store_const', const=True,
#                   help='Supress generating grayscale volume')
#           workflowSettings.add_option('--skipColorReslice', default=False,
#                   dest='skipColorReslice', action='store_const', const=True,
#                   help='Supress generating RGB volume.')
#           workflowSettings.add_option('--skipGeneratingSourceSlices', default=False,
#                   dest='skipGeneratingSourceSlices', action='store_const', const=True,
#                   help='Supress processing source slices.')
#           workflowSettings.add_option('--skipGeneratingTransforms', default=False,
#                   dest='skipGeneratingTransforms', action='store_const', const=True,
#                   help='Supress generating transforms.')
#           workflowSettings.add_option('--skipPreprocessing', default=False,
#                   dest='skipPreprocessing', action='store_const', const=True,
#                   help='Supress preprocessing images.')
#           workflowSettings.add_option('--transformationsDirectory', default=None,
#                   dest='transformationsDirectory', action='store',
#                   help='Store transformations in given directory instead of using default one.')
#           workflowSettings.add_option('--outputVolumesDirectory', default=None,
#                   dest='outputVolumesDirectory', action='store',
#                   help='Store output volumes in given directory instead of using default one.')
#           workflowSettings.add_option('--interpolationBackgorundColor', default=None,
#               type='float', dest='interpolationBackgorundColor',
#               help='Background color')

#           dataPreparationOptions= OptionGroup(parser, 'Source data preprocessing options')

#           dataPreparationOptions.add_option('--fixedImageMedianFilterRadius', default=None,
#                   dest='fixedImageMedianFilterRadius', type='str',
#                   help='Median filter radius according to ImageMagick syntax.')
#           dataPreparationOptions.add_option('--movingImageMedianFilterRadius', default=None,
#                   dest='movingImageMedianFilterRadius', type='str',
#                   help='Median filter radius according to ImageMagick syntax.')
#           dataPreparationOptions.add_option('--invertSourceImage', default=False,
#                   dest='invertSourceImage',  action='store_const', const=True,
#                   help='Invert source image: both, fixed and moving, before registration')
#           dataPreparationOptions.add_option('--invertMultichannelImage', default=False,
#                   dest='invertMultichannelImage',  action='store_const', const=True,
#                   help='Invert source image: both, grayscale and multichannel, before registration')
#           dataPreparationOptions.add_option('--fixedCustomImageMagic', default=None,
#                   dest='fixedCustomImageMagic',  action='store',
#                   help='Custom ImageMagick processing string for fixed image.')
#           dataPreparationOptions.add_option('--movingCustomImageMagic', default=None,
#                   dest='movingCustomImageMagic', action='store',
#                   help='Custom ImageMagick processing string for moving image.')

#                   action='append', help='')

#           outputVolumeSettings.add_option('--grayscaleVolumeFilename',  dest='grayscaleVolumeFilename',
#                   type='str', default=None)
#           outputVolumeSettings.add_option('--rgbVolumeFilename',  dest='rgbVolumeFilename',
#                   type='str', default=None)

#           parser.add_option_group(workflowSettings)
#           parser.add_option_group(preprocessingSettings)
#           parser.add_option_group(regSettings)
#           parser.add_option_group(additionalStackReslice)
#           parser.add_option_group(outputVolumeSettings)
#           return parser


if __name__ == '__main__':
    options, args = pairwiseRegistration.parseArgs()
    se = pairwiseRegistration(options, args)
    se.launch()
