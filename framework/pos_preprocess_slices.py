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

import os, sys
from optparse import OptionParser, OptionGroup
import copy

from pos_common import flatten
from pos_wrapper_skel import output_volume_workflow
from pos_input_data_preprocessor import worksheet_manager

import pos_parameters
import pos_wrappers
import pos_deformable_wrappers


CONST_VOLUME_ORIENTATION_CODE="RAS"
CONST_MEDIAN_FILTER_RADIUS=10
CONST_MASKING_THRESHOLD=93.7254902
CONST_DEFAULT_GRAVITY="NorthWest" #XXX:TODO: Only NorthWest and Center are allowed.
CONST_BACKGROUND_VALUE = [0, 255]
CONST_MASK_TYPE = "rbg_masked"


class input_image_padding(pos_wrappers.generic_wrapper):
    """
#   convert {temp_mask} {threshold} -alpha off -filter Point {resize} {temp_mask}
    """

    _template = """
    convert {input_image} {background} {gravity} {extent} \
    {rotation} {horizontal_flip} {vertical_flip} \
    \( +clone -write {full_size_output} \
         {color_channel} {median} -separate \
        -write {temp_mask} +delete \); \
    convert {temp_mask} {threshold} -alpha off {temp_mask}"""

    _parameters = {
        'input_image': pos_parameters.filename_parameter('input_image', None),
        'background': pos_parameters.string_parameter('background', "white", "-{_name} {_value}"),
        'gravity': pos_parameters.string_parameter('gravity', "NorthWest", "-{_name} {_value}"),
        'extent': pos_parameters.vector_parameter('extent', None, "-{_name} {_list}"),
        'horizontal_flip': pos_parameters.boolean_parameter('flip', None, "-{_name}"),
        'vertical_flip': pos_parameters.boolean_parameter('flop', None, "-{_name}"),
        'rotation': pos_parameters.value_parameter('rotate', None, "-distort ScaleRotateTranslate {_value}"),
        'full_size_output': pos_parameters.string_parameter('full_size_output', None, "{_value}"),
        'median': pos_parameters.value_parameter('median', 5, '-{_name} {_value}'),
        'color_channel': pos_parameters.string_parameter('channel', "R", '-{_name} {_value}'),
        'temp_mask': pos_parameters.string_parameter('temp_mask', None, "{_value}"),
        'threshold': pos_parameters.value_parameter('threshold', None, '-{_name} {_value}%'),
        'output_downsampled': pos_parameters.value_parameter('output_downsampled', None, "{_value}")
    }


class convert_to_niftiis(pos_wrappers.generic_wrapper):
    """
    """

    _template = """c2d -verbose -mcs {input_rgb} \
    -foreach  {origin} {spacing} {type} -endfor -omc 3 {output_rgb_full} \
    -foreach {resample} {type} -endfor -omc 3 {output_rgb_small};
    c2d -verbose {input_mask} {interpolation} {origin} {spacing} {type} {resample} -replace 0 1 255 0 -o {output_mask} ;\
    rm {input_rgb} {input_mask}"""

    _parameters = {
        'input_rgb': pos_parameters.filename_parameter('input_rgb', None),
        'resample': pos_parameters.value_parameter('resample', None, '-{_name} {_value}%'),
        'origin': pos_parameters.vector_parameter('origin', [0,0], '-{_name} {_list}mm'),
        'spacing': pos_parameters.vector_parameter('spacing', [1,1], '-{_name} {_list}mm'),
        'type': pos_parameters.string_parameter('type', 'uchar', '-{_name} {_value}'),
        'output_rgb_full': pos_parameters.filename_parameter('output_rgb_full', None),
        'output_rgb_small': pos_parameters.filename_parameter('output_rgb_small', None),
        'input_mask': pos_parameters.filename_parameter('input_mask', None),
        'interpolation': pos_parameters.string_parameter('interpolation', 'NearestNeighbor', '-{_name} {_value}'),
        'output_mask': pos_parameters.filename_parameter('output_mask', None)
    }


class remask_wrapper(pos_wrappers.generic_wrapper):
    """
    the input volume is assumed to be a rgb volume!
    pos_slice_volume.py -i masked.nii.gz -o "xxxx%04d.nii.gz" -s 2
    """

    _template = """c3d -verbose \
    {mask_file} -popas mask -clear -mcs {input_volume} \
        -foreach -push mask -times {replace} -type uchar -endfor \
    -omc 3 {masked_volume} """

    _parameters = {
        'input_volume': pos_parameters.filename_parameter('input_volume', None),
        'mask_file': pos_parameters.filename_parameter('mask_file', None),
        'masked_volume': pos_parameters.filename_parameter('masked_volume', None),
        'replace': pos_parameters.list_parameter('replace', None, '-{_name} {_list}'),
    }


class volume_reconstruction_preprocessor(output_volume_workflow):
    """
    A class for preprocessing the slices images before the volume
    reconstruction process.

    Ok. It's a bit complicated set of images and consecutive processing steps.
    This calls for a few words of explanation:

        1. raw_src - the source of this image is a raw image prvided by the
        data provider (think: a biologist).  it is expected to be quite a large
        image (few thousand times few thousand pixels).

        2. raw_png - an 'raw_src' image after processing it with ImageMagick.
        In fact, this set of images is to be deleted after the `raw_image` set
        is generated. The `raw_png` capitalizes on all the features provided by
        the ImageMagick and which are not available or difficult to achieve
        with ITK or Convert3d.

        3. `source_images_fullsize` the SOURCE images which is used in the
        pipeline. Is serves as a basis for all the further steps of processing.

        4. `source_images_downsampled` downsampled version of the SOURCE images
        files

    """

    _f = {
        'raw_src': pos_parameters.filename('raw_src', work_dir='00_raw_images', str_template='{idx:04d}.png'),
        'raw_png_full': pos_parameters.filename('raw_png_full', work_dir='01_raw_temp', str_template='_temp_img_{idx:04d}.png'),
        'raw_png_masks': pos_parameters.filename('raw_png_masks', work_dir='01_raw_temp', str_template='_temp_mask_{idx:04d}.png'),
        'source_images_fullsize': pos_parameters.filename('source_images_fullsize', work_dir='02_source_images', str_template='fullsize_{idx:04d}.nii.gz'),
        'source_images_downsampled': pos_parameters.filename('source_images_downsampled', work_dir='02_source_images', str_template='downsampled_{idx:04d}.nii.gz'),
        'source_images_downsampled_fmask': pos_parameters.filename('source_images_downsampled_fmask', work_dir='02_source_images', str_template='downsampled_%04d.nii.gz'),
        'source_masks': pos_parameters.filename('source_masks', work_dir='03_source_masks', str_template='{idx:04d}.nii.gz'),
        'source_masks_fmask': pos_parameters.filename('source_masks_fmask', work_dir='03_source_masks', str_template='%04d.nii.gz'),
        'source_stacks': pos_parameters.filename('source_stacks', work_dir='04_source_stacks', str_template="{stack_name}_stack.nii.gz"),
        'seq_input_img': pos_parameters.filename('seq_input_img', work_dir='10_seqential_input_images', str_template="%04d.nii.gz"),
        'seq_input_mask': pos_parameters.filename('seq_input_mask', work_dir='11_seqential_input_masks', str_template="%04d.nii.gz"),
        'seq_slice_to_slice': pos_parameters.filename('seq_slice_to_slice', work_dir='12_slice_to_slice', str_template="%04d.nii.gz"),
        'seq_slice_to_slice_mask': pos_parameters.filename('seq_slice_to_slice_mask', work_dir='13_slice_to_slice_masks', str_template="%04d.nii.gz"),
        'seq_slice_to_ref': pos_parameters.filename('seq_slice_to_ref', work_dir='14_slice_to_ref', str_template="%04d.nii.gz"),
        'seq_slice_to_ref_mask': pos_parameters.filename('seq_slice_to_ref_mask', work_dir='15_slice_to_ref_masks', str_template="%04d.nii.gz")
    }

    slicing_planes_settings = {
        "saggital" : {'permutation': [2,0,1], 'flip': [0, 0, 0], 'axis': 0},
        "coronal"  : {'permutation': [0,2,1], 'flip': [0, 0, 0], 'axis': 1},
        "axial"    : {'permutation': [0,1,2], 'flip': [0, 1, 0], 'axis': 2}}

    def launch(self):
        # Load the image settings chart and process and extract all the
        # required metadata.

        self.w = worksheet_manager(self.options.inputWorkbook,
            self.options.outputWorkbook,
            images_dir = self.options.inputImagesDir)
        self.w.process()

        self.__masking_threshold = CONST_MASKING_THRESHOLD
        self.__median_filter_radius = CONST_MEDIAN_FILTER_RADIUS
        self.__stack_spacing = self.w._slice_thickness
        self.__slicing_plane = self.w._slicing_plane
        self.__background = CONST_BACKGROUND_VALUE

#       self._from_source_to_masks()
#       self._to_niftis()
        self._stack_images_and_masks()
        self._remask()

        self._prepare_input_slices()

    def _from_source_to_masks(self):
        """
        Process the very source image into the rgb niftii image. Then create
        downsampled rgb nitii images and downsampled niftii masks.

        The canvas of the raw image is extended, rotaded and flipped if required.
        """

        commands = []
        for index, image in self.w._images.items():

            # Do the replacement if required:
            if image.replacement_index is not None:
                input_index = image.replacement_index
            else:
                input_index = index

            #ox = image.process_resolution * abs(image.image_size[0] - image.padded_size[0])/2
            #oy = image.process_resolution * abs(image.image_size[1] - image.padded_size[1])/2
            command = input_image_padding(
                input_image = os.path.join(self.options.inputImagesDir, self.w._images[input_index].image_name),
                extent = image.padded_size,
                rotation = image.rotation,
                horizontal_flip = [None,True][int(image.horizontal_flip)],
                vertical_flip = [None,True][int(image.vertical_flip)],
                temp_mask = self.f['raw_png_masks'](idx=index),
                full_size_output = self.f['raw_png_full'](idx=index),
                median = self.__median_filter_radius,
                gravity = CONST_DEFAULT_GRAVITY,
                threshold = self.__masking_threshold)
            # print command
            commands.append(copy.copy(command))
        self.execute(commands)

    def _to_niftis(self):
        """
        """
        sampling = self.w._images.values()[0].get_downsampling()

        commands = []
        for index, image in self.w._images.items():

            command = convert_to_niftiis(
                input_rgb = self.f['raw_png_full'](idx=index),
                resample = sampling,
                origin = [0, 0],
                spacing = [image.process_resolution]*2,
                output_rgb_small = self.f['source_images_downsampled'](idx=index),
                output_rgb_full = self.f['source_images_fullsize'](idx=index),
                input_mask = self.f['raw_png_masks'](idx=index),
                output_mask = self.f['source_masks'](idx=index))
            commands.append(copy.copy(command))

        self.execute(commands)

    def _stack_images_and_masks(self):
        """
        """

        command = self._get_stacking_wrapper(
            input_mask = self.f['source_masks_fmask'](),
            output_filename = self.f['source_stacks'](stack_name="mask"))
        command()

        command = self._get_stacking_wrapper(
            input_mask = self.f['source_images_downsampled_fmask'](),
            output_filename = self.f['source_stacks'](stack_name="rgb"))
        command()

        # Create the slice-to-slice mask
        # Create the slice-to-reference mask

        if self.options.useSliceToSliceMask:
            command = pos_wrappers.copy_wrapper(
                source = [self.f['source_stacks'](stack_name="mask")],
                target = self.f['source_stacks'](stack_name="slice_to_slice_mask"))
            command()

        if self.options.useSliceToReferenceMask:
            command = pos_wrappers.copy_wrapper(
                source = [self.f['source_stacks'](stack_name="mask")],
                target = self.f['source_stacks'](stack_name="slice_to_reference_mask"))
            command()

    def _get_stacking_wrapper(self, input_mask, output_filename):

        first_slice, last_slice = self._get_extreme_slices()
        output_stack_spacing = self._get_output_slice_spacing()

        stack_permutation_order = \
                self.slicing_planes_settings[self.__slicing_plane]['permutation']
        stack_flip_axes = \
            self.slicing_planes_settings[self.__slicing_plane]['flip']

        command = pos_wrappers.stack_and_reorient_wrapper(
            stack_mask = input_mask,
            slice_start = first_slice,
            slice_end = last_slice,
            slice_step = 1,
            output_volume_fn = output_filename,
            permutation_order = stack_permutation_order,
            flip_axes = stack_flip_axes,
            orientation_code = CONST_VOLUME_ORIENTATION_CODE,
            spacing = output_stack_spacing,
            origin = [0,0,0])
        return copy.copy(command)

    def _get_extreme_slices(self):
        first_slice = min(map(lambda x: x.image_index, self.w._images.values()))
        last_slice = max(map(lambda x: x.image_index, self.w._images.values()))

        return first_slice, last_slice

    def _get_output_slice_spacing(self):
        first_slice, last_slice = self._get_extreme_slices()
        in_plane_spacing = self.w._images[first_slice].process_resolution
        output_stack_spacing = [in_plane_spacing]*3
        output_stack_spacing[self.slicing_planes_settings[self.__slicing_plane]['axis']] = self.__stack_spacing

        return output_stack_spacing

    def _remask(self):
        """
        """
        command = remask_wrapper(
            mask_file = self.f['source_stacks'](stack_name="mask"), \
            input_volume = self.f['source_stacks'](stack_name="rgb"), \
            replace = self.__background, \
            masked_volume = self.f['source_stacks'](stack_name="rbg_masked"))
        command()

        if self.options.useSliceToSliceMask:
            command = remask_wrapper(
                mask_file = self.f['source_stacks'](stack_name="slice_to_slice_mask"), \
                input_volume = self.f['source_stacks'](stack_name="rgb"), \
                replace = self.__background, \
                masked_volume = self.f['source_stacks'](stack_name="rbg_slice_to_slice_masked"))
            command()

        if self.options.useSliceToReferenceMask:
            command = remask_wrapper(
                mask_file = self.f['source_stacks'](stack_name="slice_to_reference_mask"), \
                input_volume = self.f['source_stacks'](stack_name="rgb"), \
                replace = self.__background, \
                masked_volume = self.f['source_stacks'](stack_name="rbg_slice_to_reference_masked"))
            command()

    def _prepare_input_slices(self):
        """
        """
        first_slice, last_slice = self._get_extreme_slices()

        command = pos_deformable_wrappers.preprocess_slice_volume(
            input_image = self.f['source_stacks'](stack_name=CONST_MASK_TYPE),\
            output_naming = self.f['seq_input_img'](),\
            slicing_plane = self.slicing_planes_settings[self.__slicing_plane]['axis'],\
            start_slice = first_slice,
            end_slice = last_slice,
            shift_indexes = 1)
        command()

        command = pos_deformable_wrappers.preprocess_slice_volume(
            input_image = self.f['source_stacks'](stack_name='mask'),\
            output_naming = self.f['seq_input_mask'](),\
            slicing_plane = self.slicing_planes_settings[self.__slicing_plane]['axis'],\
            start_slice = first_slice,
            end_slice = last_slice,
            shift_indexes = 1)
        command()

        # -------------------------------------------------------------------

        command = pos_deformable_wrappers.preprocess_slice_volume(
            input_image = self.f['source_stacks'](stack_name='rbg_slice_to_slice_masked'),\
            output_naming = self.f['seq_slice_to_slice'](),\
            slicing_plane = self.slicing_planes_settings[self.__slicing_plane]['axis'],\
            start_slice = first_slice,
            end_slice = last_slice,
            shift_indexes = 1)
        command()

        command = pos_deformable_wrappers.preprocess_slice_volume(
            input_image = self.f['source_stacks'](stack_name='slice_to_slice_mask'),\
            output_naming = self.f['seq_slice_to_slice_mask'](),\
            slicing_plane = self.slicing_planes_settings[self.__slicing_plane]['axis'],\
            start_slice = first_slice,
            end_slice = last_slice,
            shift_indexes = 1)
        command()

        # -------------------------------------------------------------------

        command = pos_deformable_wrappers.preprocess_slice_volume(
            input_image = self.f['source_stacks'](stack_name='rbg_slice_to_reference_masked'),\
            output_naming = self.f['seq_slice_to_ref'](),\
            slicing_plane = self.slicing_planes_settings[self.__slicing_plane]['axis'],\
            start_slice = first_slice,
            end_slice = last_slice,
            shift_indexes = 1)
        command()

        command = pos_deformable_wrappers.preprocess_slice_volume(
            input_image = self.f['source_stacks'](stack_name='slice_to_reference_mask'),\
            output_naming = self.f['seq_slice_to_ref_mask'](),\
            slicing_plane = self.slicing_planes_settings[self.__slicing_plane]['axis'],\
            start_slice = first_slice,
            end_slice = last_slice,
            shift_indexes = 1)
        command()

    @classmethod
    def _getCommandLineParser(cls):
        """
        #TODO: Consider adding additional stacks.
        """
        parser = output_volume_workflow._getCommandLineParser()

        obligatory_options = OptionGroup(parser, 'Obligatory pipeline options.')
        obligatory_options.add_option('--inputImagesDir', default=None,
            type='str', dest='inputImagesDir',
            help='The directory from which the input images will be read.')
        obligatory_options.add_option('--inputWorkbook', default=None,
            type='str', dest='inputWorkbook',
            help='Input workbook.')
        obligatory_options.add_option('--outputWorkbook', default=None,
            type='str', dest='outputWorkbook',
            help='Output workbook.')

        stacking_options = OptionGroup(parser, 'Images staking options')

        stacking_options.add_option('--useSliceToSliceMask', default=False,
            dest='useSliceToSliceMask', action='store_const', const=True,
            help='Generate and use slice to slice mask.')
        stacking_options.add_option('--useSliceToReferenceMask', default=False,
            dest='useSliceToReferenceMask', action='store_const', const=True,
            help='Generate and use slice to reference mask.')

        parser.add_option_group(obligatory_options)
        parser.add_option_group(stacking_options)

        return parser


if __name__ == '__main__':
    options, args = volume_reconstruction_preprocessor.parseArgs()
    options.workDir = "/home/pmajka/Downloads/test/"
    se = volume_reconstruction_preprocessor(options, args)
    se.launch()
