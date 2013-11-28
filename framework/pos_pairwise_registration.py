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

import os, sys, glob
import datetime, logging
import csv
from optparse import OptionParser, OptionGroup
from pos_wrapper_skel import output_volume_workflow
import pos_wrappers, pos_parameters

# -----------------------------------------------
# Directory template update
# -----------------------------------------------

CLASS_SPECIFC_DIR_TEMPLATES = {
            'processing_group_dir'      : '70_blockface_to_histology_registration',
            'fixed_images_raw'  : '67_blockface_coronal',
            'moving_images_raw' : '66_histology_extracted_slides',
            'fixed_images_prep' : '01_fixed_prep',
            'moving_images_prep': '02_moving_prep',
            'fixed_images_src'  : '03_fixed_src',
            'moving_images_src' : '04_moving_src',
            'transforms'        : '07_transforms',
            'gray_resliced'     : '08_resliced_gray',
            'color_resliced'    : '09_resliced_rgb',
            'outputVolumes'     : '10_output_volumes',
            'misc'              : '11_misc',
            'additional_prep'   : '12_additional_prep',
            'additional_src'    : '13_additional_src',
            'additional_gray'   : '18_additional_gray',
            'additional_rgb'    : '19_additional_rgb'}

CLASS_SPECIFC_LOCAL_DIRS = \
        ['transforms', 'outputVolumes', 'misc']

CLASS_SPECIFC_PROCESS_DIRS = \
        ['fixed_images_prep', 'moving_images_prep',
         'fixed_images_src',
         'moving_images_src','transforms', 'gray_resliced',
         'color_resliced', 'misc','outputVolumes',
         'additional_prep', 'additional_src', 'additional_gray',
         'additional_rgb']

# -----------------------------------------------
# Command templates
# -----------------------------------------------
COMMAND_GENERATE_PREPROCESS = \
        """convert \
        %(inputImage)s \
        %(invertSourceImage)s \
        %(medianFilterRadius)s \
        -depth 8 -type TrueColor -colorspace RGB\
        %(outputImage)s"""

COMMAND_C2D_PREPARE_IMAGE = \
        """c2d -verbose %(inputImage)s \
        -spacing %(spacing)smm \
        -interpolation Cubic -resample %(resample)s%% \
        -type ushort \
        -o %(outputImage)s"""

COMMAND_C2D_PREPARE_MULTICHANNEL_IMAGE = \
        """c2d -verbose -mcs %(inputImage)s -popas blue -popas green -popas red \
        -clear -push %(imageChannel)s \
        -spacing %(spacing)smm \
        %(interpolation)s \
        -resample %(resample)s%% \
        -o %(outputImage)s"""

COMMAND_ANTS_GENERATE_TRANSFORM = \
    """ANTS 2 -v -m %(metric)s[%(fixedImage)s,%(movingImage)s,1,%(mp)s] \
        --affine-metric-type %(metric)s \
        -o %(outputTransformFn)s \
        -i 0 \
        --use-Histogram-Matching \
        --number-of-affine-iterations 10000x10000x10000x10000x10000 \
        --rigid-affine %(rigidAffineSetting)s \
        %(addAntsParam)s"""

COMMAND_WARP_GRAYSCALE_SLICE = \
    """c2d -verbose \
            %(fixedImage)s  -as ref -clear \
            %(movingImage)s -as moving \
            -push ref -push moving %(backgroundValue)s %(interpolation)s -reslice-itk %(transformFilename)s \
            -o %(outputImage)s"""

COMMAND_WARP_RGB_SLICE_FROM_SOURCE = \
    """c2d -verbose \
        %(fixedImage)s -popas F \
        -mcs %(movingImage)s \
             -foreach \
                    -insert F 1 \
                    -spacing %(spacing)smm \
                    %(interpolation)s \
                    %(backgroundValue)s \
                    -resample %(resample)s%% \
                    %(invertImage)s \
                    -reslice-itk %(transformFilename)s \
                    %(invertImage)s \
             -endfor \
        -omc 3 %(outputImage)s"""

class pairwiseRegistration(output_volume_workflow):
    """
    Pairwise slice to slice registration script.
    """

    _f = {
        'raw_image' : pos_parameters.filename('raw_image', work_dir = '00_override_this', str_template = '{idx:04d}.nii.gz'),

        'src_gray' : pos_parameters.filename('src_gray', work_dir = '00_source_gray', str_template='{idx:04d}.nii.gz'),
        'src_color' : pos_parameters.filename('src_color', work_dir = '01_source_color', str_template='{idx:04d}.nii.gz'),
        'additional_gray' : pos_parameters.filename('additional_gray', work_dir = '00_additional_gray', str_template='{idx:04d}.nii.gz'),
        'additional_color' : pos_parameters.filename('additional_color', work_dir = '01_additional_color', str_template='{idx:04d}.nii.gz'),

        'transf_naming' : pos_parameters.filename('transf_naming', work_dir = '11_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_'),
        'transf_file' : pos_parameters.filename('transf_file', work_dir = '12_transforms', str_template='tr_m{mIdx:04d}_f{fIdx:04d}_Affine.txt'),

        'resliced_gray' : pos_parameters.filename('resliced_gray', work_dir = '21_gray_resliced', str_template='{idx:04d}.nii.gz'),
        'resliced_gray_mask' : pos_parameters.filename('resliced_gray_mask', work_dir = '22_gray_resliced', str_template='%04d.nii.gz'),
        'resliced_color' : pos_parameters.filename('resliced_color', work_dir = '23_resliced_color', str_template='{idx:04d}.nii.gz'),
        'resliced_color_mask' : pos_parameters.filename('resliced_color_mask', work_dir = '24_resliced_color_mask', str_template='%04d.nii.gz'),
        'resliced_add_gray' : pos_parameters.filename('resliced_add_gray', work_dir = '25_resliced_add_gray', str_template='{idx:04d}.nii.gz'),
        'resliced_add_gray_mask' : pos_parameters.filename('resliced_add_gray_mask', work_dir = '26_resliced_add_gray_mask', str_template='%04d.nii.gz'),
        'resliced_add_color' : pos_parameters.filename('resliced_add_color', work_dir = '27_resliced_add_color', str_template='{idx:04d}.nii.gz'),
        'resliced_add_color_mask' : pos_parameters.filename('resliced_add_color_mask', work_dir = '28_resliced_add_color_mask', str_template='%04d.nii.gz'),

        'out_volume_gray' : pos_parameters.filename('out_volume_gray', work_dir = '31_output_volumes', str_template='{fname}_gray.nii.gz'),
        'out_volume_color' : pos_parameters.filename('out_volume_color', work_dir = '32_output_volumes', str_template='{fname}_color.nii.gz'),
        'out_volume_gray_add' : pos_parameters.filename('out_volume_gray_add', work_dir = '33_output_volumes', str_template='{fname}_gray.nii.gz'),
        'out_volume_color_add' : pos_parameters.filename('out_volume_color_add', work_dir = '34_output_volumes', str_template='{fname}_color.nii.gz')
         }

    def _validate_options(self):
        super(self.__class__, self)._initializeOptions()

        # Yes, it is extremely important to provide the slicing range.
        assert self.options.sliceRange, \
            self._logger.error("Slice range parameters (`--sliceRange`) are required. Please provide the slice range. ")

        # Validate, if an input images directory is provided,
        # Obviously, we need to load the images in order to process them.
        assert self.options.inputImageDir, \
            self._logger.error("No input images directory is provided. Please provide the input images directory (--inputImageDir)")

#       # Verify, if the provided image-to-image metric is provided.
#       assert self.options.antsImageMetric.lower() in ['mi','cc','msq'], \
#           self._logger.error("Provided image-to-image metric name is invalid. Three image-to-image metrics are allowed: MSQ, MI, CC.")

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
        if not image_pairs_filename :
            self._logger.debug(
            "No slice assignment file was provided. Using pairwise assignment.")
            self._slice_assignment = \
                dict(zip(self.options.movingSlicesRange,
                         self.options.fixedSlicesRange))
        else:
            # Here I use pretty neat code snipper for determining the
            # dialect of teh csv file. Found at:
            # http://docs.python.org/2/library/csv.html#csv.Sniffer
            self._logger.debug(\
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
            fixed_slice_index = self._slice_assignment[slice_index]
            if fixed_slice_index is None:
                self._logger.error("No fixed slice index defined for the moving slice %d.",
                                   slice_index)
                sys.exit(1)

        self._logger.debug("Mappings and slices' ranges passed the validation.")

    def _overrideDefaults(self):
        super(self.__class__, self)._overrideDefaults()

        # At the very beginning override the default dummy input images
        # directory by the actual images directory.
        self.f['raw_image'].override_dir = self.options.inputImageDir

    def _inspect_input_images(self):
        """
        Verify if all the files are availabe: All images have to be ailable. If
        the case is different, the workflow will not proceed and the user will
        be asked to supply the missing images.
        """
        # TODO: Consider veryfying additinal slices as well

        # Iterate over all filenames and check if the file exists.
        for slice_index in self.options.movingSlicesRange:
            slice_filename = self.f['raw_image'](idx=slice_index)

            self._logger.debug("Checking for image: %s.", slice_filename)
            if not os.path.isfile(slice_filename):
                self._logger.error("File does not exist: %s. Exiting",
                                   slice_filename)
                sys.exit(1)

    def _generate_slice_index(self):
        """
        Generate moving image to fixed image mappings.
        """

        # Range of images to register. It is a perfect solution to override the
        # command line argument option with some other value, but hey -
        # nobody's perfect.
        self._logger.debug("Defining default slicing range.")
        self.options.sliceRange = \
                range(self.options.sliceRange[0], self.options.sliceRange[1] + 1)

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
        if self.options.movingSlicesRange != None:
            self.options.movingSlicesRange = \
                range(self.options.movingSlicesRange[0],
                      self.options.movingSlicesRange[1] + 1)
            self._logger.debug("Using custom moving slice range.")
        else:
            self.options.movingSlicesRange = self.options.sliceRange
            self._logger.debug("Using default slice range as fixed slice range.")

        # Check if custom fixes slice range is provided.
        # If it's not, use the default slice range.
        if self.options.fixedSlicesRange != None:
            self.options.fixedSlicesRange = \
                range(self.options.fixedSlicesRange[0],
                      self.options.fixedSlicesRange[1] + 1)
            self._logger.debug("Using custom fixed slice range.")
        else:
            self.options.fixedSlicesRange = self.options.sliceRange
            self._logger.debug("Using default slice range as moving slice range.")


    def launch(self):
        self._load_slice_assignment()

        # After proving that the mappings are correct, the script verifies if
        # the files to be coregistered do actually exist. However, the
        # verification is performed only when the script is executed in not in
        # `--druRun` mode:
        if self.options.dryRun is False:
            self._inspect_input_images()

    def _generates_source_slices(self):
        self._generate_fixed_slices()
        self._generate_moving_slices()

    def _get_generic_source_slice_preparation_wrapper(self):
        """
        Get generic slice preparation wrapper for further refinement.
        """
        command = pos_wrappers.alignment_preprocessor_wrapper(
            input_image = self.f['raw_image'](idx=slice_number),
            grayscele_output_image = self.f['src_gray'](idx=slice_number),
            color_output_image = self.f['src_color'](idx=slice_number),
            registration_color = self.options.registrationColor,
            median_filter_radius = self.options.medianFilterRadius,
            invert_grayscale = self.options.invertGrayscale,
            invert_multichannel = self.options.invertMultichannel)
        return copy.deepcopy(command)

    def _generate_fixed_slices(self):
        self._logger.info("Performing fixed slices generation.")

        # The array collecting all the individual command into a commands
        # batch.
        commands = []

        for slice_number in self._slice_assignment.values():

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

        # Execute the commands in a batch.
        self.execute(commands)

        self._logger.info("Fixed slices generation is completed.")

    def _generate_moving_slices(self):
        self._logger.info("Performing fixed slices generation.")

        # The array collecting all the individual command into a commands
        # batch.
        commands = []

        for slice_number in self._slice_assignment.values():

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

        # Execute the commands in a batch.
        self.execute(commands)

        self._logger.info("Fixed slices generation is completed.")


    @classmethod
    def _getCommandLineParser(cls):
        parser = output_volume_workflow._getCommandLineParser()

        parser.add_option('--inputImageDir', default=None,
            type='str', dest='inputImageDir', help='')

        parser.add_option('--imagePairsAssignmentFile', default=None,
            type='str', dest='imagePairsAssignmentFile', help='File carrying assignment of a fixed image to corresponding moving image.')
        parser.add_option('--sliceRange', default=None, nargs = 2,
            type='int', dest='sliceRange',
            help='Index of the first and last slice of the stack')
        parser.add_option('--movingSlicesRange', default=None,
            type='int', dest='movingSlicesRange', nargs = 2,
            help='Range of moving slices (for preprocessing). By default the same as fixed slice range.')
        parser.add_option('--fixedSlicesRange', default=None,
            type='int', dest='fixedSlicesRange', nargs = 2,
            help='Range of fixed slices (for preprocessing). By default the same as fixed slice range.')

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

        return parser


#       if self.options['skipGeneratingSourceSlices'] == False:
#           self._generateSourceSlices()

#       if self.options['skipGeneratingTransforms'] == False:
#           self._calculateTransforms()

#       self._reslice()
#       self._mergeOutput()

#       self._loadAdditionalStacksResliceSettings()

#       if self.options['additionalMovingImagesDirectory'] != None:
#           self._loadAdditionalStacksResliceSettings()
#           self._runAdditionalReslice()


#   class BlockfaceHistologuLinearRegistration(posProcessingElement):
#       posProcessingElement._dirTemplates.update(CLASS_SPECIFC_DIR_TEMPLATES)

#       _localDirectories = \
#           dict([('local_' + k, k) for k in
#           CLASS_SPECIFC_LOCAL_DIRS])

#       _processingDirectories = \
#           dict([('process_' + k, posProcessingElement._dirTemplates[k]) for k in
#           CLASS_SPECIFC_PROCESS_DIRS])

#       __specificConstants = {
#               'FIXED_RAW'   : 'FIXED_RAW',
#               'MOVING_RAW'  : 'MOVING_RAW',
#               'FIXED_PRE'   : 'FIXED_PRE',
#               'MOVING_PRE'  : 'MOVING_PRE',
#               'FIXED_SRC'   : 'FIXED_SRC',
#               'MOVING_SRC'  : 'MOVING_SRC',
#               'ADD_RAW'     : 'ADD_RAW',
#               'ADD_SRC'     : 'ADD_SRC',
#               'ADD_PRE'     : 'ADD_PRE',
#               'ADD_RESLICED': 'ADD_RESLICED',
#               'ADD_RGB_RESLICED':'ADD_RGB_RESLICED',
#               'TRANSFORM'   : 'TRANSFORM',
#               'RESLICED'    : 'RESLICED',
#               'RESLICED_A'    : 'RESLICED_A',
#               'RESLICED_RGB'       : 'RESLICED_RGB',
#               'RESLICED_RGB_A'       : 'RESLICED_RGB_A',
#               'RESLICED_MASK'      : 'RESLICED_MASK',
#               'RESLICED_MASK_A'      : 'RESLICED_MASK_A',
#               'RESLICED_RGB_MASK'  : 'RESLICED_RGB_MASK',
#               'RESLICED_RGB_MASK_A'  : 'RESLICED_RGB_MASK_A',
#               'RESLICED_A'    : 'RESLICED_A',
#               'OUT_VOL_RGB'   : 'OUT_VOL_RGB',
#               'OUT_VOL_GS'    : 'OUT_VOL_GS',
#               'OUT_VOL_RGB_A' : 'OUT_VOL_RGB_A',
#               'OUT_VOL_GS_A'  : 'OUT_VOL_GS_A',
#               'FN_TPL_PRE'    : '%04d.png',
#               'FN_TPL_RAW_GS_M'    : '%04d.png',
#               'FN_TPL_RAW_GS_F'    : '%04d.png',
#               'FN_TPL_RAW_GS_A'    : '%04d.png',
#               'FN_TPL_SRC_GS'      : '%04d.nii.gz',
#               'FN_TPL_SRC_GS_A'    : '%04d.nii.gz',
#               'FN_TPL_RESL_GS'     : '%04d.nii.gz',
#               'FN_TPL_RESL_GS_A'   : '%04d.nii.gz',
#               'FN_TPL_RESL_RGB'    : '%04d.nii.gz',
#               'FN_TPL_RESL_RGB_A'  : '%04d.nii.gz',
#               'FN_TPL_RESL_GS_MASK'  : '*.nii.gz',
#               'FN_TPL_RESL_GS_MASK_A'  : '*.nii.gz',
#               'FN_TPL_LIN_TRANSFORM_PREFIX' : "tr_%(sliceNumber)04d_",
#               'FN_TPL_LIN_TRANSFORM' : "tr_%(sliceNumber)04d_Affine.txt"}

#       __c = type('specificConstantsHolder', (object,), __specificConstants)

#       def _initializeOptions(self):
#           posProcessingElement._initializeOptions(self)

#           # Range of images to register
#           self.options['sliceRange'] = \
#                   range(self.options['startSliceIndex'], self.options['endSliceIndex']+1)

#           # TODO: Optimize the syntax below
#           if self.options['movingSlicesRange'] != None:
#               self.options['movingSliceRange'] = \
#                       range(self.options['movingSlicesRange'][0],
#                           self.options['movingSlicesRange'][1]+1)
#           else:
#               self.options['movingSliceRange'] = self.options['sliceRange']

#           if self.options['fixedSlicesRange'] != None:
#               self.options['fixedSliceRange'] = \
#                       range(self.options['fixedSlicesRange'][0],
#                           self.options['fixedSlicesRange'][1]+1)
#           else:
#               self.options['fixedSliceRange'] = self.options['sliceRange']

#       def _overrideDefaults(self):

#           # Override default output volumes directory if custom directory is provided
#           if self.options['outputVolumesDirectory'] != None:
#               self.options['local_outputVolumes'] = self.options['outputVolumesDirectory']

#           # Override default transformations directory if custom directory is provided
#           if self.options['transformationsDirectory'] != None:
#               self.options['process_transforms'] = self.options['transformationsDirectory']

#       def launchFilter(self):
#           self._loadSlicesAssignment()

#           if self.options['skipPreprocessing'] == False:
#               self._preprocessImages()

#           if self.options['skipGeneratingSourceSlices'] == False:
#               self._generateSourceSlices()

#           if self.options['skipGeneratingTransforms'] == False:
#               self._calculateTransforms()

#           self._reslice()
#           self._mergeOutput()

#           self._loadAdditionalStacksResliceSettings()

#           if self.options['additionalMovingImagesDirectory'] != None:
#               self._loadAdditionalStacksResliceSettings()
#               self._runAdditionalReslice()


#       def _loadSlicesAssignment(self):
#           assignment = csv.reader(open(self.options['imagePairsAssignmentFile']), delimiter='\t', quotechar='"')

#           self._slicesAssignment = {}

#           for entry in assignment:
#               entry = map(int, entry)
#               self._slicesAssignment[entry[0]] = tuple(entry[1:])


#       def _loadAdditionalStacksResliceSettings(self):
#           self._additionalStacksSettings = []

#           fields = ['additionalMovingImagesDirectory', 'additionalInvertSource', \
#                   'additionalInvertMultichannel', 'additionalGrayscaleVolume', \
#                   'additionalMultichannelVolume', 'additionalInterpolation', \
#                   'additionalInterpolationBackground']

#           keys = ['imgDir', 'invertGs', 'invertMc', 'grayVolName', 'rgbVolName',\
#                   'interpolation', 'background']

#           for stackIdx in range(len(self.options['additionalMovingImagesDirectory'])):
#               newStack = {}
#               for field, key in zip(fields, keys):
#                   newStack[key] = self.options[field][stackIdx]
#               self._additionalStacksSettings.append(newStack)

#       def _runAdditionalReslice(self):
#           for stackIdx in range(len(self._additionalStacksSettings)):
#               for sliceNumber in self.options['movingSliceRange']:
#                   self._preprocessAdditional(sliceNumber, stackIdx)
#               for sliceNumber in self.options['sliceRange']:
#                   self._getSourceAdditional(sliceNumber, stackIdx)
#                   self._resliceAdditionalGrayscale(sliceNumber, stackIdx)
#               self._mergeOutput(stackIdx)

#       def _preprocessAdditional(self, sliceNumber, stackIdx):
#           inputFilename = self._getImagePath(
#                   self.__c.ADD_RAW, sliceNumber = sliceNumber, stackIdx=stackIdx)
#           outputFilename = self._getImagePath( \
#                   self.__c.ADD_PRE, sliceNumber = sliceNumber, stackIdx=stackIdx)

#           stackSettings = self._additionalStacksSettings[stackIdx]

#           cmdDict = {}
#           cmdDict['inputImage']  = inputFilename
#           cmdDict['outputImage'] = outputFilename

#           if stackSettings['invertGs'] == '1':
#               cmdDict['invertSourceImage'] = ' -negate '
#           else:
#               cmdDict['invertSourceImage'] = ''

#           cmdDict['medianFilterRadius'] = ''

#           order = "%02d" % (10*stackIdx + 12)
#           command = COMMAND_GENERATE_PREPROCESS % cmdDict
#           self._executeSystem(command, order = "#00" + order + "GENERATE_ADDITIONAL_PREP")

#       def _getSourceAdditional(self, sliceNumber, stackIdx):
#           fixedIdx, trueMoving, movingIdx = self._slicesAssignment[sliceNumber]

#           inputFilename = self._getImagePath( \
#                   self.__c.ADD_PRE, sliceNumber = movingIdx, stackIdx=stackIdx)
#           outputFilename = self._getImagePath( \
#                   self.__c.ADD_SRC, sliceNumber= sliceNumber, stackIdx=stackIdx)

#           cmdDict = {}
#           cmdDict['spacing']     = "x".join(map(str, self.options['movingImageSpacing']))
#           cmdDict['resample']    = str(self.options['movingImageResize']*100)
#           cmdDict['imageChannel'] = self.options['registrationColorChannelFixedImage']
#           cmdDict['inputImage']  = inputFilename
#           cmdDict['outputImage'] = outputFilename

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           order = "%02d" % (10*stackIdx + 13)
#           command = COMMAND_C2D_PREPARE_MULTICHANNEL_IMAGE % cmdDict
#           self._executeSystem(command, order = "#00" + order + "GET_ADDITIONAL_SOURCE")

#       def _resliceAdditionalGrayscale(self, sliceNumber, stackIdx):
#           fixedIdx, trueMoving, movingIdx = self._slicesAssignment[sliceNumber]
#           stackSettings = self._additionalStacksSettings[stackIdx]

#           fixedImage = self._getImagePath( \
#                   self.__c.FIXED_SRC, sliceNumber = sliceNumber)
#           movingImage= self._getImagePath( \
#                   self.__c.ADD_SRC, sliceNumber=sliceNumber, stackIdx=stackIdx)
#           transformFname = self._getImagePath( \
#                   self.__c.TRANSFORM, sliceNumber = sliceNumber)
#           outputImage = self._getImagePath( \
#                   self.__c.RESLICED_A, sliceNumber = sliceNumber)
#           outputImageRGB = self._getImagePath( \
#                   self.__c.RESLICED_RGB_A, sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['fixedImage']  = fixedImage
#           cmdDict['movingImage'] = movingImage
#           cmdDict['outputImage'] = outputImage
#           cmdDict['transformFilename'] =  transformFname

#           if stackSettings['background'] != None:
#               cmdDict['backgroundValue'] = \
#                       ' -background ' + str(stackSettings['background']) + " "
#           else:
#               cmdDict['backgroundValue'] = ''

#           if stackSettings['interpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + stackSettings['interpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           order = "%02d" % (10*stackIdx + 14)
#           command = COMMAND_WARP_GRAYSCALE_SLICE % cmdDict
#           self._executeSystem(command, order = "#00" + order + "WARP_GRAYSCALE_ADDITIONAL")
#           #------------------------

#           movingImage = self._getImagePath(
#                   self.__c.ADD_RAW, sliceNumber = movingIdx, stackIdx=stackIdx)

#           cmdDict['movingImage'] = movingImage
#           cmdDict['outputImage'] = outputImageRGB
#           cmdDict['spacing']     = "x".join(map(str, self.options['movingImageSpacing']))
#           cmdDict['resample']    = str(self.options['movingImageResize']*100)
#           cmdDict['transformFilename'] =  transformFname

#           if stackSettings['invertMc'] == '1':
#               cmdDict['invertImage'] = \
#                       ' -scale -1 -shift 255 -type uchar'
#           else:
#               cmdDict['invertImage'] = ''

#           order = "%02d" % (10*stackIdx + 15)
#           command = COMMAND_WARP_RGB_SLICE_FROM_SOURCE % cmdDict
#           self._executeSystem(command, order = "#00" + order + "WARP_RGB_ADDITIONAL")

#       #--------------------------------------------------------------------------

#       def _preprocessImages(self):
#           for sliceNumber in self.options['fixedSliceRange']:
#               self._preprocessFixedImage(sliceNumber)

#           for sliceNumber in self.options['movingSliceRange']:
#               self._preprocessMovingImage(sliceNumber)

#       def _generateSourceSlices(self):
#           for sliceNumber in self.options['sliceRange']:
#               self._getSourceFixedImage(sliceNumber)
#               self._getSourceMovingImage(sliceNumber)

#       def _calculateTransforms(self):
#           for movingSliceNumber in self.options['sliceRange']:
#               self._calculateSingleTransform(movingSliceNumber)

#       def _reslice(self):
#           for sliceNumber in self.options['sliceRange']:
#               self._resliceGrayscale(sliceNumber)
#               self._resliceMultichannel(sliceNumber)

#       def _preprocessFixedImage(self, sliceNumber):
#           inputFilename = self._getImagePath(
#                   self.__c.FIXED_RAW, sliceNumber = sliceNumber)
#           outputFilename = self._getImagePath( \
#                   self.__c.FIXED_PRE, sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['inputImage']  = inputFilename
#           cmdDict['outputImage'] = outputFilename

#           if self.options['invertSourceImage']:
#               cmdDict['invertSourceImage'] = \
#               ' -negate '
#           else:
#               cmdDict['invertSourceImage'] = ''

#           if self.options['fixedImageMedianFilterRadius']:
#               cmdDict['medianFilterRadius'] = \
#               ' -median ' + self.options['fixedImageMedianFilterRadius']
#           else:
#               cmdDict['medianFilterRadius'] = ''

#           command = COMMAND_GENERATE_PREPROCESS % cmdDict
#           self._executeSystem(command, order = "#0000GENERATE_PREPROCESS_FIXED")

#       def _preprocessMovingImage(self, sliceNumber):
#           inputFilename = self._getImagePath(
#                   self.__c.MOVING_RAW, sliceNumber = sliceNumber)
#           outputFilename = self._getImagePath( \
#                   self.__c.MOVING_PRE, sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['inputImage']  = inputFilename
#           cmdDict['outputImage'] = outputFilename

#           if self.options['invertSourceImage']:
#               cmdDict['invertSourceImage'] = \
#               ' -negate '
#           else:
#               cmdDict['invertSourceImage'] = ''

#           if self.options['movingImageMedianFilterRadius']:
#               cmdDict['medianFilterRadius'] = \
#               ' -median ' + self.options['movingImageMedianFilterRadius']
#           else:
#               cmdDict['medianFilterRadius'] = ''

#           command = COMMAND_GENERATE_PREPROCESS % cmdDict
#           self._executeSystem(command, order = "#0000GENERATE_PREPROCESS_MOVING")

#       def _getSourceFixedImage(self, sliceNumber):
#           fixedIdx, trueMoving, movingIdx = self._slicesAssignment[sliceNumber]

#           inputFilename = self._getImagePath(
#                   self.__c.FIXED_PRE, sliceNumber = fixedIdx)
#           outputFilename = self._getImagePath( \
#                   self.__c.FIXED_SRC, sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['spacing']   = "x".join(map(str, self.options['fixedImageSpacing']))
#           cmdDict['resample']  = str(self.options['fixedImageResize']*100)
#           cmdDict['imageChannel'] = self.options['registrationColorChannelFixedImage']
#           cmdDict['inputImage']  = inputFilename
#           cmdDict['outputImage'] = outputFilename

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           command = COMMAND_C2D_PREPARE_MULTICHANNEL_IMAGE % cmdDict
#           self._executeSystem(command, order = "#0001GET_FIXED_IMAGE")

#       def _getSourceMovingImage(self, sliceNumber):
#           fixedIdx, trueMoving, movingIdx = self._slicesAssignment[sliceNumber]

#           inputFilename = self._getImagePath( \
#                   self.__c.MOVING_PRE, sliceNumber = movingIdx)
#           outputFilename = self._getImagePath( \
#                   self.__c.MOVING_SRC, sliceNumber= sliceNumber)

#           cmdDict = {}
#           cmdDict['spacing']     = "x".join(map(str, self.options['movingImageSpacing']))
#           cmdDict['resample']    = str(self.options['movingImageResize']*100)
#           cmdDict['imageChannel'] = self.options['registrationColorChannelFixedImage']
#           cmdDict['inputImage']  = inputFilename
#           cmdDict['outputImage'] = outputFilename

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           command = COMMAND_C2D_PREPARE_MULTICHANNEL_IMAGE % cmdDict
#           self._executeSystem(command, order = "#0002GET_MOVING_IMAGE")

#       def _calculateSingleTransform(self, sliceNumber):
#           fixedImage, movingImage, transformFname, outputImage = \
#                   self._getNamesForSliceNumber(sliceNumber)

#           transformFname = self._getImagePath( \
#                   self.__c.FN_TPL_LIN_TRANSFORM_PREFIX, sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['fixedImage']  = fixedImage
#           cmdDict['movingImage'] = movingImage
#           cmdDict['outputTransformFn'] = transformFname
#           cmdDict['mp']     = self.options['antsImageMetricOpt']
#           cmdDict['metric'] = self.options['antsImageMetric']
#           cmdDict['rigidAffineSetting'] = \
#                   str(self.options['useRigidAffine']).lower()

#           # Pass additional ANTS registration parameters (if provided). The string
#           # is initialized as empty.
#           cmdDict['addAntsParam'] = ""
#           if self.options['additionalAntsParameters']:
#               cmdDict['addAntsParam'] = self.options['additionalAntsParameters']

#           command = COMMAND_ANTS_GENERATE_TRANSFORM % cmdDict
#           self._executeSystem(command, order = "#0004TRANSFORM")

#       def _resliceGrayscale(self, sliceNumber):
#           fixedImage, movingImage, transformFname, outputImage = \
#                   self._getNamesForSliceNumber(sliceNumber)

#           cmdDict = {}
#           cmdDict['fixedImage']  = fixedImage
#           cmdDict['movingImage'] = movingImage
#           cmdDict['outputImage'] = outputImage
#           cmdDict['transformFilename'] =  transformFname

#           if self.options['interpolationBackgorundColor'] != None:
#               cmdDict['backgroundValue'] = \
#                       ' -background ' + str(self.options['interpolationBackgorundColor']) + " "
#           else:
#               cmdDict['backgroundValue'] = ''

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           command = COMMAND_WARP_GRAYSCALE_SLICE % cmdDict
#           self._executeSystem(command, order = "#0006WARP_GRAYSCALE_SLICE")

#       def _resliceMultichannel(self, sliceNumber):
#           fixedIdx, trueMoving, movingIdx = self._slicesAssignment[sliceNumber]

#           fixedImage = self._getImagePath( \
#                   self.__c.FIXED_SRC, sliceNumber = sliceNumber)
#           movingImage = self._getImagePath(
#                   self.__c.MOVING_RAW, sliceNumber = movingIdx)
#           transformFname = self._getImagePath( \
#                   self.__c.TRANSFORM, sliceNumber = sliceNumber)
#           outputImage = self._getImagePath( \
#                   self.__c.RESLICED_RGB, sliceNumber = sliceNumber)

#           cmdDict = {}
#           cmdDict['fixedImage']  = fixedImage
#           cmdDict['movingImage'] = movingImage
#           cmdDict['outputImage'] = outputImage
#           cmdDict['spacing']     = "x".join(map(str, self.options['movingImageSpacing']))
#           cmdDict['resample']    = str(self.options['movingImageResize']*100)
#           cmdDict['transformFilename'] =  transformFname

#           if self.options['invertMultichannelImage']:
#               cmdDict['invertImage'] = \
#                       ' -scale -1 -shift 255 -type uchar'
#           else:
#               cmdDict['invertImage'] = ''

#           if self.options['interpolationBackgorundColor'] != None:
#               cmdDict['backgroundValue'] = \
#                       ' -background ' + str(self.options['interpolationBackgorundColor']) + " "
#           else:
#               cmdDict['backgroundValue'] = ''

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           command = COMMAND_WARP_RGB_SLICE_FROM_SOURCE % cmdDict
#           self._executeSystem(command, order = "#0005WARP_RGB_SLICE")

#       def _getNamesForSliceNumber(self, sliceNumber):
#           fixedImage = self._getImagePath( \
#                   self.__c.FIXED_SRC, sliceNumber = sliceNumber)
#           movingImage = self._getImagePath( \
#                   self.__c.MOVING_SRC, sliceNumber = sliceNumber)
#           transformFname = self._getImagePath( \
#                   self.__c.TRANSFORM, sliceNumber = sliceNumber)
#           outputImage = self._getImagePath( \
#                   self.__c.RESLICED, sliceNumber = sliceNumber)

#           return fixedImage, movingImage, transformFname, outputImage

#       def _getImagePath(self, imageType = None, **kwargs):
#           """
#           Return full path for the given file depending on its purpose.
#           """
#           if imageType == self.__c.RESLICED_MASK_A:
#               directory = self.options['process_additional_gray']
#               filename  = self.__c.FN_TPL_RESL_GS_MASK
#               return os.path.join(directory, filename)

#           if imageType == self.__c.RESLICED_RGB_MASK_A:
#               directory = self.options['process_additional_rgb']
#               filename  = self.__c.FN_TPL_RESL_RGB_A
#               return os.path.join(directory, filename)

#           if imageType == self.__c.RESLICED_RGB_A:
#               directory = self.options['process_additional_rgb']
#               filename  = self.__c.FN_TPL_RESL_GS_A % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.RESLICED_A:
#               directory = self.options['process_additional_gray']
#               filename  = self.__c.FN_TPL_RESL_GS_A % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.ADD_SRC:
#               directory = self.options['process_additional_src']
#               filename  = self.__c.FN_TPL_SRC_GS_A % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.ADD_PRE:
#               directory = self.options['process_additional_prep']
#               filename  = self.__c.FN_TPL_PRE % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.ADD_RAW:
#               directory = self._additionalStacksSettings[kwargs['stackIdx']]['imgDir']
#               filename  = self.__c.FN_TPL_RAW_GS_A % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.RESLICED_RGB_MASK:
#               directory = self.options['process_color_resliced']
#               filename  = self.__c.FN_TPL_RESL_RGB
#               return os.path.join(directory, filename)

#           if imageType == self.__c.RESLICED_MASK:
#               directory = self.options['process_gray_resliced']
#               filename  = self.__c.FN_TPL_RESL_GS_MASK
#               return os.path.join(directory, filename)

#           if imageType == self.__c.RESLICED:
#               directory = self.options['process_gray_resliced']
#               filename  = self.__c.FN_TPL_RESL_GS % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.RESLICED_RGB:
#               directory = self.options['process_color_resliced']
#               filename  = self.__c.FN_TPL_RESL_GS % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.FIXED_RAW:
#               if self.options['fixedImageInputDirectory']:
#                   directory = self.options['fixedImageInputDirectory']
#               else:
#                   directory = os.path.join(\
#                                   self.pathToSpecimenData,
#                                   self._dirTemplates['fixed_images_raw'])
#               filename  = self.__c.FN_TPL_RAW_GS_F % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.FIXED_SRC:
#               directory = self.options['process_fixed_images_src']
#               filename  = self.__c.FN_TPL_SRC_GS % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.MOVING_RAW:
#               if self.options['movingImageInputDirectory']:
#                   directory = self.options['movingImageInputDirectory']
#               else:
#                   directory = os.path.join(\
#                                   self.pathToSpecimenData,
#                                   self._dirTemplates['moving_images_raw'])
#               filename  = self.__c.FN_TPL_RAW_GS_M % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.MOVING_SRC:
#               directory = self.options['process_moving_images_src']
#               filename  = self.__c.FN_TPL_SRC_GS % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.FIXED_PRE:
#               directory = self.options['process_fixed_images_prep']
#               filename  = self.__c.FN_TPL_PRE % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.MOVING_PRE:
#               directory = self.options['process_moving_images_prep']
#               filename  = self.__c.FN_TPL_PRE % kwargs['sliceNumber']
#               return os.path.join(directory, filename)

#           if imageType == self.__c.TRANSFORM:
#               directory = self.options['process_transforms']
#               filename  = self.__c.FN_TPL_LIN_TRANSFORM % {'sliceNumber' : kwargs['sliceNumber']}
#               return os.path.join(directory, filename)

#           if imageType == self.__c.FN_TPL_LIN_TRANSFORM_PREFIX:
#               directory = self.options['process_transforms']
#               filename  = self.__c.FN_TPL_LIN_TRANSFORM_PREFIX % {'sliceNumber' : kwargs['sliceNumber']}
#               return os.path.join(directory, filename)

#           return None

#       def _getOutputVolumeName(self, volumeType, extension='.nii.gz', stackIdx = None):
#           retName = "out_vol_"

#           if stackIdx != None:
#               retName += "stack%02d_" % stackIdx
#               if volumeType == self.__c.OUT_VOL_GS_A: retName+="gray"
#               if volumeType == self.__c.OUT_VOL_RGB_A:  retName+="rgb"
#           else:
#               if volumeType == self.__c.OUT_VOL_GS: retName+="gray"
#               if volumeType == self.__c.OUT_VOL_RGB:  retName+="rgb"

#           retName+= "_rFCol_" + self.options['registrationColorChannelFixedImage']
#           retName+= "_rMCol_" + self.options['registrationColorChannelMovingImage']

#           retName+= "_rFRs_" + str(self.options['fixedImageResize'])
#           retName+= "_rMRs_" + str(self.options['movingImageResize'])

#           retName+= "_rFsp_" + "x".join(map(str, self.options['fixedImageSpacing']))
#           retName+= "_rMsp_" + "x".join(map(str, self.options['movingImageSpacing']))

#           retName+= "_rM_" + self.options['antsImageMetric']
#           retName+= "_rMP_" + str(self.options['antsImageMetricOpt'])

#           retName+= "_sStart_" + str(self.options['startSliceIndex'])
#           retName+= "_sEnd_" + str(self.options['endSliceIndex'])
#           retName+= "_%s_" % ('rigid' if self.options['useRigidAffine'] else 'affine')
#           retName+= extension

#           if stackIdx != None:
#               stackSettings = self._additionalStacksSettings[stackIdx]

#               if stackSettings['grayVolName'] == 'default' and volumeType == self.__c.OUT_VOL_GS_A:
#                   return retName
#               if stackSettings['rgbVolName'] == 'default' and volumeType == self.__c.OUT_VOL_RGB_A:
#                   return retName

#               if stackSettings['grayVolName'] != 'skip' and volumeType == self.__c.OUT_VOL_GS_A:
#                   retName = stackSettings['grayVolName']
#               if stackSettings['rgbVolName'] != 'skip' and volumeType == self.__c.OUT_VOL_RGB_A:
#                   retName = stackSettings['rgbVolName']
#           else:
#               # Override default output volume names with the custom names:
#               if self.options['grayscaleVolumeFilename'] != None and volumeType == self.__c.OUT_VOL_GS:
#                   retName = self.options['grayscaleVolumeFilename']
#               if self.options['rgbVolumeFilename'] != None and volumeType == self.__c.OUT_VOL_RGB:
#                   retName = self.options['rgbVolumeFilename']

#           return retName

#       def _mergeOutput(self, stackIdx = None):
#           """
#           Merge registered and resliced images into consitent volume with assigned
#           voxel spacing. Grayscale as well as multichannel volumes are created.
#           """

#           # Generate names of the output volume. The names are combination of the
#           # processing options.
#           if stackIdx != None:
#               grayVolumeName = self._getOutputVolumeName(\
#                       volumeType = self.__c.OUT_VOL_GS_A, stackIdx = stackIdx)
#               colorVolumeName= self._getOutputVolumeName(\
#                       volumeType = self.__c.OUT_VOL_RGB_A, stackIdx = stackIdx)
#           else:
#               grayVolumeName = self._getOutputVolumeName(volumeType = self.__c.OUT_VOL_GS)
#               colorVolumeName= self._getOutputVolumeName(volumeType = self.__c.OUT_VOL_RGB)

#           factor = self.options['movingImageResize']
#           outputVolumeSpacing = " ".join(map(str,self.options['outputVolumeSpacing']))
#           volumeTempFn = os.path.join( \
#                   self.options['process_outputVolumes'], '__temp__rgbvol.vtk')
#           volumeOutputMultichannelFn = os.path.join( \
#                   self.options['local_outputVolumes'], colorVolumeName)
#           volumeOutputGrayscale = os.path.join( \
#                   self.options['local_outputVolumes'], grayVolumeName)
#           outputVolumeScalarType = self.options['outputVolumeScalarType']

#           if self.options['outputVolumeResample'] != None:
#               resamplingString = '--resample ' + " ".join(map(str, self.options['outputVolumeResample']))
#           else:
#               resamplingString = ""

#           cmdDict = {}
#           if stackIdx == None:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_RGB_MASK)
#           else:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_RGB_MASK_A)
#           cmdDict['sliceStart']     = self.options['startSliceIndex']
#           cmdDict['sliceEnd']       = self.options['endSliceIndex']
#           cmdDict['spacing']        = outputVolumeSpacing
#           cmdDict['origin']         = " ".join(map(str, self.options['outputVolumeOrigin']))
#           cmdDict['volumeTempFn']   = volumeTempFn
#           cmdDict['volumeOutputFn'] = volumeOutputMultichannelFn
#           cmdDict['outputVolumeScalarType'] = outputVolumeScalarType
#           cmdDict['permutationOrder'] = " ".join(map(str, self.options['outputVolumePermutationOrder']))
#           cmdDict['orientationCode'] = self.options['outputVolumeOrientationCode']
#           cmdDict['resampling']      = resamplingString

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '-interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           if stackIdx == None:
#               if not self.options['skipColorReslice']:
#                   command = COMMAND_STACK_SLICES_RGB % cmdDict
#                   self._executeSystem(command, order = "#0009STACK_RGB")
#           else:
#               stackSettings = self._additionalStacksSettings[stackIdx]
#               if stackSettings['rgbVolName'] != 'skip':
#                   order = "%02d" % (10*stackIdx + 17)
#                   command = COMMAND_STACK_SLICES_RGB % cmdDict
#                   self._executeSystem(command, order = "#00" + order + "STACK_ADDITIONAL_RGB")

#           cmdDict = {}
#           if stackIdx == None:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_MASK)
#           else:
#               cmdDict['stackMask']      = self._getImagePath(imageType=self.__c.RESLICED_MASK_A)
#           cmdDict['volumeTempFn']   = volumeTempFn
#           cmdDict['volumeOutputFn'] = volumeOutputGrayscale
#           cmdDict['spacing']        = outputVolumeSpacing
#           cmdDict['origin']         = " ".join(map(str, self.options['outputVolumeOrigin']))
#           cmdDict['outputVolumeScalarType'] = outputVolumeScalarType
#           cmdDict['permutationOrder'] = " ".join(map(str, self.options['outputVolumePermutationOrder']))
#           cmdDict['orientationCode'] = self.options['outputVolumeOrientationCode']
#           cmdDict['resampling']      = resamplingString

#           if self.options['setInterpolation'] != None:
#               cmdDict['interpolation'] = '--interpolation ' + self.options['setInterpolation']
#           else:
#               cmdDict['interpolation'] = ""

#           if stackIdx == None:
#               if not self.options['skipGrayReslice']:
#                   command = COMMAND_STACK_SLICES_GRAY % cmdDict
#                   self._executeSystem(command, order = '#0008STACK_GRAYSCALE')
#           else:
#               stackSettings = self._additionalStacksSettings[stackIdx]
#               if stackSettings['grayVolName'] != 'skip':
#                   order = "%02d" % (10*stackIdx + 16)
#                   command = COMMAND_STACK_SLICES_GRAY % cmdDict
#                   self._executeSystem(command, order = "#00" + order + "STACK_ADDITIONAL_GRAYSCALE")

#       @classmethod
#       def _getCommandLineParser(cls):
#           parser = posProcessingElement._getCommandLineParser()

#           regSettings = \
#                   OptionGroup(parser, 'Registration setttings.')

#           regSettings.add_option('--antsImageMetric', default='MI',
#                   type='str', dest='antsImageMetric',
#                   help='ANTS image to image metric. See ANTS documentation.')
#           regSettings.add_option('--useRigidAffine', default=False,
#                   dest='useRigidAffine', action='store_const', const=True,
#                   help='Use rigid affine transformation. By default affine transformation is used to drive the registration ')
#           regSettings.add_option('--antsImageMetricOpt', default=32,
#                   type='int', dest='antsImageMetricOpt',
#                   help='Parameter of ANTS i2i metric.')
#           regSettings.add_option('--additionalAntsParameters', default=None,
#                   type='str', dest='additionalAntsParameters',  help='Addidtional ANTS command line parameters (provide within double quote: "")')
#           regSettings.add_option('--startSliceIndex', default=0,
#                   type='int', dest='startSliceIndex',
#                   help='Index of the first slice of the stack')
#           regSettings.add_option('--endSliceIndex', default=None,
#                   type='int', dest='endSliceIndex',
#                   help='Index of the last slice of the stack')
#           regSettings.add_option('--movingSlicesRange', default=None,
#                   type='int', dest='movingSlicesRange', nargs = 2,
#                   help='Range of moving slices (for preprocessing). By default the same as fixed slice range.')
#           regSettings.add_option('--fixedSlicesRange', default=None,
#                   type='int', dest='fixedSlicesRange', nargs = 2,
#                   help='Range of fixed slices (for preprocessing). By default the same as fixed slice range.')
#           regSettings.add_option('--imagePairsAssignmentFile', default=None,
#                   type='str', dest='imagePairsAssignmentFile', help='File carrying assignment of a fixed image to corresponding moving image.')
#           regSettings.add_option('--registrationColorChannelMovingImage', default='blue',
#                       type='str', dest='registrationColorChannelMovingImage',
#                       help='In rgb images - color channel on which \
#                       registration will be performed. Has no meaning for \
#                       grayscale input images. Possible values: r/red, g/green, b/blue.')
#           regSettings.add_option('--registrationColorChannelFixedImage', default='red',
#                       type='str', dest='registrationColorChannelFixedImage',
#                       help='In rgb images - color channel on which \
#                       registration will be performed. Has no meaning for \
#                       grayscale input images. Possible values: r/red, g/green, b/blue.')

#           preprocessingSettings = \
#                   OptionGroup(parser, 'Image preprocessing settings')
#           preprocessingSettings.add_option('--fixedImageSpacing', dest='fixedImageSpacing',
#                   default=[1.,1.], action='store', type='float', nargs = 2, help='Spacing of the fixed image in 1:1 scale (before resizing).')
#           preprocessingSettings.add_option('--movingImageSpacing', dest='movingImageSpacing',
#                   default=[1.,1.], action='store', type='float', nargs =2, help='Spacing of the moving image in 1:1 scale (before resizing).')
#           preprocessingSettings.add_option('--fixedImageResize', dest='fixedImageResize',
#                   default=1., action='store', type='float', nargs =1, help='Resampling ratio (optional). Allows to alter registration speed and accuracy. Determines size of the ouput volume.')
#           preprocessingSettings.add_option('--movingImageResize', dest='movingImageResize',
#                   default=1., action='store', type='float', nargs =1, help='Resampling ratio (optional). Allows to alter registration speed and accuracy. Determines size of the ouput volume.')
#           preprocessingSettings.add_option('--fixedImageInputDirectory', default=None,
#                       type='str', dest='fixedImageInputDirectory', help='')
#           preprocessingSettings.add_option('--movingImageInputDirectory', default=None,
#                       type='str', dest='movingImageInputDirectory', help='')

#           workflowSettings = \
#                   OptionGroup(parser, 'Workflow settings')
#           workflowSettings.add_option('--skipGrayReslice', default=False,
#                   dest='skipGrayReslice', action='store_const', const=True,
#                   help='Supress generating grayscale volume')
#           workflowSettings.add_option('--skipColorReslice', default=False,
#                   dest='skipColorReslice', action='store_const', const=True,
#                   help='Supress generating RGB volume.')
#           workflowSettings.add_option('--skipGeneratingSourceSlices', default=False,
#                   dest='skipGeneratingSourceSlices', action='store_const', const=True,
#                   help='Supress processing source slices.')
#           workflowSettings.add_option('--skipGeneratingTransforms', default=False,
#                   dest='skipGeneratingTransforms', action='store_const', const=True,
#                   help='Supress generating transforms.')
#           workflowSettings.add_option('--skipPreprocessing', default=False,
#                   dest='skipPreprocessing', action='store_const', const=True,
#                   help='Supress preprocessing images.')
#           workflowSettings.add_option('--transformationsDirectory', default=None,
#                   dest='transformationsDirectory', action='store',
#                   help='Store transformations in given directory instead of using default one.')
#           workflowSettings.add_option('--outputVolumesDirectory', default=None,
#                   dest='outputVolumesDirectory', action='store',
#                   help='Store output volumes in given directory instead of using default one.')
#           workflowSettings.add_option('--interpolationBackgorundColor', default=None,
#               type='float', dest='interpolationBackgorundColor',
#               help='Background color')

#           dataPreparationOptions= OptionGroup(parser, 'Source data preprocessing options')

#           dataPreparationOptions.add_option('--fixedImageMedianFilterRadius', default=None,
#                   dest='fixedImageMedianFilterRadius', type='str',
#                   help='Median filter radius according to ImageMagick syntax.')
#           dataPreparationOptions.add_option('--movingImageMedianFilterRadius', default=None,
#                   dest='movingImageMedianFilterRadius', type='str',
#                   help='Median filter radius according to ImageMagick syntax.')
#           dataPreparationOptions.add_option('--invertSourceImage', default=False,
#                   dest='invertSourceImage',  action='store_const', const=True,
#                   help='Invert source image: both, fixed and moving, before registration')
#           dataPreparationOptions.add_option('--invertMultichannelImage', default=False,
#                   dest='invertMultichannelImage',  action='store_const', const=True,
#                   help='Invert source image: both, grayscale and multichannel, before registration')
#           dataPreparationOptions.add_option('--fixedCustomImageMagic', default=None,
#                   dest='fixedCustomImageMagic',  action='store',
#                   help='Custom ImageMagick processing string for fixed image.')
#           dataPreparationOptions.add_option('--movingCustomImageMagic', default=None,
#                   dest='movingCustomImageMagic', action='store',
#                   help='Custom ImageMagick processing string for moving image.')

#           additionalStackReslice = OptionGroup(parser, 'Settings for reslicing additional image stacks')
#           additionalStackReslice.add_option('--additionalMovingImagesDirectory', default=None,
#                   dest='additionalMovingImagesDirectory', type='str',
#                   action='append', help='')
#           additionalStackReslice.add_option('--additionalInvertSource', default=None,
#                   dest='additionalInvertSource', type='str',
#                   action='append', help='')
#           additionalStackReslice.add_option('--additionalInvertMultichannel', default=None,
#                   dest='additionalInvertMultichannel', type='str',
#                   action='append', help='')
#           additionalStackReslice.add_option('--additionalGrayscaleVolume', default=None,
#                   dest='additionalGrayscaleVolume', type='str',
#                   action='append', help='')
#           additionalStackReslice.add_option('--additionalMultichannelVolume', default=None,
#                   dest='additionalMultichannelVolume', type='str',
#                   action='append', help='')
#           additionalStackReslice.add_option('--additionalInterpolation', default=None,
#                   dest='additionalInterpolation', type='str',
#                   action='append', help='')
#           additionalStackReslice.add_option('--additionalInterpolationBackground', default=None,
#                   dest='additionalInterpolationBackground', type='str',
#                   action='append', help='')

#           outputVolumeSettings = \
#                   OptionGroup(parser, 'OutputVolumeSettings.')
#           outputVolumeSettings.add_option('--outputVolumeOrigin', dest='outputVolumeOrigin',
#                   default=[0.,0.,0.], action='store', type='float', nargs =3, help='')
#           outputVolumeSettings.add_option('--outputVolumeScalarType', default='uchar',
#                   type='str', dest='outputVolumeScalarType',
#                   help='Data type for output volume\'s voxels. Allowed values: char | uchar | short | ushort | int | uint | float | double')
#           outputVolumeSettings.add_option('--outputVolumeSpacing', default=[1,1,1],
#               type='float', nargs=3, dest='outputVolumeSpacing',
#               help='Spacing of the output volume in mm (both grayscale and color volume).')
#           outputVolumeSettings.add_option('--outputVolumeResample',
#                           dest='outputVolumeResample', type='float', nargs=3, default=None,
#                           help='Apply additional resampling to the volume')
#           outputVolumeSettings.add_option('--outputVolumePermutationOrder', default=[0,1,2],
#               type='int', nargs=3, dest='outputVolumePermutationOrder',
#               help='Apply axes permutation. Permutation has to be provided as sequence of 3 integers separated by space. Identity (0,1,2) permutation is a default one.')
#           outputVolumeSettings.add_option('--outputVolumeOrientationCode',  dest='outputVolumeOrientationCode', type='str',
#                   default='RAS', help='')
#           outputVolumeSettings.add_option('--grayscaleVolumeFilename',  dest='grayscaleVolumeFilename',
#                   type='str', default=None)
#           outputVolumeSettings.add_option('--rgbVolumeFilename',  dest='rgbVolumeFilename',
#                   type='str', default=None)
#           outputVolumeSettings.add_option('--setInterpolation',
#                           dest='setInterpolation', type='str', default=None,
#                           help='<NearestNeighbor|Linear|Cubic|Sinc|Gaussian>')

#           parser.add_option_group(workflowSettings)
#           parser.add_option_group(preprocessingSettings)
#           parser.add_option_group(regSettings)
#           parser.add_option_group(additionalStackReslice)
#           parser.add_option_group(outputVolumeSettings)
#           return parser


if __name__ == '__main__':
    options, args = pairwiseRegistration.parseArgs()
    se = pairwiseRegistration(options, args)
    se.launch()
