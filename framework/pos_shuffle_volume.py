import itk
import random
import sys
from pos_itk_core import autodetect_file_type, reorder_volume

_rgb_out_type = itk.Image.RGBUC3
_rgb_out_component_type = itk.Image.UC3

# TODO: This is just to assert that the numner of dimensions is indeed 3
input_filename = sys.argv[1]
output_filename = sys.argv[2]
slicing_plane = 2
input_image_type = autodetect_file_type(input_filename)

_image_reader = itk.ImageFileReader[input_image_type].New()
_image_reader.SetFileName(input_filename)
_image_reader.Update()

# Read number of the components of the image.
_numbers_of_components =\
    _image_reader.GetOutput().GetNumberOfComponentsPerPixel()

_original_image = _image_reader.GetOutput()

_image_shape = _original_image.GetLargestPossibleRegion().GetSize()
reorder_mapping = range(_image_shape[slicing_plane])
random.shuffle(reorder_mapping)

if _numbers_of_components > 1:
    print _numbers_of_components
    processed_components = []
    for i in range(_numbers_of_components):
        print i
        extract_filter = itk.VectorIndexSelectionCastImageFilter[_image_reader.GetOutput(),_rgb_out_component_type].New(\
            Input = _image_reader.GetOutput(),
            Index = i)
        extract_filter.Update()
        processed_channel = reorder_volume(extract_filter.GetOutput(), reorder_mapping, slicing_plane)
        processed_components.append(processed_channel)
        print processed_channel
    compose = itk.ComposeImageFilter[_rgb_out_component_type,_image_reader.GetOutput()].New(
                Input1 = processed_components[0],
                Input2 = processed_components[1],
                Input3 = processed_components[2])
    compose.Update()
    itk.write(compose.GetOutput(), output_filename)
else:
    processed_channel = reorder_volume(_image_reader.GetOutput(), reorder_mapping, slicing_plane)
    itk.write(processed_channel, output_filename)


#TODO Assert the structure of the mapping!
#TODO Assert if the input image is 3d
#python pos_shuffle_volume.py ~/Dropbox/Photos/oposy_skrawki/02_02_NN2/myelin.nii.gz ~/app.nii.gz
