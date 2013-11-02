import itk
import random
import sys
from pos_itk_core import autodetect_file_type, reorder_volume

# TODO: This is just to assert that the numner of dimensions is indeed 3
input_filename = sys.argv[1]
output_filename = sys.argv[2]
slicing_plane = 2
input_image_type = autodetect_file_type(input_filename)

_image_reader = itk.ImageFileReader[input_image_type].New()
_image_reader.SetFileName(input_filename)
_image_reader.Update()

_original_image = _image_reader.GetOutput()

_image_shape = _original_image.GetLargestPossibleRegion().GetSize()
reorder_mapping = range(_image_shape[slicing_plane])
random.shuffle(reorder_mapping)

_output_image = reorder_volume(_original_image, reorder_mapping, slicing_plane)

#TODO Assert the structure of the mapping!
#TODO Assert if the input image is 3d

itk.write(_output_image, output_filename, compression=True)
