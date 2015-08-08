import os, sys
import numpy as np
import pickle
from config import Config

import itk
from possum import pos_itk_transforms

# -----------------------------------------------
# Load constatnts from the config file
# -----------------------------------------------
CONFIG = Config(file(sys.argv[1]))


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
    moving_image = pos_itk_transforms.read_itk_image(moving_file)

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

    resliced_image = pos_itk_transforms.reslice_image([vol_transform],
        moving_image, default_pixel_value=CONFIG['default_pixel_value'])
    pos_itk_transforms.write_itk_image(resliced_image, output_file)

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
