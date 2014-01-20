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


class input_image_padding(pos_wrappers.generic_wrapper):
    """
    """

    _template = """convert {input_image} {background} {gravity} {extent} \
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
    -foreach  {origin} {type} {native_spacing} -endfor -omc 3 {output_rgb_full} \
    -foreach {resample} {type} -endfor -omc 3 {output_rgb_small};
    c2d -verbose {input_mask} {interpolation} {origin} {resample} {type} \
    -replace 0 1 255 0 -popas second {output_rgb_small} -push second -copy-transform -o {output_mask}; \
    rm {input_rgb} {input_mask}"""

    _parameters = {
        'input_rgb': pos_parameters.filename_parameter('input_rgb', None),
        'origin': pos_parameters.vector_parameter('origin', [0,0], '-{_name} {_list}mm'),
        'type': pos_parameters.string_parameter('type', 'uchar', '-{_name} {_value}'),
        'native_spacing': pos_parameters.vector_parameter('spacing', None, '-{_name} {_list}mm'),
        'output_rgb_full': pos_parameters.filename_parameter('output_rgb_full', None),
        'resample': pos_parameters.value_parameter('resample', None, '-{_name} {_value}%'),
        'origin': pos_parameters.vector_parameter('origin', [0,0], '-{_name} {_list}mm'),
        'output_rgb_small': pos_parameters.filename_parameter('output_rgb_small', None),
        'input_mask': pos_parameters.filename_parameter('input_mask', None),
        'interpolation': pos_parameters.string_parameter('interpolation', 'NearestNeighbor', '-{_name} {_value}'),
        'output_mask': pos_parameters.filename_parameter('output_mask', None)
    }


class preprocess_reference(pos_wrappers.generic_wrapper):
    """
    """

    _template = """convert {input_image} \
        {resize} {background} {gravity} {extent} -alpha off -colors 256 \
        \( +clone -write {output_image} +delete \) \
        {threshold} -fill "#010101" -opaque "#000000" \
        -fill "#000000" -opaque "#ffffff" {output_mask};"""

    _parameters = {\
        'input_image'  : pos_parameters.filename_parameter('input_image'),
        'resize' : pos_parameters.value_parameter('resize', 100., str_template = '-{_name} {_value}%'),
        'background' : pos_parameters.string_parameter('background', 'white', str_template = '-{_name} {_value}'),
        'gravity' : pos_parameters.value_parameter('gravity', 'NorthWest', str_template = '-{_name} {_value}'),
        'extent' : pos_parameters.vector_parameter('extent', None, str_template = '-{_name} {_list}'),
        'output_image' : pos_parameters.filename_parameter('output_image', str_template = 'PNG8:{_value}'),
        'threshold' : pos_parameters.value_parameter('threshold', None, str_template = '-{_name} {_value}%'),
        'output_mask' : pos_parameters.filename_parameter('output_mask')
        }


class remask_wrapper(pos_wrappers.generic_wrapper):
    """
    the input volume is assumed to be a rgb volume!
    """

    _template = """c3d -verbose \
    {mask_file} -popas mask -clear -mcs {input_volume} \
        -foreach -push mask -times {replace} -type uchar -endfor \
    -omc 3 {masked_volume}"""

    _parameters = {
        'input_volume': pos_parameters.filename_parameter('input_volume', None),
        'mask_file': pos_parameters.filename_parameter('mask_file', None),
        'masked_volume': pos_parameters.filename_parameter('masked_volume', None),
        'replace': pos_parameters.list_parameter('replace', None, '-{_name} {_list}'),
    }

class origin_readout_wrapper(pos_wrappers.generic_wrapper):
    """
    Extracts the information about origin and spacing of an image in a very
    crapy way -- by a series of the command line parameters and bash trics.
    Very ugly but the fastest way of actually doing it.
    """

    _template = """PrintHeader {input_image} | grep qoffset"""

    _parameters = {
        'input_image': pos_parameters.filename_parameter('input_image', None),
    }

class spacing_readout_wrapper(pos_wrappers.generic_wrapper):
    """
    Extracts the information about origin and spacing of an image in a very
    crapy way -- by a series of the command line parameters and bash trics.
    Very ugly but the fastest way of actually doing it.
    """

    _template = """PrintHeader {input_image} | grep 'Voxel Spacing' \
        | cut -f2 -d: | tr -d " " | tr -d '[]'"""

    _parameters = {
        'input_image': pos_parameters.filename_parameter('input_image', None),
    }


class volume_reconstruction_preprocessor(output_volume_workflow):
    """
    The whole script which you are starting to read through encapsulates the
    process of converting the user-supplied experimental slices into several
    datasets which are suitable for further processing (i.e. reconstruction of the
    3d volume). Below you will find a detailed description of the consecutive
    processing steps.

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

        # TODO: Explain what does it mean: default mask, slice-to-slice mask
        # and slice-to-reference mask.
    """

    _f = {
        'raw_src': pos_parameters.filename('raw_src', work_dir='00_raw_images', str_template='{idx:04d}.png'),
        'raw_png_full': pos_parameters.filename('raw_png_full', work_dir='01_raw_temp', str_template='_temp_img_{idx:04d}.png'),
        'raw_png_masks': pos_parameters.filename('raw_png_masks', work_dir='01_raw_temp', str_template='_temp_mask_{idx:04d}.png'),
        'raw_ref_imgs': pos_parameters.filename('raw_ref_imgs', work_dir='02_ref_imgs', str_template='{idx:04d}.png'),
        'source_images_fullsize': pos_parameters.filename('source_images_fullsize', work_dir='04_source_images', str_template='fullsize_{idx:04d}.nii.gz'),
        'source_images_downsampled': pos_parameters.filename('source_images_downsampled', work_dir='04_source_images', str_template='downsampled_{idx:04d}.nii.gz'),
        'source_images_downsampled_fmask': pos_parameters.filename('source_images_downsampled_fmask', work_dir='04_source_images', str_template='downsampled_%04d.nii.gz'),
        'source_masks': pos_parameters.filename('source_masks', work_dir='05_source_masks', str_template='{idx:04d}.nii.gz'),
        'source_masks_fmask': pos_parameters.filename('source_masks_fmask', work_dir='05_source_masks', str_template='%04d.nii.gz'),
        'source_ref_imgs': pos_parameters.filename('source_ref_imgs', work_dir='06_source_ref_imgs', str_template='{idx:04d}.png'),
        'source_ref_imgs_fmask': pos_parameters.filename('source_ref_imgs_fmask', work_dir='06_source_ref_imgs', str_template='%04d.png'),
        'source_ref_imgs_mask': pos_parameters.filename('source_ref_imgs_mask', work_dir='07_source_ref_masks', str_template='{idx:04d}.png'),
        'source_ref_imgs_mask_fmask': pos_parameters.filename('source_ref_imgs_mask_fmask', work_dir='07_source_ref_masks', str_template='%04d.png'),
        'source_stacks': pos_parameters.filename('source_stacks', work_dir='08_source_stacks', str_template="{stack_name}_stack.nii.gz"),
        'seq_input_img': pos_parameters.filename('seq_input_img', work_dir='10_seqential_input_images', str_template="%04d.nii.gz"),
        'seq_input_mask': pos_parameters.filename('seq_input_mask', work_dir='11_seqential_input_masks', str_template="%04d.nii.gz"),
        'seq_slice_to_slice': pos_parameters.filename('seq_slice_to_slice', work_dir='12_slice_to_slice', str_template="%04d.nii.gz"),
        'seq_slice_to_slice_mask': pos_parameters.filename('seq_slice_to_slice_mask', work_dir='13_slice_to_slice_masks', str_template="%04d.nii.gz"),
        'seq_slice_to_ref': pos_parameters.filename('seq_slice_to_ref', work_dir='14_slice_to_ref', str_template="%04d.nii.gz"),
        'seq_slice_to_ref_mask': pos_parameters.filename('seq_slice_to_ref_mask', work_dir='15_slice_to_ref_masks', str_template="%04d.nii.gz"),
        'seq_ref_to_slice': pos_parameters.filename('seq_ref_to_slice', work_dir='16_ref_to_slice', str_template="%04d.nii.gz"),
        'seq_ref_to_slice_mask': pos_parameters.filename('seq_ref_to_slice_mask', work_dir='17_ref_to_slice_mask', str_template="%04d.nii.gz")
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

        # -----------------------------------------------------------
        # Then start processing the dataset.

        if self.options.doProcessSourceImages:
            self._from_source_to_masks()
            self._to_niftis()

        if self.options.doSourceStacking:
            self._stack_images_and_masks()

        # Process the reference dataset processing only when it is actually
        # enabled by the command line parameter as well as by the contents of
        # the excell file.
        if self.options.doReference and self.w._use_atlas:
            self._process_reference()

        # Remasking means applying a certain type of mask to the input rgb
        # image. There are several types of masks, read trough the code to find
        # out more.
        if self.options.doRemasking:
            self._remask()

        # Slice extraction means extracting the individual slices stacks from the
        # masked volumes. Bla bla...
        if self.options.doSliceExtraction:
            self._prepare_input_slices()

    def _process_reference(self):
        """

        Process the reference images. The reference processing rutine consists
        of the following activities:

            1. Process each individual reference images ine the following
            order:

                a. Resample the reference images to match the resolution of the
                downsampled experimental images.

                b. Extent (or reduce the canvas) to the size passed as a
                command line parameter. If no custom canvas size was requested
                than the extent is not altered. Set the background color and
                the gravity settings as well. Save the images processed this
                way as a 256 color png image.

                c. Continue processing the images describes in the previous
                point, threshold it and save the resulting images as a mask
                (which is called the reference-to-slice image mask and which
                can be easily midified further).

                d. Stack both the images and the masks in the similar way as
                the experimental images.

                e. Multiply the rgb stack by the mask image.
        """

        # Extract the extreme indexed (indexes of the first and the last slices
        # of the stack).
        first_slice, last_slice = self.slices_span

        # Get the spacing of the downsampled moving images.
        process_resolution = self.w._images[first_slice].process_resolution
        reference_resize_factor = (self.w._atlas_plate_spacing /
                                   process_resolution) * 100

        # Process the individual reference images according to the command line
        # parameters.
        commands = []
        for index, image in self.w._images.items():
            reference_index = image.reference_image_index
            command = preprocess_reference(
                input_image = self.f['raw_ref_imgs'](idx=reference_index),
                resize = reference_resize_factor,
                background = self.options.referenceBackground,
                gravity = self.options.referenceGravity,
                extent = self.options.referenceExtent,
                threshold = self.options.referenceThreshold,
                output_image = self.f['source_ref_imgs'](idx=index),
                output_mask = self.f['source_ref_imgs_mask'](idx=index))
            commands.append(copy.copy(command))
        self.execute(commands)

        # Stack the reference images and their masks into 3d stacks.
        commands = []
        command = self._get_stacking_wrapper(
            input_mask = self.f['source_ref_imgs_fmask'](),
            output_filename = self.f['source_stacks'](stack_name="atlas_rgb"))
        commands.append(copy.copy(command))
        self.execute(commands)

        # The same as above but this time the masks.
        commands = []
        command = self._get_stacking_wrapper(
            input_mask = self.f['source_ref_imgs_mask_fmask'](),
            output_filename = self.f['source_stacks'](stack_name="atlas_mask"))
        commands.append(copy.copy(command))
        self.execute(commands)

        # Remask the reference image.
        commands = []
        command = self._get_remask_wrapper("atlas_mask", "atlas_rgb", "atlas_masked")
        commands.append(copy.copy(command))
        self.execute(commands)

    def _from_source_to_masks(self):
        """
        Process the very source image into the rgb niftii image. Then create
        downsampled rgb nitii images and downsampled niftii masks.

        The routine below performs the following processing:

            1. Extend the canvas of the images in the way that all the images fit into the same canvas.
            2. Rotate, flip vertically or horizontaly (all optional)
            3. Extract the defined color channel and then blur it with median filter.
            4. Write the image to the disk (note, that the image is still a high res version -- the source version)
            5. Binarize the images with a given threshold, remove the transparency and store.


        After all the steps we end up with two images:

            1. Full resolution input images with extended canvas,
            2. Full resoultion mask of the input image with extended canvas.

        """

        commands = []
        for index, image in self.w._images.items():

            # Do the replacement if required:
            if image.replacement_index is not None:
                input_index = image.replacement_index
            else:
                input_index = index

            # Define the name of the input image filename.
            # The name is composed from the source images directory,
            # which is passed as a command line parameter.
            source_image_filename =\
                os.path.join(self.options.inputImagesDir,\
                self.w._images[input_index].image_name)

            # There is some syntax below which is a bit stupid:
            # the: [None,True][int(image.vertical_flip)]
            # means that we can pass only None or True values
            # and we cannot pass False. It's ugly. I know that.
            command = input_image_padding(
                input_image = source_image_filename,
                extent = image.padded_size,
                rotation = image.rotation,
                horizontal_flip = [None,True][int(image.horizontal_flip)],
                vertical_flip = [None,True][int(image.vertical_flip)],
                temp_mask = self.f['raw_png_masks'](idx=index),
                full_size_output = self.f['raw_png_full'](idx=index),
                median = self.options.maskMedian,
                color_channel = self.options.maskColorChannel,
                gravity = self.options.canvasGravity,
                threshold = self.options.maskThreshold)
            commands.append(copy.copy(command))

        self.execute(commands)

    def _to_niftis(self):
        """
        This method processed the images produced by the `_from_source_to_masks` method into the niftii files.
        The following procedures are performed:

            1. The full sized rgb image is converted to the niftii format and saved.
            2. The full-sized rgb image is downsampled to the defined low resolution and saved as niftii file.
            3. The full-sized image mask is downsampled and saved as in niftii format.

        Thus, after executing this file we got all of the processed images (but
        not the reference images). The next step is to prepare images stacks.

        """

        # Ok, few words of explanation here. Three niftii filer are crated
        # from a single image. See the docstrings from details.
        commands = []
        for index, image in self.w._images.items():
            # Get the native resolution per images as it can be different for
            # each individual slice images (imagine that some of them could be
            # high resolution version and some other might be downsampled
            # versions or something of this manner.
            # Note that the resolution passed to the wrapper is a two element
            # array
            native_resolution = [image.image_resolution]*2

            # Ok, get the resampling factor, which is simple downsampling ratio
            # telling how much downsample the raw image to get the downsampled
            # image. Again, the reampling factor might be different for
            # different images.
            resampling_factor = image.get_downsampling()

            # Some more things to notice: the origin is set only for the full
            # sized images. Why? To maintain spatial corespondence between the
            # both of the images.

            command = convert_to_niftiis(
                input_rgb = self.f['raw_png_full'](idx=index),
                native_spacing = native_resolution,
                resample = resampling_factor,
                origin = [0, 0],
                output_rgb_small = self.f['source_images_downsampled'](idx=index),
                output_rgb_full = self.f['source_images_fullsize'](idx=index),
                input_mask = self.f['raw_png_masks'](idx=index),
                output_mask = self.f['source_masks'](idx=index))
            commands.append(copy.copy(command))
        self.execute(commands)


    def _stack_images_and_masks(self):
        """
        Ok, once we have the the images it is time to stack them into 3d Niftii
        stacks.  The downsampled rgb images are stacked into RGB niftii staick
        by default. The source stack mask is stacked into 3d stack as well.

        The remaining two volumes are stacked only upon request
        (useSliceToSliceMask and useSliceToReferenceMask).
        """

        # Collect all the commands into a single batch instead of executing
        # them manually. Collecting the commands into a batch makes possible to
        # switch their execution on and off with the --dry-run.  This is the
        # reason why all the commands are collected into separate batches.

        input_masks = []
        output_filenames = []

        # Ok this goes by the default default.
        # Stack the RGB image into the stack.
        input_masks.append(self.f['source_images_downsampled_fmask']())
        output_filenames.append(self.f['source_stacks'](stack_name="rgb"))

        # Stack the masks of the downsampled input images.
        input_masks.append(self.f['source_masks_fmask']())
        output_filenames.append(self.f['source_stacks'](stack_name="mask"))

        for in_mask, out_fname in zip(input_masks, output_filenames):
            commands = []
            command = self._get_stacking_wrapper(
                input_mask = in_mask,
                output_filename = out_fname)
            commands.append(copy.copy(command))
            self.execute(commands)

        # Ok, if we are using slice-to-slice masks then we need to create
        # proper slice to slice mask image Create the slice-to-slice mask
        if self.options.useSliceToSliceMask:
            commands = []
            command = pos_wrappers.copy_wrapper(
                source = [self.f['source_stacks'](stack_name="mask")],
                target = self.f['source_stacks'](stack_name="slice_to_slice_mask"))
            commands.append(copy.copy(command))
            self.execute(commands)

        # Similarly, if we are planning to use a slice-to-reference mask
        # Then create the slice-to-reference mask.
        if self.options.useSliceToReferenceMask:
            commands = []
            command = pos_wrappers.copy_wrapper(
                source = [self.f['source_stacks'](stack_name="mask")],
                target = self.f['source_stacks'](stack_name="slice_to_reference_mask"))
            commands.append(copy.copy(command))
            self.execute(commands)

    def _get_stacking_wrapper(self, input_mask, output_filename):
        """
        Returns a stacking wrapper for... creating the image stacks.

        :param input_mask: a unix-like shell mask of the files to stack. The
            filenames should be named in such a way that the mask will reruen them
            in order.
        :type input_maks: str

        :param output_filename: output filename if the stack.
        :type output_filename: str

        :return: Slice stacking wrapper
        :rtype: `pos_wrappers.stack_and_reorient_wrapper`
        """

        first_slice, last_slice = self.slices_span

        command = pos_wrappers.stack_and_reorient_wrapper(
            stack_mask = input_mask,
            slice_start = first_slice,
            slice_end = last_slice,
            slice_step = 1,
            output_volume_fn = output_filename,
            permutation_order = self.permutation,
            flip_axes = self.flipping,
            orientation_code = self.options.outputVolumeOrientationCode,
            spacing = self.output_volume_spacing,
            origin = self.output_volume_origin)
        return copy.copy(command)

    def _get_remask_wrapper(self, mask_file, image_file, output_file):
        """
        Returns a remasking command line wrapper customised by the provided
        arguments.

        :param mask_file: input ask filename (binary 3d niftii file)
        :type mask_file: str

        :param mask_file: input rgb file (rgb, uchar, 3d niftii file)
        :type mask_file: str

        :param output_file: output rgb file (rgb, uchar, 3d niftii file)
        :type output_file: str
        """

        # Create the remask wrapper.
        wrapper = remask_wrapper(
            mask_file = self.f['source_stacks'](stack_name=mask_file), \
            input_volume = self.f['source_stacks'](stack_name=image_file), \
            replace = [0, self.options.maskingBackground],
            masked_volume = self.f['source_stacks'](stack_name=output_file))
        return copy.copy(wrapper)

    def _remask(self):
        """
        Remasking means multiplying the 3d rgb images stack with the proper
        mask (either slice-to-slice mask or slice-to-reference mask). In this
        method, the input image stack is by default multiplied by the default
        mask. This cannot be turned off.
        """
        # We will be gathering all the commands in the batch below.
        commands = []

        # The regular masked volume is always generated.
        command = self._get_remask_wrapper("mask", "rgb", "rbg_masked")
        commands.append(command)

        # If required, the slice-to-slice masked volume is generated.
        if self.options.useSliceToSliceMask:
            command = self._get_remask_wrapper("slice_to_slice_mask",\
                "rgb", "rbg_slice_to_slice_masked")
            commands.append(command)

        # If required, the slice-to-reference mask is generated.
        if self.options.useSliceToReferenceMask:
            command = self._get_remask_wrapper("slice_to_reference_mask",\
                "rgb", "rbg_slice_to_reference_masked")
            commands.append(command)

        # Execute all the batch.
        self.execute(commands)

    def _prepare_input_slices(self):
        """
        Preparing input slices means that the 3D niftii files with stacked
        images are splitted into individual slices for the purpose of the
        histological volume reconstruction.
        """

        # Get the indexes of the extreme slices,
        # which means the index of the first slice and the index of the last
        # slice of the stack.
        first_slice, last_slice = self.slices_span

        # The default volume is resliced automatically
        input_names = [
            self.f['source_stacks'](stack_name='rbg_masked'),
            self.f['source_stacks'](stack_name='mask')]

        output_namings = [
            self.f['seq_input_img'](),
            self.f['seq_input_mask']()]

        # Slice-to-slice slices and masks are extracted upon request
        if self.options.useSliceToSliceMask:
            input_names.append(self.f['source_stacks'](stack_name='rbg_slice_to_slice_masked'))
            input_names.append(self.f['source_stacks'](stack_name='slice_to_slice_mask'))
            output_namings.append(self.f['seq_slice_to_slice']())
            output_namings.append(self.f['seq_slice_to_slice_mask']())

        # Slice-to-reference slices and masks are extracted upon purpose
        if self.options.useSliceToReferenceMask:
            input_names.append(self.f['source_stacks'](stack_name='rbg_slice_to_reference_masked'))
            input_names.append(self.f['source_stacks'](stack_name='slice_to_reference_mask'))
            output_namings.append(self.f['seq_slice_to_ref']())
            output_namings.append(self.f['seq_slice_to_ref_mask']())

        # If reference-to-slice images are required, extract them.
        # We perform the slice extraction only when the
        # 'useReferenceToSliceMask'
        # as well as the proper "use atlas" switch in the excel file are
        # defined.
        if self.options.useReferenceToSliceMask and self.w._use_atlas:
            input_names.append(self.f['source_stacks'](stack_name='atlas_masked'))
            input_names.append(self.f['source_stacks'](stack_name='atlas_mask'))
            output_namings.append(self.f['seq_ref_to_slice']())
            output_namings.append(self.f['seq_ref_to_slice_mask']())

        # Gather all the commands into a single batch,
        commands = []
        for input_name, output_naming_scheme in zip(input_names, output_namings):
            command = pos_deformable_wrappers.preprocess_slice_volume(
                input_image = input_name,
                output_naming = output_naming_scheme,
                slicing_plane = self.slicing_plane,
                start_slice = 0,
                end_slice = last_slice,
                shift_indexes = first_slice)
            commands.append(copy.copy(command))
        self.execute(commands)

    # Some convenient functions below: properties to make all the code more
    # prettier.

    def __get_slicing_plane(self):
        """
        Extracts and returns the slicing plane index in RAS convention,
        following the `slicing_planes_settings` variable. So: 0 goes for
        saggital, 1 goes for coronal, 2 goes for axial.
        """
        # Note that this method requires the self.w._slicing_plane  to be set.
        # usually it is.
        try:
            return self.slicing_planes_settings[self.w._slicing_plane]['axis']
        except:
            return None

    def __get_flipping(self):
        """
        Get the flipping masks for the invidual axes.
        """
        # Note that this method requires the self.w._slicing_plane to be set.
        # usually it is.
        try:
            return self.slicing_planes_settings[self.w._slicing_plane]['flip']
        except:
            return None

    def __get_permutation(self):
        """
        Get the permutation order for the given axis
        """
        # Note that this method requires the self.w._slicing_plane to be set.
        # usually it is.
        try:
            return self.slicing_planes_settings[self.w._slicing_plane]['permutation']
        except:
            return None

    def __get_extreme_slices(self):
        """
        Extract the extreme indexed (indexes of the first and the last slices
        of the stack).

        :return: Indexed of the first and the last slices in the image stack.
        :rtype: (int, int)
        """
        first_slice = min(map(lambda x: x.image_index, self.w._images.values()))
        last_slice = max(map(lambda x: x.image_index, self.w._images.values()))

        return first_slice, last_slice

    def __get_output_slice_spacing(self):
        """
        Returns the output volume spacing based on the slices parameters.
        """
        # Initialize the commands batch
        commands = []

        # We extract the altered orgin from the first image in the stack.
        image = self.w._images.items()[0]
        index = self.slices_span[0]

        # Then, define theorigin readout command line wrapper and then
        # append this single command into the commands batch.
        command = spacing_readout_wrapper(
            input_image = self.f['source_images_downsampled'](idx=index))
        commands.append(copy.copy(command))

        # Execute the commands and capture the stdout and stderr.
        stdout, stderr = self.execute(commands)

        # Ok, we extract only the x spacing of the code since the assumption
        # that the x spacing is the same as y spacing (the images are
        # isotropic) which is a very basic assumption.
        spacing_x =  float(stdout.split(",")[0])
        spacing = [spacing_x]*3
        spacing[self.slicing_plane] = self.w._slice_thickness
        return spacing

    def __get_output_volume_origin(self):
        """
        Extract the origin of the resampled image. This is important as the
        resampling is performed in the way that the sampling is not the exact
        sampling requested. Also, the origin is a bit changes due this not
        exact way of resampling.

        The actual origin is determinated by executing some shell command which
        stdout is processed. Not an optimal way of performing the task but at
        least it works.
        """
        # Initialize the commands batch
        commands = []

        # We extract the altered orgin from the first image in the stack.
        image = self.w._images.items()[0]
        index = self.slices_span[0]

        # Then, define theorigin readout command line wrapper and then
        # append this single command into the commands batch.
        command = origin_readout_wrapper(
            input_image = self.f['source_images_downsampled'](idx=index))
        commands.append(copy.copy(command))

        # Execute the commands and capture the stdout and stderr.
        stdout, stderr = self.execute(commands)

        # Process the stdout string and extract the actual origin value. The
        # value extracted is the offset_x. It is assumed that the offset_x
        # is the same as the offset_y, and, since the image is an 2d image,
        # the offset_z value is usually zero, but we don't care about it at
        # all.
        origin_x = float(stdout.split("\n")[0].split()[2])
        origin = [origin_x]*3
        origin[self.slicing_plane] = 0
        # TODO: Until fixed properly we return [0,0,0]
        return [0, 0, 0]

    slicing_plane = property(__get_slicing_plane)
    flipping = property(__get_flipping)
    permutation = property(__get_permutation)
    slices_span = property(__get_extreme_slices)
    output_volume_spacing = property(__get_output_slice_spacing)
    output_volume_origin = property(__get_output_volume_origin)

    @classmethod
    def _getCommandLineParser(cls):
        """
        """
        parser = output_volume_workflow._getCommandLineParser()

        obligatory_options = OptionGroup(parser, 'Obligatory pipeline options.')
        obligatory_options.add_option('--input-images-dir', default=None,
            type='str', dest='inputImagesDir',
            help='The directory from which the input images will be read.')
        obligatory_options.add_option('--input-workbook', default=None,
            type='str', dest='inputWorkbook',
            help='Input workbook.')
        obligatory_options.add_option('--output-workbook', default=None,
            type='str', dest='outputWorkbook',
            help='Output workbook.')


        source_processing = OptionGroup(parser, 'Source data processing.')

        source_processing.add_option('--enable-process-source-images', default=False,
            dest='doProcessSourceImages', action='store_true',
            help='Enable source dataset processing. Which means preparing the input niftii stacks.')
        source_processing.add_option('--disable-process-source-images', default=False,
            dest='doProcessSourceImages', action='store_false')

        source_processing.add_option('--canvas-gravity', default="NorthWest",
            dest='canvasGravity', action='store', type="choice",
            choices=["NorthWest","Center"],
            help='Image canvas extention gravity.')
        source_processing.add_option('--canvas-background', default="white",
            dest='canvasBackground', action='store', type="str",
            help='Canvas color.')
        source_processing.add_option('--mask-threshold', default=93.,
            dest='maskThreshold', action='store', type="float",
            help='0-100 value.')
        source_processing.add_option('--mask-median', default=5,
            dest='maskMedian', action='store', type="int",
            help='Integer')
        source_processing.add_option('--mask-color-channel', default="red",
            dest='maskColorChannel', action='store', type="choice",
            choices=["R","G","B","Red","Green","Blue","red","green","blue","r","g","b"],
            help='red|green|blue|r|g|b')
        source_processing.add_option('--masking-background', default=255,
            dest='maskingBackground', action='store', type="int",
            help='Integer to which background value will be replaced.')


        stacking_options = OptionGroup(parser, 'Images staking options')

        stacking_options.add_option('--enable-remasking', default=False,
            dest='doRemasking', action='store_true',
            help='Do remasking')
        stacking_options.add_option('--disable-remasking', default=False,
            dest='doRemasking', action='store_false')

        stacking_options.add_option('--enable-slice-extraction', default=False,
            dest='doSliceExtraction', action='store_true',
            help='Do slice extration.')
        stacking_options.add_option('--disable-slice-extraction', default=False,
            dest='doSliceExtraction', action='store_false')

        stacking_options.add_option('--enable-source-stacking', default=False,
            dest='doSourceStacking', action='store_true',
            help='Process the initial slices into the initial stacks.')
        stacking_options.add_option('--disable-source-stacking', default=False,
            dest='doSourceStacking', action='store_false')

        stacking_options.add_option('--use-slice-to-slice-mask', default=False,
            dest='useSliceToSliceMask', action='store_true',
            help='Generate and use slice to slice mask.')
        stacking_options.add_option('--use-slice-to-reference-mask', default=False,
            dest='useSliceToReferenceMask', action='store_true',
            help='Generate and use slice to reference mask.')


        reference_options = OptionGroup(parser, 'Reference images processing options')
        reference_options.add_option('--enable-reference', default=False,
            dest='doReference', action='store_true',
            help='General switch for the reference images processing.')
        reference_options.add_option('--disable-reference', default=False,
            dest='doReference', action='store_false')

        reference_options.add_option('--use-reference-to-slice-mask', default=False,
            dest='useReferenceToSliceMask', action='store_true',
            help='Generate and use reference to slice mask.')
        reference_options.add_option('--reference-extent', default=None,
            dest='referenceExtent', action='store', type="int", nargs=2,
            help='Extent of the reference images.')
        reference_options.add_option('--reference-gravity', default="NorthWest",
            dest='referenceGravity', action='store', type="choice",
            choices=["NorthWest","Center"],
            help='Gravity of the reference extent.')
        reference_options.add_option('--reference-background', default='white',
            dest='referenceBackground', action='store', type="str",
            help='Background of the reference image.')
        reference_options.add_option('--reference-threshold', default=99.,
            dest='referenceThreshold', action='store', type="float",
            help='0-100 value.')

        parser.add_option_group(obligatory_options)
        parser.add_option_group(stacking_options)
        parser.add_option_group(source_processing)
        parser.add_option_group(reference_options)

        return parser


if __name__ == '__main__':
    options, args = volume_reconstruction_preprocessor.parseArgs()
    se = volume_reconstruction_preprocessor(options, args)
    se.launch()
