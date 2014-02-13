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
import csv
import copy
from optparse import OptionGroup

from pos_wrapper_skel import output_volume_workflow
import pos_wrappers, pos_parameters

"""
Pos pairwise alignment script
*****************************

:author: Piotr Majka <pmajka@nencki.gov.pl>
:revision: $Rev$
:date: $LastChangedDate$

`pos_pairwise_registration` -- a pairwise registration script.

This file is part of imaging data integration framework,
a private property of Piotr Majka
(c) Piotr Majka 2011-2013. Restricted, damnit!

Syntax
======

.. highlight:: bash

Providing information on slices to process
------------------------------------------

There are two ways of defining the moving slice image. Either 1) it can go from
the source movins slices that were used for the registration purposes or 2) the
moving images can go from the additional images stack. This is solved by
passing the whole `filename` parameter.

Ok, what is going on here? In the workflow there are two types of ranges: the
moving slices range and the fixed slices range. In general they do not
necessarily overlap thus in general they are two different ranges. The
corespondence between ranges is established according to the
`imagePairsAssignmentFile` file supplied via the command line. If neither
moving slices range nor fixes slices range are provided, the approperiate
ranges are copied from the general slice range. When provided, the custom
slices ranges override the default slice range value.



How to process additional image stacks
--------------------------------------

First of all: additional stack settings are optional while the primary image
stacks are obligatory.

Second of all: The additional image stack should comprise only three channel,
8bit RGB images. The workflow will not work for any other type of images. Period.

This workflow supports a very nice functionality of handling more than one
image stack to process. While the transformations are caluclated based on a
single image stack (let's call it a primary image stack), the transformation
may be applied to other image stacks (reffered as the additional image stacks).
Obviously, the additional image stacks are optional.



Providing additional image stacks
---------------------------------

Information on additional image stacks is provided using several command line
arguments, namely: `--additionalMovingImagesDirectory`,
`--additionalInvertMultichannel`, `--additionalMultichannelVolume`,
`--additionalInterpolation`, `--additionalInterpolationBackground`. For every
additional image stacks all of the command arguments have to be provided.
Skipping any of the parametrers will cause the workflow to collapse.

The parameters have the following meaning:

    1. `--additionalInvertMultichannel`: directory containing the input images
    comprising the image stack. The input images have to provided as three
    channel, 8bit per channel RGB images. The names should comply the
    "%04d.nii.gz" format and the indexes of the slices have to be the same as
    the indexed of the primary moving stack.

    2. `--additionalInvertMultichannel`: Determines of the input images are
    inverted ofr the purpose of reslicing. Only two values are allowed: Either
    "1" or "0".

    3. `--additionalMultichannelVolume`: Filename of the output rgb volume. The
    parameters is no less obligatory than all the other parameters. Output
    volumes of additional image stacks are created in the same directory as the
    volumes of the regular image stacks.

    4. `--additionalInterpolation`: Determines the interpolation method to
    apply during reslicing of the given stack. The allowed values are the same
    as those for interpolation of the primary image stacks.

    5. `--additionalInterpolationBackground`: Default background color to be
    used during reslicing of the image stack (a value for the individual
    channels).

Only when all the parameters describing single additional image stack are
provided, the setting of the another stack could be specified. On other words:
one have to specify a block of parameteter for the one image stack before
specifying description of the another one.



Setting the properties of the resliced images
---------------------------------------------

Define output images stack origin and and size according to the
providing command line arguments. If provided, the resliced images are
cropped before stacking into volumes. Note that when the slices are
cropped their origin is preserved. That should be taken into
consideration when origin of the stacked volume if provided.

When the output ROI is not defined, nothing special will happen.
Resliced images will not be cropped in any way.


An example of pretty complicated usage
--------------------------------------

Here is a pretty comprehensive example of a pairwise registration script.
Utilizes typical options:

pos_pairwise_registration.py \
        --fixedImagesDir fixed_images_directory/ \
        --movingImagesDir moving_images_directory/ \
        --movingSlicesRange 10 20  \
        --fixedSlicesRange 10 20   \
        --registrationColorChannelMovingImage blue  \
        --registrationColorChannelFixedImage green  \
        --resliceBackgorund 255  \
        --medianFilterRadius 4 4 \
        --outputVolumesDirectory output_volumes_directory/ \
        --useRigidAffine \
        --loglevel DEBUG \
        --outputVolumeSpacing 0.02 0.02 0.06 \
        --dryRun

"""


class image_voxel_count_wrapper(pos_wrappers.generic_wrapper):
    """
    """

    _template = """c{dimension}d {image} -shift -{background} \
        -thresh 0 0 0 1 {voxel_sum} {voxel_integral} | cut -f3 -d' ' """

    _parameters = {
        'dimension': pos_parameters.value_parameter('dimension', 2),
        'image': pos_parameters.filename_parameter('image', False),
        'background' : pos_parameters.value_parameter('shift', 0, '{_value}'),
        'voxel_sum' : pos_parameters.boolean_parameter('voxel-sum', None, str_template='-{_name}'),
        'voxel_integral' : pos_parameters.boolean_parameter('voxel-integral', None, str_template='-{_name}')
    }


class pairwiseRegistration(output_volume_workflow):
    """
    Pairwise slice to slice registration script.
    """

    _f = {
        'fixed_raw_image' : pos_parameters.filename('fixed_raw_image', work_dir = '99_override_this', str_template = '{idx:04d}.nii.gz'),
        'moving_raw_image' : pos_parameters.filename('moving_raw_image', work_dir = '99_override_this', str_template = '{idx:04d}.nii.gz'),

        'moving_gray' : pos_parameters.filename('src_gray', work_dir = '00_moving_gray', str_template='{idx:04d}.nii.gz'),
        'moving_color' : pos_parameters.filename('src_color', work_dir = '01_moving_color', str_template='{idx:04d}.nii.gz'),
        'fixed_gray' : pos_parameters.filename('fixed_gray', work_dir = '02_fixed_gray', str_template='{idx:04d}.nii.gz'),
        'fixed_color' : pos_parameters.filename('fixed_color', work_dir = '03_fixed_color', str_template='{idx:04d}.nii.gz'),
        'additional_gray' : pos_parameters.filename('additional_gray', work_dir = '04_additional_gray', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),
        'additional_color' : pos_parameters.filename('additional_color', work_dir = '05_additional_color', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),

        'transf_naming' : pos_parameters.filename('transf_naming', work_dir = '11_transforms', str_template='tr_m{mIdx:04d}_'),
        'transf_file' : pos_parameters.filename('transf_file', work_dir = '11_transforms', str_template='tr_m{mIdx:04d}_Affine.txt'),

        'resliced_gray' : pos_parameters.filename('resliced_gray', work_dir = '21_gray_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_gray_mask' : pos_parameters.filename('resliced_gray_mask', work_dir = '21_gray_resliced', str_template='%04d.nii.gz'),
        'resliced_color' : pos_parameters.filename('resliced_color', work_dir = '23_resliced_color', str_template='{idx:04d}.nii.gz'),
        'resliced_color_mask' : pos_parameters.filename('resliced_color_mask', work_dir = '23_resliced_color', str_template='%04d.nii.gz'),
        'resliced_add_gray' : pos_parameters.filename('resliced_add_gray', work_dir = '25_resliced_add_gray', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),
        'resliced_add_gray_mask' : pos_parameters.filename('resliced_add_gray_mask', work_dir = '25_resliced_add_gray', str_template='stack_{stack_id:02d}_slice_%04d.nii.gz'),
        'resliced_add_color' : pos_parameters.filename('resliced_add_color', work_dir = '27_resliced_add_color', str_template='stack_{stack_id:02d}_slice_{idx:04d}.nii.gz'),
        'resliced_add_color_mask' : pos_parameters.filename('resliced_add_color_mask', work_dir = '27_resliced_add_color', str_template='stack_{stack_id:02d}_slice_%04d.nii.gz'),

        'out_volume_gray' : pos_parameters.filename('out_volume_gray', work_dir = '31_output_volumes', str_template='{fname}_gray.nii.gz'),
        'out_volume_color' : pos_parameters.filename('out_volume_color', work_dir = '31_output_volumes', str_template='{fname}_color.nii.gz'),
        'out_volume_color_add' : pos_parameters.filename('out_volume_color_add', work_dir = '31_output_volumes', str_template='additional_stack_{stack_id:02d}_{fname}_color.nii.gz')
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
        super(self.__class__, self)._validate_options()

        # Ok, the first thing to check is to make sure that both slice ranges
        # are provided: the moving slice range and the fixed slice range
        assert self.options.fixedSlicesRange, \
            self._logger.error("Fixed slices range (`--fixedSlicesRange`) is obligatory. Please provide the fixed slices range. ")

        assert self.options.movingSlicesRange, \
            self._logger.error("Moving range parameters (`--movingSlicesRange`) are required. Please provide the moving slices range. ")

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
        if not image_pairs_filename:
            self._logger.debug(
            "No slice assignment file was provided. Using pairwise assignment.")
            self._slice_assignment = \
                dict(zip(self.options.movingSlicesRange,
                         self.options.fixedSlicesRange))
        else:
            # Here I use pretty neat code snipper for determining the
            # dialect of teh csv file. Found at:
            # http://docs.python.org/2/library/csv.html#csv.Sniffer
            self._logger.debug(
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
            fixed_slice_index = self._slice_assignment.get(slice_index)
            if fixed_slice_index is None:
                self._logger.error(
                    "No fixed slice index defined for the moving slice %d.",
                    slice_index)
                sys.exit(1)
            else:
                self._logger.debug(
                "Fixed slice %d is assigned to the moving slice %d.",
                fixed_slice_index, slice_index)

        self._logger.debug("Mappings and slices' ranges passed the validation.")

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # At the very beginning override the default dummy input images
        # directory by the actual images directory.
        self.f['fixed_raw_image'].override_dir = self.options.fixedImagesDir
        self.f['moving_raw_image'].override_dir = self.options.movingImagesDir

        # Override transformation directory
        if self.options.transformationsDirectory is not False:
            self.f['transf_naming'].override_dir = \
                self.options.transformationsDirectory
            self.f['transf_file'].override_dir = \
                self.options.transformationsDirectory

        # Override output volumes directory
        if self.options.outputVolumesDirectory is not False:
            self.f['out_volume_gray'].override_dir = \
                self.options.outputVolumesDirectory
            self.f['out_volume_color'].override_dir = \
                self.options.outputVolumesDirectory
            self.f['out_volume_color_add'].override_dir = \
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

    def _inspect_input_images(self):
        """
        Verify if all the files are availabe: All images have to be ailable. If
        the case is different, the workflow will not proceed and the user will
        be asked to supply the missing images.
        """

        # Iterate over all filenames beeing used it the whole workflow
        # and check if all of them exists.
        filenames_to_check = map(lambda x: self.f['moving_raw_image'](idx=x),
                                 self.options.movingSlicesRange)
        filenames_to_check += map(lambda x: self.f['fixed_raw_image'](idx=x),
                                 self.options.fixedSlicesRange)

        for slice_filename in filenames_to_check:
            self._logger.debug("Checking for image: %s.", slice_filename)

            if not os.path.isfile(slice_filename):
                self._logger.error("File does not exist: %s. Exiting",
                                   slice_filename)
                sys.exit(1)

    def _correct_slice_assignment(self):
        """
        Replace inaproperiate reference slices with their approperiate
        counterparts. What's all the buzz about. Well, sometimes  a given
        reference slice may happen to be a entirely blank slice. In such case
        it cannot be used as any registration cannot be performed with such an
        image (a non-blank image to a blank image. This will not work).

        To avoid pitfalls related with these blank reference images, the
        workflow elliminates such images and replaces them with a valid (non
        blank) images.
        """
        # Well, we need numpy here.
        import numpy as np

        # Repair indexes of moving slices for which a blank reference slice was
        # defined:
        self._logger.debug("Correcting slice to slice assignment for those moving slice for which a blank reference slice was assigned.")

        # This array will collect all the number of non-blank voxels for each
        # slice.
        ref_slice_voxel_counts = []

        # Iterate over all reference slices and detect the number of voxels per
        # slice.
        for fixed_index in self._slice_assignment.values():
            command = image_voxel_count_wrapper(
                image = self.f['fixed_gray'](idx=fixed_index),
                background = self.options.resliceBackgorund,
                voxel_sum = True)
            vox_count = float(command()['stdout'].strip())
            ref_slice_voxel_counts.append(vox_count)

        # Convert the list into a numpy array, and then extract the index of
        # the first and the last nonzero slices.
        ref_slice_voxel_counts = np.array(ref_slice_voxel_counts)
        first_nonzero = np.nonzero(ref_slice_voxel_counts)[0][3]
        last_nonzero = np.nonzero(ref_slice_voxel_counts)[0][-3]

        # Calculate the offset from zero to the index of the first moving slice
        # (yeah, crazy, but we assumed that the slice indexing may start not
        # from zero.
        np_offset = min(self._slice_assignment.keys())

        for moving_index in self._slice_assignment.keys():

            # Check if the number of voxels in given reference slice is zero?
            if ref_slice_voxel_counts[moving_index - np_offset] == 0:

                # If we're in the first half of the slice, we use first nonzero
                # slice index. In the other case, the last nonzero image is
                # used.
                if moving_index < len(self._slice_assignment.keys()) / 2:
                    self._slice_assignment[moving_index] = first_nonzero
                    self._logger.debug("Setting ref(%d) = %d." \
                        % (moving_index, first_nonzero + np_offset))
                else:
                    self._slice_assignment[moving_index] = last_nonzero
                    self._logger.debug("Setting ref(%d) = %d." \
                        % (moving_index, last_nonzero + np_offset))

    def _generate_slice_index(self):
        """
        Generate moving image to fixed image mappings.
        """

        # Range of images to register. It is a perfect solution to override the
        # command line argument option with some other value, but hey -
        # nobody's perfect.
        self._logger.debug("Defining default slicing range.")

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
        self._logger.debug("Setting the moving slice range.")
        self.options.movingSlicesRange = \
            range(self.options.movingSlicesRange[0],
                    self.options.movingSlicesRange[1] + 1)

        # Check if custom fixes slice range is provided.
        # If it's not, use the default slice range.
        self._logger.debug("Setting the fixed slice range.")
        self.options.fixedSlicesRange = \
            range(self.options.fixedSlicesRange[0],
                    self.options.fixedSlicesRange[1] + 1)

    def launch(self):
        # Simple as it looks: load the fixed slice to moving slice assignment.
        # This step cannot be skipped for obvious reasons.
        self._load_slice_assignment()

        # After proving that the mappings are correct, the script verifies if
        # the files to be coregistered do actually exist. However, the
        # verification is performed only when the script is executed in not in
        # `--druRun` mode:
        if self.options.dryRun is False:
            self._inspect_input_images()

        # The slice preprocessing may be skipped if required.
        if self.options.skipPreprocessing is not True:
            self._generate_fixed_slices()
            self._generate_moving_slices()

        # Elliminate blank reference slices.
        if self.options.dryRun is False:
            self._correct_slice_assignment()

        # Generate transforms. This step may be switched off by providing
        # aproperiate command line parameter.
        if self.options.skipTranasformGeneration is not True:
            self._calculate_transforms()

        # Reslice the input slices according to the generated transforms.
        # This step may be skipped by providing approperiate command line
        # parameter.
        self._reslice()

        # Stack both grayscale as well as the rgb slices into a volume.
        # This step may be skipped by providing approperiate command line
        # parameter.
        if self.options.skipOutputVolumes is not True:
            self._stack_output_images()

        # This workflow supports a very nice functionality of handling more
        # than one image stack to process. While the transformations are
        # caluclated based on a single image stack (let's call it a primary
        # image stack), the transformation may be applied to other image stacks
        # (reffered as the additional image stacks). Obviously, the additional
        # image stacks are optional.
        if self.options.additionalMovingImagesDirectory is not None:
            self._load_additional_stacks_settings()
            self._reslice_additional_stack()
            self._stack_additional_image_stacks()

    def _get_generic_source_slice_preparation_wrapper(self):
        """
        Get generic slice preparation wrapper for further refinement.
        """
        command = pos_wrappers.alignment_preprocessor_wrapper(
            median_filter_radius=self.options.medianFilterRadius,
            invert_multichannel=self.options.invertMultichannel)
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
                'registration_color': self.options.registrationColorChannelFixedImage,
                'registration_resize': self.options.fixedImageResize,
                'input_image': self.f['fixed_raw_image'](idx=slice_number),
                'grayscale_output_image': self.f['fixed_gray'](idx=slice_number),
                'color_output_image': self.f['fixed_color'](idx=slice_number)})
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

        for slice_number in self._slice_assignment.keys():

            command = self._get_generic_source_slice_preparation_wrapper()
            command.updateParameters({
                'registration_color': self.options.registrationColorChannelMovingImage,
                'registration_resize': self.options.movingImageResize,
                'input_image': self.f['moving_raw_image'](idx=slice_number),
                'grayscale_output_image': self.f['moving_gray'](idx=slice_number),
                'color_output_image': self.f['moving_color'](idx=slice_number)})
            commands.append(copy.deepcopy(command))

        # Execute the commands in a batch.
        self.execute(commands)
        self._logger.info("Generating moving slices. Done.")

    def _calculate_transforms(self):
        commands = []
        for moving_slice, fixed_slice in self._slice_assignment.items():
            transform_command = self._calculate_single_transform(moving_slice, fixed_slice)
            if not os.path.isfile(self.f['transf_file'](mIdx=moving_slice)):
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
            dimension=self.__IMAGE_DIMENSION,
            outputNaming=output_naming,
            iterations=self.__DEFORMABLE_ITERATIONS,
            affineIterations=affine_iterations,
            continueAffine=None,
            rigidAffine=use_rigid_transformation,
            imageMetrics=metrics,
            histogramMatching=str(self.__HISTOGRAM_MATCHING).lower(),
            miOption=[metric_parameter, self.__MI_SAMPLES],
            affineMetricType=affine_metric_type)

        # Return the registration command.
        return copy.deepcopy(registration)

    def _reslice(self):

        # Reslicing grayscale images.  Reslicing multichannel images. Collect
        # all reslicing commands into an array and then execute the batch.
        if self.options.skipGrayReslice is not True:
            self._logger.info("Reslicing grayscale images.")
            commands = []
            for slice_index in self.options.movingSlicesRange:
                commands.append(self._reslice_grayscale(slice_index))
            self.execute(commands)
        else:
            self._logger.info("Reslicing grayscale images is TURNED OFF.")

        # Reslicing multichannel images. Again, collect all reslicing commands
        # into an array and then execute the batch.
        if self.options.skipColorReslice is not True:
            self._logger.info("Reslicing multichannel images.")
            commands = []
            for slice_index in self.options.movingSlicesRange:
                commands.append(self._reslice_multichannel(slice_index))
            self.execute(commands)
        else:
            self._logger.info("Reslicing multichannel images is TURNED OFF.")

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

        # There are two ways of defining the moving slice image. Either 1) it
        # can go from the source movins slices that were used for the
        # registration purposes or 2) the moving images can go from the
        # additional images stack. This is solved by passing the whole
        # `filename` parameter.
        moving_image_filename = moving_filename_generator(idx=slice_number)
        resliced_image_filename = resliced_type
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
            reference_image=reference_image_filename,
            moving_image=moving_image_filename,
            transformation=transformation_file,
            output_image=resliced_image_filename,
            region_origin=region_origin_roi,
            region_size=region_size_roi)
        return copy.deepcopy(command)

    def _reslice_grayscale(self, slice_number):
        """
        Reslice grayscale images.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        command = self._get_reslice_wrapper(
            wrapper_type=pos_wrappers.command_warp_grayscale_image,
            moving_filename_generator=self.f['moving_color'],
            resliced_type=self.f['resliced_gray'](idx=slice_number),
            slice_number=slice_number)
        command.updateParameters({
            'background':self.options.resliceBackgorund,
            'interpolation':self.options.resliceInterpolation})

        return copy.deepcopy(command)

    def _reslice_multichannel(self, slice_number):
        """
        Reslice grayscale images.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        command = self._get_reslice_wrapper(
            wrapper_type=pos_wrappers.command_warp_rgb_slice,
            moving_filename_generator=self.f['moving_color'],
            resliced_type=self.f['resliced_color'](idx=slice_number),
            slice_number=slice_number)
        command.updateParameters({
            'background': self.options.resliceBackgorund,
            'interpolation': self.options.resliceInterpolation,
            'inversion_flag': self.options.invertMultichannel})

        return copy.deepcopy(command)

    def _get_generic_stack_slice_wrapper(self, mask_type, output_filename):
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

        :param output_filename: output filename itself.
        :type output_filename: str
        """

        # Assign some usefull aliases. The processing regards only slices that
        # are withing the moving slices index.
        start = self.options.movingSlicesRange[0]
        stop = self.options.movingSlicesRange[-1]

        # Define the warpper according to the provided settings.
        command = pos_wrappers.stack_and_reorient_wrapper(
            stack_mask=mask_type,
            slice_start=start,
            slice_end=stop,
            slice_step=self.__VOL_STACK_SLICE_SPACING,
            output_volume_fn=output_filename,
            permutation_order=self.options.outputVolumePermutationOrder,
            orientation_code=self.options.outputVolumeOrientationCode,
            output_type=self.options.outputVolumeScalarType,
            spacing=self.options.outputVolumeSpacing,
            origin=self.options.outputVolumeOrigin,
            interpolation=self.options.setInterpolation,
            resample=self.options.outputVolumeResample)

        # Return the created wrapper.
        return copy.deepcopy(command)

    def _stack_output_images(self):
        """
        Execute stacking images based on grayscale and multichannel images.
        """
        # Define the output volume filename. If no custom colume name is
        # provided, the filename is based on the provided processing
        # parameters. In the other case the provided custom filename is used.
        # We get the output filename prefix only once as it's shared between
        # grayscale and multichannel output volume filenames.
        filename_prefix = self._get_parameter_based_output_prefix()

        # Get the output filename for the grayscale output image.
        # and generate the output volume itself.
        output_filename = self.f['out_volume_gray'](fname=filename_prefix)
        command = self._get_generic_stack_slice_wrapper(
            self.f['resliced_gray_mask'](),
            output_filename)
        self.execute(command)

        # Get the output filename for the multichannel output image.
        # and generate the output volume itself.
        output_filename = self.f['out_volume_color'](fname=filename_prefix)
        command = self._get_generic_stack_slice_wrapper(
            self.f['resliced_color_mask'](),
            output_filename)
        self.execute(command)

    def _load_additional_stacks_settings(self):
        """
        Loads settings for parsing additional image stacks. Such settings may
        be provided by the user in order to process more than one stack (more
        than only the moving stack) of images using the transfomations obtained
        for the moving stack.

        Additional stack settings are optional.

        # TODO: Validate the provided properties (e.g. length of all the
        # 'additional' command line parameters).
        """

        # Array holding parameters of the adddtional images stacks
        self._additional_stacks_settings = []
        self._add_stacks_inputs = []

        # List of command line parameters (`add_stack_fields`) which are
        # translated to given dictionary keys (`add_stack_key`).
        add_stack_fields = ['additionalMovingImagesDirectory',
                'additionalInvertMultichannel',
                'additionalMultichannelVolume', 'additionalInterpolation',
                'additionalInterpolationBackground']
        add_stack_keys = ['imgDir',  'invert_rgb', 'rgbVolName',
                'interpolation', 'background']

        # Validation if all the additional image stacks are properly defined.
        # The validation is performed in a two steps. First step is pretty
        # simple - length of all command-line based arrays for additional image
        # stack has to be equal.
        lenghts = map(lambda x: len(getattr(self.options, x)), add_stack_fields)
        if len(set(lenghts)) != 1:
            self._logger.error("Provided additional stack information is invalid.")

        # Iterate over all additional images stacks and copy information from
        # command line into an array.
        for stack_index in range(len(self.options.additionalMovingImagesDirectory)):
            # The dictionary below will hold all parameters related do a given
            # stack. Then the dictionary will be appended to an array.
            new_stack = {}
            for field, key in zip(add_stack_fields, add_stack_keys):
                new_stack[key] = getattr(self.options, field)[stack_index]
            self._additional_stacks_settings.append(new_stack)

        # This is really cool: prepare a decicated file object for each
        # additional stack: Iterate over all additional image stacks and create
        # an array of `filename` object holding a file generator of slices
        # belonging to the given stack.
        for stack_index in range(len(self._additional_stacks_settings)):
            # Create and append a filename object:
            self._add_stacks_inputs.append(
                pos_parameters.filename('add_stack_%02d' % stack_index,
                                        str_template='{idx:04d}.nii.gz'))
            # Since the initial filename object has a wrong (or empty)
            # directory name, the directory name has to be overriden with the
            # proper directory name. Note that the slices names are forced
            self._add_stacks_inputs[stack_index].override_dir = \
                self.options.additionalMovingImagesDirectory[stack_index]

    def _reslice_additional_stack(self):
        """
        Reslice the additional images stacks. Note that there is no possibility
        to switch of reslicing the additional image stacks.
        """
        commands = []

        for stack_index in range(len(self._additional_stacks_settings)):
            for sliceNumber in self.options.movingSlicesRange :
                commands.append(
                    self._reslice_additional_multichannel(
                    sliceNumber, stack_index))

        self.execute(commands)

    def _reslice_additional_multichannel(self, slice_index, stack_index):
        """
        :param slice_index: Index of the processed moving slice. Note: moving
        slice index.
        :type slice_index: int

        :param stack_index: Index of the processed additional stack. Note that
        indexing of the additional stacks starts from zreo.
        :type stack_index: int

        :return:  multichannel reslice wrapper.
        :rtype:  :py:class:`command_warp_rgb_slice`
        """
        # Just a pretty alias
        stackSettings = self._additional_stacks_settings[stack_index]

        # Generate a generic reslice wrapper and then customize it
        command = self._get_reslice_wrapper(
            wrapper_type=pos_wrappers.command_warp_rgb_slice,
            moving_filename_generator=self._add_stacks_inputs[stack_index],
            resliced_type=self.f['resliced_add_color'](stack_id=stack_index,idx=slice_index),
            slice_number=slice_index)

        # Note that, in oposition to the moving stack, additional image stacks
        # are to be processed with different settings for each additional
        # images stack.

        # This non-optimal code below describes convert "0" or "1" into
        # boolean value. Sorry for the mess :)
        inversion_flag = [None, True][int(stackSettings['invert_rgb'])]

        command.updateParameters({
            'interpolation': stackSettings['interpolation'],
            'inversion_flag': inversion_flag,
            'background': stackSettings['background']})
        return copy.deepcopy(command)

    def _stack_additional_image_stacks(self):
        for stackIdx in range(len(self._additional_stacks_settings)):
            command = self._get_generic_stack_slice_wrapper(
                self.f['resliced_add_color_mask'](stack_id=stackIdx),
                self.f['out_volume_color_add'](
                    stack_id=stackIdx, fname='output_volume'))
            self.execute(command)

    def _get_parameter_based_output_prefix(self):
        """
        Generate filename prefix base on the provided processing parameters.
        The filename prefix is used when no other naming scheme is provided.
        """

        filename_prefix = "out_"

        filename_prefix += "_FixedResize-%s" % str(self.options.fixedImageResize)
        filename_prefix += "_MovingResize-%s" % str(self.options.movingImageResize)
        filename_prefix += "_fixedColor-%s" % str(self.options.registrationColorChannelFixedImage)
        filename_prefix += "_movingColor-%s" % str(self.options.registrationColorChannelMovingImage)

        try:
            filename_prefix += "_Median-%s" % "x".join(map(str, self.options.medianFilterRadius))
        except:
            filename_prefix += "_Median-None"

        filename_prefix += "_Metric-%s" % self.options.antsImageMetric
        filename_prefix += "_MetricOpt-%d" % self.options.antsImageMetricOpt
        filename_prefix += "_Affine-%s" % str(self.options.useRigidAffine)

        try:
            filename_prefix += "_Median-%s" % "x".join(map(str, self.options.medianFilterRadius))
        except:
            filename_prefix += "_Median-None"

        try:
            filename_prefix += "outROI-%s" % "x".join(map(str, self.options.outputVolumeROI))
        except:
            filename_prefix += "outROI-None"

        return filename_prefix

    @classmethod
    def _getCommandLineParser(cls):
        parser = output_volume_workflow._getCommandLineParser()

        parser.add_option('--fixedImagesDir', default=None,
            type='str', dest='fixedImagesDir', help='')
        parser.add_option('--movingImagesDir', default=None,
            type='str', dest='movingImagesDir', help='')

        parser.add_option('--imagePairsAssignmentFile', default=None,
            type='str', dest='imagePairsAssignmentFile', help='File carrying assignment of a fixed image to corresponding moving image.')
        parser.add_option('--movingSlicesRange', default=None,
            type='int', dest='movingSlicesRange', nargs = 2,
            help='Range of moving slices (for preprocessing). By default the same as fixed slice range.')
        parser.add_option('--fixedSlicesRange', default=None,
            type='int', dest='fixedSlicesRange', nargs = 2,
            help='Range of fixed slices (for preprocessing). By default the same as fixed slice range.')

        parser.add_option('--fixedImageResize',  default=None,
            type='float', dest='fixedImageResize',
            action='store', nargs = 1, help='Resampling ratio (optional). Allows to alter registration speed and accuracy.')
        parser.add_option('--movingImageResize', default=None,
            type='float', dest='movingImageResize',
            action='store', nargs = 1, help='Resampling ratio (optional). Allows to alter registration speed and accuracy.')

        parser.add_option('--registrationColorChannelMovingImage', default='blue',
            type='str', dest='registrationColorChannelMovingImage',
            help='In rgb images - color channel on which \
            registration will be performed. Has no meaning for \
            grayscale input images. Possible values: r/red, g/green, b/blue.')
        parser.add_option('--registrationColorChannelFixedImage', default='red',
            type='str', dest='registrationColorChannelFixedImage',
            help='In rgb images - color channel on which \
            registration will be performed. Has no meaning for \
            grayscale input images. Possible values: r/red, g/green, b/blue.')
        parser.add_option('--resliceInterpolation',
            dest='resliceInterpolation', default=None, type='str',
            help='Cubic Gaussian Linear Nearest Sinc cubic gaussian linear nearest sinc')
        parser.add_option('--resliceBackgorund', default=None,
            type='float', dest='resliceBackgorund',
            help='Background color')
        parser.add_option('--medianFilterRadius', dest='medianFilterRadius',
            default=None, type='int', nargs=2,
            help='Median filter radius in voxels e.g. 2 2')
        parser.add_option('--invertMultichannel', dest='invertMultichannel',
            default=None, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
        parser.add_option('--outputVolumeROI', default=None,
            type='int', dest='outputVolumeROI',  nargs=4,
            help='ROI of the output volume - in respect to registration ROI.')

        parser.add_option('--skipPreprocessing', default=False,
                dest='skipPreprocessing', action='store_const', const=True,
                help='Supress preprocessing images.')
        parser.add_option('--skipGrayReslice', default=False,
                dest='skipGrayReslice', action='store_const', const=True,
                help='Supress generating grayscale volume')
        parser.add_option('--skipColorReslice', default=False,
                dest='skipColorReslice', action='store_const', const=True,
                help='Supress generating RGB volume.')
        parser.add_option('--skipTransformGeneration', default=False,
                dest='skipTranasformGeneration', action='store_const', const=True,
                help='Supress generating transforms.')
        parser.add_option('--skipOutputVolumes', default=False,
                dest='skipOutputVolumes', action='store_const', const=True,
                help='Supress generating volumes.')
        parser.add_option('--outputVolumesDirectory', default=None,
                dest='outputVolumesDirectory', action='store',
                help='Store output volumes in given directory instead of using default one.')

        parser.add_option('--antsImageMetric', default='MI',
                type='str', dest='antsImageMetric',
                help='ANTS image to image metric. See ANTS documentation.')
        parser.add_option('--useRigidAffine', default=False,
                dest='useRigidAffine', action='store_const', const=True,
                help='Use rigid affine transformation. By default affine transformation is used to drive the registration ')
        parser.add_option('--antsImageMetricOpt', default=32,
                type='int', dest='antsImageMetricOpt',
                help='Parameter of ANTS i2i metric.')
        parser.add_option('--transformationsDirectory', default=None,
                dest='transformationsDirectory', action='store',
                help='Store transformations in given directory instead of using default one.')
        parser.add_option('--grayscaleVolumeFilename', default=False,
            dest='grayscaleVolumeFilename', type='str',
            help='Filename for the output grayscale volume')
        parser.add_option('--multichannelVolumeFilename', default=False,
            dest='multichannelVolumeFilename', type='str',
            help='Filename for the output multichannel volume.')

        additionalStackReslice = OptionGroup(parser, 'Settings for reslicing additional image stacks')
        additionalStackReslice.add_option('--additionalMovingImagesDirectory', default=None,
                dest='additionalMovingImagesDirectory', type='str',
                action='append', help='')
        additionalStackReslice.add_option('--additionalInvertMultichannel', default=None,
                dest='additionalInvertMultichannel', type='int',
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


if __name__ == '__main__':
    options, args = pairwiseRegistration.parseArgs()
    se = pairwiseRegistration(options, args)
    se.launch()
