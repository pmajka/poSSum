#!/usr/bin/python
# -*- coding: utf-8 -*-

import os,sys
import copy
import logging
import json
from optparse import OptionParser, OptionGroup

import pos_parameters
import pos_wrappers
from pos_wrapper_skel import generic_workflow

# A friendly reminder to use pep8 style guide
# e.g. http://www.python.org/dev/peps/pep-0008/#function-names

class reorient_permute_flip(pos_wrappers.generic_wrapper):
    _template = """PermuteFlipImageOrientationAxes {dimension} \
    {input_image} {output_image} {permutation} \
    {flip_axes} {flip_around_origin}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 3),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'permutation': pos_parameters.list_parameter('permutation', None),
        'flip_axes': pos_parameters.list_parameter('flip_axes', None),
        'flip_around_origin': pos_parameters.value_parameter('flip_around_origin', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class reorient_image(pos_wrappers.generic_wrapper):
    """
    A generic template for reorienting and resampling grayscale images.
    For dealing with multichannel images, see "reorient_multichannel_image".
    """
    _template = """c{dimension}d {input_image} \
       {orientation} {interpolation} \
       {origin} {resample} {spacing} {resamplemm} \
       {outputScalarType} \
       -o {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 3),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'orientation': pos_parameters.string_parameter('orient', None, "-{_name} {_value}"),
        'interpolation': pos_parameters.string_parameter('interpolation', None, "-{_name} {_value}"),
        'origin': pos_parameters.vector_parameter('origin', None, "-{_name} {_list}mm"),
        'spacing': pos_parameters.vector_parameter('spacing', None, "-{_name} {_list}mm"),
        'resample': pos_parameters.vector_parameter('resample', None, "-{_name} {_list}%"),
        'resamplemm': pos_parameters.vector_parameter('resample-mm',None, "-{_name} {_list}mm"),
        'outputScalarType': pos_parameters.string_parameter('type', None, "-{_name} {_value}"),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class reorient_multichannel_image(pos_wrappers.generic_wrapper):
    """
    A generic template for reorienting and resampling multichannel images.
    For dealing with grayscale images, see "reorient_image".
    """
    _template = """c{dimension}d -mcs {input_image} \
       -foreach {orientation} {interpolation} \
       {origin} {resample} {spacing} {resamplemm} \
       {outputScalarType} -endfor \
       -omc 3 {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 3),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'orientation': pos_parameters.string_parameter('orient', None, "-{_name} {_value}"),
        'interpolation': pos_parameters.string_parameter('interpolation', None, "-{_name} {_value}"),
        'origin': pos_parameters.vector_parameter('origin', None, "-{_name} {_list}mm"),
        'spacing': pos_parameters.vector_parameter('spacing', None, "-{_name} {_list}mm"),
        'resample': pos_parameters.vector_parameter('resample', None, "-{_name} {_list}%"),
        'resamplemm': pos_parameters.vector_parameter('resample-mm',None, "-{_name} {_list}mm"),
        'outputScalarType': pos_parameters.string_parameter('type', None, "-{_name} {_value}"),
        'output_image': pos_parameters.filename_parameter('output_image', None)
    }

    _io_pass = {
        'dimension': 'dimension',
        'output_image': 'input_image'
    }


class split_multichannel_image(pos_wrappers.generic_wrapper):
    _template = """c{dimension}d -mcs {input_image} {outputScalarType} \
        -oo {red_component} {green_component} {blue_component}s"""
    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 3),
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'outputScalarType': pos_parameters.string_parameter('type', None, "-{_name} {_value}"),
        'red_component': pos_parameters.filename_parameter('red_component', None),
        'green_component': pos_parameters.filename_parameter('green_component', None),
        'blue_component': pos_parameters.filename_parameter('blue_component', None)
    }


class merge_multichannel_image(pos_wrappers.generic_wrapper):
    _template = """c{dimension}d {red_component} {green_component} {blue_component} \
            {outputScalarType} -omc 3 {output_image}"""

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 3),
        'red_component': pos_parameters.filename_parameter('red_component', None),
        'green_component': pos_parameters.filename_parameter('green_component', None),
        'blue_component': pos_parameters.filename_parameter('blue_component', None),
        'output_image': pos_parameters.filename_parameter('output_image', None),
        'outputScalarType': pos_parameters.string_parameter('type', None, "-{_name} {_value}")
    }


class reorient_image_wrokflow(generic_workflow):
    """
    This class is suposed to be a swiss army knife for orienting volumes (even
    multichannel volumes) in spatial coordinates. The class was created as no
    tool has (or had? I don't konw what is the status at this very moment) all
    required functionalities regarding reorienting multichannel images and
    some tools had even difficulties in dealing with grayscale images.
    """

    _f = { \
        'src_rgb' : pos_parameters.filename('src_rgb', work_dir = '01_source_color', str_template = 'channel_{channel}.nii.gz'),
        'gray_perm' : pos_parameters.filename('gray_perm', work_dir = '02_gray_permuted', str_template = 'channel_{channel}.nii.gz'),
        'rgb_perm' : pos_parameters.filename('rgb_perm', work_dir = '03_rgb_permuted', str_template = 'channel_{channel}.nii.gz'),
        'rgb_oriented' : pos_parameters.filename('rgb_oriented', work_dir = '05_rgb_processed', str_template = 'channel_{channel}.nii.gz'),
        }

    def _validateOptions(self):
        # Handling situation when no input volume is provided
        assert self.options.inputFile, \
            self._logger.error("No input file provided. Please provide input file (-i) and try again.")

        assert self.options.outputFile, \
            self._logger.error("No output file provided. Please provie output file (-o) and try again.")

    def launch(self):
        """
        Launch the filter. If multicomponent image is provided approperiate
        workflow is used to process it. In case of grayscale image - grayscale
        workflow is used.
        """
        if self.options.multichannelImage:
            self._process_multichannel()
        else:
            self._process_grayscale()

        if self.options.cleanup:
            self._clean_up()

    def _process_grayscale(self):
        """
        Grayscale workflow is rather simple:

          1. Apply axes permutation and image flipping
          2. Alter image orientation and then set srs origin.
        """
        self._logger.debug("Entering grayscale workflow:")

        input_image = self.options.inputFile
        permuted_image = self.f['gray_perm'](channel='gray')
        output_image = self.options.outputFile

        # If the is no axes premutation or axis flipping in plans,
        # we use a bit better optimized version of the workflow which does only
        # resampling.
        # Otherwise, all the flipping, permutation, reorientation and
        # resampling are conducted which takes a bit more time.
        if self.options.permutation == [0,1,2] and \
           self.options.flipAxes    == [0,0,0]:
            self._logger.debug("No axes parmutation and flipping will be done.")
            self._reorient_and_set_origin(input_image, output_image)
        else:
            self._logger.debug("Performing full grayscale workflow.")
            self._permute_and_flip_axes(input_image, permuted_image)
            self._reorient_and_set_origin(permuted_image, output_image)

    def _process_multichannel(self):
        """
        Processing of multichannel images is more demanding due its...
        multichannel nature:

          1. Separate multichannel image into individual channels
          2. Apply axes permutation and image flipping to each channel
          3. Alter image orientation and then set srs origin of each channel
          4. Merge back individual channels into final multichannel image.
        """
        self._logger.debug("Entering multichannel workflow:")

        # The multichannel workflow executed in a two ways, simmilar to the
        # grayscale workflow the same way as in grayscale workflow - depending
        # on the provided permutation and flip axes settings.
        if self.options.permutation == [0,1,2] and \
           self.options.flipAxes    == [0,0,0]:

           self._logger.debug("No axes parmutation and flipping will be done.")
           self._reorient_and_set_origin(\
                self.options.inputFile,
                self.options.outputFile,
                multichannel=True)
        else:
            self._logger.debug("Performing full multichannel workflow.")

            # Split multichannel image into separate channels
            self._logger.debug("Splitting multichannel image into separate channels.")
            self._split_multichannel_image()

            # Process each individual image
            for channel in ['red', 'green', 'blue']:
                self._logger.debug("Processing %s channel." % channel)
                command = self._permute_and_flip_axes(\
                    self.f['src_rgb'](channel=channel),
                    self.f['rgb_perm'](channel=channel))

                command = self._reorient_and_set_origin(\
                    self.f['rgb_perm'](channel=channel),
                    self.f['rgb_oriented'](channel=channel),
                    multichannel=False)
                self._logger.debug("Done.")

            # Merge back channels into rgb volume
            self._logger.debug("Merging back individual grayscale images")
            self._logger.debug("into the output multichannel image.")
            self._merge_to_multichannel( \
                [self.f['rgb_oriented'](channel='red'),
                self.f['rgb_oriented'](channel='green'),
                self.f['rgb_oriented'](channel='blue')],
                self.options.outputFile)

    def _split_multichannel_image(self):
        """
        """
        command = split_multichannel_image(\
            dimension = self.options.antsDimension,
            input_image = self.options.inputFile,
            red_component = self.f['src_rgb'](channel='red'),
            green_component = self.f['src_rgb'](channel='blue'),
            blue_component = self.f['src_rgb'](channel='blue'))
        self.execute(command)

    def _merge_to_multichannel(self, input_channels, output_filename):
        """
        """
        command = merge_multichannel_image(\
            dimension = self.options.antsDimension,
            red_component   = input_channels[0],
            green_component = input_channels[1],
            blue_component  = input_channels[2],
            outputScalarType = self.options.outputVolumeScalarType,
            output_image = output_filename)
        self.execute(command)

    def _permute_and_flip_axes(self, input_filename, output_filename):
        """
        """
        command = reorient_permute_flip( \
            dimension = self.options.antsDimension,
            input_image = input_filename,
            output_image = output_filename,
            permutation = self.options.permutation,
            flip_axes = self.options.flipAxes,
            flip_around_origin = [0,1][self.options.flipAroundOrigin])
        self.execute(command)

    def _reorient_and_set_origin(self, input_filename, oputput_filename,\
                                 multichannel=False):
        """
        """
        if multichannel:
            reorient_class = reorient_multichannel_image
        else:
            reorient_class = reorient_image

        command = reorient_class(\
            dimension = self.options.antsDimension,
            orientation = self.options.orientationCode,
            input_image = input_filename,
            output_image = oputput_filename,
            origin = self.options.setOrigin,
            spacing = self.options.setSpacing,
            resample = self.options.resample,
            resamplemm = self.options.resamplemm,
            outputScalarType = self.options.outputVolumeScalarType)
        self.execute(command)

    @classmethod
    def _getCommandLineParser(cls):
        parser = generic_workflow._getCommandLineParser()

        parser.add_option('--outputFile', '-o', dest='outputFile', type='str',
                default=None, help='')
        parser.add_option('--inputFile', '-i', dest='inputFile', type='str',
                default=None, help='')
        parser.add_option('--orientationCode',  dest='orientationCode', type='str',
                default=None, help='')
        parser.add_option('--antsDimension', default=3, type=int, dest="antsDimension", help="")
        parser.add_option('--multichannelImage', default=False,
                dest='multichannelImage', action='store_const', const=True,
                help='Use multichannel image workflow.')

        parser.add_option('--interpolation', default=None,
                type='str', dest='interpolation',
                help='<NearestNeighbor|Linear|Cubic|Sinc|Gaussian>')
        parser.add_option('--resample', default=None,
                type='float', nargs=3, dest='resample',
                help='Resampling vector (%, floats ). Mutualy exclusive with --resample-mm option.')
        parser.add_option('--resample-mm', default=None,
                type='float', nargs=3, dest='resamplemm',
                help='Resample volume to specific resolution (in mm, provide float values). Mutualy exclusive with the resample option.')
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
                help='Set spacing values. Spacing has to be provided as three floats.')
        parser.add_option('--setOrigin', dest='setOrigin', type='float',
                nargs=3, default=None,
                help='Set origin values instead of voxel location. Origin has to be provided as three floats.')
        parser.add_option('--outputVolumeScalarType', default=None,
                type='str', dest='outputVolumeScalarType',
                help='Data type for output volume\'s voxels. Allowed values: char | uchar | short | ushort | int | uint | float | double')

        return parser

if __name__ == '__main__':
    options, args = reorient_image_wrokflow.parseArgs()
    d = reorient_image_wrokflow(options, args)
    d.launch()
