#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys
from optparse import OptionParser, OptionGroup
import copy
import networkx as nx

import pos_wrappers
import pos_parameters
from pos_wrapper_skel import output_volume_workflow
from pos_common import flatten

"""
Note that the input files are required to be niftii files!!

python pos_sequential_alignment.py
    --sliceRange 50 70 60
    --inputImageDir /home/pmajka/possum/data/03_01_NN3/66_histology_extracted_slides
    --invertMultichannel --loglevel=DEBUG
    -d /dev/shm/x
    --outputVolumeSpacing 0.1 0.1 0.06
    --skipTransformations
    --skipSourceSlicesGeneration
    --skipReslice
    --skipOutputVolumes
"""

class command_warp_rgb_slice(pos_wrappers.generic_wrapper):
    """
    #TODO: Provide provide doctests and eventually move to a separated module
    # dedicated to linear reconstruction workflow.
    A special instance of reslice rgb.
    """

    _template = "c{dimension}d -verbose \
       {reference_image} -as ref -clear \
       -mcs {moving_image}\
       -as b \
       -pop -as g \
       -pop -as r \
       -push ref -push r -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rr -clear \
       -push ref -push g -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rg -clear \
       -push ref -push b -reslice-itk {transformation} {region_origin} {region_size} {inversion_flag} -as rb -clear \
       -push rr -push rg -push rb -omc 3 {output_image}"

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
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


class sequential_alignment(output_volume_workflow):
    """
    Input images: three channel rgb images (uchar per channel) in niftii format. That's it.
    """

    _f = {
        'raw_image' : pos_parameters.filename('raw_image', work_dir = '00_override_this', str_template = '{idx:04d}.nii.gz'),
        'src_gray' : pos_parameters.filename('src_gray', work_dir = '00_source_gray', str_template='{idx:04d}.nii.gz'),
        'src_color' : pos_parameters.filename('src_color', work_dir = '01_source_color', str_template='{idx:04d}.nii.gz'),
        'part_naming' : pos_parameters.filename('part_naming', work_dir = '02_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_'),
        'part_transf' : pos_parameters.filename('part_transf', work_dir = '02_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_Affine.txt'),
        'comp_transf' : pos_parameters.filename('comp_transf', work_dir = '02_transforms', str_template='ct_m{mIdx:04d}_f{fIdx:04d}_Affine.txt'),
        'resliced_gray' : pos_parameters.filename('resliced_gray', work_dir = '04_gray_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_gray_mask' : pos_parameters.filename('resliced_gray_mask', work_dir = '04_gray_resliced', str_template='%04d.nii.gz'),
        'resliced_color' : pos_parameters.filename('resliced_color', work_dir = '05_color_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_color_mask' : pos_parameters.filename('resliced_color_mask', work_dir = '05_color_resliced', str_template='%04d.nii.gz'),
        'out_volume_gray' : pos_parameters.filename('out_volume_gray', work_dir = '06_output_volumes', str_template='{fname}_gray.nii.gz'),
        'out_volume_color' : pos_parameters.filename('out_volume_color', work_dir = '06_output_volumes', str_template='{fname}_color.nii.gz'),
        'transform_plot' : pos_parameters.filename('transform_plot', work_dir = '06_output_volumes', str_template='{fname}.png'),
         }

    _usage = ""

    # Define the magic numbers:
    #__AFFINE_ITERATIONS = [10000, 10000, 10000, 10000, 10000]
    __AFFINE_ITERATIONS = [10000,0,0,0,0,0]
    __DEFORMABLE_ITERATIONS = [0]
    __IMAGE_DIMENSION = 2
    __HISTOGRAM_MATCHING = True
    __MI_SAMPLES = 16000
    __ALIGNMENT_EPSILON = 1
    __VOL_STACK_SLICE_SPACING = 1

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

    def _initializeOptions(self):
        super(self.__class__, self)._initializeOptions()

        # Yes, it is extremely important to provide the slicing range.
        assert self.options.sliceRange, \
            self._logger.error("Slice range parameters (`--sliceRange`) are required. Please provide the slice range. ")

        # Define slices' range. All slices within given range will be
        # processed. Make sure that all images are available.
        self.options.slice_range = \
            range(self.options.sliceRange[0], self.options.sliceRange[1] + 1)

        # Validate, if an input images directory is provided,
        # Obviously, we need to load the images in order to process them.
        assert self.options.inputImageDir, \
            self._logger.error("No input images directory is provided. Please provide the input images directory (--inputImageDir)")

        # Verify, if the provided image-to-image metric is provided.
        assert self.options.antsImageMetric.lower() in ['mi','cc','msq'], \
            self._logger.error("Provided image-to-image metric name is invalid. Three image-to-image metrics are allowed: MSQ, MI, CC.")

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # At the very beginning override the default dummy input images
        # directory by the actual images directory.
        self.f['raw_image'].override_dir = self.options.inputImageDir

        # Overriding the transformations directory
        # It might be usefull i.e. when one wants to save the transformation
        # to a different directory than the default one.
        # Note that directory names for two file types has to be switched.
        if self.options.transformationsDirectory is not False:
            self.f['part_naming'].override_dir = \
                self.options.transformationsDirectory
            self.f['part_transf'].override_dir = \
                self.options.transformationsDirectory
            self.f['comp_transf'].override_dir = \
                self.options.transformationsDirectory

        # The output volumes directory may be overriden as well
        # Note that the the output volumes directory stores also
        # transformation analyses plots.
        if self.options.outputVolumesDirectory is not False:
            self.f['out_volume_gray'].override_dir = \
                self.options.outputVolumesDirectory
            self.f['out_volume_color'].override_dir = \
                self.options.outputVolumesDirectory
            self.f['transform_plot'].override_dir = \
                self.options.outputVolumesDirectory

        # Apart from just setting the custom output volumes directory, one can
        # also customize even the output filename of both, grayscale and
        # multichannel volumes! That a variety of options!
        if self.options.grayscaleVolumeFilename:
            self.f['out_volume_gray'].override_fname = \
                self.options.grayscaleVolumeFilename
        if self.options.multichannelVolumeFilename:
            self.f['out_volume_color'].override_fname = \
                self.options.multichannelVolumeFilename

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Before launching the registration process check, if the intput
        # directory and all the input images exist.
        self._inspect_input_images()

        # Prepare the input slices. Both, grayscale and rgb slices are prepared
        # simltaneously by a single routine. Slices preparation may be
        # disabled, switched off by providing approperiate command line
        # parameter. In that's the case, this step will be skipped.
        if self.options.skipSourceSlicesGeneration is not True:
            self._generate_source_slices()

        # Generate transforms. This step may be switched off by providing
        # aproperiate command line parameter.
        if self.options.skipTransformations is not True:
            self._calculate_transforms()

        # Reslice the input slices according to the generated transforms.
        # This step may be skipped by providing approperiate command line
        # parameter.
        if self.options.skipReslice is not True:
            self._reslice()

        # Stack both grayscale as well as the rgb slices into a volume.
        # This step may be skipped by providing approperiate command line
        # parameter.
        if self.options.skipOutputVolumes is not True:
            self._stack_output_images()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _inspect_input_images(self):
        """
        Verify if all the files are availabe: All images have to be ailable. If
        the case is different, the workflow will not proceed and the user will
        be asked to supply the missing images.
        """

        # Iterate over all filenames and check if the file exists.
        for slice_index in self.options.slice_range:
            slice_filename = self.f['raw_image'](idx=slice_index)

            self._logger.debug("Checking for image: %s.", slice_filename)
            if not os.path.isfile(slice_filename):
                self._logger.error("File does not exist: %s. Exiting",
                                   slice_filename)
                sys.exit(1)

    def _generate_source_slices(self):
        """
        Generate source slices for the registration purposes. Both grayscale
        and multichannel images are generates by this routine.
        """

        self._logger.info("Performing source slice generation.")

        # The array collecting all the individual command into a commands
        # batch.
        commands = []

        for slice_number in self.options.slice_range:

            command = pos_wrappers.alignment_preprocessor_wrapper(
               input_image = self.f['raw_image'](idx=slice_number),
               grayscele_output_image = self.f['src_gray'](idx=slice_number),
               color_output_image = self.f['src_color'](idx=slice_number),
               registration_roi = self.options.registrationROI,
               registration_resize = self.options.registrationResize,
               registration_color = self.options.registrationColor,
               median_filter_radius = self.options.medianFilterRadius,
               invert_grayscale = self.options.invertGrayscale,
               invert_multichannel = self.options.invertMultichannel)
            commands.append(copy.deepcopy(command))

        # Execute the commands in a batch.
        self.execute(commands)

        self._logger.info("Source slice generation is completed.")

    def _calculate_transforms(self):
        """
        This rutine calculates the affine (or rigid transformations) for the
        sequential alignment. This step consists of two stages. The first stage
        calculates a partial transformation while the second stage composes the
        partial transformation into the composite transformations.

        The partial transformation 'connects' two consecutive slices and the
        composite trasformation binds given moving slice with the reference
        slice.

        Note that this routine does not apply the calculated transformations to
        the source images. This is done in further steps of processing.
        """

        self._logger.info("Generating transformations.")

        # Calculate partial transforms - get partial transformation chain;
        partial_transformation_pairs = \
            map(lambda idx: self._get_slice_pair(idx),
                            self.options.slice_range)

        # Flatten the slices pairs
        partial_transformation_pairs =\
                list(flatten(partial_transformation_pairs))

        # Calculate affine transformation for each slices pair
        commands = map(lambda x: self._get_partial_transform(*x),
                                 partial_transformation_pairs)
        self.execute(commands)

        # Finally, calculate composite transforms
        commands = []
        for moving_slice_index in self.options.slice_range:
            commands.append(self._calculate_composite(moving_slice_index))
        self.execute(commands)

        self._logger.info("Done with transformations.")

    def _get_slice_pair(self, moving_slice_index):
        """
        Returns pairs of slices between which partial transformations will be
        calculated.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        # Just convenient aliases
        i = moving_slice_index
        s, e, r = tuple(self.options.sliceRange)

        retDict = []
        epsilon = self.__ALIGNMENT_EPSILON

        if i == r:
            j = i
            retDict.append((i, j))
        if i > r:
            for j in list(range(i - epsilon, i)):
                if j <= e and i != j and j >= r:
                    retDict.append((i, j))
        if i < r:
            for j in list(range(i, i + epsilon + 1)):
                if j >= s and i != j and j <= r:
                    retDict.append((i, j))

        return retDict

    def _get_partial_transform(self, moving_slice_index, fixed_slice_index):
        """
        Get a single partial transform which registers given moving slice into
        a fixed slice.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int

        :param fixed_slice_index: fixed slice index
        :type fixed_slice_index: int

        :return: Registration command.
        """

        # Define the registration settings: image-to-image metric and its
        # parameter, number of iterations, output naming, type of the affine
        # transformation.
        similarity_metric = self.options.antsImageMetric
        affine_metric_type = self.options.antsImageMetric
        metric_parameter = self.options.antsImageMetricOpt
        affine_iterations = self.__AFFINE_ITERATIONS
        output_naming = self.f['part_naming'](mIdx=moving_slice_index,
                                              fIdx=fixed_slice_index)
        use_rigid_transformation = self.options.useRigidAffine

        # Define the image-to-image metric.
        metrics = []
        metric = pos_wrappers.ants_intensity_meric(
            fixed_image=self.f['src_gray'](idx=fixed_slice_index),
            moving_image=self.f['src_gray'](idx=moving_slice_index),
            metric=similarity_metric,
            weight=1.0,
            parameter=metric_parameter)
        metrics.append(copy.deepcopy(metric))

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
            histogramMatching = self.__HISTOGRAM_MATCHING,
            miOption = [metric_parameter, self.__MI_SAMPLES],
            affineMetricType = affine_metric_type)

        # Return the registration command.
        return copy.deepcopy(registration)

    def _get_transformation_chain(self, moving_slice_index):
        """
        :param moving_slice_index: moving slice index
        :type moving_slice_index: int

        :return: chain of partial transformations connecting
                 given moving slice with the reference image
        :rtype: array
        """

        # Define some convenient aliases
        i = moving_slice_index
        s, e, r = tuple(self.options.sliceRange)

        retDict = []

        if i == r:
            retDict.append((i, i))
        if i > r:
            for j in list(reversed(range(r, i))):
                retDict.append((j + 1, j))
        if i < r:
            for j in range(i, r):
                retDict.append((j, j + 1))

        return retDict

    def _calculate_composite(self, moving_slice_index):
        """
        Composes individual partial transformations into composite
        transformation registering provided moving slice to the reference
        image.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """
        transformation_chain = \
            self._get_transformation_chain(moving_slice_index)

        # Initialize the partial transforms array and then collect all partial
        # transformations constituting given composite transformation.
        partial_transformations = []
        for (m_slice, r_slice) in transformation_chain:
            partial_transformations.append(
                self.f['part_transf'](mIdx=m_slice, fIdx=r_slice))

        # Define the output transformation filename
        composite_transform_filename = \
            self.f['comp_transf'](mIdx=moving_slice_index, fIdx=r_slice)

        # Initialize and define the composite transformation wrapper
        command = pos_wrappers.ants_compose_multi_transform(
            dimension = self.__IMAGE_DIMENSION,
            output_image = composite_transform_filename,
            deformable_list = [],
            affine_list = partial_transformations)

        return copy.deepcopy(command)

    def _reslice(self):
        """
        Reslice input images according to composed transformations. Both,
        grayscale and multichannel images are resliced.
        """

        # Reslicing grayscale images.  Reslicing multichannel images. Collect
        # all reslicing commands into an array and then execute the batch.
        self._logger.info("Reslicing grayscale images.")
        commands = []
        for slice_index in self.options.slice_range:
            commands.append(self._resliceGrayscale(slice_index))
        self.execute(commands)

        # Reslicing multichannel images. Again, collect all reslicing commands
        # into an array and then execute the batch.
        self._logger.info("Reslicing multichannel images.")
        commands = []
        for slice_index in self.options.slice_range:
            commands.append(self._resliceColor(slice_index))
        self.execute(commands)

        # Yeap, it's done.
        self._logger.info("Finished reslicing.")

    def _resliceGrayscale(self, slice_number):
        """
        Reslice grayscale images.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        # Define all the filenames required by the reslice command
        moving_image_filename = self.f['src_gray'](idx=slice_number)
        resliced_image_filename = self.f['resliced_gray'](idx=slice_number)
        reference_image_filename = self.f['src_gray'](
            idx=self.options.slice_range[2])
        transformation_file = self.f['comp_transf'](
            mIdx=slice_number, fIdx=self.options.sliceRange[2])

        # Get output volume region of interest (if such region is defined)
        region_origin_roi, region_size_roi =\
            self._get_output_volume_roi()

        # And finally initialize and customize reslice command.
        command = command_warp_grayscale_image(
            reference_image = reference_image_filename,
            moving_image = moving_image_filename,
            transformation = transformation_file,
            output_image = resliced_image_filename,
            region_origin = region_origin_roi,
            region_size = region_size_roi)
        return copy.deepcopy(command)

    def _resliceColor(self, slice_number):
        """
        Reslice multichannel image stack.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        # Define all the filenames required by the reslice command
        moving_image_filename = self.f['src_color'](idx=slice_number)
        resliced_image_filename = self.f['resliced_color'](idx=slice_number)
        reference_image_filename = self.f['src_gray'](
            idx=self.options.slice_range[2])
        transformation_file = self.f['comp_transf'](
            mIdx=slice_number, fIdx=self.options.sliceRange[2])

        # Get output volume region of interest (if such region is defined)
        region_origin_roi, region_size_roi =\
            self._get_output_volume_roi()

        # And finally initialize and customize reslice command.
        command = command_warp_rgb_slice(
            reference_image = reference_image_filename,
            moving_image = moving_image_filename,
            transformation = transformation_file,
            output_image = resliced_image_filename,
            region_origin = region_origin_roi,
            region_size = region_size_roi,
            inversion_flag = self.options.invertMultichannel)

        # Return the created command line parser.
        return copy.deepcopy(command)

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


    @classmethod
    def _getCommandLineParser(cls):
        parser = output_volume_workflow._getCommandLineParser()

        parser.add_option('--sliceRange', default=None,
            type='int', dest='sliceRange', nargs = 3,
            help='Slice range: start, stop, reference. Requires three integers. REQUIRED')
        parser.add_option('--inputImageDir', default=None,
            type='str', dest='inputImageDir',
            help='')

        generalOptions = OptionGroup(parser, 'General workflow options.')

        generalOptions.add_option('--outputVolumesDirectory', default=False,
            dest='outputVolumesDirectory', type="str",
            help='Directory to which registration results will be sored.')
        generalOptions.add_option('--grayscaleVolumeFilename', default=False,
            dest='grayscaleVolumeFilename', type='str',
            help='Filename for the output grayscale volume')
        generalOptions.add_option('--multichannelVolumeFilename', default=False,
            dest='multichannelVolumeFilename', type='str',
            help='Filename for the output multichannel volume.')
        generalOptions.add_option('--transformationsDirectory', default=False,
            dest='transformationsDirectory', type="str",
            help='Use provided transformation directory instead of the default one.')
        generalOptions.add_option('--skipTransformations', default=False,
            dest='skipTransformations', action='store_const', const=True,
            help='Supress transformation calculation')
        generalOptions.add_option('--skipSourceSlicesGeneration', default=False,
            dest='skipSourceSlicesGeneration', action='store_const', const=True,
            help='Supress generation source slices')
        generalOptions.add_option('--skipReslice', default=False,
            dest='skipReslice', action='store_const', const=True,
            help='Supress generating grayscale volume')
        generalOptions.add_option('--skipOutputVolumes', default=False,
            dest='skipOutputVolumes', action='store_const', const=True,
            help='Supress generating color volume')

        registrationOptions = OptionGroup(parser, 'Options driving the registration process.')
        registrationOptions.add_option('--registrationROI', dest='registrationROI',
            default=None, type='int', nargs=4,
            help='ROI of the input image used for registration (ox, oy, sx, sy).')
        registrationOptions.add_option('--registrationResize', dest='registrationResize',
            default=None, type='float',
            help='Scaling factor for the source image used for registration. Float between 0 and 1.')
        registrationOptions.add_option('--registrationColor',
            dest='registrationColor', default='blue', type='str',
            help='In rgb images - color channel on which \
            registration will be performed. Has no meaning for \
            grayscale input images. Possible values: r/red, g/green, b/blue.')
        registrationOptions.add_option('--medianFilterRadius', dest='medianFilterRadius',
            default=None, type='int', nargs=2,
            help='Median filter radius in voxels e.g. 2 2')
        registrationOptions.add_option('--invertGrayscale', dest='invertGrayscale',
            default=None, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
        registrationOptions.add_option('--invertMultichannel', dest='invertMultichannel',
            default=None, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
        registrationOptions.add_option('--outputVolumeROI', default=None,
            type='int', dest='outputVolumeROI',  nargs=4,
            help='ROI of the output volume - in respect to registration ROI.')
        registrationOptions.add_option('--antsImageMetric', default='MI',
            type='str', dest='antsImageMetric',
            help='ANTS affine image to image metric. Three values are allowed: CC, MI, MSQ.')
        registrationOptions.add_option('--antsImageMetricOpt', default=32,
            type='int', dest='antsImageMetricOpt',
            help='Parameter of ANTS i2i metric. Makes a sense only when provided metric can be customized.')
        registrationOptions.add_option('--useRigidAffine', default=False,
            dest='useRigidAffine', action='store_const', const=True,
            help='Use rigid affine transformation.')

        parser.add_option_group(registrationOptions)
        parser.add_option_group(generalOptions)

        return parser


if __name__ == '__main__':
    options, args = sequential_alignment.parseArgs()
    d = sequential_alignment(options, args)
    d.launch()
