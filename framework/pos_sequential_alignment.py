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
        'part_transf' : pos_parameters.filename('part_transf', work_dir = '02_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_Affine'),
        'comp_transf' : pos_parameters.filename('comp_transf', work_dir = '02_transforms', str_template='ct_m{mIdx:04d}_f{fIdx:04d}_Affine'),
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

        self.options.slice_range = \
            range(self.options.sliceRange[0], self.options.sliceRange[1]+1)


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
        Iterate over all the input filenames and verify if they exeist!
        #TODO: Verify if the input directory exists
        #TODO: Validate if all the input file exist.
        #TODO add is_file in pos_common module
        """
        pass

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
        # The two loops below have to stay separated

        # Calculate partial transforms;
        for moving_slice_index in self.options.slice_range:
            self._calculate_individual_partial_transform(moving_slice_index)

        # Calculate composite transforms
        for moving_slice_index in self.options.slice_range:
            self._calculate_individual_composed_transform(moving_slice_index)

    def _get_partial_transform(self, moving_slice_index):
        i = moving_slice_index
        s, e, r = tuple(self.options.sliceRange)

        ret_dict= []
        if i==r:
            j=i
            ret_dict.append((i, j))
        if i > r:
            j = i-1
            ret_dict.append((i, j))
        if i < r:
            j = i+1
            ret_dict.append((i, j))
        return ret_dict

    def _calculate_individual_partial_transform(self, moving_slice_index):
        #XXX TODO: Here's the place where you stopped!
        transforms_chain = self._get_partial_transform(moving_slice_index)
        moving_slice_index, fixed_slice_index = transforms_chain[0]

        similarity_metric = self.options.antsImageMetric
        metric_parameter = self.options.antsImageMetricOpt
        affine_iterations = [10000,10000,10000,10000,10000]
        output_naming = self.f['part_transf'](mIdx=moving_slice_index, fIdx=fixed_slice_index)
        use_rigid_transformation = self.options.useRigidAffine
        affine_metric_type = self.options.antsImageMetric

        metrics  = []
        metric = pos_wrappers.ants_intensity_meric(
                    fixed_image  = self.f['src_gray'](idx=fixed_slice_index),
                    moving_image = self.f['src_gray'](idx=moving_slice_index),
                    metric = similarity_metric,
                    weight = 1.0,
                    parameter = metric_parameter)
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

        print registration
        #commands.append(copy.deepcopy(registration))

    def _calculate_individual_composed_transform(self, moving_slice_index):
        pass

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
