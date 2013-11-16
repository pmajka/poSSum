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

        #TODO: Provide input slice path and filename template a as comman line input
        # parameter
        # Define the input slice range
        # XXX: Input slice range is assumed to be: <first_slice> <last_slice>
        # TODO: Check validity of the input slices.
        self.options.slice_range = \
            range(self.options.sliceRange[0], self.options.sliceRange[1]+1)

    def _overrideDefaults(self):
        #TODO: Check if given directory exists! Validate of all the input file
        # exists.
        #TODO: This should be moved to the override_paths section of the script.
        self.f['raw_image'].override_dir = self.options.inputImageDir
        #TODO add is_file in pos_common module

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Prepare the input slices
        self._generate_source_slices()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

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
            print command
            commands.append(copy.deepcopy(command))
        self.execute(commands)

    @classmethod
    def _getCommandLineParser(cls):
        parser = output_volume_workflow._getCommandLineParser()

        parser.add_option('--sliceRange', default=None,
            type='int', dest='sliceRange', nargs = 2,
            help='Slice range. Requires two integers. REQUIRED')
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

        # -----------------------------------------------------------
        return parser

if __name__ == '__main__':
    options, args = sequential_alignment.parseArgs()
    d = sequential_alignment(options, args)
    d.launch()
