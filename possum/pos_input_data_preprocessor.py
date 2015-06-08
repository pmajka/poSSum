#!/usr/bin/env python
# encoding: utf-8

import os
import pickle

import xlrd
import xlutils.copy

import hashlib
import math

from PIL import Image


_ROW_OF_THE_FIRST_SLICE = 14 - 1
_DEFAULT_PADDING_ROUNDING = 100
_DEFAULT_SHEET_INDEX = 0

_CELL_SPECIMEN_ID = (1, 2)
_CELL_STACK_SIZE = (3, 2)
_CELL_SLICING_PLANE = (4, 2)
_CELL_SLICE_THICKNESS = (5, 2)

_ATLAS_USE_REFERENCE = (2, 5)
_ATLAS_PLATE_EXTENT = (3, 5)
_ATLAS_PLATE_SPACING = (4, 5)

_SLICE_INDEX_COLUMN = 1  # column B
_IMAGE_NAME_COLUMN = 2  # column C
_IMAGE_MASK_COLLUMN = 3  # column D
_IMAGE_RESOLUTION_COLUMN = 4  # column E
_REFERENCE_PLATE_INDEX_COLUMN = 5  # column F
_REFERENCE_COORDINATE_COLUMN = 6  # column G
_DISTORTION_INDEX_COLUMN = 8  # column I
_REPLACEMENT_INDEX_COLUMN = 9  # column J

_PROCESSING_RESOLUTION = 11  # column L
_ROTATION_COLUMN = 12  # column M
_HORIZONTAL_FLIP_COLLUMN = 13  # column N
_VERTICAL_FLIP_COLUMN = 14  # column O

_IMAGE_SIZE_COLUMN = 16  # column Q
_FILE_SIZE_COLUMN = 17  # column R
_FILE_HASH_COLUMN = 18  # column S
_PADDING_COLUMN = 19  # column T
_OFFSET_COLLUMN = 20  # column U

COLUMN_MAPPING = {
    'image_index': (_SLICE_INDEX_COLUMN, int),
    'image_name': (_IMAGE_NAME_COLUMN, str),
    'mask_name': (_IMAGE_MASK_COLLUMN, str),
    'image_resolution': (_IMAGE_RESOLUTION_COLUMN, float),
    'reference_image_index': (_REFERENCE_PLATE_INDEX_COLUMN, int),
    'reference_coordinate': (_REFERENCE_COORDINATE_COLUMN, float),
    'distortion': (_DISTORTION_INDEX_COLUMN, str),
    'replacement_index': (_REPLACEMENT_INDEX_COLUMN, int),
    'process_resolution': (_PROCESSING_RESOLUTION, float),
    'rotation': (_ROTATION_COLUMN, int),
    'horizontal_flip': (_HORIZONTAL_FLIP_COLLUMN, bool),
    'vertical_flip': (_VERTICAL_FLIP_COLUMN, bool),
    'image_size': (_IMAGE_SIZE_COLUMN, list),
    'file_size': (_FILE_SIZE_COLUMN, int),
    'image_hash': (_FILE_HASH_COLUMN, str),
    'padded_size': (_PADDING_COLUMN, list),
    'offset': (_OFFSET_COLLUMN, list)}


def round_custom(value, level=_DEFAULT_PADDING_ROUNDING):
    """
    Rounds the provided integer _up_ to nearest 1, 100, 1000 or any other value
    defined by the `level` arguments.

    :param value: value to be rounded. Integer is required.
    :type value: int

    :param level: value to multiple of which the `value` number will be
                  rounded.
    :type level: int

    :return: `value` rounded up to nearest multiple of `level`
    :rtype: int
    """

    return math.ceil(value / level + 1) * level


def md5sum(filename):
    """
    Calculate a md5sum of a given file. Code borrowed from
    http://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python

    :param filename: filename to calculate a md5 sum of
    :type filename: str

    :return: md5 sum of the `filename`
    :rtype: str
    """

    md5 = hashlib.md5()

    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)

    return md5.hexdigest()


def read_image_size(filename):
    """
    Determines the width and height of the `filename` image.

    :param filename: filename to get a width and height of
    :type filename: str

    :return: tuple containing the width and height of the image.
    :rtype: (int, int)
    """

    image = Image.open(filename)
    width, height = image.size
    return width, height


class input_image(object):
    """
    An instance of the input image along with its metadata. Carries the cruical
    metadata as well as some auxiliary information e.g.:

        - Image filename,
        - Coresponding image mask (if assigned), NOT USED,
        - Image spatial resolution,
        - Reference image index nad refrence plane coordinate,
        - Type of distortion if the image is distorted,
        - Spatial resolution of the downsampled images,
        - Angle of rotation, if applied,
        - Horizontal and vertical flip, if applied,
        - Image file size, hash and dimensions
        - and many, many other.

    Some information is stored within the excel file, but some of the data has
    to be calculated during runtime.
    """

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
        self.offset = None

    def get_downsampling(self):
        return float((self.image_resolution / self.process_resolution) * 100.)

    def __str__(self):
        return str(self.__dict__)


class worksheet_manager(object):
    """
    #TODO XXX: Put some documentation here
    """

    _metadata_to_load = ['image_index', 'image_name', 'mask_name',
        'image_resolution', 'reference_image_index', 'reference_coordinate',
        'replacement_index', 'distortion', 'process_resolution', 'rotation',
        'horizontal_flip', 'vertical_flip']

    _metadata_to_establish = ['file_size', 'image_hash', 'image_size']

    def __init__(self, workbook_in, workbook_out=None, images_dir=None):
        """
        :param workbook_in: path to the workflow to read the data from
        :type workbook_in: str

        :param workbook_out: path to the workflow to write the updated data to
        (in when no `workbook_out` is provided, the `workbook_in` is used and
        the opration is performed 'in place'.
        :type workbook_out: str

        :param images_dir: directory containing the source images described by
        the workbook.
        :type image_dir: str
        """

        # When no output workbook is provided, use the input workbook as the
        # output workbook so whole the operation will be perfomed 'in place'.
        if workbook_out is None:
            workbook_out = workbook_in

        # Assign all the important things.
        self._workbook_in = workbook_in
        self._workbook_out = workbook_out
        self._images_dir = images_dir

        # Open the workbook and immediately assign the workbook writer to be
        # able to edit the opened workbook.
        self._workbook = xlrd.open_workbook(workbook_in, formatting_info=True)
        self._worksheet = self._workbook.sheet_by_index(_DEFAULT_SHEET_INDEX)
        self._workbook_writer = xlutils.copy.copy(self._workbook)

        # Create a dictionary for all the slices within given file
        # This is the MOST IMPORTANT data structure within this class.
        self._images = {}

    def process(self):
        """
        Execute the pipeline.
        """

        self.load_settings_from_workbook()
        self.load_metadata_from_workbook()
        self.calculate_padding()
        self.save_workbook()

    def load_settings_from_workbook(self):
        """
        Load those data from the workbook which are common for all the images.
        These could be e.g. masking options, stack size, etc. Anyway we need
        them before we start processing the individial images.

        In other words -- extract metadata not associated with individual
        images.
        """

        # Extract the stack size. Based in the stack size, the number and the
        # indexes of the consecutive slices.
        self._specimen_id = str(self._worksheet.cell_value(*_CELL_SPECIMEN_ID))
        self._stack_size = int(self._worksheet.cell_value(*_CELL_STACK_SIZE))
        self._slice_thickness = \
            float(self._worksheet.cell_value(*_CELL_SLICE_THICKNESS))
        self._slicing_plane = \
            str(self._worksheet.cell_value(*_CELL_SLICING_PLANE))

        # Also, extract the information about the reference atlas
        # We can use the atlas or not. Depending on the xls content, a proper
        # switch is defined.
        self._use_atlas = False
        if bool(int(self._worksheet.cell_value(*_ATLAS_USE_REFERENCE))):
            self._use_atlas = True
            self._atlas_plate_spacing = \
                self._worksheet.cell_value(*_ATLAS_PLATE_SPACING)
            self._atlas_plate_size = \
                map(int, self._worksheet.cell_value(*_ATLAS_PLATE_EXTENT).strip().split("x"))

    def load_metadata_from_workbook(self):
        """
        Load the metadata associated with individial images.
        """

        # Iterate over all slices defined in the workbook and read the metadata
        # form the workbook cells. The metadata will be saved into the
        # `input_image` data structures ultimately passed for further
        # manipulation in next steps of the workflow.
        for slice_index in range(self._stack_size):
            new_slice = input_image()

            # There are two kinds of metadata. The first kind are the values
            # which can be simply read from the workbook. They are processed
            # below.
            for metadata in self._metadata_to_load:
                value = self._read_from_workbook(metadata, slice_index)
                setattr(new_slice, metadata, value)

            # The other kind of metadata are the attributes which require
            # additional calculations or processing. They are dealt with in the
            # code below.
            for metadata in self._metadata_to_establish:
                attribute_name = 'determine_and_set_' + metadata
                value = getattr(self, attribute_name)(new_slice)
                setattr(new_slice, metadata, value)
                self._write_to_workbook(metadata, slice_index, value)

            # Finally the given image is appended to the global image stack.
            self._images[new_slice.image_index] = new_slice

    def save_workbook(self):
        """
        Save the the updated workflow under the provided filename. See the
        `__init__` method for documentation on how to set the filename.
        """
        self._workbook_writer.save(self._workbook_out)

        # Also save a pickled version of the image dictionary. This will be
        # usefull in other python sctipts.
        pth, ext = os.path.splitext(self._workbook_out)
        pickle.dump(self._images, open(pth + ".pickle", "w"))

    def calculate_padding(self):
        """
        Sets a padded image size. The padded image size is a size which is
        larger that the largest extent of the images.

        The padded width and height are calculated by taking the maximal width
        and height among all the images and then rounding them up to a multiple
        on some base value (e.g. 10, 100, 500, etc.)

        An example might be: 154 -> 200, or 1045 -> 1500.
        """

        # Get the padding size and update the internal data structure:
        # `self._images`.
        padded_size = tuple(map(int, self._get_padding()))
        map(lambda x: setattr(x, 'padded_size', padded_size),
            self._images.values())

        # Then update the workbook with the calculated padding.
        for slice_index in range(self._stack_size):
            self._write_to_workbook('padded_size', slice_index, padded_size)

        # Now, calculate the offset from the initial origin for each of the
        # images. This is only possible after calculating the padding.
        for (index, (key, image)) in enumerate(sorted(self._images.iteritems())):
            offset_x = float(image.padded_size[0] - image.image_size[0]) *\
                       image.image_resolution / 2.0
            offset_y = float(image.padded_size[1] - image.image_size[1]) *\
                       image.image_resolution / 2.0

            offset = "x".join(map(str, (offset_x, offset_y)))
            self._write_to_workbook('offset', index, offset)
            image.offset = [offset_x, offset_y]

    def _read_from_workbook(self, attribute, slice_index):
        """
        Read an attribute of a given slice from the workbook.

        :param attribute: attribute to be extracted from the workbook. it is
            assumed that the attribute name is the valid one.
        :type attribute: str

        :param slice_index: index of the slice of which the attribute will be
            extracted.  Of course the provided slice index has to a valid one.
        :type slice_index: int
        """
        # Extract the colum containing the given attribute and the proper
        # converted function which converts a string value extracted from the
        # workbook cell into an actual parameters value.
        column, converter = COLUMN_MAPPING[attribute]

        # Get the workbook row describing particular slice index.
        row = self._get_row_index(slice_index)

        # Try to extract the attribute value. If the readout causes an
        # exception, just accept it and put None as the attribute value.
        try:
            value = converter(self._worksheet.cell_value(row, column))
        except:
            value = None
        return value

    def _write_to_workbook(self, attribute, slice_index, value):
        """
        Write a given attribute value into the workbook file.

        :param attribute: attribute to be extracted from the workbook. it is
            assumed that the attribute name is the valid one.
        :type attribute: str

        :param slice_index: index of the slice of which the attribute will be
            extracted.  Of course the provided slice index has to a valid one.
        :type slice_index: int

        :param value: Value of the attribute
        :type value: various, depends on the particular attribute.
        """
        # Again, get the column index corresponding to the given attribute, as
        # well as the converter function (which will not be used in this
        # function) and the row describing given slice.
        column, converter = COLUMN_MAPPING[attribute]
        row = self._get_row_index(slice_index)

        # Some paramteres are threaed in a different way than the other.
        if attribute in ['image_size', 'padded_size']:
            value = "x".join(map(str, value))

        # Put the parameter value into the proper cell.
        self._workbook_writer.get_sheet(0).write(row, column, str(value))

    def _get_row_index(self, slice_index):
        """
        Get the workbook row index corresponding to a given slice inde.

        :param slice_index: index of the slice for which the row index will be
            determined.
        :type slice_index: int

        :return: slice index
        :rtype: int
        """
        return _ROW_OF_THE_FIRST_SLICE + slice_index

    def determine_and_set_file_size(self, new_slice):
        """
        Get the size of the image file.

        :param new_slice: slice for which the size of the filename will be
            determined.
        :type new_slice: `input_image`

        :return: size of the file in bytes.
        :rtype: int
        """
        filename = os.path.join(self._images_dir, new_slice.image_name)
        stat = os.stat(filename)
        return stat.st_size

    def determine_and_set_image_hash(self, new_slice):
        """
        Get the md5 checksum of the file corresponding to the given slice.

        :param new_slice: slice for which the md5 checksum will be caluculated.
        :type new_slice: `input_image`

        :return: md5 sum of the image file.
        :rtype: str
        """
        filename = os.path.join(self._images_dir, new_slice.image_name)
        return md5sum(filename)

    def determine_and_set_image_size(self, new_slice):
        """
        Get the image size (width and height of the image file).

        :param new_slice: slice to determine the size of
        :type new_slice: `input_image`

        :return: tuple containing the width and height of the image.
        :rtype: (int, int)
        """
        filename = os.path.join(self._images_dir, new_slice.image_name)
        return read_image_size(filename)

    def _get_padding(self, new_slice=None):
        """
        Get the padding size for the image stack.

        :param new_slice: Leave the default value. The actual parameter value
        is never used and the function header looks the way it looks only for
        compatibility reasons.
        :type new_slice: None, just leave it as it is.

        :return: a padded images size (which is common for the whole image
            stack).
        :rtype: (int, int)
        """
        max_w = max(map(lambda x: x.image_size[0], self._images.values()))
        max_h = max(map(lambda x: x.image_size[1], self._images.values()))
        pad_w = round_custom(max_w)
        pad_h = round_custom(max_h)
        return pad_w, pad_h


if __name__ == "__main__":
    pass
