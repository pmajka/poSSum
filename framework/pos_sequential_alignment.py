#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys
from optparse import OptionParser, OptionGroup
import copy

import pos_wrappers
import pos_parameters
from pos_wrapper_skel import output_volume_workflow


class sequential_alignment(output_volume_workflow):
    """
    Input images: three channel rgb images (uchar per channel) in niftii format. That's it.
    """

    _f = {
        'raw_image' : pos_parameters.filename('raw_image', work_dir = '00_override_this', str_template = '{idx:04d}.nii.gz'),
        'src_gray' : pos_parameters.filename('src_gray', work_dir = '00_source_gray', str_template='{idx:04d}.nii.gz'),
        'src_color' : pos_parameters.filename('src_color', work_dir = '01_source_color', str_template='{idx:04d}.nii.gz'),
        'part_naming' : pos_parameters.filename('part_naming', work_dir = '02_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_Affine'),
        'part_transf' : pos_parameters.filename('part_transf', work_dir = '02_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_Affine.txt'),
        'comp_transf' : pos_parameters.filename('comp_transf', work_dir = '02_transforms', str_template='ct_m{mIdx:04d}_f{fIdx:04d}_Affine.txt'),
        'resliced_gray' : pos_parameters.filename('resliced_gray', work_dir = '04_gray_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_color' : pos_parameters.filename('resliced_color', work_dir = '05_color_resliced', str_template='{idx:04d}.nii.gz'),
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
        # processed.
        self.options.slice_range = \
            range(self.options.sliceRange[0], self.options.sliceRange[1] + 1)

    def _overrideDefaults(self):
        self.f['raw_image'].override_dir = self.options.inputImageDir

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Before launching the registration process check, if the intput
        # directory and all the input images exist.
        self._inspect_input_images()

        # Prepare the input slices
        self._generate_source_slices()

        # Generate transforms
        self._calculate_transforms()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _inspect_input_images(self):
        """
        """
        # Verify if all the files are availabe:
        # All images have to be ailable. If the case is different, the workflow
        # will not proceed.
        for slice_index in self.options.slice_range:
            slice_filename = self.f['raw_image'](idx=slice_index)

            self._logger.debug("Checking for image: %s.", slice_filename)
            if not os.path.isfile(slice_filename):
                self._logger.error("File does not exist: %s. Exiting",
                                   slice_filename)
                sys.exit(1)

    def _generate_source_slices(self):
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
            self.f['comp_transf'](mIdx=m_slice, fIdx=r_slice)

        command = pos_wrappers.ants_compose_multi_transform(
            dimension = 2,
            output_image = composite_transform_filename,
            reference_image = self.f['src_gray'](idx=r_slice),
            deformable_list = [],
            affine_list = partial_transformations)

        return copy.deepcopy(command)

    def _reslice(self):
        for slice_index in self.options.slice_range:
            self._resliceGrayscale(slice_index)
            self._resliceColor(slice_index)

    def _resliceGrayscale(self, sliceNumber):
        moving_image = self.f['src_gray'](idx=sliceNumber)
        resliced_image = self.f['resliced_gray'](idx=sliceNumber)
        reference_image = self.f['src_gray'](idx=self.options.slice_range[2])
        transformation_file = self.f['comp_transf'](mIdx=sliceNumber,fIdx=self.options.slice_range[2])

        #cmdDict['region'] = self._getOutputVolumeROIstr(strType = 'c2d')
        #command = COMMAND_WARP_GRAYSCALE_SLICE % cmdDict
        #executeSystem(command)


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

        return parser

if __name__ == '__main__':
    options, args = sequential_alignment.parseArgs()
    d = sequential_alignment(options, args)
    d.launch()
