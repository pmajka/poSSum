import os, sys
import numpy as np
import pickle
from config import Config

import itk
from possum import pos_itk_core

# -----------------------------------------------
# Load constatnts from the config file
# -----------------------------------------------
CONFIG = Config(file(sys.argv[1]))

def read_itk_image(image_filename):
    """
    Loads the `image_filename` image.  Automatically detects the type of the
    image and selects approperiate image loader to handle the image file. The
    returned object is of `itk.Image` type.

    :param image_filename: File to load
    :type image_filename: str

    :return: Itk image object
    :rtype: `itk.Image`

    TODO: Move this function to the pos_itk_core.
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

    TODO: Move this function to the pos_itk_core.
    """
    writer = itk.ImageFileWriter[image_to_save].New()
    writer.SetInput(image_to_save)
    writer.SetFileName(filename)
    writer.Update()


def reslice_image(transforms, moving_image, reference_image=None, interpolator=None, \
        default_pixel_value=0):
    """
    Apply `transforms` to the `moving_image` an reslice to the `reference_image` space.

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

    TODO: Document interpolator
    TODO: Document process of composing transformations.O
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


def write_itk_matrix_transformation_to_file(transformation, filename):
    """
    Writes itk transformation which is a subclass of
    `itk.MatrixOffsetTransformBase` into a text file. Fairly promitive.

    :param transformation: a transformation to be written to the file
    :type transformation: a subclass of `itk.MatrixOffsetTransformBase`

    :param filename: a file to write the transformation into
    :type filename: str
    """

    # TODO: Explain WTF?
    # http://www.itk.org/Wiki/ITK/Examples/IO/TransformFileReader
    # http://review.source.kitware.com/#/c/14293/1
    if (itk.Version.GetITKMajorVersion() == 4 and
        itk.Version.GetITKMinorVersion() >= 5) or \
       (itk.Version.GetITKMajorVersion() > 4):
        transform_writer = itk.TransformFileWriterTemplate.D.New()
    else:
        transform_writer = itk.TransformFileWriter.New()
    
    transform_writer.SetInput(transformation)
    transform_writer.SetFileName(filename)
    transform_writer.Update()


def get_random_rigid_3d_tranform_parameters(tmean, tsigma, rmean, rsigma):
    translations = np.random.normal(loc=tmean, scale=tsigma)
    rotations = np.random.normal(loc=np.radians(rmean), scale=np.radians(rsigma))

    return translations, rotations


def get_random_rigid_2d_params(tmean, tsigma, rmean, rsigma):
    translations = np.random.normal(loc=tmean, scale=tsigma)
    rotations = np.random.normal(
        loc=np.radians(rmean), scale=np.radians(rsigma))

    transform = itk.Euler2DTransform.D.New()
    transform.SetTranslation(list(translations))
    transform.SetRotation(rotations)
    transform.SetCenter(CONFIG['slice_image_center'])

    return transform


def apply_transformation_workflow(moving_file, output_file, output_transform_file=None):
    """
    """
    moving_image = read_itk_image(moving_file)

    translation, rotation = get_random_rigid_3d_tranform_parameters(
        tmean=CONFIG['tmean'], tsigma=CONFIG['tsigma'],
        rmean=CONFIG['rmean'], rsigma=CONFIG['rsigma'])

    vol_transform = itk.Euler3DTransform.D.New()
    vol_transform.SetTranslation([0, 0, 0])
    vol_transform.SetRotation(*list(rotation))

    center = [0, 0, 0]
    center[0] = moving_image.GetLargestPossibleRegion().GetSize()[0]/2
    center[1] = moving_image.GetLargestPossibleRegion().GetSize()[1]/2
    center[2] = moving_image.GetLargestPossibleRegion().GetSize()[2]/2
    center = map(int, center) # Sometimes the indexes are returned as long ints
    phisycal_center = moving_image.TransformIndexToPhysicalPoint(center)
    vol_transform.SetCenter(phisycal_center)

    resliced_image = reslice_image([vol_transform], moving_image,
                default_pixel_value=CONFIG['default_pixel_value'])
    write_itk_image(resliced_image, output_file)

    if output_transform_file:
        write_itk_matrix_transformation_to_file(vol_transform, output_transform_file)

def execute():
    apply_transformation_workflow(CONFIG['files']['ref_input'],
                                  CONFIG['files']['ref_deformed'],
                                  CONFIG['files']['ref_to_ref_transform'])

    for section_index in range(*CONFIG['range']):
        section_transform = get_random_rigid_2d_params(
            tmean=CONFIG['stmean'], tsigma=CONFIG['stsigma'],
            rmean=CONFIG['srmean'], rsigma=CONFIG['srsigma'])

        write_itk_matrix_transformation_to_file(section_transform,
                os.path.join(CONFIG['files']['slicewise_transf'] % section_index))

if __name__ == "__main__":
    execute()
