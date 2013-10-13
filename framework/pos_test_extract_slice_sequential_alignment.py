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

import sys, os
import datetime, logging
from optparse import OptionParser, OptionGroup

import itk
from pos_slice_volume import autodetect_file_type, types_reduced_dimensions
import pos_common

def resample_image_filter(input_image, input_type, output_type,
                          scaling_factor, default_value=0):
    """
    Reimplemented after:
    http://sourceforge.net/p/c3d/git/ci/master/tree/adapters/ResampleImage.cxx#l12

    """

    # Read out the image dimension to be to use it further in the routine.
    # This is done by pretty simple yet effective way :)
    image_dim = len(input_image.GetSpacing())

    # Declare an image interpolation function. The function is by default a
    # linear interpolation function, however it my be switched to any other
    # image interpolation function by altering the code below.
    interpolator = itk.LinearInterpolateImageFunction[input_type, itk.D].New()

    # Declare resampling filter and initialize the filter with two dimensional
    # identity transformation as well as image interpolation function
    resample_filter = itk.ResampleImageFilter[input_type, output_type].New()
    resample_filter.SetInput(input_image)
    resample_filter.SetTransform(itk.IdentityTransform[itk.D, image_dim].New())
    resample_filter.SetInterpolator(interpolator)

    # Compute the spacing of the new image
    # The new spacing is computed by

    # Get original spacing of the input image:
    pre_spacing = input_image.GetSpacing()

    # Initialize recomputed size vector. Note that the vector is initialized
    # with zeroes:
    post_size = itk.Vector[itk.US, image_dim]([0]*image_dim)

    # Initialize scaling vector based on provided scaling factor
    scaling = itk.Vector[itk.F, image_dim]([scaling_factor]*image_dim)

    # Initialize vector holding spacing of the output image. Note that the
    # vector is initalized with zeroes.
    post_spacing = itk.Vector[itk.F, image_dim]([0]*image_dim)

    for i in range(image_dim):
        post_spacing[i] = pre_spacing[i] * 1.0 / scaling[i]
        post_size[i] = int(input_image.GetBufferedRegion().GetSize()[i] * \
                           1.0 * scaling[i])

    print "Spacing post", post_spacing
    print "Size post", post_size

    # Get the bounding box of the input image
    pre_origin = input_image.GetOrigin()

    # Recalculate the origin. The origin describes the center of voxel 0,0,0
    # so that as the voxel size changes, the origin will change as well.
    pre_offset = input_image.GetDirection() * pre_spacing
    post_offset = input_image.GetDirection() * post_spacing
    for i in range(pre_offset.Size()):
        pre_offset[i] *= 0.5
        post_offset[i] *= 0.5
    origin_post = pre_origin - pre_offset + post_offset

    # Set the image sizes, spacing, origins and image direction matrix:
    resample_filter.SetSize(post_size)
    resample_filter.SetOutputSpacing(post_spacing)
    resample_filter.SetOutputOrigin(origin_post)
    resample_filter.SetOutputDirection(input_image.GetDirection())

    # Set the unknown intensity to positive value
    resample_filter.SetDefaultPixelValue(default_value)

    # Describe what we are doing
    print " Input spacing: " , pre_spacing
    print " Input origin: " , pre_origin
    print " Output spacing: " , post_spacing
    print " Output origin: " , origin_post

    # Perform resampling
    resample_filter.UpdateLargestPossibleRegion()

    # Return resampled image:
    return resample_filter.GetOutput()


def get_image_region(image_dim, crop_index, crop_size):
    bounding_box = itk.ImageRegion[image_dim]()
    bounding_box.SetIndex(map(int, crop_index))
    bounding_box.SetSize(map(int, crop_size))

    return bounding_box


def prepare_single_channel(input_image, input_type,
                           scale_factor=None, crop_index=None, crop_size=None,
                           median_radius=None, invert=False, invert_max=255,
                           rescale_min=None, rescale_max=None):

    # Determine image dimensionality:
    image_dim = len(input_image.GetSpacing())

    # Declare an variable holding output of the last applied filter:
    last_res = None

    # Handle image cropping:
    if crop_index and crop_size:
        bounding_box = get_image_region(image_dim, crop_index, crop_size)

        crop_filter = itk.RegionOfInterestImageFilter[input_type, input_type].New()
        crop_filter.SetInput(input_image)
        crop_filter.SetRegionOfInterest(bounding_box)
        crop_filter.Update()

        last_res = crop_filter.GetOutput()
    else:
        last_res = input_image
        last_res.Update()
        last_res.UpdateOutputData()
        last_res.UpdateOutputInformation()

    # Handle image inversion:
    if invert:
        max_filter = itk.MinimumMaximumImageFilter[input_type].New()
        max_filter.SetInput(last_res)

        invert_filter = itk.InvertIntensityImageFilter[input_type, input_type].New()
        invert_filter.SetInput(last_res)

        if invert_max:
            invert_filter.SetMaximum(invert_max)
        else:
            invert_filter.SetMaximum(max_filter.GetMaximum())

        invert_filter.Update()
        last_res = invert_filter.GetOutput()

    # Handle median filtering
    if median_radius :
        median = itk.MedianImageFilter[input_type, input_type].New()
        median.SetInput(last_res)
        median.SetRadius(median_radius)
        median.Update()

        last_res = median.GetOutput()

    # Handle image rescaling
    if (scale_factor is not None) and (int(scale_factor) != 1):
        last_res  = resample_image_filter(last_res, input_type,
                                          input_type, scale_factor)

    # Handle results rescaling
    if all([rescale_min, rescale_max]):
        rescaler = itk.RescaleIntensityImageFilter[input_type, input_type].New()
        rescaler.SetInput(last_res)
        rescaler.SetOutputMinimum(rescale_min)
        rescaler.SetOutputMaximum(rescale_max)

        last_res = rescaler.GetOutput()

    return last_res


def collapse_pseudo_3d_image(input_image, input_type,
                             plane_to_collapse=2, plane_to_extract=0):
    """
    Colapses three dimensional image by extracting single a two dimensional
    slice. The extraction is performed only if the input image is three
    dimensional. The procedure will not work for images with dimensionality
    larger than 3. For dimensionality equal to 2, no processing is performed.
    """
    #TODO: Insert assertion checking if dimensionality is larger than 3.

    # Determine image dimensionality:
    image_dim = len(input_image.GetSpacing())

    # In case if dimensionality equals 3, do the extraction:
    if image_dim == 3:
        region = input_image.GetBufferedRegion()
        region.SetSize(plane_to_collapse, 0)
        region.SetIndex(plane_to_collapse, plane_to_extract)

        # Determine the type of the collapsed image by cheking it in an
        # approperiate lookup table.
        collapsed_img_type = types_reduced_dimensions[input_type]

        # Initialize and set up image slicing filter
        extract_slice = itk.ExtractImageFilter[input_type, collapsed_img_type].New()
        extract_slice.SetExtractionRegion(region)
        extract_slice.SetInput(input_image)
        extract_slice.SetDirectionCollapseToIdentity()
        extract_slice.Update()

        # Return new, collapsed image type as well as the collapsed image
        result = extract_slice.GetOutput()
        return result, collapsed_img_type
    else:
        # Just pass the initial images and input types
        result = input_image
        return input_image, input_type


class prepare_slice_for_seq_alignment(object):
    """
    Assumptions:
        1) RGB: three channel integer (0-255) image.
        2) Grayscale: single channel 8-bit (0-255) image.
        Providing images not matching provided.

    Output image types:
        1) RGB: three channel 8-bit integer images.
        2) Grayscale: single channel float image.
    """
    _rgb_out_type = itk.Image.RGBUC2
    _rgb_out_component_type = itk.Image.UC2
    _grayscale_out_type = itk.Image.F2

    def __init__(self, optionsDict, args):
        """
        """
        # Store filter configuration withing the class instance
        if type(optionsDict) != type({}):
            self.options = eval(str(optionsDict))
        else:
            self.options = optionsDict

        self._args = args

        # Yes, we need logging even in so simple script.
        self._initializeLogging()

        # Check, if all the provided parameters are valid and mutually
        # consistent.
        self._validate_options()

    def _initializeLogging(self):
        pos_common.setup_logging(self.options['logFilename'],
                      self.options['loglevel'])

        logging.debug("Logging module initialized. Saving to: %s, Loglevel: %s",
                      self.options['logFilename'], self.options['loglevel'])

        # Assign the the string that will identify all messages from this
        # script
        self._logger = logging.getLogger(self.__class__.__name__)

        self._logger.info("%s workflow options:", self.__class__.__name__)
        for k,v in self.options.items():
            self._logger.info("%s : %s", k, v)

    def _validate_options(self):
        assert self.options['inputFilename'] is not None , \
            self._logger.error("The input image is a required option!")

    def launch_filter(self):
        """
        """
        # Determine the filetype and then load the image to be processed.
        self._logger.debug("Reading volume file %s", self.options['inputFilename'])
        self._input_type = autodetect_file_type(self.options['inputFilename'])
        reader = itk.ImageFileReader[self._input_type].New()
        reader.SetFileName(self.options['inputFilename'])
        reader.Update()

        # Read number of the components of the image.
        self._numbers_of_components =\
                reader.GetOutput().GetNumberOfComponentsPerPixel()
        self._logger.info("Determined number of components: %d",
                          self._numbers_of_components)

        # Collapse the image if required. The purpose of the collapsing
        # procedure is to make trully two dimensional image out of pseudo
        # threedimensional image (an image with third dimension equal to 1).
        # This often happens due to sloppiness of some software. Collapsing the
        # image also updates the input image type.
        self._logger.debug("Collapsing the input image")
        self._collapsed, self._input_type = \
                collapse_pseudo_3d_image(reader.GetOutput(), self._input_type)

        # Just determine number of dimensions of the image. Should be always
        # two as we have just collapsed 3D images. Check it by an assertion:
        self._image_dim = len(self._collapsed.GetSpacing())
        assert (self._image_dim == 2), "Number of dimensions should be 2!"
        self._logger.debug("Determined image dimensionality: %d", self._image_dim)

        # If the number of components is higher than one, it means we are
        # dealing with a multichannel image. In such case every component is
        # processed separately. The grayscale image is extracted from the
        # multichannel image according to the provided options.
        if self._numbers_of_components > 1:
            self._process_multichannel_image()
        else:
            self._process_grayscale_image()

    def _process_multichannel_image(self):
        """
        """

        if self.options['colorOutputImage']:
            # Just initialize an array holding processed individual channels.
            processed_components = []

            # Now, we iterate over all components. Each component is processed
            # according to provided settings
            self._logger.debug("Extracting rgb image from rgb slice.")

            for i in range(self._numbers_of_components):
                self._logger.debug("Processing component: %s.", i)

                # Extract individual component from the multichannel image
                self._logger.debug("Extracting component: %s.", i)
                extract_filter = itk.VectorIndexSelectionCastImageFilter[
                            self._collapsed, self._rgb_out_component_type].New(
                            Input = self._collapsed,
                            Index = i)

                # Process the extracted components.
                self._logger.debug("Processing component: %s.", i)
                crop_index_s, crop_size_s = self._get_crop_settings()
                processed_channel = prepare_single_channel(
                    extract_filter.GetOutput(), self._rgb_out_component_type,
                    scale_factor = self.options['registrationResize'],
                    crop_index = crop_index_s,
                    crop_size = crop_size_s,
                    median_radius = None,
                    invert = self.options['invertMultichannelImage'])

                # Cast the processed channel to approperiate type (the type
                # based on which multicomponent image will be created)
                caster = itk.CastImageFilter[
                    self._rgb_out_component_type,
                    self._rgb_out_component_type].New(processed_channel)
                caster.Update()

                # Collect the processed channel in the results array
                self._logger.debug("Appending component %s to the results.", i)
                processed_components.append(caster.GetOutput())

            # Compose back the processed individual components into
            # multichannel image.
            compose = itk.ComposeImageFilter[
                self._rgb_out_component_type,
                self._input_type].New(
                    Input1 = processed_components[0],
                    Input2 = processed_components[1],
                    Input3 = processed_components[2])

            # Write the processed multichannel image.
            self._logger.debug("Writing the rgb(rgb) image to: %s.",
                            self.options['colorOutputImage'])
            writer = itk.ImageFileWriter[self._rgb_out_type].New(
                compose, FileName=self.options['colorOutputImage'])
            writer.Update()

        if self.options['grayscaleOutputImage']:
            # --- Now extract a grayscale image from the provided multichannel
            # image. The channel to extract is a specific color provided via
            # command line options.
            self._logger.debug("Extracting grayscale image from rgb slice.")

            # A simple dictionary mapping string provided via command line to a
            # specific image channel (image channel is provided as string while the
            # filter requires an integer)
            str_to_num_map = {'r':0, 'g':1, 'b':2, 'red':0, 'green':1, 'blue': 2}

            # Extract a specific color channel based on which grayscale image will
            # be prepared.
            registration_channel = self.options['registrationColorChannel']
            self._logger.debug("Extract color channel: %s.",
                               registration_channel)
            extract_filter = itk.VectorIndexSelectionCastImageFilter[\
                self._input_type, self._rgb_out_component_type].New(
                Input = self._collapsed,
                Index = str_to_num_map[registration_channel])
            extract_filter.Update()

            # A casting is required before processing the extracted color channel
            # as the extracted image type may be different than the grayscale
            # working type.
            caster = itk.CastImageFilter[
                self._rgb_out_component_type,
                self._grayscale_out_type].New(extract_filter)
            caster.Update()

            self._logger.debug("Processing a single channel...")
            crop_index_s, crop_size_s = self._get_crop_settings()
            processed_channel = prepare_single_channel(
                    caster.GetOutput(), self._grayscale_out_type,
                    scale_factor = self.options['registrationResize'],
                    crop_index = crop_index_s,
                    crop_size = crop_size_s,
                    median_radius = self.options['medianFilterRadius'],
                    invert = self.options['invertSourceImage'])

            # Write the grayscale(rgb) image to file.
            self._logger.debug("Writing the grayscale image to %s.",
                            self.options['grayscaleOutputImage'])
            writer = itk.ImageFileWriter[self._grayscale_out_type].New()
            print processed_channel
            print self._grayscale_out_type
            writer.SetInput(processed_channel)
            writer.SetFileName(self.options['grayscaleOutputImage'])
            writer.Update()

    def _get_crop_settings(self):
        try :
            crop_index = self.options['registrationROI'][0:2]
        except:
            crop_index = None

        try:
            crop_size = self.options['registrationROI'][2:4]
        except:
            crop_size = None

        return crop_index, crop_size

    def _process_grayscale_image(self):
        """
        """
        if self.options['colorOutputImage']:
            self._logger.debug("Extracting rgb(grayscale) image.")

            # The rgb(grayscale) image is created by simply cloning the grayscale
            # channel three times. However, before composing, the source image has
            # to be casted to the float type.
            self._logger.debug("Casting the image from %s, to %s",
                        str(self._input_type), str(self._rgb_out_component_type))
            caster = itk.CastImageFilter[self._input_type,
                                         self._rgb_out_component_type].New()
            caster.SetInput(self._collapsed)
            caster.Update()

            crop_index_s, crop_size_s = self._get_crop_settings()
            processed_channel = prepare_single_channel(
                caster.GetOutput(), self._rgb_out_component_type,
                scale_factor = self.options['registrationResize'],
                crop_index = crop_index_s,
                crop_size = crop_size_s,
                median_radius = None,
                invert = self.options['invertMultichannelImage'])

            # Finally the multichannel image can be composed from individual
            # grayscale channel(s) prepared in the previous step.
            self._logger.debug("Cloning the grayscale image into rgb image.")
            compose_filter = itk.ComposeImageFilter[
                self._rgb_out_component_type,
                self._rgb_out_type].New(
                    Input1=processed_channel,
                    Input2=processed_channel,
                    Input3=processed_channel)

            self._logger.debug("Writing the rgb(grayscale) image to %s.",
                            self.options['colorOutputImage'])
            writer = itk.ImageFileWriter[self._rgb_out_type].New(
                compose_filter, FileName=self.options['colorOutputImage'])
            writer.Update()

        # Now, let's extraxct the processed grayscale image (only if such
        # option is requested).
        if self.options['grayscaleOutputImage']:
            self._logger.debug("Extracting grayscale(grayscale) image.")
            crop_index_s, crop_size_s = self._get_crop_settings()
            processed_channel = prepare_single_channel(
                    self._collapsed, self._input_type,
                    scale_factor = self.options['registrationResize'],
                    crop_index = crop_index_s,
                    crop_size = crop_size_s,
                    median_radius = self.options['medianFilterRadius'],
                    invert = self.options['invertSourceImage'])

            # Cast the processed grayscale image to the grayscale image output type
            # as we want to keep the code flexible (it is possible that the output
            # type is different than grayscale writer type)
            self._logger.debug("Casting the image from %s, to %s",
                        str(self._input_type), str(self._grayscale_out_type))
            caster = itk.CastImageFilter[
                self._input_type, self._grayscale_out_type].New(processed_channel)
            caster.Update()

            # Finally we write the processed grayscale image to a file.
            self._logger.debug("Writing the grayscale(grayscale) image to %s.",
                            self.options['grayscaleOutputImage'])
            writer = itk.ImageFileWriter[self._grayscale_out_type].New(caster,\
                        FileName=self.options['grayscaleOutputImage'])
            writer.Update()


    @staticmethod
    def parseArgs():
        usage = "python [options]"
        parser = OptionParser(usage = usage)

        parser.add_option('--inputFilename', '-i', dest='inputFilename', type='str',
                default=None, help='File for preparation.')
        parser.add_option('--grayscaleOutputImage', '-g',
                        dest='grayscaleOutputImage', type='str', default=None,
                        help='Name of the output grayscale image.')
        parser.add_option('--colorOutputImage', '-r',
                        dest='colorOutputImage', type='str', default=None,
                        help='Name of the output multichannel image.')

        parser.add_option('--registrationROI', default=None,
                            type='int', dest='registrationROI',  nargs=4,
                            help='ROI of the input image used for registration (ox, oy, sx, sy).')
        parser.add_option('--registrationResize', default=None,
                            type='float', dest='registrationResize',
                            help='Scaling factor for the source image used for registration. Float between 0 and 1.')
        parser.add_option('--registrationColorChannel', default='blue',
                            type='str', dest='registrationColorChannel',
                            help='In rgb images - color channel on which \
                            registration will be performed. Has no meaning for \
                            grayscale input images. Possible values: r/red, g/green, b/blue.')
        parser.add_option('--medianFilterRadius', default=None,
                dest='medianFilterRadius', type='str',
                help='Median filter radius according to ImageMagick syntax.')
        parser.add_option('--invertSourceImage', default=False,
                dest='invertSourceImage',  action='store_const', const=True,
                help='Invert source image: both, grayscale and multichannel, before registration')
        parser.add_option('--invertMultichannelImage', default=False,
                dest='invertMultichannelImage',  action='store_const', const=True,
                help='Invert source image: both, grayscale and multichannel, before registration')

        logging_settings = OptionGroup(parser, 'Logging options')
        logging_settings.add_option('--loglevel', dest='loglevel', type='str',
                default='INFO', help='Severity of the messages to report: CRITICAL | ERROR | WARNING | INFO | DEBUG')
        logging_settings.add_option('--logFilename', dest='logFilename',
                default=None, action='store', type='str',
                help='If defined, puts the log into given file instead of printing it to stderr.')

        parser.add_option_group(logging_settings)
        (options, args) = parser.parse_args()

        return (options, args)


if __name__ == '__main__':
    options, args = prepare_slice_for_seq_alignment.parseArgs()
    filter = prepare_slice_for_seq_alignment(options, args)
    filter.launch_filter()
