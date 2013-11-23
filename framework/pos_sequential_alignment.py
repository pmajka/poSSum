#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys
from optparse import OptionParser, OptionGroup
import copy

import pos_wrappers
import pos_parameters
from pos_wrapper_skel import output_volume_workflow

class command_warp_rgb_slice(pos_wrappers.generic_wrapper):
    """
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
    # TODO: Allow for overriding the output volumes filenames
    # TODO: Generate output filenames based on the provided parameters

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

    def __init__(self, options, args):
        super(self.__class__, self).__init__(options, args)

    def _initializeOptions(self):
        super(self.__class__, self)._initializeOptions()

        # Define slices' range. All slices within given range will be
        # processed. Make sure that all images are available.
        self.options.slice_range = \
            range(self.options.sliceRange[0], self.options.sliceRange[1] + 1)

    def _overrideDefaults(self):
        self.f['raw_image'].override_dir = self.options.inputImageDir

        #TODO: Override output transformation directory if required
        #TODO: Override the output volumes path if required by the command line parameters
        # whole filename, not only path or only filename.

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Before launching the registration process check, if the intput
        # directory and all the input images exist.
        self._inspect_input_images()

        # Prepare the input slices
        # Source slices preparation is not performed when it is switched off by
        # the command line parameters. In such case just report that fact and
        # then return.
        if self.options.skipSourceSlicesGeneration is not True:
            self._generate_source_slices()

        # Generate transforms
        if self.options.skipTransformations is not True:
            self._calculate_transforms()

        # Reslice all the images:
        if self.options.skipReslice is not True:
            self._reslice()

        # Stack both grayscale as well as the rgb slices:
        if self.options.skipOutputVolumes is not True:
            self.stack_output_volumes()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _inspect_input_images(self):
        """
        Verify if all the files are availabe: All images have to be ailable. If
        the case is different, the workflow will not proceed.
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

        # The array collecting all the partial commands.
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

        self.execute(commands)

    def _calculate_transforms(self):
        """
        """
        # Calculate partial transforms - get partial transformation chain;
        partial_transformation_pairs = \
            map(lambda idx: self._get_slice_pair(idx),
                            self.options.slice_range)

        commands = map(lambda x: self._get_partial_transform(*x),
                                 partial_transformation_pairs)
        self.execute(commands)

        # Calculate composite transforms
        commands = []
        for moving_slice_index in self.options.slice_range:
            commands.append(self._calculate_individual_composed_transform(moving_slice_index))
        self.execute(commands)

    def _get_slice_pair(self, moving_slice_index):
        i = moving_slice_index
        s, e, r = tuple(self.options.sliceRange)

        if i == r:
            j = i
            retval = (i, j)
        if i > r:
            j = i - 1
            retval = (i, j)
        if i < r:
            j = i + 1
            retval = (i, j)
        return retval

    def _get_partial_transform(self, moving_slice_index, fixed_slice_index):
        """
        """
        similarity_metric = self.options.antsImageMetric
        metric_parameter = self.options.antsImageMetricOpt
        affine_iterations = [10000, 10000, 10000, 10000, 10000]
        output_naming = self.f['part_naming'](mIdx=moving_slice_index,
                                              fIdx=fixed_slice_index)
        use_rigid_transformation = self.options.useRigidAffine
        affine_metric_type = self.options.antsImageMetric

        metrics = []
        metric = pos_wrappers.ants_intensity_meric(
            fixed_image=self.f['src_gray'](idx=fixed_slice_index),
            moving_image=self.f['src_gray'](idx=moving_slice_index),
            metric=similarity_metric,
            weight=1.0,
            parameter=metric_parameter)
        metrics.append(copy.deepcopy(metric))

        registration = pos_wrappers.ants_registration(
            dimension = 2,
            outputNaming = output_naming,
            iterations = [0],
            affineIterations = affine_iterations,
            continueAffine = None,
            rigidAffine = use_rigid_transformation,
            imageMetrics = metrics,
            histogramMatching = True,
            miOption = [metric_parameter, 16000],
            affineMetricType = affine_metric_type)

        return copy.deepcopy(registration)

    def _get_transformation_chain(self, moving_slice_index):
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
        print moving_slice_index, retDict
        return retDict

    def _calculate_individual_composed_transform(self, moving_slice_index):
        """
        """
        transformation_chain = \
            self._get_transformation_chain(moving_slice_index)

        # Initialize the partial transforms array and then collect all partial
        # transformations constituting given composite transformation.
        partial_transformations = []
        for (m_slice, r_slice) in transformation_chain:
            partial_transformations.append(
                self.f['part_transf'](mIdx=m_slice, fIdx=r_slice))

        composite_transform_filename = \
            self.f['comp_transf'](mIdx=moving_slice_index, fIdx=r_slice)

        command = pos_wrappers.ants_compose_multi_transform(
            dimension = 2,
            output_image = composite_transform_filename,
            deformable_list = [],
            affine_list = partial_transformations)
           #reference_image = self.f['src_gray'](idx=r_slice),

        return copy.deepcopy(command)

    def _reslice(self):
        commands = []
        for slice_index in self.options.slice_range:
            commands.append(self._resliceGrayscale(slice_index))
        self.execute(commands)

        commands = []
        for slice_index in self.options.slice_range:
            commands.append(self._resliceColor(slice_index))
        self.execute(commands)

    def _resliceGrayscale(self, sliceNumber):
        moving_image_filename = self.f['src_gray'](idx=sliceNumber)
        resliced_image_filename = self.f['resliced_gray'](idx=sliceNumber)
        reference_image_filename = self.f['src_gray'](
            idx=self.options.slice_range[2])
        transformation_file = self.f['comp_transf'](
            mIdx=sliceNumber, fIdx=self.options.sliceRange[2])

        if self.options.outputVolumeROI:
            region_origin_roi = self.options.outputVolumeROI[0:2]
            region_size_roi = self.options.outputVolumeROI[2:4]
        else:
            region_origin_roi = None
            region_size_roi = None

        command = command_warp_grayscale_image(
            reference_image = reference_image_filename,
            moving_image = moving_image_filename,
            transformation = transformation_file,
            output_image = resliced_image_filename,
            region_origin = region_origin_roi,
            region_size = region_size_roi)
        return copy.deepcopy(command)

    def _resliceColor(self, sliceNumber):
        moving_image_filename = self.f['src_color'](idx=sliceNumber)
        resliced_image_filename = self.f['resliced_color'](idx=sliceNumber)
        reference_image_filename = self.f['src_gray'](
            idx=self.options.slice_range[2])
        transformation_file = self.f['comp_transf'](
            mIdx=sliceNumber, fIdx=self.options.sliceRange[2])

        if self.options.outputVolumeROI:
            region_origin_roi = self.options.outputVolumeROI[0:2]
            region_size_roi = self.options.outputVolumeROI[2:4]
        else:
            region_origin_roi = None
            region_size_roi = None

        command = command_warp_rgb_slice(
            reference_image = reference_image_filename,
            moving_image = moving_image_filename,
            transformation = transformation_file,
            output_image = resliced_image_filename,
            region_origin = region_origin_roi,
            region_size = region_size_roi,
            inversion_flag = self.options.invertMultichannel)
        return copy.deepcopy(command)

    def _get_generic_stack_slice_wrapper(self, mask_type, ouput_filename_type):
        start, stop, reference = self.options.sliceRange
        output_filename = self.f[ouput_filename_type](fname='output_volume')

        command = pos_wrappers.stack_and_reorient_wrapper(
            stack_mask = self.f[mask_type](),
            slice_start = start,
            slice_end = stop,
            slice_step = 1,
            output_volume_fn = output_filename,
            permutation_order = self.options.outputVolumePermutationOrder,
            orientation_code = self.options.outputVolumeOrientationCode,
            output_type = self.options.outputVolumeScalarType,
            spacing = self.options.outputVolumeSpacing,
            origin = self.options.outputVolumeOrigin,
            interpolation = self.options.setInterpolation,
            resample = self.options.outputVolumeResample)
        return copy.deepcopy(command)

    def stack_output_volumes(self):
        command = self._get_generic_stack_slice_wrapper('resliced_gray_mask','out_volume_gray')
        self.execute(command)

        command = self._get_generic_stack_slice_wrapper('resliced_color_mask','out_volume_color')
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

        parser.add_option('--registrationROI', dest='registrationROI',
            default=None, type='int', nargs=4,
            help='ROI of the input image used for registration (ox, oy, sx, sy).')
        parser.add_option('--registrationResize', dest='registrationResize',
            default=None, type='float',
            help='Scaling factor for the source image used for registration. Float between 0 and 1.')
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

        generalOptions = OptionGroup(parser, 'General workflow options')

        generalOptions.add_option('--outputVolumesDirectory', default=False,
                dest='outputVolumesDirectory', type="str",
                help='Directory to which registration results will be sored.')
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

        registrationOptions = OptionGroup(parser, 'Registration options')
        registrationOptions.add_option('--antsImageMetric', default='MI',
                            type='str', dest='antsImageMetric',
                            help='ANTS image to image metric. See ANTS documentation.')
        registrationOptions.add_option('--antsImageMetricOpt', default=32,
                            type='int', dest='antsImageMetricOpt',
                            help='Parameter of ANTS i2i metric.')
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
