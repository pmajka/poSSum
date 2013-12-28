#!/usr/bin/python
# -*- coding: utf-8 -*

import os, sys

import xlrd
import xlwt
import xlutils.copy

import hashlib
import math

from PIL import Image

# TODO: Validate column names
# TODO: Validate image filenames
# TODO: Validate masks filenames.

#SOURCE_IMAGES_DIR='/home/pmajka/possum/data/03_02_NN4/66_histology_extracted_slides/'
SOURCE_IMAGES_DIR='/home/pmajka/possum/data/03_01_NN3/66_histology_extracted_slides/'
_ROW_OF_THE_FIRST_SLICE = 14 - 1
_DEFAULT_PADDING_ROUNDING = 100
_DEFAULT_SHEET_INDEX = 0

_CELL_STACK_SIZE = (3, 2)

_SLICE_INDEX_COLUMN = 1 # column B
_IMAGE_NAME_COLUMN = 2 # column C
_IMAGE_MASK_COLLUMN = 3 # column D
_IMAGE_RESOLUTION_COLUMN = 4 # column E
_REFERENCE_PLATE_INDEX_COLUMN = 5 # column F
_REFERENCE_COORDINATE_COLUMN = 6 # column G
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

COLUMN_MAPPING = {
    'image_index' : (_SLICE_INDEX_COLUMN, int),
    'image_name' : (_IMAGE_NAME_COLUMN, str),
    'mask_name' : (_IMAGE_MASK_COLLUMN, str),
    'image_resolution' : (_IMAGE_RESOLUTION_COLUMN, float),
    'reference_image_index' : (_REFERENCE_PLATE_INDEX_COLUMN, int),
    'reference_coordinate' : (_REFERENCE_COORDINATE_COLUMN, float),
    'distortion' : (_DISTORTION_INDEX_COLUMN, str),
    'replacement_index' : (_REPLACEMENT_INDEX_COLUMN, int),
    'process_resolution' : (_PROCESSING_RESOLUTION, float),
    'rotation' : (_ROTATION_COLUMN, int),
    'horizontal_flip' : (_HORIZONTAL_FLIP_COLLUMN, bool),
    'vertical_flip' : (_VERTICAL_FLIP_COLUMN, bool),
    'image_size' : (_IMAGE_SIZE_COLUMN, list),
    'file_size' : (_FILE_SIZE_COLUMN, int),
    'image_hash' : (_FILE_HASH_COLUMN, str),
    'padded_size' : (_PADDING_COLUMN, list)}


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

class input_image(object):

    def __init__(self):
        self.index = None
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



workbook_in = '/home/pmajka/Dropbox/administracja/u.xls'

class worksheet_manager(object):
    self._metadata_to_load = ['image_index', 'image_name', 'mask_name',
        'image_resolution', 'reference_image_index', 'reference_coordinate',
        'replacement_index', 'distortion', 'process_resolution', 'rotation',
        'horizontal_flip', 'vertical_flip']
    self._metadata_to_establish = ['file_size', 'image_hash', 'image_size']

    def __init__(self, workbook_in, workbook_out):

        self._workbook_in = workbook_in
        self._workbook_out = workbook_out

        self._workbook = xlrd.open_workbook(workbook_in, formatting_info=True)
        self._worksheet = self._workbook.sheet_by_index(_DEFAULT_SHEET_INDEX)
        self._workbook_writer = xlutils.copy.copy(self._workbook)

        self._stack_size = int(self._worksheet.cell(*_CELL_STACK_SIZE).value)
        print "Stack size", self._stack_size

        # Create a dictionary for all the slices within given file
        self._images = {}

    def process(self):
        self.load_metadata_from_workbook()
        self.calculate_padding()
        self.save_workbook()

    def load_metadata_from_workbook(self):
        for slice_index in range(self._stack_size):
            new_slice = input_image()

            for metadata in self._metadata_to_load:
                value = self._read_from_workbook(metadata, slice_index)
                setattr(new_slice, metadata, value)

            for metadata in self._metadata_to_establish:
                value = getattr(self, ['determine_and_set_' + metadata])(new_slice)
                setattr(new_slice, metadata, value)
                self._write_to_workbook(metadata, slice_index, getattr(new_slice, metadata))

            self._images[new_slice.image_index] = new_slice

    def save_workbook(self):
        workbook_writer.save(self._workbook_out)

    def calculate_padding(self):
        padded_image_size = tuple(map(int, self.determine_and_set_padding()))
        map(lambda x: setattr(x,'padded_size', padded_image_size), self.images.values())

        for slice_index in range(self._stack_size):
            self._write_to_workbook('padded_size', slice_index, padded_image_size)

    def _read_from_workbook(self, attribute, slice_index):
        column, converter = COLUMN_MAPPING[attribute]
        row = self._get_row_index(slice_index)
        try:
            value = converter(self._worksheet.cell_value(row, column))
        except:
            value = None
        return value

    def _write_to_workbook(self, attribute, slice_index, value):
        column, converter = COLUMN_MAPPING[attribute]
        row = self._get_row_index(slice_index)

        if attribute in ['image_size', 'padded_size']:
            value = "x".join(map(str, value))

        workbook_writer.get_sheet(0).write(row, column, str(value))

    def _get_row_index(self, slice_index):
        return _ROW_OF_THE_FIRST_SLICE + slice_index

    def determine_and_set_file_size(self, new_slice):
        filename = os.path.join(SOURCE_IMAGES_DIR, new_slice.image_name)
        stat = os.stat(filename)
        return stat.st_size

    def determine_and_set_image_hash(self, new_slice):
        filename = os.path.join(SOURCE_IMAGES_DIR, new_slice.image_name)
        return md5sum(filename)

    def determine_and_set_image_size(self, new_slice):
        filename = os.path.join(SOURCE_IMAGES_DIR, new_slice.image_name)
        return get_image_size_pixels(filename)

    def determine_and_set_padding(self, new_slice=None):
        max_w = max(map(lambda x: x.image_size[0], self.images.values()))
        max_h = max(map(lambda x: x.image_size[1], self.images.values()))
        pad_w = round_custom(max_w)
        pad_h = round_custom(max_h)
        return pad_w, pad_h

if __name__ == "__main__":
    pass
