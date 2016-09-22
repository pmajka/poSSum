#!/usr/bin/python
# -*- coding: utf-8 -*

import itk
import logging

"""
# http://sphinx-doc.org/domains.html#the-python-domain
"""

# Dictionary below copied from (Sun Apr  7 14:04:28 CEST 2013)
# http://code.google.com/p/medipy/source/browse/lib/medipy/itk/types.py?name=default&r=0da35e1099e5947151dee239f7a09f405f4e105c
io_component_type_to_type = {
    itk.ImageIOBase.UCHAR: itk.UC,
        itk.ImageIOBase.CHAR: itk.SC,
        itk.ImageIOBase.USHORT: itk.US,
        itk.ImageIOBase.SHORT: itk.SS,
        itk.ImageIOBase.UINT: itk.UI,
        itk.ImageIOBase.INT: itk.SI,
        itk.ImageIOBase.ULONG: itk.UL,
        itk.ImageIOBase.LONG: itk.SL,
        itk.ImageIOBase.FLOAT: itk.F,
        itk.ImageIOBase.DOUBLE: itk.D,
}

# And this is my own invention: a dictionary that converts tuple of specific
# image parameters into itk image type. We all love ITK heavy templated code
# style!
io_component_string_name_to_image_type = {
    ('scalar', 'short', 3): itk.Image.SS3,
        ('scalar', 'unsigned_short', 3): itk.Image.US3,
        ('scalar', 'unsigned_char', 3): itk.Image.UC3,
        ('scalar', 'float', 3): itk.Image.F3,
        ('scalar', 'short', 2): itk.Image.SS2,
        ('scalar', 'unsigned_short', 2): itk.Image.US2,
        ('vector', 'float', 3): itk.Image.VF33,
        ('vector', 'double', 3): itk.Image.VD33,
        ('vector', 'float', 2): itk.Image.VF22,
        ('vector', 'double', 2): itk.Image.VD22,
        ('scalar', 'unsigned_char', 2): itk.Image.UC2,
        ('scalar', 'float', 2): itk.Image.F2,
        ('scalar', 'double', 3): itk.Image.D3,
        ('scalar', 'double', 2): itk.Image.D2,
        ('rgb', 'unsigned_char', 2): itk.Image.RGBUC2,
        ('rgb', 'unsigned_char', 3): itk.Image.RGBUC3,
        ('vector', 'unsigned_char', 3): itk.Image.RGBUC3,
        ('vector', 'unsigned_char', 2): itk.Image.RGBUC2
}

# Here we define mapping which allows us to quickly map an
# image class to its data type, pixel type and dimensionality.
# This turns out to be very usefull, believe me.
io_image_type_to_component_string_name = \
    dict((io_component_string_name_to_image_type[k], k)
         for k in io_component_string_name_to_image_type)


# Another quite clever dictionary. This one converts given image type to the
# same type but with number of dimensions reduced by one (e.g. 3->2).
types_reduced_dimensions = {
    itk.Image.SS3: itk.Image.SS2,
        itk.Image.US3: itk.Image.US2,
        itk.Image.UC3: itk.Image.UC2,
        itk.Image.RGBUC3: itk.Image.RGBUC2,
        itk.Image.F3: itk.Image.F2,
        itk.Image.D3: itk.Image.D2,
        itk.Image.VD33: itk.Image.VD22,
        itk.Image.VF33: itk.Image.VF22
}

# This time a dictionary for stacking slices (a reverse of
# types_reduced_dimensions dict):
types_increased_dimensions = dict((types_reduced_dimensions[k], k)
                                  for k in types_reduced_dimensions)


def get_image_region(image_dim, crop_index, crop_size):
    """
    This functions makes `itk.ImageRegion` out of index and size tuples of
    aproperiate size. What is an image region? According to itk reference:

    | ImageRegion is an class that represents some structured portion or piece of
    | an Image. The ImageRegion is represented with an index and a size in each
    | of the n-dimensions of the image. (The index is the corner of the image,
    | the size is the lengths of the image in each of the topological
    | directions.)

    Don't believe? Check it out:
    http://www.itk.org/Wiki/ITK/Examples/Images/ImageRegion

    Anyway, it seems that the image region is a one of the most important
    classes in the whole `itk` universe.

    :param image_dim: dimensionality of the region.
    :type image_dim: int, either 2 or 3

    :param crop_index: index of the beginning of the image region
    :type crop_index: tuple of 2 or 3 integer values, it depends on the region
                      dimensionality

    :param crop_size: size of the region.
    :type crop_size: tuple of 2 or 3 integer values.
    """
    bounding_box = itk.ImageRegion[image_dim]()
    bounding_box.SetIndex(map(int, crop_index))
    bounding_box.SetSize(map(int, crop_size))

    return bounding_box


def autodetect_file_type(image_path, ret_itk=True):
    """
    Autodetects image dimensions and size as well as pixel type and component
    size. `autodetect_file_type(*image_path*)`

    :param image_path: filename to be investigated
    :type image_path: str

    :param ret_itk: A boolean value determining if the itkImageType for given
    input image will be determined (if `True`). If `False`, only a tuple
    describibg the image properties will be returned without trying to match
    the itkImage.
    :type ret_itk: bool

    :returns: (pixel_type, component_type, number_of_dimensions) of the image
              according to ITK classes
    """
    logger = logging.getLogger('autodetect_file_type')
    logger.info("Autodetecting file type: %s",  image_path)

    # Initialize itk imageIO factory which allows to do some strange things
    # (this function a pythonized code of an itk example from
    # http://www.itk.org/Wiki/ITK/Examples/IO/ReadUnknownImageType
    # Cheers!
    image_io = itk.ImageIOFactory.CreateImageIO(image_path,
                                                itk.ImageIOFactory.ReadMode)
    image_io.SetFileName(image_path)
    image_io.ReadImageInformation()

    # Extracting information for determining image type
    image_size = map(image_io.GetDimensions,
                     range(image_io.GetNumberOfDimensions()))
    component_type = \
        image_io.GetComponentTypeAsString(image_io.GetComponentType())
    pixel_type = image_io.GetPixelTypeAsString(image_io.GetPixelType())
    number_of_dimensions = image_io.GetNumberOfDimensions()

    logger.debug("Finished extracting header information.")

    logger.info("   Number of dimensions: %d", number_of_dimensions)
    logger.info("   Image size: %s", str(image_size))
    logger.info("   Component type: %s", component_type)
    logger.info("   Pixel type: %s", pixel_type)
    logger.debug(image_io)
    logger.info("Matching image type...")

    # If we do not intent to return itk image type then just return
    # the tuple with the image type. Do not check it given file type is
    # suported by the itk.
    if not ret_itk:
        return (pixel_type, component_type, number_of_dimensions)

    # Matching corresponding image type
    image_type = io_component_string_name_to_image_type[
        (pixel_type, component_type, number_of_dimensions)]

    logger.info("Matched ITK image type: %s", image_type)

    # Hurrayy!!
    return image_type


class pos_itk_image_info(object):

    """
    This class reads the most important information about the image, but only
    the information which can be recovered from the image's header. To be
    even more precise, only such image properties which can be recovered
    from the image header using the Itk's ImageIO object::

        http://www.itk.org/Doxygen/html/classitk_1_1ImageIOBase.html

    Since the ImageIO reads only the image header, usually without reading the
    image itself, no image values-based arributes like min. and max. values or
    the average value cannot be calculated. To get these, one has to read the
    image and compute these values by oneself.

    .. note::

        This class has a bit similar purpose as the `autodetect_file_type`
        function but there's nothing that can be easilu done to merge
        these two. Perhaps in the future...

    .. warning::

        This class is only an draft and its far from complete.
        Therefore it is used internally and should not be used
        anywhere at a user level. Kapish?

    In order to conduct the test we need to store save the test image to the disk:

    >>> import base64
    >>> nii_enc = 'H4sIAAAAAAAAA+2Y22+SdxjH34K4Opu5qKW08HJ6OZQzlHIqlEOxpS1QCgWqTg52Vtu62myiHcYZ3WK6aOZ0Tt1mOvViS90pznTZvJqLWXazLLvp5f6Xvc/ze2niejHmoHDBl5Dnw+/9HZ7n4XeCI21UFXqL4lO7KCnVRbVxr+fFo9rRXvw5k9kIwlv4+M/g1n4ehdk6gc1GDRbvuTguBjIZx1N4Cx9bWbvxtPIAygC4ss3PIDZOrP/Pvk8ZbPVyu6Wq1cXZ3c/sBLoffknAffk7Ar53nxB49aaTq216abv8q6MiPz4j8NfgidcQPrjx/QaC98hvq2D5nsh8FkAw6JueAmj3+Qc8WOIYCRWx8mgsmEOYMS3vRFhMHuDGMNQ9ihdTZP0PsrI/PZZ+CJYXOD9fBhCN55YXARbCmZkUxHPfm1jw0yw80HmTA90sPDE5Z/rh0fumTNEBlct6W8EI8IPNbu8FWOo1qqQAPptNhTnkTzppPg6aiA9zfuzYhli3SMHZz/NrZxBcpU9ug7WOZ89NA3w2kn9zTMXC733lG5EECz/1zUVMERbu2spRd5yF0hullQE9C1FrpN8qYqEYy8b0kJbjplhEC/0s6hgGs+HuCYVxWIdCk4BcUgVGp+wDSBm1KgbdCMtMxLH92vomAGSWE3svnXwElp89eeo6wFJ89sI0rO+18Fl/DFb8uiObG/Kz8LXbPhmBkOcD6bkJIQtDw7K8F77UsE2hR+8P9SmzZoCcxSWButQF+5AIQz7hzI5AUqlRSy+tAbC4jRKcJJq9KrEEQCmViTAbCYVBis13KmX7iau0vl7JuJR8ex2heLr0Ldij+ZNHUxDgauDS6RCs4vPXXaFhOQueRMoSgcUjCB0ujmMrhdexgHCrX3uN9GNznUU4JLceRJgzSCfAthnM8jzAHr1aHwTIylVMCOAdsziEs0XJ+MViAPE+iZTkh2ZEuJc4jAzdAcCjaXltkyD4ao1cOH69UvoFbMf07eMY1+TwnXi0kwVhIl5IQgl/xO0hcV0bG7uKMOU5YyEdXZngehRVMWqQs+05B4EC40I3OjS9Glwyr7v6GdxPFZ6oH+eYNkSr8PLAdGu7cNuJa3RS0lwirc3Z1JN+j2ze5ZVz5EQ8+M2HswiH7y2OIRzwRBMIV3uWyQlCfRSuyehbxZvsJGDZQwZPqrWqlwHswVE9Zt5vVJhfAUg4VbjgKL5coyat+P/zLmkZJefFaiF1F2Ell/oC4eNk/Bapc/8OV7mqG3ONVJljx+ggWrdOLUMIGJaUCEmziZTs0Oq5jVUgeKGxHJUv18LNdEo9yMHNB1zQndsZ/L8ro8Ydl9pl0pFfFUKjUk4e7ZXWaIypdAX21ajHukvl46ByDFIWTYNcaUp1qRvtQVPJUYHdjfSiWWSqQOV/im3d8JtNm7HPVkDeED+aVdVcAltqqaWWWmrpv+tvgz1QS6IZAAA='
    >>> open("/tmp/pos_itk_image_info.nii.gz", "w").write(base64.decodestring(nii_enc))

    >>> image_info = pos_itk_image_info("/tmp/pos_itk_image_info.nii.gz")
    >>> print str(image_info.ByteOrder)
    2

    >>> print str(image_info.ComponentSize)
    1

    >>> print str(image_info.DefaultDirection)
    [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]

    >>> print str(image_info.ComponentTypeAsString)
    unsigned_char

    >>> print str(image_info.FileType)
    2

    >>> print str(image_info.Dimensions)
    [9, 30, 23]

    >>> print str(image_info.FileTypeAsString)
    TypeNotApplicable

    >>> print str(image_info.ImageSizeInBytes)
    6210

    >>> print str(image_info.ImageSizeInComponents)
    6210

    >>> print str(image_info.ImageSizeInPixels)
    6210

    >>> print str(image_info.NameOfClass)
    NiftiImageIO

    >>> print str(image_info.NumberOfComponents)
    1

    >>> print str(image_info.NumberOfDimensions)
    3

    >>> print str(map(lambda x: round(x,4), image_info.Origin))
    [2.8333, 2.8333, -2.7609]

    >>> print str(image_info.PixelType)
    1

    >>> print str(image_info.PixelTypeAsString)
    scalar

    >>> print str(map(lambda x: round(x,4), image_info.Spacing))
    [6.6667, 6.6667, 6.5217]

    >>> print str(sorted(image_info.SupportedReadExtensions))
    ['.hdr', '.img', '.img.gz', '.nia', '.nii', '.nii.gz']

    >>> import os
    >>> os.remove("/tmp/pos_itk_image_info.nii.gz")

    # Here's another example. This time we process 2D, RGBA png file:

    >>> nii_enc = 'iVBORw0KGgoAAAANSUhEUgAAACYAAAAmEAYAAAD4rTXtAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAZiS0dE////////CVj33AAAAAlwSFlzAAAASAAAAEgARslrPgAAAZtJREFUaN7t2itIQ3EYxuGflzEvzPucIggmRbzATPMSTGISsUyL2WAxKyKaLQazRS0iJhGDQXTJgRfEJUGQOe9zTDdvM8z1fWkM3qccTvvz8n4f5xxOQSpVsQ/fq1CyCwDlgfTVNQ/Aa/UFAHN1QYDf2fobgJ8XTyvA15lnFSDR1FABED9yTwJEr2r8AE/nleO0Q2SrbJkg3O04/YVOCF879oovIewr2nb2QuSgwFfaAw/TTLgO4bUbqk4hNsC6ewU+TlIBzyAkj39GGwPw3f411NgCv8nkZsMI4H2f8YwBl9GN2k6A583KNoCHtfI+gLu3kluAyJSjCyASKqoGuG8uXAJ49LII8NJBFUBsIZ1D3Je+JoYBitM3nyEkK/+BJVtzfZB8kQlsINcHyReZkezP9UHyhRpmlAlMDcuSGmaU2WEKLEsaSSONpJEaZqSGGWnpG6lhRtphRmqYkXaYkUbSSCNppMCM9AHRSDvMSCNppMCM9BxmpB1mpJE0UmBGGkkjLX0jNcxIO8xIgRnp5dtIDTPSH4hG+sfV6A+/3H/IJeHXVgAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxNi0wMS0wNFQxMjoxMzoxOCsxMTowMKYo+UIAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMTUtMTAtMDVUMTg6MzE6MDgrMTE6MDBYjMl1AAAAAElFTkSuQmCC'
    >>> open("/tmp/pos_itk_image_info.png", "w").write(base64.decodestring(nii_enc))
    >>> image_info = pos_itk_image_info("/tmp/pos_itk_image_info.png")

    >>> print str(image_info.ByteOrder)
    2

    >>> print str(image_info.ComponentSize)
    2

    >>> print str(image_info.DefaultDirection)
    [(1.0, 0.0), (0.0, 1.0)]

    >>> print str(image_info.ComponentTypeAsString)
    unsigned_short

    >>> print str(image_info.FileType)
    2

    >>> print str(image_info.Dimensions)
    [38, 38]

    >>> print str(image_info.FileTypeAsString)
    TypeNotApplicable

    >>> print str(image_info.ImageSizeInBytes)
    11552

    >>> print str(image_info.ImageSizeInComponents)
    5776

    >>> print str(image_info.ImageSizeInPixels)
    1444

    >>> print str(image_info.NameOfClass)
    PNGImageIO

    >>> print str(image_info.NumberOfComponents)
    4

    >>> print str(image_info.NumberOfDimensions)
    2

    >>> print str(map(lambda x: round(x,4), image_info.Origin))
    [0.0, 0.0]

    >>> print str(image_info.PixelType)
    3

    >>> print str(image_info.PixelTypeAsString)
    rgba

    >>> print str(map(lambda x: round(x,4), image_info.Spacing))
    [1.0, 1.0]

    >>> print str(sorted(image_info.SupportedReadExtensions))
    ['.PNG', '.png']

    >>> import os
    >>> os.remove("/tmp/pos_itk_image_info.png")
    """

    _DIMENSION_INDEPENDENT_ATTRS = [
        "ByteOrder", "ByteOrderAsString",
        "ComponentSize", "ComponentTypeAsString", "FileName",
        "FileType", "FileTypeAsString", "ImageSizeInBytes",
        "ImageSizeInComponents", "ImageSizeInPixels", "NameOfClass",
        "NumberOfComponents", "NumberOfDimensions", "PixelStride",
        "PixelType", "PixelTypeAsString",
        "SupportedReadExtensions", "SupportedWriteExtensions"]

    _DIMENSION_DEPENDENT_ATTRS = [
        "DefaultDirection", "Dimensions", "Direction", "Origin",
        "Spacing"]
    _DIMENSION_DEPENDENT_TYPES = {
        "Dimensions": int, "Origin": float, "Spacing": float}

    def __init__(self, image_path):
        """
        :param image_path: Name of the image file to be analyzed.
        :type image_path: str
        """

        self._logger = logging.getLogger('pos_itk_image_info')
        self._logger.debug("Reading %s file header details." % image_path)
        self._logger.debug("Setting up the ITK ImageIO object...")

        self._image_io = itk.ImageIOFactory.CreateImageIO(image_path,
                                                          itk.ImageIOFactory.ReadMode)
        self._image_io.SetFileName(image_path)

        self._logger.debug("Reading image information.")
        self._image_io.ReadImageInformation()

        # Once we read the IO details from the file,
        # it is time to pass the interesting IO values
        # from the itk IO object to the python object.
        self._logger.debug("Copying stuff from the ImageIO to self.")
        self._get_dimension_independent_properties()
        self._get_diemsion_dependent_properties()

        # Then, just in case (to be sure that we do not
        # have unncecessary references) remove the
        # ImageIO object:
        self._logger.debug("Removing the ITK ImageIO object reference.")
        del self._image_io

    def _get_dimension_independent_properties(self):
        """
        """

        for prop in self._DIMENSION_INDEPENDENT_ATTRS:

            self._logger.debug("Processing the %s property.", prop)

            # I love the itk Get/Set convention so much!
            attr_name = "Get" + prop

            # Some attributes express some properties of the
            # image using string. But the string representation
            # requires first a int number to be read from the
            # image IO. Therefore all the code below!
            if attr_name.endswith("AsString"):
                mod_attr_name = attr_name[0:-8]
                prop_val = getattr(self._image_io, mod_attr_name)()

                self._logger.debug("%s method found.", mod_attr_name)
                attr_value = getattr(self._image_io, attr_name)(prop_val)

                self._logger.debug("%s method found.", attr_name)
                setattr(self, prop, attr_value)
            else:
                attr_value = getattr(self._image_io, attr_name)()
                self._logger.debug("%s method found.", attr_name)
                setattr(self, prop, attr_value)

            self._logger.debug("Setting %s to %s .", prop, str(attr_value))

    def _get_diemsion_dependent_properties(self):
        """
        """

        # Just make a quick alias, so the code
        # will remain clean
        n_dims = self.NumberOfDimensions

        for prop in self._DIMENSION_DEPENDENT_ATTRS:

            self._logger.debug("Processing the %s property.", prop)

            # I love the itk Get/Set convention so much!
            attr_name = "Get" + prop

            # Get a reference to the actual itk ImageIO
            # function based on the name of the attribute
            io_function = getattr(self._image_io, attr_name)
            attr_value = map(io_function, range(n_dims))
            self._logger.debug("%s method found.", attr_name)

            # Sometimes, the value of the arribute obtained
            # directly ftom the itk function has to be casted
            # to a different type to maintain compatibility with
            # native python (e.g. long_int -> int).
            # This is where this is done:
            type_ = self._DIMENSION_DEPENDENT_TYPES.get(prop, None)
            if type_:
                self._logger.debug("Mapping %s to %s.",
                                   attr_name, str(type_))
                attr_value = map(type_, attr_value)

            setattr(self, prop, attr_value)
            self._logger.debug("Setting %s to %s .", prop, str(attr_value))


def resample_image_filter(input_image, scaling_factor, default_value=0,
                          interpolation='linear'):
    """
    An image resampling function - pipeline - small workflow. Reimplemented after:
    http://sourceforge.net/p/c3d/git/ci/master/tree/adapters/ResampleImage.cxx#l12

    :param input_image: Input image to resample
    :type input_image: itk image

    :param scaling_factor:
    :type scaling_factor: two options possible, either float or iterable of floats.

    :param default_value: default voxel value (used, when the actual voxel
                          value cannot be defined. Leave default, if you are not sure.
    :type default_value: the same type as the `input_image` type. Usually
                         `uchar`, `ushort`, or `float`.

    :param interpolation: defines image interpolation function. Several options
        are possible: `n`, `NEAREST` or `NEARESTNEIGHBOR` causes the function to
        use NN interpolation.  'L' or 'linear' switches to linear interpolation.
    The case of the letters does not matter.  :type interpolation: str """

    logger = logging.getLogger('resample_image_filter')
    logger.info("Resampling image: %s times", str(scaling_factor))

    logger.debug(str(input_image))
    logger.debug("   + Using %s interpolation.", interpolation)
    logger.debug("   + Setting %s as a default pixel value.", default_value)

    # Read out the image dimension to be to use it further in the routine.
    # This is done by pretty simple yet effective way :)
    image_dim = len(input_image.GetSpacing())

    # Declare an image interpolation function. The function is by default a
    # linear interpolation function, however it my be switched to any other
    # image interpolation function.
    if interpolation.upper() in ['NN', 'NEAREST', 'NEARESTNEIGHBOR', 'NN']:
        interpolator = \
            itk.NearestNeighborInterpolateImageFunction[
                input_image, itk.D].New()

    if interpolation.upper() in ['L', 'LINEAR']:
        interpolator = \
            itk.LinearInterpolateImageFunction[input_image, itk.D].New()

    logger.debug("   + Selected image interpolation function: %s",
                 str(itk.LinearInterpolateImageFunction))

    # Declare resampling filter and initialize the filter with two dimensional
    # identity transformation as well as image interpolation function
    logger.debug("   + Initializing resampling filter.")
    resample_filter = itk.ResampleImageFilter[input_image, input_image].New()
    resample_filter.SetInput(input_image)
    resample_filter.SetTransform(itk.IdentityTransform[itk.D, image_dim].New())
    resample_filter.SetInterpolator(interpolator)

    # Get original spacing of the input image:
    pre_spacing = input_image.GetSpacing()

    # Initialize recomputed size vector. Note that the vector is initialized
    # with zeroes:
    post_size = itk.Vector[itk.US, image_dim]([0] * image_dim)

    # Initialize scaling vector based on provided scaling factor
    if hasattr(scaling_factor, '__iter__'):
        logger.debug("   + Multiple scaling factors provided.")
        scaling = itk.Vector[itk.F, image_dim](scaling_factor)
    else:
        logger.debug("   + A single scaling factor was provided.")
        scaling = itk.Vector[itk.F, image_dim]([scaling_factor] * image_dim)

    # Initialize vector holding spacing of the output image. Note that the
    # vector is initalized with zeroes.
    post_spacing = itk.Vector[itk.F, image_dim]([0] * image_dim)

    for i in range(image_dim):
        post_spacing[i] = pre_spacing[i] * 1.0 / scaling[i]
        post_size[i] = int(input_image.GetBufferedRegion().GetSize()[i] *
                           1.0 * scaling[i])
    logger.info("   + Computed final size: %s", str(post_size))
    logger.info("   + Computed final spacing: %s", str(post_spacing))

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
    logger.info("   + Computed final origin: %s", str(origin_post))

    # Set the image sizes, spacing, origins and image direction matrix:
    resample_filter.SetSize(map(int, post_size))
    resample_filter.SetOutputSpacing(post_spacing)
    resample_filter.SetOutputOrigin(origin_post)
    resample_filter.SetOutputDirection(input_image.GetDirection())

    # Set the unknown intensity to positive value
    resample_filter.SetDefaultPixelValue(default_value)

    # Perform resampling
    resample_filter.UpdateLargestPossibleRegion()

    # Return resampled image:
    return resample_filter.GetOutput()


def get_itk_direction_matrix(code):
    """
    Generates direction matrix based on provided RAI code.
    Implemented after:
    http://sourceforge.net/p/c3d/git/ci/master/tree/adapters/SetOrientation.cxx

    :param code: RAI orientation code.
    :type code: str

    :return: `itk.Matrix.D33` orientation matric, according to the provided
              orientation code.

    .. note::
        The function assumes that the provided RAI code has the proper form.

    """
    # Just make the code upper case to avoid any ambiguity
    rai = code.upper()

    logger = logging.getLogger('get_itk_direction_matrix')
    logger.info("Generating direction matrix for the RAI code of %s.", code)

    eye_matrix = itk.vnl_matrix_fixed.D_3_3()
    eye_matrix.set_identity()

    dir_matrix = itk.vnl_matrix_fixed.D_3_3()
    dir_matrix.set_identity()

    rai_codes = [["R", "L"], ["A", "P"], ["I", "S"]]

    # The code below is awful! But sorry, that is what happens, if you use itk
    # from python!. Anyway, the code below created direction matrix based on
    # provided RAI code.
    for i in range(3):
        matched = False
        for j in range(3):
            for k in range(2):
                if rai[i] == rai_codes[j][k]:
                    m = [-1.0, 1.0][k == 0]
                    dir_matrix.set(0, i, eye_matrix.get(j, 0) * m)
                    dir_matrix.set(1, i, eye_matrix.get(j, 1) * m)
                    dir_matrix.set(2, i, eye_matrix.get(j, 2) * m)

                    rai_codes[j][0] = rai_codes[j][1] = 'X'
                    matched = True

    return itk.Matrix.D33(dir_matrix)


def itk_get_transformation_from_file(transformation_filename):
    """
    Reads the first `itk.Transform` from the provided file.

    :param transformation_filename: filename of the transformation file.
    :type transformation_filename: str

    .. note::
        This function reads only the first transformation from the file, even
        that there more than one stored.

        Some transformation will cause ITK to crash. Sorry. You have to sort
        these things out yourself.

    """
    logger = logging.getLogger('itk_get_transformation_from_file')
    logger.info("Loading transformation file: %s",
                transformation_filename)

    # Define the transformation reader and load the transformation file
    transform_reader = itk.TransformFileReader.New()
    transform_reader.SetFileName(transformation_filename)
    transform_reader.Update()

    # Load the transformation from the file.
    transformation = transform_reader.GetTransformList().front()

    # Then get the parameters
    parameters = transformation.GetParameters()
    param_list = map(lambda i: parameters.get(i), range(parameters.size()))

    # Finally, print all the parameters as well as the transformation type
    logger.info("Detected transformation type: %s",
                transformation.GetTransformTypeAsString())
    logger.info("Size of the parameters vector: %d",
                parameters.size())

    for i in range(parameters.size()):
        logger.info("Printing parameter %d: %d", i, parameters.get(i))

    return (transformation.GetTransformTypeAsString(),
            param_list)


def get_cast_image_type_from_string(target_image_type, dim=3):
    """
    Cast a itk image type to a given type. Not all combinations are allowed.
    This function works only with single channel images.

    :param target_image_type: type of the output images provided as string
    :type target_image_type: str

    :param dim: ouput image dimensionality
    :type dim: int (either 2 or 3)

    :returns: `itkImage`

    """
    types = {'uchar': ('scalar', 'unsigned_char', dim),
             'short':  ('scalar', 'short', dim),
             'ushort': ('scalar', 'unsigned_short', dim),
             'float': ('scalar', 'float', dim),
             'double': ('scalar', 'double', dim)}
    return io_component_string_name_to_image_type[types[target_image_type]]


def print_vnl_matrix(matrix):
    """
    Echoes `itk` `vnl_matrix`

    :param matrix: matrix to print
    :type matrix: `itk.vnl_matrix`
    """

    for i in range(matrix.rows()):
        row = map(lambda x: matrix.get(i, x), range(matrix.cols()))
        print "[ " + " ".map(str, row) + " ]"


def reorder_volume(input_image, reorder_mapping, slicing_plane):
    """
    Funtion for reordering the slices along the `slicing_plane` in the provided
    `input_image` according to the `reorder_mapping`.

    .. note::
        Only grayscale images are supported. Poor python `itk` bindings...

    :param input_image: Input image which serves as a source for the reordering
                        routine. Only grayscale images are supported.
    :type input_image: `itk.Image`

    :param reorder_mapping: Mapping from the input image slice order to the
        output image slice order. The length of the mapping has to be the same
        as the numer of slices in the slicing plane.

    :type reorder_mapping: `iterable`. The length of the iterable has to be
        the same as the number of slices in the `slicing_plane`.
        However it has not to be 1:1 mapping. The form of the mapping has to be
        `mapping[output_slice] = input_slice`.

    :param slicing_plane: Image plane along with the slices will be reordered.
        Allowed values are: 0,1,2.
    :type slicing_plane: int

    :returns: `itk.image` with reordered slices.
    """
    logger = logging.getLogger('reorder_volume')

    image_shape = input_image.GetLargestPossibleRegion().GetSize()
    ndim = len(image_shape)
    logger.info("Provided image has a shape of : %s", map(str, image_shape))
    logger.info("Selected slicing plane: %d", slicing_plane)

    logger.debug("Duplicating the input image.")
    image_duplicator = itk.ImageDuplicator[input_image].New()
    image_duplicator.SetInputImage(input_image)
    image_duplicator.Update()
    duplicate = image_duplicator.GetOutput()

    # This is a filter that will erase (make all voxel values to zero)
    # it is not necessary step, but will help to catch any errors.
    logger.debug("Zeroing the duplicated image.")
    zeroer = itk.ShiftScaleImageFilter[duplicate, duplicate].New()
    zeroer.SetScale(0)
    zeroer.SetInput(image_duplicator.GetOutput())

    # This is a filter that will copy consecutive slices from one volume
    # to the other
    paste_filter = itk.PasteImageFilter[duplicate].New()

    # Now we extract the number of slices in a given slicng plane
    slicing_plane_extent = image_shape[slicing_plane]
    logger.debug("Defining the number of slices along the slicing plane: %d",
                 slicing_plane_extent)

    # This is the empty image of the same size and shape as the original
    # image. This image fill be filled with consecutive slices from the
    # original image.
    output_image = zeroer.GetOutput()

    # The next step is to loop over all slices' indexes in the slicing
    # plane, and copy each slice to its new location in the output image.
    for slice_idx in range(slicing_plane_extent):

        logger.info("Copying: (intput) %d --> %d (output)",
                    reorder_mapping[slice_idx], slice_idx)

        # Input region changes with each iteration (obviously)
        input_region_origin = [0, 0, 0]
        input_region_origin[slicing_plane] = reorder_mapping[slice_idx]

        # Define the input region size, the input region size it, actually,
        # the same in each iteration. Technically this could easily go outside
        # the loop but to keep the region definition close togeather, it is
        # inside the loop.
        input_region_size = list(image_shape)
        input_region_size[slicing_plane] = 1

        # Compose input region origin and size into itk region.
        input_region = get_image_region(ndim,
                                        input_region_origin, input_region_size)

        # The output region index is the place where the given slice will be
        # located. To define the output region we use the provided lookup
        # table.
        output_region_origin = [0, 0, 0]
        output_region_origin[slicing_plane] = slice_idx

        # Configure the image pasting filter.
        logger.debug("Input image origin: %s", input_region_origin)
        logger.debug("Input image size: %s", input_region_size)
        logger.debug("Output image origin: %s", output_region_origin)
        paste_filter.SetSourceImage(input_image)
        paste_filter.SetDestinationImage(output_image)
        paste_filter.SetSourceRegion(input_region)
        paste_filter.SetDestinationIndex(output_region_origin)

        # Latch the filter and capture the output.
        paste_filter.Update()
        output_image = paste_filter.GetOutput()

    logger.info("Done.")
    # After conducting all iterations return the output image.
    return output_image


def itk_is_point_inside_region(image, point, region=None):
    """

    :param image: Image inside which the point in question is or is not.
                  Required argument.
    :type image: `itk.Image`

    :param point: Point in physical coordinates to be tested. `Iterable` of two
        or three float values (depending on the dimensionality of the provided
        image.  The point is expected to be provided in physical coordinates using
        float numbers.  Explicit float conversion is suggested just in case.
    :type point: An iterable compatibile with the `itk.Index` class (`list`,
        `tuple`, or other `iterable`).

    :param region: If the `region` is provided the `point` is tested against
        the provided `region` instead of the provided `image`. The provided regions
        has to match the `point` in terms of dimensionality. An instance of
        `itk.ImageRegion` can be obtained using the `pos_itk_core.get_image_region`
        function. I am unable to tell if the `region` has to be within the largest
        possible region of the `image` but I think it would be better if it was.
    :type region: `itk.ImageRegion`

    :return: `True` when the point is within the image or within the provided
             region. Returns `False` otherwise.
    :rtype: bool

    Determines if given point is inside provided image

    Based on example from the ITK wiki:
    http://itk.org/Wiki/ITK/Examples/SimpleOperations/PixelInsideRegion

    According to the ITK

    For a given index I3X1, the physical location P3X1 is calculated as following:
        P3X1 = O3X1 + D3X3*diag(S3X1)3x3*I3X1

    spacing = test_image.GetSpacing()
    origin = test_image.GetOrigin()
    cosines = test_image.GetDirection().GetVnlMatrix()
    map(int,test_image.GetLargestPossibleRegion().GetSize())
    origin[0] + cosines.get(0,0) * spacing[0] * 128
    origin[1] + cosines.get(1,1) * spacing[0] * 128

    >>> from possum import pos_itk_core

    Testing the inside / outside point detection for a simple 3D image:

    >>> test_image = itk.Image[itk.F,3].New()
    >>> region =  itk.ImageRegion[(3,)]()
    >>> region.SetIndex([0, 0, 0])
    >>> region.SetSize([128, 128, 128])
    >>> test_image.SetRegions(region)
    >>> test_image.SetOrigin([0, 0, 0])
    >>> test_image.SetSpacing([1, 1, 1])
    >>> test_image.Allocate()
    >>> test_image.FillBuffer(0)


    This is close to the origin of the image
    >>> pos_itk_core.itk_is_point_inside_region(test_image, [0, 0, 0])
    True

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-1, -1, -1])
    False

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [0, -1, 0])
    False

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [0, 1, 0])
    True

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [0.01, 0, 0])
    True


    Note the interpolation scheme:
    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-0.5, 0, 0])
    True

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-0.51, 0, 0])
    False


    Now we move to the oposite side of the image. Again, mind the way, how the values
    are interpolated
    >>> map(int,test_image.GetLargestPossibleRegion().GetSize())
    [128, 128, 128]

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [127.499, 127.499, 127.499])
    True

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [127.501, 127.501, 127.501])
    False

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [127.0, 127.0, -31.23])
    False

    >>> pos_itk_core.itk_is_point_inside_region(test_image, (-2.9, 17., 0))
    False


    Let's test some exceptions:
    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-2.9, 17.])
    Traceback (most recent call last):
    TypeError: Expecting an itkPointD3, an int, a float, a sequence of int or a sequence of float.

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-2.9, 17., "x"])
    Traceback (most recent call last):
    ValueError: could not convert string to float: x

    >>> pos_itk_core.itk_is_point_inside_region(test_image)
    Traceback (most recent call last):
    TypeError: itk_is_point_inside_region() takes at least 2 arguments (1 given)


    And now something a bit more complicated. There is an optional `region`
    argument. When provided this argument provides the actual region against
    which the region will be tested. In the `region` is not provided, the
    `LagrestPossibleRegion` of the tested image is used.

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [11., 11.2, 10.232], \
        get_image_region(3, [10, 10, 10], [20, 20, 20]))
    True

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [0.2, -1., 0.], \
        get_image_region(3, [10, 10, 10], [20, 20, 20]))
    False

    Now we test the whole stuff using a 2D image. When one uses negative indexed,
    things might get tricky!
    >>> region =  itk.ImageRegion[(2,)]()
    >>> region.SetIndex([0, 0])
    >>> region.SetSize([128, 128])

    >>> test_image = itk.Image[itk.F,2].New()
    >>> test_image.SetRegions(region)
    >>> test_image.SetOrigin([-8, 12])
    >>> test_image.SetSpacing([0.04, 0.04])
    >>> test_image.Allocate()
    >>> test_image.FillBuffer(0)

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [0, 0])
    False

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-7, 13])
    True

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-2.9, 17.])
    True

    Let's test some exceptions:
    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-2.9, 17., 1])
    Traceback (most recent call last):
    TypeError: Expecting an itkPointD2, an int, a float, a sequence of int or a sequence of float.


    And now testing the point against a region:
    >>> pos_itk_core.itk_is_point_inside_region(test_image, [11, 11], \
        get_image_region(2, [10, 10], [20, 20]))
    False

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-7.4, 12.5], \
        get_image_region(2, [10, 10], [20, 20]))
    True

    >>> pos_itk_core.itk_is_point_inside_region(test_image, [-7.4, 12.0], \
        get_image_region(2, [10, 10], [20, 20]))
    False
    """

    point_index = image.TransformPhysicalPointToIndex(map(float, point))

    if region is None:
        region = image.GetLargestPossibleRegion()

    return region.IsInside(map(int, point_index))


def generate_empty_image(reference_image, default_value, type_=None):
    """
    Generates empty image based on the provided reference image. The newly
    created, empty image has the same size, dimensionality, directions, origin
    and spacing as the reference image. The data type of the newly created
    image might be determined by setting the `type_` argument. Note that the
    lenth of the default default_value vector has to be equal to the bumber of
    components of the canvas image.

    :param reference_image: Image from which the spacing, origin, directions,
         dimensionality, pixel type and, by default, data type will be copied.
    :type reference_image: `itk.Image`

    :param type_: Pixel type of the canvas. This overrides the pixel type of
        the refrence image.
    :type type_: `itkTypes.itkCType`

    :param default_value: The default_value which will be used to fill the
    image buffer. Note that the default_value has to match the image type. For
    instance if you want to create black RGB image you have to fill it with
    (0,0,0). If you're creating 'black' grayscale image use 0.  :type
    default_value: depends on `type_` and `reference_image`.

    :return: Two canvas images based on the provided reference image
    :rtype: `itk.Image`
    """

    # Things are pretty simple here. If the reference image is provided just
    # get another instance of the reference image class.
    if not type_:
        output_canvas = reference_image.New()
    else:
        # Otherwise, extract the dimensionality of the image and compose it
        # with the provided ppixel type and bu this, create
        n_dimensions = reference_image.GetImageDimension()
        canvas_pixel_type = type_
        canvas_image_type = itk.Image[canvas_pixel_type, n_dimensions]
        output_canvas = canvas_image_type.New()

    output_canvas.CopyInformation(reference_image)
    output_canvas.SetRegions(reference_image.GetLargestPossibleRegion())
    output_canvas.Allocate()
    output_canvas.FillBuffer(default_value)

    return output_canvas


# if __name__ == 'possum.pos_itk_core':
if __name__ == '__main__':
    import doctest
    print doctest.testfile("../test/test_check_itk_build/pos_check_itk_build.txt")
    print doctest.testmod(verbose=True)
