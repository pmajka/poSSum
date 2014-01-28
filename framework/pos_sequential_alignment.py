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

import networkx as nx

from pos_common import flatten
from pos_wrapper_skel import output_volume_workflow
import pos_parameters
import pos_wrappers

"""

Sequential alignment workflow
*****************************

:author: Piotr Majka <pmajka@nencki.gov.pl>
:revision: $Rev$
:date: $LastChangedDate$

`pos_sequential_alignment` -- a sequential alignment script.

This file is part of imaging data integration framework,
a private property of Piotr Majka
(c) Piotr Majka 2011-2013. Restricted, damnit!

Syntax
======

.. highlight:: bash


Summary
-------

A minimum working example of the sequential alignment script ::

    $python pos_sequential_alignment.py \
    [start stop ref] --sliceRange 50 70 60 \
    [directory]      --inputImageDir <directory_name>


Assumptions according the input images
--------------------------------------

All the input images are expected to be in one of the formats described below:

    1) Three channel, 8-bit per channel RGB image in NIFTII format.
    2) Single channel 8-bit (0-255) image, for instance a 8-bit grayscale image
    in NIFTII format.

No other input image type is supported, trying to apply any other image
specification will surely cause errors. Obviously, the spacing as well as the
image origin and directions does matter. All transformations are generated
based on the input images reference system thus, the best way is to supply
Nifti files as the input images.


Input images naming scheme
--------------------------

 - Images in order
 - Continous naming
 - Reference slice.

python pos_sequential_alignment.py \
        --inputImageDir /home/pmajka/Downloads/cb_test/ \
        --sliceRange 10 120 60 -d /dev/shm/x/ \
        --loglevel DEBUG \
        --registrationColor blue \
        --medianFilterRadius 4 4 \
        --resliceBackgorund 255 \
        --skipSourceSlicesGeneration \
        --useRigidAffine \
        --skipTransformations \
        --skipReslice \
        --outputVolumeSpacing 0.02 0.02 0.06 \
        --outputVolumesDirectory ~/Downloads/cb_test
"""


class sequential_alignment(output_volume_workflow):
    """
    """

    _f = {
        'raw_image': pos_parameters.filename('raw_image', work_dir='00_override_this', str_template='{idx:04d}.nii.gz'),
        'src_gray': pos_parameters.filename('src_gray', work_dir='00_source_gray', str_template='{idx:04d}.nii.gz'),
        'src_color': pos_parameters.filename('src_color', work_dir='01_source_color', str_template='{idx:04d}.nii.gz'),
        'part_naming': pos_parameters.filename('part_naming', work_dir='02_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_'),
        'part_transf': pos_parameters.filename('part_transf', work_dir='02_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_Affine.txt'),
        'comp_transf': pos_parameters.filename('comp_transf', work_dir='02_transforms', str_template='ct_m{mIdx:04d}_f{fIdx:04d}_Affine.txt'),
        'comp_transf_mask': pos_parameters.filename('comp_transf_mask', work_dir='02_transforms', str_template='ct_*_Affine.txt'),
        'resliced_gray': pos_parameters.filename('resliced_gray', work_dir='04_gray_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_gray_mask': pos_parameters.filename('resliced_gray_mask', work_dir='04_gray_resliced', str_template='%04d.nii.gz'),
        'resliced_color': pos_parameters.filename('resliced_color', work_dir='05_color_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_color_mask': pos_parameters.filename('resliced_color_mask', work_dir='05_color_resliced', str_template='%04d.nii.gz'),
        'out_volume_gray': pos_parameters.filename('out_volume_gray', work_dir='06_output_volumes', str_template='{fname}_gray.nii.gz'),
        'out_volume_color': pos_parameters.filename('out_volume_color', work_dir='06_output_volumes', str_template='{fname}_color.nii.gz'),
        'transform_plot': pos_parameters.filename('transform_plot', work_dir='06_output_volumes', str_template='{fname}.png'),
        'transform_report': pos_parameters.filename('transform_report', work_dir='06_output_volumes', str_template='{fname}.txt'),
        'graph_edges': pos_parameters.filename('graph_edges', work_dir='06_output_volumes', str_template='graph_edges_{sign}.csv'),
        'similarity': pos_parameters.filename('similarity', work_dir='06_output_volumes', str_template='similarity_{sign}.csv'),
         }

    _usage = ""

    # Define the magic numbers:
    __AFFINE_ITERATIONS = [10000, 10000, 10000, 10000, 10000]
    __DEFORMABLE_ITERATIONS = [0]
    __IMAGE_DIMENSION = 2
    __HISTOGRAM_MATCHING = True
    __MI_SAMPLES = 16000
    __ALIGNMENT_EPSILON = 4
    __VOL_STACK_SLICE_SPACING = 1

    def _initializeOptions(self):
        super(self.__class__, self)._initializeOptions()

        # Yes, it is extremely important to provide the slicing range.
        assert self.options.sliceRange, \
            self._logger.error("Slice range parameters (`--sliceRange`) are required. Please provide the slice range. ")

        # Define slices' range. All slices within given range will be
        # processed. Make sure that all images are available.
        self.options.slice_range = \
            range(self.options.sliceRange[0], self.options.sliceRange[1] + 1)

        # Verify if the reference slice index is provided and if ti is correct.
        # The reference slice index cannot be the same as either the starting
        # and the last slice index. This will cause an error.
        assert self.options.sliceRange[0] < self.options.sliceRange[2] and \
            self.options.sliceRange[2] < self.options.sliceRange[1], \
            self._logger.error("Incorrect reference slice index. The reference slice index has to be larger than the first slice index and smaller than the last slice index.")

        # Validate, if an input images directory is provided,
        # Obviously, we need to load the images in order to process them.
        assert self.options.inputImageDir, \
            self._logger.error("No input images directory is provided. Please provide the input images directory (--inputImageDir)")

        # Verify, if the provided image-to-image metric is provided.
        assert self.options.antsImageMetric.lower() in ['mi', 'cc', 'msq'], \
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
            self.f['comp_transf_mask'].override_dir = \
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
            self.f['transform_report'].override_dir = \
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
        # directory and all the input images exist. Note that the input image
        # inspection is performed in case of performing the actual
        # computations. In case of trial runs, no validation if performed.
        if self.options.dryRun is not True:
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

        # Composite transformations take relatively small amount of time to
        # compute:
        self._calculate_composite_transforms()

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

        self._plot_transformations()

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def _inspect_input_images(self):
        """
        Verify if all the files are availabe: All images have to be ailable. If
        the case is different, the workflow will not proceed and the user will
        be asked to supply the missing images.
        """
        self._logger.debug("Inspecting if all the input images are available.")

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

        # Iterate over all the slices and prepare aproperiate slice preparation
        # commands.
        for slice_number in self.options.slice_range:
            command = pos_wrappers.alignment_preprocessor_wrapper(
                input_image=self.f['raw_image'](idx=slice_number),
                grayscale_output_image=self.f['src_gray'](idx=slice_number),
                color_output_image=self.f['src_color'](idx=slice_number),
                registration_roi=self.options.registrationROI,
                registration_resize=self.options.registrationResize,
                registration_color=self.options.registrationColor,
                median_filter_radius=self.options.medianFilterRadius,
                invert_multichannel=self.options.invertMultichannel)
            commands.append(copy.deepcopy(command))

        self._logger.info("Executing the source slice generation commands.")
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
        self._logger.info("Executing the transformation commands.")
        self.execute(commands)

    def _calculate_composite_transforms(self):
        """
        Calculates the composite transformations which means transformations
        linking the reference slice with the processed one.
        """

        self._calculate_similarity()
        # Finally, calculate composite transforms
        commands = []
        for moving_slice_index in self.options.slice_range:
            commands.append(self._calculate_composite(moving_slice_index))
        self.execute(commands)

        self._logger.info("Done with calculating the transformations.")

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

        # Array holding pairs of transformations between which the
        # transformations will be calculated.
        retDict = []
        epsilon = self.options.graphEdgeEpsilon

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

        :return: Registration command wrapper.
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

        # TODO: correct all true / false switches!
        use_rigid_transformation = str(self.options.useRigidAffine).lower()

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

    def _calculate_similarity(self):
        """
        Calculate similarities between images for which the transformations
        were computed. Based on the similarity measures, a graph connecting
        individual images is created as saves for further calculations.

        The higher the lambda, the more reluctant the slice skipping is.
        """
        self._logger.info("Calculating the similarity between images.")

        # Create a helper function to simplify the loops below:
        def get_wrapper(fdx, mdx):
            wrapper = pos_wrappers.image_similarity_wrapper(
                reference_image= self.f['src_gray'](idx=fdx),
                moving_image = self.f['src_gray'](idx=mdx),
                affine_transformation = self.f['part_transf'](mIdx=mdx,fIdx=fdx))
            return copy.copy(wrapper)

        commands = [] # Will hold commands for calculating the similarity

        # Will hold (moving, fixed) images partial_transforms basically: all
        # partial transformations array
        partial_transforms = []

        self._logger.debug("Generating similarity measure warppers.")
        for moving_slice in self.options.slice_range:
            # Get all fixed images to which given moving slice will be aligned:
            tpair = list(flatten(self._get_slice_pair(moving_slice)))

            # Append partial transformations for given moving slice to the
            # global partial transformations array
            partial_transforms.append(tpair)

            # Generate wrapper for measuring similarity for a given partial
            # transformation.
            for mdx, fdx in tpair:
                commands.append(get_wrapper(fdx, mdx))

        # Execute and commands and process the similarity measurements.
        stdout, stderr = self.execute(commands)
        simmilarity = map(lambda x: float(x.strip()),
                          stdout.strip().split("\n"))
        simmilarity = dict(zip(flatten(partial_transforms), simmilarity))

        self._logger.debug("Generating graph edges.")
        graph_connections = []

        # Lambda defines slice skipping is preffered (lower l), or reluctant
        # to slice skipping (higher)
        l = self.options.graphEdgeLambda

        for (mdx, fdx), s in simmilarity.iteritems():
            w = (1.0 + s) * abs(mdx-fdx) * (1.0 + l)**(abs(mdx-fdx))
            graph_connections.append((fdx, mdx, w))

        self._logger.info("Creating a graph based on image similarities.")
        # Generate the graph basen on the weight of the edges
        self.G = nx.DiGraph()
        self.G.add_weighted_edges_from(graph_connections)

        self._logger.debug("Saving the graph to a file.")
        # Save the edges for some further analysis.
        nx.write_weighted_edgelist(self.G,
            self.f['graph_edges'](sign=self.signature))

        # Also, save the individual similarity metrics:
        simm_fh = open(self.f['similarity'](sign=self.signature), 'w')
        for (mdx, fdx), s in sorted(simmilarity.iteritems()):
            simm_fh.write("%d %d %f\n" % (mdx, fdx, s))
        simm_fh.close()

    def _get_transformation_chain(self, moving_slice_index):
        """
        Generate transformation chain based on the Dijkstra's shortest path
        algorithm.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int

        :return: chain of partial transformations connecting
                 given moving slice with the reference image
        :rtype: array
        """

        i = moving_slice_index
        s, e, r = tuple(self.options.sliceRange)

        # Calculate shortest paths between individual slices
        slice_paths = nx.all_pairs_dijkstra_path(self.G)

        # Get the shortest path linking given moving slice with the reference
        # slice.
        path = list(reversed(slice_paths[r][i]))
        chain = []

        # In case we hit a reference slice :)
        if i == r:
            chain.append((r, r))

        # For all the other cases collect partial transforms.
        for step in range(len(path) - 1):
            chain.append((path[step], path[step + 1]))

        return chain

    def _calculate_composite(self, moving_slice_index):
        """
        Composes individual partial transformations into composite
        transformation registering provided moving slice to the reference
        image.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int
        """

        # The transformation chain is a sequence of pairs of (fixed, moving)
        # slices. This sequence links the reference slices with given moving
        # slice.
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
        grayscale and multichannel images are resliced. Also reslicing of both
        volumes can be switched of when required - but this is set somewhere
        else :)
        """

        # Reslicing grayscale images.  Reslicing multichannel images. Collect
        # all reslicing commands into an array and then execute the batch.
        self._logger.info("Reslicing grayscale images.")
        commands = []
        for slice_index in self.options.slice_range:
            commands.append(self._reslice_grayscale(slice_index))
        self.execute(commands)

        # Reslicing multichannel images. Again, collect all reslicing commands
        # into an array and then execute the batch.
        self._logger.info("Reslicing multichannel images.")
        commands = []
        for slice_index in self.options.slice_range:
            commands.append(self._reslice_color(slice_index))
        self.execute(commands)

        # Yeap, it's done.
        self._logger.info("Finished reslicing.")

    def _reslice_grayscale(self, slice_number):
        """
        Reslice grayscalce slice of the index `slice_number`.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int

        :return: Command for reslicing given slice with the calculated
                 transform.
        :rtype: `pos_wrappers.command_warp_grayscale_image`
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
        command = pos_wrappers.command_warp_grayscale_image(
            reference_image = reference_image_filename,
            moving_image = moving_image_filename,
            transformation = transformation_file,
            output_image = resliced_image_filename,
            background = self.options.resliceBackgorund,
            interpolation = self.options.resliceInterpolation,
            region_origin = region_origin_roi,
            region_size = region_size_roi)
        return copy.deepcopy(command)

    def _reslice_color(self, slice_number):
        """
        Reslice multichannel image with the given `slice_number`.

        :param moving_slice_index: moving slice index
        :type moving_slice_index: int

        :return: Command for reslicing given slice with the calculated
                 transform.
        :rtype: `pos_wrappers.command_warp_grayscale_image`
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
        command = pos_wrappers.command_warp_rgb_slice(
            reference_image = reference_image_filename,
            moving_image = moving_image_filename,
            transformation = transformation_file,
            output_image = resliced_image_filename,
            region_origin = region_origin_roi,
            region_size = region_size_roi,
            background = self.options.resliceBackgorund,
            interpolation = self.options.resliceInterpolation,
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
        Return generic command wrapper suitable either for stacking
        grayscale images or multichannel images. Aproperiate command line
        wrapper is returned depending on provided `mask_type` and
        `output_filename_type`.  The command line wrapper is prepared mostly
        based on the command line parameters which are common between both
        images stacks thus so there is no need to parametrize them
        individually.

        :param mask_type: mask type determining which images stack will be
                          converted into a volume.
        :type mask_type: str

        :param ouput_filename_type: output filename naming scheme.
        :type ouput_filename_type: str
        """

        # Assign some usefull aliases.
        start, stop, reference = self.options.sliceRange

        # Define the output volume filename. If no custom colume name is
        # provided, the filename is based on the provided processing
        # parameters. In the other case the provided custom filename is used.
        output_filename = self.f[ouput_filename_type](fname=self.signature)

        # Define the warpper according to the provided settings.
        command = pos_wrappers.stack_and_reorient_wrapper(
            stack_mask=self.f[mask_type](),
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

        # Return the created parser.
        return copy.deepcopy(command)

    def _stack_output_images(self):
        """
        Execute stacking images based on grayscale and multichannel images.
        Both resliced image stacks are turned into volumetric files by this
        method.
        """

        self._logger.info("Stacking the grayscale image stack.")
        command = self._get_generic_stack_slice_wrapper(
                    'resliced_gray_mask', 'out_volume_gray')
        self.execute(command)

        self._logger.info("Stacking the multichannel image stack.")
        command = self._get_generic_stack_slice_wrapper(
                    'resliced_color_mask', 'out_volume_color')
        self.execute(command)

        self._logger.info("Reslicing is done.")

    def _get_parameter_based_output_prefix(self):
        """
        Generate filename prefix base on the provided processing parameters.
        The filename prefix is used when no other naming scheme is provided.
        """

        # As you can see the generation of the output filename prefix is
        # straigthforward but pretty tireingsome.
        filename_prefix = "sequential_alignment_"

        filename_prefix += "s-%d_e-%d_r-%d_" % tuple(self.options.sliceRange)

        try:
            filename_prefix += "ROI-%s" % "x".join(map(str, self.options.registrationROI))
        except:
            filename_prefix += "ROI-None"

        try:
            filename_prefix += "_Resize-%s" % "x".join(map(str, self.options.registrationResize))
        except:
            filename_prefix += "_Resize-None"

        filename_prefix += "_Color-%s" % self.options.registrationColor

        try:
            filename_prefix += "_Median-%s" % "x".join(map(str, self.options.medianFilterRadius))
        except:
            filename_prefix += "_Median-None"

        filename_prefix += "_Metric-%s" % self.options.antsImageMetric
        filename_prefix += "_MetricOpt-%d" % self.options.antsImageMetricOpt
        filename_prefix += "_Affine-%s" % str(self.options.useRigidAffine)

        filename_prefix += "_eps-%d_lam%02.2f" % \
            (self.options.graphEdgeEpsilon, self.options.graphEdgeLambda)

        try:
            filename_prefix += "outROI-%s" % "x".join(map(str, self.options.outputVolumeROI))
        except:
            filename_prefix += "outROI-None"

        return filename_prefix

    signature = property(_get_parameter_based_output_prefix)

    def _plot_transformations(self):
        """
        Plots the calculated composed transformations.
        """

        # Define and execute the transformation plotting script.
        command = pos_wrappers.rigid_transformations_plotter_wapper(
            signature=self.signature,
            report_filename=self.f['transform_report'](fname=self.signature),
            plot_filename=self.f['transform_plot'](fname=self.signature),
            transformation_mask=self.f['comp_transf_mask']())
        self.execute(command)

    @classmethod
    def _getCommandLineParser(cls):
        """
        """
        parser = output_volume_workflow._getCommandLineParser()

        obligatory_options = OptionGroup(parser, 'Obligatory pipeline options.')
        obligatory_options.add_option('--sliceRange', default=None,
            type='int', dest='sliceRange', nargs=3,
            help='Slice range: start, stop, reference. Requires three integers.')
        obligatory_options.add_option('--inputImageDir', default=None,
            type='str', dest='inputImageDir',
            help='The directory from which the input slices will be read. The directory has to contain images named according to "%04d.nii.gz" scheme.')

        workflow_options = OptionGroup(parser, 'Pipeline options.')
        workflow_options.add_option('--outputVolumesDirectory', default=False,
            dest='outputVolumesDirectory', type="str",
            help='Directory to which registration results will be sored.')
        workflow_options.add_option('--grayscaleVolumeFilename', default=False,
            dest='grayscaleVolumeFilename', type='str',
            help='Filename for the output grayscale volume.')
        workflow_options.add_option('--multichannelVolumeFilename', default=False,
            dest='multichannelVolumeFilename', type='str',
            help='Filename for the output multichannel volume.')
        workflow_options.add_option('--transformationsDirectory', default=False,
            dest='transformationsDirectory', type="str",
            help='Use provided transformation directory instead of the default one.')
        workflow_options.add_option('--skipTransformations', default=False,
            dest='skipTransformations', action='store_const', const=True,
            help='Supress transformation calculation')
        workflow_options.add_option('--skipSourceSlicesGeneration', default=False,
            dest='skipSourceSlicesGeneration', action='store_const', const=True,
            help='Supress generation of the source slices')
        workflow_options.add_option('--skipReslice', default=False,
            dest='skipReslice', action='store_const', const=True,
            help='Supress generating grayscale volume')
        workflow_options.add_option('--skipOutputVolumes', default=False,
            dest='skipOutputVolumes', action='store_const', const=True,
            help='Supress generating color volume')
        workflow_options.add_option('--resliceBackgorund', default=None,
            type='float', dest='resliceBackgorund',
            help='Background color')
        workflow_options.add_option('--resliceInterpolation',
            dest='resliceInterpolation', default=None, type='choice',
            choices=['Cubic','Gaussian','Linear','Nearest','Sinc','cubic'],
            help='Interpolation during applying the transforms to individual slices.')

        registration_options = OptionGroup(parser, 'Options driving the registration process.')
        registration_options.add_option('--registrationROI', dest='registrationROI',
            default=None, type='int', nargs=4,
            help='ROI of the input image used for registration (ox, oy, sx, sy).')
        registration_options.add_option('--registrationResize', dest='registrationResize',
            default=None, type='float',
            help='Scaling factor for the source image used for registration. Float between 0 and 1.')
        registration_options.add_option('--registrationColor',
            dest='registrationColor', default='blue', type='choice',
            choices=['r','g','b','red','green','blue'],
            help='In rgb images - color channel on which \
            registration will be performed. Has no meaning for \
            grayscale input images. Possible values: r/red, g/green, b/blue.')
        registration_options.add_option('--medianFilterRadius', dest='medianFilterRadius',
            default=None, type='int', nargs=2,
            help='Median filter radius in voxels e.g. 2 2')
        registration_options.add_option('--invertMultichannel', dest='invertMultichannel',
            default=None, action='store_const', const=True,
            help='Invert source image: both, grayscale and multichannel, before registration')
        registration_options.add_option('--outputVolumeROI', default=None,
            type='int', dest='outputVolumeROI',  nargs=4,
            help='ROI of the output volume - in respect to registration ROI.')
        registration_options.add_option('--antsImageMetric', default='MI',
            type='choice', dest='antsImageMetric', choices=['MI','CC','MSQ'],
            help='ANTS affine image to image metric. Three values are allowed: CC, MI, MSQ.')
        registration_options.add_option('--antsImageMetricOpt', default=32,
            type='int', dest='antsImageMetricOpt',
            help='Parameter of ANTS i2i metric. Makes a sense only when provided metric can be customized.')
        registration_options.add_option('--useRigidAffine', default=False,
            dest='useRigidAffine', action='store_const', const=True,
            help='Use rigid affine transformation.')
        registration_options.add_option('--graphEdgeLambda', default=0.0,
            dest='graphEdgeLambda', action='store', type="float",
            help='Provedes lambda value for the graph edges generation.')
        registration_options.add_option('--graphEdgeEpsilon', default=1,
            dest='graphEdgeEpsilon', action='store', type="int",
            help='Provedes epsilon value for the graph edges generation.')

        parser.add_option_group(obligatory_options)
        parser.add_option_group(registration_options)
        parser.add_option_group(workflow_options)

        return parser

if __name__ == '__main__':
    options, args = sequential_alignment.parseArgs()
    process = sequential_alignment(options, args)
    process.launch()
