#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys
from optparse import OptionParser, OptionGroup
import copy

from pos_wrapper_skel
import pos_wrappers
import pos_parameters

class sequential_alignment(pos_wrapper_skel.output_volume_workflow):
    """
    Input images: three channel rgb images (uchar per channel) in niftii format. That's it.
    """

    _f = {
        'raw_image' : pos_parameters.filename('raw_image', work_dir = None, str_template = '{idx:04d}.nii.gz'),
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

        #TODO: Provide input slice path and filename template a as comman line input
        # parameter

        #TODO: Update the 'raw_image' workdir

        # Define the input slice range
        # XXX: Input slice range is assumed to be: <first_slice> <last_slice>
        self.options.slice_range = \
            range(self.options.sliceRange[0], self.options.sliceRange[1]+1)

        # Override default raw_images directory (which, in fact, is just a
        # stub) with the directory with actual images.
        self.f['raw_images'].override_dir = self.options.inputVolume

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()


        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _generate_source_slices(self):

        for slice_number in self.options.slice_range:
            pos_wrappers.alignment_preprocessor_wrapper(
               intput_image = self.f['raw_image'](idx=slice_number),
               grayscele_output_image = self.f['src_gray'](idx=slice_number),
               color_output_image = self.f['src_color'](idx=slice_number),
               registration_roi = self.options.registrationROI,
               registration_resize = self.options.registrationResize,
               registration_color = self.options.registrationColor,
               median_filter_radius = self.options.medianFilterRadius,
               invert_grayscale = self.options.invertGrayscale,
               invert_multichannel = self.options.invertMultichannel)

    @classmethod
    def _getCommandLineParser(cls):
        parser = output_volume_workflow._getCommandLineParser()

        parser.add_option('--sliceRange', default=None,
            type='int', dest='sliceRange', nargs = 2,
            help='Slice range. Requires two integers.')
        parser.add_option('--inputImageDir', default=None,
            type='str', dest='inputImageDir',
            help='

        parser.add_option('--registrationROI', dest='registrationROI',
            default=None, type='int', nargs=4,
            help='ROI of the input image used for registration (ox, oy, sx, sy).')
        parser.add_option('--registrationResize', dest='registrationResize',
            default=None, type='float',
            help='Scaling factor for the source image used for registration. Float between 0 and 1.')
        parser.add_option('--medianFilterRadius', dest='medianFilterRadius',
            default=None, type='int', nargs=2,
            help='Median filter radius in voxels e.g. 2 2')
        parser.add_option('--invertGrayscale', dest='invertGrayscale',
            default=False, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
        parser.add_option('--invertMultichannel', dest='invertMultichannel',
            default=False, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')

        # -----------------------------------------------------------
        return parser

    def launch(self):
        pass

if __name__ == '__main__':
    options, args = sequential_alignment.parseArgs()
    d = sequential_alignment(options, args)
    d.launch()
