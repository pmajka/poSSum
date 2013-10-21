import itk
import logging

# Dictionary below copied from (Sun Apr  7 14:04:28 CEST 2013)
# http://code.google.com/p/medipy/source/browse/lib/medipy/itk/types.py?name=default&r=0da35e1099e5947151dee239f7a09f405f4e105c
io_component_type_to_type = {
        itk.ImageIOBase.UCHAR : itk.UC,
        itk.ImageIOBase.CHAR : itk.SC,
        itk.ImageIOBase.USHORT : itk.US,
        itk.ImageIOBase.SHORT : itk.SS,
        itk.ImageIOBase.UINT : itk.UI,
        itk.ImageIOBase.INT : itk.SI,
        itk.ImageIOBase.ULONG : itk.UL,
        itk.ImageIOBase.LONG : itk.SL,
        itk.ImageIOBase.FLOAT : itk.F,
        itk.ImageIOBase.DOUBLE : itk.D,
        }

# And this is my own invention: a dictionary that converts tuple of specific
# image parameters into itk image type. We all love ITK heavy templated code
# style!
io_component_string_name_to_image_type = {
        ('scalar', 'short', 3) : itk.Image.SS3,
        ('scalar', 'unsigned_short', 3) : itk.Image.US3,
        ('scalar', 'unsigned_char', 3) : itk.Image.UC3,
        ('vector', 'unsigned_char', 3) : itk.Image.RGBUC3,
        ('scalar', 'float', 3) : itk.Image.F3,
        ('scalar', 'short', 2) : itk.Image.SS2,
        ('scalar', 'unsigned_short', 2) : itk.Image.US2,
        ('vector', 'unsigned_char', 2) : itk.Image.RGBUC2,
        ('vector', 'float', 3) : itk.Image.VF33,
        ('scalar', 'unsigned_char', 2) : itk.Image.UC2,
        ('scalar', 'float', 2) : itk.Image.F2,
        ('rgb', 'unsigned_char', 2) : itk.Image.RGBUC2,
        ('rgb', 'unsigned_char', 3) : itk.Image.RGBUC3
        }

# Another quite clever dictionary. This one converts given image type to the
# same type but with number of dimensions reduced by one (e.g. 3->2).
types_reduced_dimensions = {
        itk.Image.SS3 : itk.Image.SS2,
        itk.Image.US3 : itk.Image.US2,
        itk.Image.UC3 : itk.Image.UC2,
        itk.Image.RGBUC3 : itk.Image.RGBUC2,
        itk.Image.F3 : itk.Image.F2
    }

# This time a dictionary for stacking slices (a reverse of
# types_reduced_dimensions dict):
types_increased_dimensions = dict((types_reduced_dimensions[k], k)
                               for k in types_reduced_dimensions)


def get_image_region(image_dim, crop_index, crop_size):
    bounding_box = itk.ImageRegion[image_dim]()
    bounding_box.SetIndex(map(int, crop_index))
    bounding_box.SetSize(map(int, crop_size))

    return bounding_box


def autodetect_file_type(image_path):
    """
    Autodetects image dimensions and size as well as pixel type and component
    size.

    :param image_path: filename to be investigated
    :type image_path: str

    :returns: (pixel_type, component_type, number_of_dimensions) of the image
              according to ITK classes
    """
    logger = logging.getLogger('autodetect_file_type')
    logger.info("Autodetecting file type: %s",  image_path)

    # Initialize itk imageIO factory which allows to do some strange things
    # (this function a pythonized code of an itk example from
    # http://www.itk.org/Wiki/ITK/Examples/IO/ReadUnknownImageType
    # Cheers!
    image_io = itk.ImageIOFactory.CreateImageIO(image_path,\
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

    # Matching corresponding image type
    image_type = io_component_string_name_to_image_type[
        (pixel_type, component_type, number_of_dimensions)]

    logger.info("Matched ITK image type: %s", image_type)

    # Hurrayy!!
    return image_type


def resample_image_filter(input_image, scaling_factor, default_value=0,
                          interpolation='linear'):
    """
    Reimplemented after:
    http://sourceforge.net/p/c3d/git/ci/master/tree/adapters/ResampleImage.cxx#l12
	TODO: ADD VERBOSE INFORMATION
    TODO: Add interpolation function (actually: create a separate function that created
    a dedicated interpolator depending on provided settings)
    TODO: Document the interpolation function
    TODO: Scaling: single value or array of dim floats
    """

    # Read out the image dimension to be to use it further in the routine.
    # This is done by pretty simple yet effective way :)
    image_dim = len(input_image.GetSpacing())

    # Declare an image interpolation function. The function is by default a
    # linear interpolation function, however it my be switched to any other
    # image interpolation function.
    if interpolation.upper() in ['NN', 'NEAREST', 'NEARESTNEIGHBOR']:
        interpolator = \
            itk.NearestNeighborInterpolateImageFunction[input_image, itk.D].New()

    if interpolation.upper() in ['L', 'LINEAR']:
        interpolator = \
            itk.LinearInterpolateImageFunction[input_image, itk.D].New()

    # Declare resampling filter and initialize the filter with two dimensional
    # identity transformation as well as image interpolation function
    resample_filter = itk.ResampleImageFilter[input_image, input_image].New()
    resample_filter.SetInput(input_image)
    resample_filter.SetTransform(itk.IdentityTransform[itk.D, image_dim].New())
    resample_filter.SetInterpolator(interpolator)

    # Compute the spacing of the new image
    # The new spacing is computed by

    # Get original spacing of the input image:
    pre_spacing = input_image.GetSpacing()

    # Initialize recomputed size vector. Note that the vector is initialized
    # with zeroes:
    post_size = itk.Vector[itk.US, image_dim]([0] * image_dim)

    # Initialize scaling vector based on provided scaling factor
    if hasattr(scaling_factor, '__iter__'):
        scaling = itk.Vector[itk.F, image_dim](scaling_factor)
    else:
        scaling = itk.Vector[itk.F, image_dim]([scaling_factor] * image_dim)

    # Initialize vector holding spacing of the output image. Note that the
    # vector is initalized with zeroes.
    post_spacing = itk.Vector[itk.F, image_dim]([0] * image_dim)

    for i in range(image_dim):
        post_spacing[i] = pre_spacing[i] * 1.0 / scaling[i]
        post_size[i] = int(input_image.GetBufferedRegion().GetSize()[i] *
                           1.0 * scaling[i])

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

    # Perform resampling
    resample_filter.UpdateLargestPossibleRegion()

    # Return resampled image:
    return resample_filter.GetOutput()
