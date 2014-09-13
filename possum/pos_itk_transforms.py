import itk
import possum.pos_itk_core

"""
http://www.vtk.org/doc/nightly/html/classvtkShepardMethod.html
http://www.itk.org/Wiki/ITK/Examples/ImageProcessing/TileImageFilter_CreateVolume
http://www.itk.org/Doxygen/html/classitk_1_1DisplacementFieldTransform.html
http://www.itk.org/Doxygen/html/classitk_1_1CompositeTransform.html
"""


def read_transformation_txt_file(transformation_file):
    """
    Extracts transformation parameters from the transformation file
    and packs them into an returns them as a dictionary.

    :param transformation_string: the contents of the transformation file.
    :type: transformation_string: string

    :return: An array of the parameters results.
    :rtype: list
    """

    # Well - open the file and read its contents:
    transformation_string = open(transformation_file).readlines()

    # Then extract the transformation class name (it is very important which
    # type of transformation given file carries :)
    transformation_class = transformation_string[2].strip().split(':')[1].strip()

    # Extract the actual parametres from the parameters string.
    parameters = \
        transformation_string[3].strip().split(':')[1].strip().split(' ')
    parameters = map(float, parameters)

    # And then the same for the fixed parameters. Make them floats afterwards,
    fixed_parameters = \
        transformation_string[4].strip().split(':')[1].strip().split(' ')
    fixed_parameters =  map(float, fixed_parameters)

    result = {'transformation_class': transformation_class,
              'parameters': parameters,
              'fixed_parameters': fixed_parameters}
    return result


def load_itk_matrix_transform_from_file(filename):
    """
    :param filename: File to load the transformation from. The transformation
        file has to be a valid itk transformation file saved by
        itkTransformFileWriter.
    :type filename: str

    :return: subclass of `itk.MatrixOffsetTransformBase`
    """

    # Just a simple mapping of data type to itk object representing given data
    # type. Probably paraneter type for all the transformations will be double
    # anyway.
    data_type_dict = {'double': itk.D}

    # Red the transformation file, extract parameters
    file_transform_data = read_transformation_txt_file(filename)
    file_transform_class = \
        file_transform_data['transformation_class'].split("_")
    file_transform_params = file_transform_data['parameters']
    file_transform_fparams = file_transform_data['fixed_parameters']

    # Here we extract the actual class name (as string) so we could instantiace
    # the actual class afterwards. Then the data type and the image dimensions
    # are extracted as well.
    class_name = file_transform_class[0].strip()
    data_type = data_type_dict[file_transform_class[1].strip()]
    dim = int(file_transform_class[2].strip())

    # Finally! Instanciate the transformation.
    transform = getattr(itk, class_name)[(data_type, dim, dim)].New()

    # Fill the transformation with parameters
    parameters = itk.OptimizerParameters[(data_type,)]()
    parameters.SetSize(transform.GetNumberOfParameters())
    for i in range(transform.GetNumberOfParameters()):
        parameters.SetElement(i, file_transform_params[i])

    # And then set the fixed paramters as well
    fixed_parameters = itk.OptimizerParameters[(data_type,)]()
    fixed_parameters.SetSize(dim)
    for i in range(dim):
        fixed_parameters.SetElement(i, file_transform_fparams[i])

    # Assign the parameters to the transformation and the transfordmation is
    # ready!
    transform.SetParameters(parameters)
    transform.SetFixedParameters(fixed_parameters)

    return transform


def write_itk_matrix_transformation_to_file(transformation, filename):
    """
    Writes itk transformation which is a subclass of
    `itk.MatrixOffsetTransformBase` into a text file. Fairly promitive.

    :param transformation: a transformation to be written to the file
    :type transformation: a subclass of `itk.MatrixOffsetTransformBase`

    :param filename: a file to write the transformation into
    :type filename: str
    """

    transform_writer = itk.TransformFileWriter.New()
    transform_writer.SetInput(transformation)
    transform_writer.SetFileName(filename)
    transform_writer.Update()


def load_warp_field_transform_from_file(warp_filed_filename):
    """
    Loads a warp field from the provided file and builds
    `itk.DisplacementFieldTransform` upon the loaded displacement filed. The
    displacement field should be a decent one, which means it should work with
    ANTS :)

    :paran warp_filed_filename: filename of the image containing the displacement field.
    :type warp_filed_filename: str
    """

    warp_image_type = pos_itk_core.autodetect_file_type(warp_filed_filename)
    dimension = warp_image_type.GetImageDimension()

    warp_image_reader = itk.ImageFileReader[warp_image_type].New()
    warp_image_reader.SetFileName(warp_filed_filename)
    warp_image_reader.Update()

    warp_transform = itk.DisplacementFieldTransform[(itk.D, dimension)].New()
    warp_transform.SetDisplacementField(warp_image_reader.GetOutput())

    return warp_transform


def reslice_image(transforms, moving_image, reference_image=None, interpolator=None, \
        default_pixel_value=0):
    """
    Apply `transforms` to the `moving_image` an reslice to the `reference_image` space.
    Reslicing is performed using the `interpolator`.

    :param transforms: iterable of transformations to be applied. All
    transformations are expected to be subclasses of the `itk.Transform` class.
    :type transforms: list

    :param moving_image: image to be resliced
    :type moving_image: `itk.Image`

    :param reference_image: Reference image for the reslicing process.
    :type rewference_image: `itk.Image`

    :param default_pixel_value: The default value of the pixel/voxel. Note that
    the provided value has to be compatibile with the image type. E.g. int for
    scalar integer, float for float data types and, for the vector images -- an
    iterable of aproperiate type and size. Be carefull here. Segfault will
    surely occur in case of incompatibility.
    :type default_pixel_value: int, float or tupe

    :param interpolator: Ready-to-use interpolation image function.
    Linear image interpolation function is used by default. Check `http://www.itk.org/Doxygen/html/group__ImageInterpolators.html`
    for a list of available image interpolation functions.
    :type interpolator: `itk.InterpolateImageFunction`
    """

    # Instanciate composite transform which will handle all the partial
    # transformations.
    composite_transform = \
        itk.CompositeTransform[(itk.D, moving_image.GetImageDimension())].New()

    # Fill the composite transformation with the partial transformations:
    for transform in transforms:
        composite_transform.AddTransform(transform)

    # Assign the reference image, If there is no reference image provided, the
    # moving image becomes a reference for itself.
    if reference_image is None:
        reference_image = moving_image

    # Set up the resampling filter.
    resample = itk.ResampleImageFilter[moving_image, reference_image].New()
    resample.SetTransform(composite_transform)
    resample.SetInput(moving_image)

    resample.SetSize(reference_image.GetLargestPossibleRegion().GetSize())
    resample.SetOutputOrigin(reference_image.GetOrigin())
    resample.SetOutputSpacing(reference_image.GetSpacing())
    resample.SetOutputDirection(reference_image.GetDirection())
    resample.SetDefaultPixelValue(default_pixel_value)
    resample.Update()

    return resample.GetOutput()


def read_itk_image(image_filename):
    """
    Loads the `image_filename` image.  Automatically detects the type of the
    image and selects approperiate image loader to handle the image file. The
    returned object is of `itk.Image` type.

    :param image_filename: File to load
    :type image_filename: str

    :return: Itk image object
    :rtype: `itk.Image`
    """

    # Autodetect the image type, instanciate approperiate reader type, load and
    # return the image.
    image_type = pos_itk_core.autodetect_file_type(image_filename)
    image_reader = itk.ImageFileReader[image_type].New()
    image_reader.SetFileName(image_filename)
    image_reader.Update()

    return image_reader.GetOutput()


def write_itk_image(image_to_save, filename):
    """
    Writes the provided `image_to_save` into `filename`. Fairly simple wrapper
    for the itk class `itk.ImageFileWriter`.

    :param image_to_save: Image to be saved.
    :type image_to_save: subclass of `itk.Image`.

    :param filename: Filename to store the image.
    :type filename: str
    """

    writer = itk.ImageFileWriter[image_to_save].New()
    writer.SetInput(image_to_save)
    writer.SetFileName(filename)
    writer.Update()


def apply_transformation_workflow(moving_file, output_file, reference_file, transformation_list=None):
    """
    Currently only two types of transformations are supported. If the
    transformation file a a text file it is assumed that is is a matrix based
    transformation althought this is not alway true. When the transformation
    file ends with '.nii' it is assumed to be deformation field. This is,
    actually, almost always true :)

    :param moving_file: Image to reslice filename
    :type moving_file: str

    :param output_file: Filename of the resliced image
    :type output_file: str

    :param reference_file: reference image filename
    :type reference_file: str

    :param transformation_list: List of filenames containing the individual
    (partial transformations).
    :type transformation_list: list of strings
    """

    moving_image = read_itk_image(moving_file)
    reference_image = read_itk_image(reference_file)

    transformations = []

    # Load transformations from the list. The transformations will be most
    # probably applied in the reverse order than the order of the list.
    for transformation_filename in transformation_list:
        if transformation_filename.endswith(".txt"):
            transformations.append(\
                load_itk_matrix_transform_from_file(transformation_filename))
        elif transformation_filename.endswith(".nii.gz"):
            transformations.append(\
                load_warp_field_transform_from_file(transformation_filename))
        else:
            print "Unrecognized transformation type"

    resliced_image = reslice_image(transformations,
        moving_image, reference_image)

    write_itk_image(resliced_image, output_file)


if __name__ == "__main__":
    pass
    #apply_transformation_workflow("0070.png", "x.nii.gz", "0070.nii.gz",
    #    ["x.txt", "d.nii.gz"])
