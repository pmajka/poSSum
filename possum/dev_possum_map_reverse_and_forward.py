#!/usr/bin/python
# -*- coding: utf-8 -*

import os
import sys
import itk

from optparse import OptionGroup

from possum.pos_wrapper_skel import enclosed_workflow
from possum.pos_common import r
from possum import pos_itk_transforms
from possum import pos_itk_core


# Forward direction of processing. This means the images are transformed
# from the experimental image stack towards the reference atlas image.
C_DIR_FWD = "from_raw_to_atlas"

# Inverse direction means, on the other hand, that the data is mapped
# from the reference atlas space towards the expeimental dataset.
C_DIR_INV = "from_atlas_to_raw"

# Just store these values in an array
C_ALLOWED_DIRECTIONS = [C_DIR_FWD, C_DIR_INV]

# Define the single component processing type. All single component data
# type will be converted to this tupe for the purpose of processing.
# It will be converted back to its initial data type upon completion of
# the processing.
C_INTERMEDIATE_SINGLE_COMPONENT_TYPEDEF = ('scalar', 'double', 3)

# Define constants for the interpolation types. Just to avoid
# using hardcoded numbers.
C_NN_INTERPOLATOR = 0
C_LINEAR_INTERPOLATOR = 1
C_BSPLINE_INTERPOLATOR = 2


class bidirectional_coregistration_mapper(enclosed_workflow):
    """
    Assumptions about data types:

        1) RGB image has to have pixel type of 24bpp uchar. This means that
        each component is a uchar image - the values are integers spanning
        from 0 to 255. No RGBA images are supported. Floating point RGB images
        are not supported either.

        .. note::

            Again: only uchar, three channel RGB images.
            No other color images are supported.

        2) Vector images of (preferably) three components. At least, I've
        tested it with three components. It should workder with an arbitrary
        number of components. Should is a keyword here.

    Some usage examples.

    This example maps data from the atlas space to the raw image stack.
    This is determined by the `--direction "from_atlas_to_raw"` argument.
    This particular example uses linear interpolation (`--interpolation 1`)
    which is a good idea when one is dealing with RGB images.

    Sections in this example are cut in the coronal plane (`-s 1` parameter).
    Indexing of the sections starts from one (`--offset 1`)

    Here is the actual code::
    this_script.py \
        -i reference_atlas.nii.gz \
        -r rgb_stack.nii.gz \
        -o from_atlas_to_raw.nii \
        --loglevel INFO \
        --coregistration-affine reference_to_deformable_image_affine.txt \
        --coregistration-deformable-forward reference_to_deformable_image_deformable_warp.nii.gz \
        --coregistration-deformable-inverse reference_to_deformable_image_deformable_inverse_warp.nii.gz \
        -s 1 \
        --section-affine-template "012_sections_affine_transformations/%04d.txt" \
        --section-deformable-inv-template "013_sections_deformable_transformations_fwd_and_inv/%04dInverse.nii.gz" \
        --section-deformable-fwd-template "013_sections_deformable_transformations_fwd_and_inv/%04d.nii.gz" \
        --direction "from_atlas_to_raw" \
        --offset 1 \
        --interpolation 1

    Here is an analogous example which maps the data from the raw image stack
    coordinate system to the atlas space image::

    this_script.py \
        -i reference_atlas.nii.gz \
        -r rgb_stack.nii.gz \
        -o from_raw_to_atlas.nii \
        --loglevel INFO \
        --coregistration-affine reference_to_deformable_image_affine.txt \
        --coregistration-deformable-forward reference_to_deformable_image_deformable_warp.nii.gz \
        --coregistration-deformable-inverse reference_to_deformable_image_deformable_inverse_warp.nii.gz \
        -s 1 \
        --section-affine-template "012_sections_affine_transformations/%04d.txt" \
        --section-deformable-inv-template "013_sections_deformable_transformations_fwd_and_inv/%04dInverse.nii.gz" \
        --section-deformable-fwd-template "013_sections_deformable_transformations_fwd_and_inv/%04d.nii.gz" \
        --direction "from_raw_to_atlas" \
        --offset 1 \
        --interpolation 1

    """

    _slicing_planes_settings = {
        "sagittal": {'permutation': [2, 0, 1], 'flip': [0, 0, 0], 'axis': 0},
        "coronal": {'permutation': [0, 2, 1], 'flip': [0, 0, 0], 'axis': 1},
        "axial": {'permutation': [0, 1, 2], 'flip': [0, 0, 0], 'axis': 2},
        "horizontal": {'permutation': [0, 1, 2], 'flip': [0, 0, 0], 'axis': 2},
        0: {'permutation': [2, 0, 1], 'flip': [0, 0, 0], 'axis': 0},
        1: {'permutation': [0, 2, 1], 'flip': [0, 0, 0], 'axis': 1},
        2: {'permutation': [0, 1, 2], 'flip': [0, 0, 0], 'axis': 2}}

    _interpolators = {
        C_NN_INTERPOLATOR: itk.NearestNeighborInterpolateImageFunction,
        C_LINEAR_INTERPOLATOR: itk.LinearInterpolateImageFunction,
        C_BSPLINE_INTERPOLATOR: itk.BSplineInterpolateImageFunction}

    def _validate_options(self):
        super(self.__class__, self)._validate_options()

        # This is to validate potentially all input data,
        # Unfortunately, some of the parameters are defined
        # after this validation step and cannot be validated
        # here. They will be checked individually later.

        assert self.options.input_image, \
            self._logger.error(r("Moving image is required, Please provide \
            the `--input-image` parameter."))

        assert self.options.output_image, \
            self._logger.error(r("Output image is required, Please provide \
            the `--output-image` parameter."))

        assert self.options.reference_image, \
            self._logger.error(r("Reference image is required. Please provide \
            the `--reference-image` parameter"))

        assert self.options.coregistration_affine, \
            self._logger.error(r("Affine, 3D transform is not provided. Please \
            supply the `--coregistration-affine` parameter"))

        assert self.options.coregistration_deformable_forward and \
               self.options.coregistration_deformable_inverse ,\
            self._logger.error(r("Both, forward and inverse 3D warps are \
            required. One or both warp fields are not provided. Please \
            supply both, `--coregistration-deformable-forward` and \
            `--coregistration-deformable-inverse` parameters."))

        assert self.options.section_deformable_fwd_template and \
                self.options.section_deformable_inv_template ,\
            self._logger.error(r("Both forward and inverse 2D warps are \
            required. One or both warp field filename templates are \
            missing. Please provide `--section-deformable-fwd-template` \
            and `--section-deformable-inv-template`."))

    def _load_images(self):
        """
        Load the reference image (target for mapping) and the input image
        (which is the source of the data). Which image is which is determined
        by the mapping direction which is provided by the command line.

        :return: None
        :rtype: None
        """

        # Just convenient aliases
        input_ = self.options.input_image
        reference = self.options.reference_image

        images = {
            C_DIR_INV: (input_, reference),
            C_DIR_FWD: (reference, input_)}

        # Set moving and fixed images based on the direction
        # of mapping provided as the command line parameter..
        moving_image, fixed_image = images[self.direction]

        self._load_single_image("fixed", fixed_image)
        self._load_single_image("moving", moving_image)

    def _load_single_image(self, attr_base, filename):
        """
        Load itk image and store the image itself and its type
        as a class attribute. The image is stored as
        `<prefix>_image` attribute and the type of the image
        is stored under the `<prefix> type` attribute.

        :param attr_base: The base for the class attribute name.
        :type attr_base: str

        :return: None
        :rtype: None
        """

        # Generating the attributes names based on
        # the image type.
        image_attr_name = "_" + attr_base + "_image"
        type_attr_name = "_" + attr_base + "_type"

        setattr(self, image_attr_name,
            pos_itk_transforms.read_itk_image(filename))
        setattr(self, type_attr_name,
            pos_itk_core.autodetect_file_type(filename))

        # We read and report the number of components of the image.
        numbers_of_components = \
            getattr(self, image_attr_name).GetNumberOfComponentsPerPixel()
        self._logger.info("Number of components of the image %s is: %d.",
            filename, numbers_of_components)

    def _load_coregistration_transformation(self):
        """
        Load the coregistration transformation so it will be loaded once
        and once only. Different methods are used to provide the coregistration
        transforms in different directions. See documentation of these individual
        methods for details.

        :return: None
        :rtype: None
        """

        coregistration = {
            C_DIR_INV: self._get_atlas_to_reconstruction_coreg,
            C_DIR_FWD: self._get_reconstruction_to_atlas_coreg}
        self._coregistration_transform = coregistration[self.direction]()

    def _inspect_input_images(self, sections_range):
        """
        Verify if all the files are availabe: All images have to be available. If
        the case is different, the workflow will not proceed and the user will
        be asked to supply the missing images.

        :param sections_range: list (oh well... actually any iterable) with
                               indexes of consecutive sections
        :type sections_range: list

        :return: `True` if all required files are available.
                 Exits otherwise.
        :rtype: Bool
        """

        # Iterate over all filenames beeing used it the whole workflow
        # and check if all of them exists.
        filenames_to_check = map(lambda x: \
          self.options.section_deformable_fwd_template% x, sections_range)
        filenames_to_check += map(lambda x: \
          self.options.section_deformable_inv_template % x, sections_range)
        filenames_to_check += map(lambda x: \
          self.options.section_affine_template % x, sections_range)

        # Just go trought all the filenames and check if the files
        # exitst. If a files does not exist... well sorry...
        # we cannot continue.
        for slice_filename in filenames_to_check:
            self._logger.debug("Checking for image: %s.", slice_filename)

            if not os.path.isfile(slice_filename):
                self._logger.error("File does not exist: %s. Exiting",
                                   slice_filename)
                sys.exit(1)

        # If everything goes ok, return True.
        return True

    def launch(self):
        # Execute the parents before-execution activities
        super(self.__class__, self)._pre_launch()

        # Just for our convenience, we make an alias
        # for the direction of the computations
        self.direction = self.options.direction

        self._load_images()
        self._load_coregistration_transformation()

        # Define the single component processing type All single component data
        # type will be converted to this tupe for the purpose of processing.
        # It will be converted back to its initial data type upon completion of
        # the processing.
        self._processing_type = \
            pos_itk_core.io_component_string_name_to_image_type[
            C_INTERMEDIATE_SINGLE_COMPONENT_TYPEDEF]

        # Determine the number of components in the image to be processed.
        # Single component image is easy to process. Multichannel workflow
        # is a bit more complicated
        self._numbers_of_components = \
            self._moving_image.GetNumberOfComponentsPerPixel()

        # There are different workflows depending on the number of components,
        # of the provided input image.
        if self._numbers_of_components > 1:
            processed_image = \
                self.use_multicomponent_workflow()
        else:
            processed_image = \
                self.use_single_component_workflow()

        # This is a very important line of code. It gives us the final image!
        # Yey....
        pos_itk_transforms.write_itk_image(
            processed_image, self.options.output_image)

        # Run parent's post execution activities
        super(self.__class__, self)._post_launch()

    def use_single_component_workflow(self):
        """
        This is a subpart of the mapping worklfow dedicated for processing
        an image comprising only one component. Such images might
        be for instance the grayscale images, some sort of density maps
        or label images.
        """

        self._logger.debug("Entering grayscale workflow.")

        # Single component workflow is simple enough so that the type of a
        # single component is the same as the actual type of the image.
        # (as the the image has only single channel:)
        self._component_type = self._moving_type

        # Before we start the processing, we cast the image to an intermediate
        # type which we'll be using throught the rest of the processing.
        pre_cast_filter = \
            itk.CastImageFilter[
            (self._component_type, self._processing_type)].New()
        pre_cast_filter.SetInput(self._moving_image)
        pre_cast_filter.Update()

        # Here we process a single channel. In this case there is only single
        # channel.
        processed_component = \
            self.process_single_component(pre_cast_filter.GetOutput())

        # After the component is processed, it is time to cast it back to the
        # initial data type the image was provided in.
        cast_filter = \
            itk.CastImageFilter[
            (self._processing_type, self._component_type)].New()
        cast_filter.SetInput(processed_component)
        cast_filter.Update()
        processed_image = cast_filter.GetOutput()

        self._logger.debug("Exiting grayscale workflow.")

        # That's it. We return the processed image here.
        return processed_image

    def use_multicomponent_workflow(self):
        """
        This method executes a multichannel workflow. This part of the mapping
        workflow is a bit more complicated. In this workflow, the multichannel
        / multicomponent image is siplit into individual components and each of
        the components is processed separately. At the end of the processing,
        all individual channels are merged back into a multicomponent image and
        returned.
        """

        self._logger.debug("Entering multichannel workflow.")

        # Ok, this is a bit complicated. What do we do here is that we
        # determine the datatype of a single component. This is not easy as ITK
        # is quite inconsistent when it comes to handling vector and RGB
        # images. Basically what is going one here is:
        # 1) RGB images => ('scalar', 'unsigned_char', 3)
        # 2) Vector images =>
        #    ('scalar', type_derived_from_the_actual_image, 3)
        # So below we determine data type of a single component according to
        # these rules.

        image_type = \
            pos_itk_core.io_image_type_to_component_string_name[self._moving_type]
        if image_type[0] == 'rgb' and image_type[1] == 'unsigned_char':
            image_type_tuple = ('scalar', 'unsigned_char', 3)
        if image_type[0] == 'vector':
            image_type_tuple = ('scalar', image_type[1], 3)

        # Define a single component image type
        component_type = \
            pos_itk_core.io_component_string_name_to_image_type[image_type_tuple]

        # We will collect the consecutive processed components
        # into this array
        processed_components = []

        # Extract the component `i` from the composite image,
        # and process each component independently.
        for i in range(self._numbers_of_components):

            self._logger.debug("Starting processing channel %d of %d.",
                i + 1, self._numbers_of_components)

            extract_filter = \
                itk.VectorIndexSelectionCastImageFilter[
                self._moving_type, component_type].New()
            extract_filter.SetIndex(i)
            extract_filter.SetInput(self._moving_image)

            # Cast the image to an intermediate data type fo the
            # purposes of processing.
            cast_filter = \
                itk.CastImageFilter[
                    (component_type, self._processing_type)].New()
            cast_filter.SetInput(extract_filter)
            cast_filter.Update()

            # Process the component.
            processed_component = \
                self.process_single_component(cast_filter.GetOutput())

            # And then, cast the processed component into the data
            # type of the initial image.
            writer_cast_filter = \
                itk.CastImageFilter[
                    (self._processing_type, component_type)].New()
            writer_cast_filter.SetInput(processed_component)
            writer_cast_filter.Update()

            # Store the processed component in an array.
            processed_components.append(writer_cast_filter.GetOutput())

            self._logger.debug("Finished processing channel %d of %d.",
                i + 1, self._numbers_of_components)

        # After iterating over all channels, compose the individual
        # components back into multichannel image.
        self._logger.info(r("Composing processed channels back \
            into multichannel image."))

        # Compose individual components back into multicomponent image.  In
        # theory arbitrary number of components is supported but it has to be
        # more than one :)
        compose = \
            itk.ComposeImageFilter[component_type, self._moving_type].New()

        for i in range(self._numbers_of_components):
            compose.SetInput(i, processed_components[i])
        compose.Update()

        return compose.GetOutput()

    def process_single_component(self, single_component_image):
        """
        This is where things get a bit more complicated. What happend here is
        that, depending on the direction of processing (either forward or
        reverse).

        When we map data from the raw image space to the atlas space, the
        coregistration with the atlas is conducted after the (affine and
        deformable) reconstruction step.

        When we map data from the atlas space to the raw image space, the
        mapping to the raw image is conducted as the first stage of processing
        before inverse mapping from the deformable reconstruction to the raw
        image space.

        This method handles mapping in both directions therefore its
        implementation may look a bit convoluted.

        :param single_component_image: The three-dimensional image to be
          processed. The provided image has to be three-dimensional.
        :type single_component_image: `itk.Image` class instance.

        :return: Provided single component image processed
                 according to provided options.
        :rtype: `itk.Image`
        """

        if self.direction == C_DIR_INV:
            interpolator = self._build_interpolator(single_component_image)
            input_image = pos_itk_transforms.reslice_image(
                self._coregistration_transform,
                single_component_image,
                self._fixed_image,
                interpolator=interpolator)
        elif self.direction == C_DIR_FWD:
            input_image = single_component_image

        # Determine the type of the single section. The type of the single
        # section is determined based on the type of the 3D image.
        self._section_type = \
            pos_itk_core.types_reduced_dimensions[self._processing_type]

        # This array will hold individual sections once they are processed.
        collect_sections = []

        # Here we determine the number of individual 2D sections to be
        # processed. The number of sections is determined based on the provided
        # slicing axis.
        sections_number = \
            input_image.GetLargestPossibleRegion().GetSize()[\
            self.options.slicing_axis]
        sections_range = \
            range(self.options.offset,
                  sections_number + self.options.offset)

        self._logger.info("Determined number of sections: %d.",
            sections_number)
        self._logger.info("Indexes of sections to be processed: %s.",
            " ".join(map(str, sections_range)))
        self._inspect_input_images(sections_range)

        # Nothing special going one, we process each section one
        # by one.
        for section_index in sections_range:
            collect_sections.append(
                self._process_single_section(input_image, section_index))

        # Once all sections are processed, we merge them back into
        # 3D image. Pretty cool, huh...
        cast_to_volume = itk.JoinSeriesImageFilter[
            (self._section_type, self._processing_type)].New()
        for i, section in enumerate(collect_sections):
            cast_to_volume.SetInput(i, section)
        cast_to_volume.Update()

        # Then we reorient the 3D iamge and we set all the parameters of the
        # volume so it matches exactly the input stack.
        permutation_filter = \
            itk.PermuteAxesImageFilter[cast_to_volume.GetOutput()].New()
        permutation_filter.SetInput(cast_to_volume)
        permutation_filter.SetOrder(
            self._slicing_planes_settings[
                self.options.slicing_axis]['permutation'])
        permutation_filter.Update()

        change_stack_information = \
            itk.ChangeInformationImageFilter[(self._processing_type,)].New()
        change_stack_information.ChangeDirectionOn()
        change_stack_information.ChangeOriginOn()
        change_stack_information.ChangeSpacingOn()
        change_stack_information.UseReferenceImageOn()
        change_stack_information.SetReferenceImage(input_image)
        change_stack_information.SetInput(permutation_filter)
        change_stack_information.Update()

        # Again, depending on the direction of mapping, we either conduct
        # mapping to the atlas space or not.
        if self.direction == C_DIR_INV:
            return change_stack_information.GetOutput()
        elif self.direction == C_DIR_FWD:
            interpolator = self._build_interpolator(
                change_stack_information.GetOutput())
            coregistered_to_atlas = pos_itk_transforms.reslice_image(
                self._coregistration_transform,
                change_stack_information.GetOutput(),
                self._fixed_image,
                interpolator=interpolator)
            return coregistered_to_atlas

    def _build_interpolator(self, image_to_interpolate):
        """
        This function is a bit irritating as preparing a correct validator
        takes a while and highldy depends on the type of the interpolator
        (e.g. the BSpline interpolator reguires one to set an additional
        parameter while other interpolators do not.)

        :param image_to_interpolate: `itk.Image` for which we need to
          build the image interpolation function.
        :type image_to_interpolate: `itk.Image`

        :return: Image interpolation function to be supplied to a
                 `itk.ResampleImageFilter` filter.
        :rtype: One of the `itk.InterpolateImageFunction`
                template subclasses
        """

        # Get the type of the interpolation based on the provided command
        # line parameters.
        interpolation_type = self.options.interpolation

        # We use double as an data type for intermediate stages
        # of processing.
        data_type = itk.D

        if interpolation_type == C_BSPLINE_INTERPOLATOR:
            interpolator_type = (image_to_interpolate, data_type, data_type)
            interpolator = \
              self._interpolators[interpolation_type][interpolator_type].New()
            interpolator.SetSplineOrder(3)
        else:
            interpolator_type = (image_to_interpolate, data_type)
            interpolator = \
              self._interpolators[interpolation_type][interpolator_type].New()

        return interpolator

    def _process_single_section(self, section, section_index):
        """
        Applies relevant transformations to a single two dimensional image (aka
        a section). This method actually extracts an image from the 3D stack
        and only then reslices it. Therefore we need to provide the method
        with the actual section index to process.

        :param section: Two dimensional image to be resliced.
        :type section: `itk.Image`

        :param section_index: Index of the section to be extracted from the
          three-dimensional image stack and to be resliced. Note that this
          comes as section index as to be passed to the filename templates
          no the one starting from zero. The section index which starts from
          zero will be calculated automatically.
        :type section_index: int

        :return: Image resliced with appropriate transformations.
        :rtype: `itk.Image`

        """

        # This is super irritating, but yes, we have to
        # convert the section index back to plane_index
        # to propoerly define an itk region.
        input_region = self._get_extration_region(section_index, section)

        extract_single_section = \
            itk.ExtractImageFilter[
            (self._processing_type, self._section_type)].New()
        extract_single_section.SetExtractionRegion(input_region)

        extract_single_section.SetInput(section)
        extract_single_section.SetDirectionCollapseToIdentity()
        extract_single_section.Update()

        section_transform = self.section_transform(section_index)

        interpolator = \
            self._build_interpolator(extract_single_section.GetOutput())
        transformed_image = pos_itk_transforms.reslice_image(
            section_transform, extract_single_section.GetOutput(),
            interpolator=interpolator)

        return transformed_image

    def _get_extration_region(self, section_index, section):
        """
        Define a image region to extract from a three dimensional image in
        order to get a two dimensional image (aka section).

        :param section: Two dimensional image to be resliced.
        :type section: `itk.Image`

        :param section_index: Index of the section to be extracted from the
          three-dimensional image stack and to be resliced. Note that this
          comes as section index as to be passed to the filename templates
          no the one starting from zero. The section index which starts from
          zero will be calculated automatically.
        :type section_index: int

        :return: Image region which defines a 2D section in a 3D image.
        :rtype: `itk.Region` instance.
        """

        # This is super irritating, but yes, we have to
        # convert the section index back to plane_index
        # to propoerly define an itk region.
        plane_index = section_index - self.options.offset

        ndim = self._moving_image.GetImageDimension()
        input_region_origin = [0] * ndim
        input_region_origin[self.options.slicing_axis] = plane_index
        input_region_size = \
            list(section.GetLargestPossibleRegion().GetSize())
        input_region_size[self.options.slicing_axis] = 0

        input_region = \
            pos_itk_core.get_image_region(ndim,
                input_region_origin,
                input_region_size)

        return input_region

    def _get_deformable_to_raw_transformation(self, section_index):
        """
        Reads a series of transformations which take a raw image (i.e. image
        from the image stack before processing) into the deformable
        reconstruction image space.

        :param section_index: Index of the section to be extracted from the
          three-dimensional image stack and to be resliced. Note that this
          comes as section index as to be passed to the filename templates
          no the one starting from zero. The section index which starts from
          zero will be calculated automatically.
        :type section_index: int

        :return: List of itk transformations.
        :rtype: [``itk.Tranfsorm``, ...]
        """

        transforms = \
            pos_itk_transforms.itk_read_transformations_from_files(
                [self.options.section_affine_template % section_index,
                self.options.section_deformable_inv_template % section_index])
        transforms = \
            [transforms[1], transforms[0].GetInverseTransform()]

        return transforms

    def _get_raw_to_deformable_transformation(self, section_index):
        """
        Reads a series of transformations which take an image from the
        deformable reconstruction and map it to the raw image space.

        :param section_index: Index of the section to be extracted from the
          three-dimensional image stack and to be resliced. Note that this
          comes as section index as to be passed to the filename templates
          no the one starting from zero. The section index which starts from
          zero will be calculated automatically.
        :type section_index: int

        :return: List of itk transformations.
        :rtype: [``itk.Tranfsorm``, ...]
        """

        transforms = \
            pos_itk_transforms.itk_read_transformations_from_files(
                [self.options.section_affine_template % section_index,
                self.options.section_deformable_fwd_template % section_index])
        transforms = \
            [transforms[0], transforms[1]]
        return transforms

    def _get_atlas_to_reconstruction_coreg(self):
        """
        Reads a series of transformations which map the deformable
        reconstruction into the reference (atlas) image.

        :return: List of itk transformations.
        :rtype: [``itk.Tranfsorm``, ...]
        """

        transforms = \
            pos_itk_transforms.itk_read_transformations_from_files(
            [self.options.coregistration_affine,
             self.options.coregistration_deformable_forward])

        transforms = [transforms[0], transforms[1]]
        return transforms

    def _get_reconstruction_to_atlas_coreg(self):
        """
        Reads a series of transformations which map an 3D image from the
        reference image space (the atlas space) into the deformable
        reconstruction space.

        :return: List of itk transformations.
        :rtype: [``itk.Tranfsorm``, ...]
        """

        transforms = \
            pos_itk_transforms.itk_read_transformations_from_files(
            [self.options.coregistration_affine,
             self.options.coregistration_deformable_inverse])

        transforms = [transforms[1], transforms[0].GetInverseTransform()]
        return transforms

    def _get_direction(self):
        return self._direction

    def _set_direction(self, value):
        self._direction = value

    def _get_section_transform(self):
        section_transforms = {
            C_DIR_INV: self._get_deformable_to_raw_transformation,
            C_DIR_FWD: self._get_raw_to_deformable_transformation}
        return section_transforms[self.direction]

    def _set_section_transform(self, value):
        raise ReadOnlyError(value)

    section_transform = \
        property(_get_section_transform, _set_section_transform, None, None)
    direction = \
        property(_get_direction, _set_direction, None, None)

    @staticmethod
    def parseArgs():
        usage_string = "%\nprog -i FILE -r FILE -o FILE \n\
            --coregistration-affine FILE \n\
            --coregistration-deformable-forward FILE \n\
            --coregistration-deformable-inverse FILE \n\
            --section-affine-template FILE \n\
            --section-deformable-fwd-template FILE \n\
            --section-deformable-inv-template FILE \n\
            [other options]"

        parser = \
            enclosed._getCommandLineParser()
        parser.set_description(r("""The main purpose of the %prog workflow is to \
            map any kind of spatial imaging data defined in the space of \
            the experimental image into the space of the reference image \
            and the other way around: to map spatially defined imaging data \
            from the reference space into the space (coordinate system) of the \
            raw (experimental) image stack. As this kind of mapping involves \
            a lot of transformations, this script may look a bit complicated. \
            Just follow the examples from the docstring of the class and \
            its all gonna be fine. So stop reading this description and go \
            check the DOCSTRING of this class."""))
        parser.set_usage(usage_string)

        parser.add_option('--input-image', '-i', dest='input_image',
            type='str', default=None, metavar="FILE",
            help=r("Input image of the mapping. \
            This alway the 'experimental image' which is an image with the \
            experimental data. This is never the reference image - the atlas image.\
            Anyway, this image is anything located in the experimental image \
            stack space."))
        parser.add_option('--reference-image', '-r', dest='reference_image',
            type='str', default=None, metavar="FILE",
            help=r("Reference image of the mapping \
            or any image data located in the reference (atlas) space. Usually \
            this will be indeed the reference atlas itself."))
        parser.add_option('--output-image', '-o', dest='output_image',
            type='str', default=None, metavar="FILE",
            help=r("The output image filename. \
            This is where the result of the computations will be saved to. \
            The type of the output image is the same as the type of the \
            input image."))
        parser.add_option('--slicing-axis', '-s',
            dest='slicing_axis', type='int', default=1, metavar="INT",
            help=r('Index of the slicing axis: 0, 1 or 2. Default is 1. \
            Zero corresponds to sagittal plane, One corresponds to \
            coronal plane while two represents the horizontal plane.\
            This works only when the images follow the RAS orientation.'))
        parser.add_option('--direction', dest='direction',
            default='from_atlas_to_raw', type="choice",
            choices=C_ALLOWED_DIRECTIONS, metavar="DIRECTION",
            help=r("Direction in which the mapping will be conducted. \
            There are two directions allowed. The 'from_raw_to_atlas' \
            value will map the data from the raw (experimental) stack \
            space into the reference space (the atlas spce). \
            The 'from_atlas_to_raw' will use data located in the atlas \
            space into the space of the input image stack."))
        parser.add_option('--offset', dest='offset',
            default=0, type='int', metavar="INT",
            help=r('Index of the first section. Defaults to 0, but \
            will be usually 1. Use this if numberinf of your sections starts \
            with number other that zero. Please, to not use negative \
            numbers. This will not work.'))
        parser.add_option('--interpolation', dest='interpolation',
            default=1, type='int', metavar="INT",
            help=r('Define interpolation type used for reslicing the images. \
            Three options are allowed at the moment: 0 for NN interpolation, \
            1 for linear interpolation and 2 for order 3 BSpline \
            interpolation.'))
        parser.add_option('--coregistration-affine',
            dest='coregistration_affine', type='str', default=None,
            metavar="FILE",
            help=r("Affine transformation from the deformable reconstruction \
            3D image to the reference image (i.e. the atlas image).\
            This is an obligatory parameter."))
        parser.add_option('--coregistration-deformable-forward',
            dest='coregistration_deformable_forward', type='str',
            metavar="FILE",
            default=None, help=r("Forward deformable warp which maps the \
            3D deformable reconstruction image to the reference image \
            space. This is an obligatory parameter."))
        parser.add_option('--coregistration-deformable-inverse',
            dest='coregistration_deformable_inverse', type='str',
            metavar="FILE",
            default=None, help=r("Inverse deformable warp which maps the \
            3D deformable reconstruction image to the reference image \
            space. This is an obligatory parameter."))
        parser.add_option('--section-affine-template',
            dest='section_affine_template', type='str', default=None,
            metavar="FILE",
            help=r("Filename template for affine transformation from raw stack \
            to affine reconstruction. One should provide values like this: \
            'affine_\%04d.txt'."))
        parser.add_option('--section-deformable-fwd-template',
            dest='section_deformable_fwd_template', type='str', default=None,
            metavar="FILE",
            help=r("Filename template for forward warps from the affine \
            reconstruction to deformable reconstruction. The values should be \
            provided like this: 'section_\%04d_Warp.nii.gz'."))
        parser.add_option('--section-deformable-inv-template',
            dest='section_deformable_inv_template', type='str', default=None,
            metavar="FILE",
            help=r("Filename template for inverse warps from affine \
            reconstruction to deformable reconstruction. Therefore, in fact \
            they are warps from deformably reconstructed sections into the \
            affine recosntruction spcae. The values should be like this: \
            'section_\%04d_Warp.nii.gz'."))

        (options, args) = parser.parse_args()
        return (options, args)


if __name__ == '__main__':
    options, args = bidirectional_coregistration_mapper.parseArgs()
    workflow = bidirectional_coregistration_mapper(options, args)
    workflow.launch()
