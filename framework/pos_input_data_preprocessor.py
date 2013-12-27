#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys

import xlrd
import xlwt
import xlutils.copy

import hashlib
import math

from PIL import Image

SOURCE_IMAGES_DIR='/home/pmajka/possum/data/03_02_NN4/66_histology_extracted_slides/'
_ROW_OF_THE_FIRST_SLICE = 14 - 1
_DEFAULT_PADDING_ROUNDING = 100

_SLICE_INDEX_COLUMN = 1 # column b
_IMAGE_NAME_COLUMN = 2 # column c
_IMAGE_MASK_COLLUMN = 3 # column d
_IMAGE_RESOLUTION_COLUMN = 4 # column e
_REFERENCE_PLATE_INDEX_COLUMN = 5 # column f
_REFERENCE_COORDINATE_COLUMN = 6 # column g
_DISTORTION_INDEX_COLUMN = 8 # column I
_REPLACEMENT_INDEX_COLUMN = 9 # column J

_PROCESSING_RESOLUTION = 11 # column L
_ROTATION_COLUMN = 12 # column M
_HORIZONTAL_FLIP_COLLUMN = 13 # column N
_VERTICAL_FLIP_COLUMN = 14 # column O

_IMAGE_SIZE_COLUMN = 16 # column Q
_FILE_SIZE_COLUMN = 17 # column R
_FILE_HASH_COLUMN = 18 # column S
_PADDING_COLUMN = 19 # column T

def round_custom(value, level = _DEFAULT_PADDING_ROUNDING):
    return math.ceil(value / level + 1) * level

def md5sum(filename):
    """
    Borrowed from
    http://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
    """
    md5 = hashlib.md5()
    with open(filename,'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def get_image_size_pixels(filename):
    im = Image.open(filename)
    width, height = im.size
    return width, height


def get_padding(images):
    max_w = max(map(lambda x: x.image_size[0], images.values()))
    max_h = max(map(lambda x: x.image_size[1], images.values()))
    pad_w = round_custom(max_w)
    pad_h = round_custom(max_h)
    return pad_w, pad_h

class input_image(object):

    def __init__(self):
        self.image_index = None
        self.image_name = None
        self.mask_name = None
        self.image_resolution = None
        self.reference_image_index = None
        self.reference_coordinate = None
        self.distortion = None
        self.replacement_index = None

        self.process_resolution = None
        self.rotation = None
        self.horizontal_flip = False
        self.vertical_flip = False

        self.image_size = None
        self.file_size = None
        self.image_hash = None
        self.padded_size = None

    def get_downsampling(self):
        return self.process_resolution / self.image_resolution

    def __str__(self):
        return str(self.__dict__)


b = xlrd.open_workbook('/home/pmajka/Dropbox/administracja/u.xls')
s = b.sheet_by_index(0)
wb = xlutils.copy.copy(b)
stack_size = int(s.cell(3,2).value)
print "Stack size", stack_size

# TODO: Validate column names
# TODO: Validate image filenames
# TODO: Validate masks filenames.

# Create a dictionary for all the slices within given file
images = {}


# -------------------------------------------------------------------
# Extract all data related with a given slice.

for slice_index in range(stack_size):
    new_slice = input_image()
    new_slice.image_index = int(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _SLICE_INDEX_COLUMN).value)
    new_slice.image_name = str(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _IMAGE_NAME_COLUMN).value)
    new_slice.image_mask = str(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _IMAGE_MASK_COLLUMN).value)
    new_slice.image_resolution = float(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _IMAGE_RESOLUTION_COLUMN).value)

    cell_value = s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _REFERENCE_PLATE_INDEX_COLUMN).value
    try:
        value = int(cell_value)
    except:
        value = None
    new_slice.reference_image_index = value

    cell_value = s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _REFERENCE_COORDINATE_COLUMN).value
    try:
        value = float(cell_value)
    except:
        value = None
    new_slice.reference_coordinate = value

    new_slice.image_mask = str(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _DISTORTION_INDEX_COLUMN).value)

    cell_value = s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _REPLACEMENT_INDEX_COLUMN).value
    try:
        value = int(cell_value)
    except:
        value = None
    new_slice.replacement_index = value
    wb.get_sheet(0).write(_ROW_OF_THE_FIRST_SLICE + slice_index, _REPLACEMENT_INDEX_COLUMN, str(new_slice.replacement_index).lower())

    new_slice.process_resolution = float(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _PROCESSING_RESOLUTION).value)
    new_slice.rotation = int(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _ROTATION_COLUMN).value)
    new_slice.horizontal_flip = bool(int(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _HORIZONTAL_FLIP_COLLUMN).value))
    new_slice.vertical_flip = bool(int(s.cell(_ROW_OF_THE_FIRST_SLICE + slice_index, _VERTICAL_FLIP_COLUMN).value))

    filename = os.path.join(SOURCE_IMAGES_DIR, new_slice.image_name)
    stat = os.stat(filename)
    new_slice.file_size = stat.st_size
    wb.get_sheet(0).write(_ROW_OF_THE_FIRST_SLICE + slice_index, _FILE_SIZE_COLUMN, new_slice.file_size)

    new_slice.image_hash = md5sum(filename)
    wb.get_sheet(0).write(_ROW_OF_THE_FIRST_SLICE + slice_index, _FILE_HASH_COLUMN, new_slice.image_hash)

    new_slice.image_size = get_image_size_pixels(filename)
    wb.get_sheet(0).write(_ROW_OF_THE_FIRST_SLICE + slice_index, _IMAGE_SIZE_COLUMN, "x".join(map(str,new_slice.image_size)))

    new_slice.padded_size = None

    images[new_slice.image_index] = new_slice

    print new_slice

padded_image_size = tuple(map(int,get_padding(images)))
map(lambda x: setattr(x,'padded_size', padded_image_size), images.values())
# Put padding into the excel file:
for slice_index in range(stack_size):
    wb.get_sheet(0).write(_ROW_OF_THE_FIRST_SLICE + slice_index, _PADDING_COLUMN, "x".join(map(str,new_slice.padded_size)))

wb.save(os.path.join('/home/pmajka','output.xls'))
