#!/usr/bin/python
# -*- coding: utf-8 -*

"""
.. module:: pos_itk_core
    :platform: Ubuntu
    :synopsis: Core functions for itk support in Python.

.. moduleauthor:: Piotr Majka <pmajka@nencki.gov.pl>
"""
import itk
import logging

# http://sphinx-doc.org/domains.html#the-python-domain

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
        ('scalar', 'double', 3) : itk.Image.D3,
        ('rgb', 'unsigned_char', 2) : itk.Image.RGBUC2,
        ('rgb', 'unsigned_char', 3) : itk.Image.RGBUC3,
        }

# Another quite clever dictionary. This one converts given image type to the
# same type but with number of dimensions reduced by one (e.g. 3->2).
types_reduced_dimensions = {
        itk.Image.SS3 : itk.Image.SS2,
        itk.Image.US3 : itk.Image.US2,
        itk.Image.UC3 : itk.Image.UC2,
        itk.Image.RGBUC3 : itk.Image.RGBUC2,
        itk.Image.F3 : itk.Image.F2,
        itk.Image.D3 : itk.Image.D2
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
    if interpolation.upper() in ['NN', 'NEAREST', 'NEARESTNEIGHBOR','NN']:
        interpolator = \
            itk.NearestNeighborInterpolateImageFunction[input_image, itk.D].New()

    if interpolation.upper() in ['L', 'LINEAR']:
        interpolator = \
            itk.LinearInterpolateImageFunction[input_image, itk.D].New()

    logger.debug("   + Selected image interpolation function: %s", \
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


def get_itk_direction_matrix(code):
    """
    Generates direction matrix based on provided RAI code.
    Reimplemented from:
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

    rai_codes = [["R","L"], ["A","P"], ["I","S"]]

    # The code below is awful! But sorry, that is what happens, if you use itk
    # from python!. Anyway, the code below created direction matrix based on
    # provided RAI code.
    for i in range(3):
        matched = False
        for j in range(3):
            for k in range(2):
                if rai[i] == rai_codes[j][k]:
                    m = [-1.0, 1.0][k==0]
                    dir_matrix.set(0, i, eye_matrix.get(j,0) * m)
                    dir_matrix.set(1, i, eye_matrix.get(j,1) * m)
                    dir_matrix.set(2, i, eye_matrix.get(j,2) * m)

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
    types = {'uchar' : ('scalar', 'unsigned_char', dim),
             'short':  ('scalar', 'short', dim),
             'ushort': ('scalar', 'unsigned_short', dim),
             'float' : ('scalar', 'float', dim),
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
