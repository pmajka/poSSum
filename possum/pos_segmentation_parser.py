import csv
from pos_color import pos_color


__author__ = "Konrad Solarz, Piotr Majka"
__maintainer__ = "Piotr Majka"
__email__ = "pmajka@nencki.gov.pl"


class snap_label(object):

    def __init__(self, idx, (r, g, b), transparency, label_visibility,
            mesh_visibility, description):
        """
        All parameters are required.

        .. note::
            Not providing all parameters leads to a immediate error :)

        :param idx: Index of label
        :type int: int

        :param r: Red color intensity in RGB color model
        :type int: int

        :param g: Green color intensity in RGB color model
        :type int: int

        :param b: Blue color intensity in RGB color model
        :type int: int

        :param transparency: snap_label transparency expressed
            as a float from 0.00 to 1.00
        :type int: float

        :param label_visibility: Whether structure is visible in 2d overview
        :type int: bool

        :param mesh_visibility: Whether structure is visible in 3d overview
        :type int: bool

        :param description: Description of structure
        :type int: str

        And now a pleny of doctests ahead:

        >>> snap_label
        <class 'possum.pos_segmentation_parser.snap_label'>

        >>> snap_label()
        Traceback (most recent call last):
        TypeError: __init__() takes exactly 7 arguments (1 given)

        >>> snap_label(34, (30, 150, 244), 0.5, True, False, "Desc") #doctest: +ELLIPSIS
        <possum.pos_segmentation_parser.snap_label object at 0x...>

        >>> print snap_label(34, (30, 150, 244), 0.5, True, False, 3235)
           34    30   150   244     0.50  1  0    "3235"

        >>> print snap_label(34, (30, 150, 244), 0.5, True, False, False)
           34    30   150   244     0.50  1  0    "False"

        >>> snap_label(34, (30, 150, 244), 0.5, True, 4, "Desc.")
        Traceback (most recent call last):
        AssertionError: Boolean value expected

        >>> snap_label(34, (30, 150, 244), 0.5, "0", False, "Desc.")
        Traceback (most recent call last):
        AssertionError: Boolean value expected

        >>> snap_label(34, (30, 150, 244), 0.5, True, False)
        Traceback (most recent call last):
        TypeError: __init__() takes exactly 7 arguments (6 given)

        >>> snap_label(34, (30, 150, 244), -1, False, False, "Desc.")
        Traceback (most recent call last):
        AssertionError: A value between 0 and 1 is required

        >>> snap_label(34, (30, 150, 244), 1.1, False, False, "Desc.")
        Traceback (most recent call last):
        AssertionError: A value between 0 and 1 is required

        >>> snap_label(34, (30, 150, "ds"), 0.4, False, False, "Desc.")
        Traceback (most recent call last):
        AssertionError: A tuple of three integers ranging from 0 to 255 is required.

        >>> snap_label(34, (30, 150, 300), 0.4, False, False, "Desc.")
        Traceback (most recent call last):
        AssertionError: A tuple of three integers ranging from 0 to 255 is required.

        And now some testing of the properties:

        >>> label = snap_label(30, (150, 100, 200), 0.5, True, True, "Desc.")
        >>> label.color
        (150, 100, 200)

        >>> label.idx
        30

        >>> label.label_visibility
        True

        >>> label.mesh_visibility
        True

        >>> label.transparency
        0.5

        >>> label.description
        'Desc.'

        Now, let's change some properties:

        >>> label.idx = 40
        >>> label.idx == 40
        True

        >>> label.idx = "wrong"
        Traceback (most recent call last):
        AssertionError: Integer value expected

        >>> label.description = "Description"
        >>> label.description == "Description"
        True

        >>> label.color = (40, 100, 200)
        >>> label.color == (40, 100, 200)
        True

        >>> label.color = "#ff33aa"
        Traceback (most recent call last):
        ValueError: too many values to unpack

        >>> label.label_visibility = False
        >>> label.label_visibility == False
        True

        >>> label.mesh_visibility = False
        >>> label.mesh_visibility == False
        True

        >>> label.transparency = 1.0
        >>> label.transparency == 1.0
        True

        >>> str(label)
        '   40    40   100   200     1.00  0  0    "Description"'
        """

        self.idx = int(idx)

        self.color = (r, g, b)
        self.transparency = transparency
        self.label_visibility = label_visibility
        self.mesh_visibility = mesh_visibility
        self.description = description

    @staticmethod
    def from_row(row):
        """
        The provided list has to contain exactly eight elements:
            - Label index (integer)
            - Label red, green and blue color components which are to be
            integers between 0 and 255.
            - Label visibility (boolean)
            - Label mesh visibility (boolean)
            - Label description (string)

        :param row: Row from csv file, split in different values.
        :type row: [str, str, .... ]

        :returns: `snap_label` object

        Now, let's test this function out:

        >>> str(snap_label.from_row([0, 100, 150, 200, 0.5, 0, 1, "Test"]))
        '    0   100   150   200     0.50  0  1    "Test"'

        >>> str(snap_label.from_row(["0", "100", "150", "200", "0.5", "0", "1", "Test"]))
        '    0   100   150   200     0.50  0  1    "Test"'

        >>> str(snap_label.from_row([0, 100, 150, 200, 0.5, "False", 1, "Test"]))
        Traceback (most recent call last):
        ValueError: invalid literal for int() with base 10: 'False'

        >>> str(snap_label.from_row(["10", 100, 150, "200", 0.5, "0", 1, "Test"]))
        '   10   100   150   200     0.50  0  1    "Test"'
        """

        # Simply extract individual values from the list provided.
        idx, r, g, b = map(int, row[0:4])
        transparency = float(row[4])
        label_visibility = bool(int(row[5]))
        mesh_visibility = bool(int(row[6]))
        description = row[7].strip()

        # And then generate the label object
        label = snap_label(idx, (r, g, b), transparency,
                label_visibility, mesh_visibility, description)
        return label

    def __str__(self):
        idx = "{:>5d}".format(self.idx)
        color = "{:>6d}{:>6d}{:>6d}".format(*self.color)
        transparency = "{:>9}".format("{:.2f}".format(self.transparency))
        label_visibility = "{:>3d}".format(self.label_visibility)
        mesh_visibility = "{:>3d}".format(self.mesh_visibility)
        description = "    " + '"{}"'.format(self.description)

        return_line = [idx, color, transparency, label_visibility,
                       mesh_visibility, description]
        return "".join(return_line)

    def _get_color(self):
        return self._color.rgb

    def _set_color(self, (r, g, b)):
        """
        :param r: Red color intensity in RGB color model
        :type int: int

        :param g: Green color intensity in RGB color model
        :type int: int

        :param b: Blue color intensity in RGB color model
        :type int: int
        """
        self._color = pos_color.from_int((r, g, b))

    def _get_idx(self):
        return self._idx

    def _set_idx(self, value):
        assert isinstance(value, int), "Integer value expected"
        self._idx = value

    def _get_transparency(self):
        return self._transparency

    def _set_transparency(self, value):
        assert 0 <= value <= 1, \
            "A value between 0 and 1 is required"
        self._transparency = float(value)

    def _get_label_visibility(self):
        return self._visibility

    def _set_label_visibility(self, value):
        assert isinstance(value, bool), "Boolean value expected"
        self._visibility = value

    def _get_mesh_visibility(self):
        return self._mesh_visibility

    def _set_mesh_visibility(self, value):
        assert isinstance(value, bool), "Boolean value expected"
        self._mesh_visibility = value

    def _get_description(self):
        return self._description

    def _set_description(self, value):
        self._description = str(value)

    idx = property(_get_idx, _set_idx, None)
    color = property(_get_color, _set_color, None)
    transparency = property(_get_transparency, _set_transparency, None)
    label_visibility = property(_get_label_visibility, _set_label_visibility, None)
    mesh_visibility = property(_get_mesh_visibility, _set_mesh_visibility, None)
    description = property(_get_description, _set_description, None)


WHS_TOY_DELINEATION = \
r"""    0     0     0     0     0.00  0  0    "Clear_Label"
    1    51    51   255     1.00  1  1    "3rd_ventricle"
    2    51    51   255     1.00  1  1    "4th_ventricle"
    3   204   204   204     1.00  1  1    "Brain"
    4    78   189    13     1.00  1  1    "CNS"
    5   153   255   153     1.00  1  1    "Forebrain"
    6   255   102     0     1.00  1  1    "Hind_brain"
    7   255   153   153     1.00  1  1    "Midbrain"
    8   189    40   204     1.00  1  1    "amygdala"
    9   255   204     0     1.00  1  1    "anterior_commisure"
   10   255   255     0     1.00  1  1    "basal_forebrain" # doctest: +SKIP"""

ITKSNAP_DESCRIPTION_FILE_HEADER = \
"""################################################
# ITK-SnAP Label Description File
# File format:
# IDX   -R-  -G-  -B-  -A--  VIS MSH  LABEL
# Fields:
#    IDX:   Zero-based index
#    -R-:   Red color component (0..255)
#    -G-:   Green color component (0..255)
#    -B-:   Blue color component (0..255)
#    -A-:   Label transparency (0.00 .. 1.00)
#    VIS:   Label visibility (0 or 1)
#    IDX:   Label mesh visibility (0 or 1)
#  LABEL:   Label description
################################################"""

class snap_label_description(object):

    def __init__(self, labels=None):
        """
        :param labels: an iterable of labels with which the
                       `snap_label_description` object is
                       to be initialized. It is an optional kwarg
                       and it can be ommited.

        :type labels: an iterable of `snap_label` objects

        >>> snap_label_description
        <class 'possum.pos_segmentation_parser.snap_label_description'>

        >>> ld = snap_label_description() #doctest: +ELLIPSIS
        >>> ld #doctest: +ELLIPSIS
        <possum.pos_segmentation_parser.snap_label_description object at 0x...>

        >>> list(ld.iteritems())
        []

        >>> str(ld) == ITKSNAP_DESCRIPTION_FILE_HEADER + "\\n"
        True

        >>> label_1 = snap_label(4, (153, 255, 153), 1.0, True, True, "Forebrain")
        >>> label_2 = snap_label(8, (189, 40, 204), 1.0, True, True, "Amygdala")

        >>> ld = snap_label_description(label_1, label_2)
        Traceback (most recent call last):
        TypeError: __init__() takes at most 2 arguments (3 given)

        >>> ld = snap_label_description(label_1)
        Traceback (most recent call last):
        TypeError: argument 2 to map() must support iteration

        >>> ld = snap_label_description([label_1, label_2])

        And now testing with some actual content stored in a file-like object.
        As a toy example
        a Waxholm mouse brain reference delineation (a fragment) is used.
        See: http://www.3dbar.org:8080/getVolume?cafDatasetName=whs_0.51
        for more details.

        >>> labels = []
        >>> for line in WHS_TOY_DELINEATION.split("\\n"):
        ...    l = snap_label.from_row((line.replace('"','').split()))
        ...    labels.append(l)
        >>> ld = snap_label_description(labels)
        >>> ld.keys()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        >>> len(ld.values()) == 11
        True

        >>> len(ld.items()) == 11
        True

        >>> len(list(ld.iteritems())) == 11
        True

        >>> len(list(ld.itervalues())) == 11
        True

        >>> len(list(ld.iterkeys())) == 11
        True

        >>> str(ld[2])
        '    2    51    51   255     1.00  1  1    "4th_ventricle"'

        >>> ld[21] = snap_label(21, (153, 255, 153), 1.0, True, True, "Unknown")
        >>> ld[22] = snap_label(21, (153, 255, 153), 1.0, True, True, "Unknown")
        Traceback (most recent call last):
        AssertionError: The provided key (22) does not match the index of the label (21).

        >>> len(ld)
        12

        >>> del ld[21]
        >>> for k in ld.keys():
        ...     del ld[k]


        >>> import urllib, zipfile, os
        >>> urllib.urlretrieve("http://www.3dbar.org:8080/getVolume?cafDatasetName=whs_0.6.2", \
            "/tmp/whs_0.6.2.zip") #doctest: +ELLIPSIS
        ('/tmp/whs_0.6.2.zip', <httplib.HTTPMessage instance at 0x...>)
        >>> myzip = zipfile.ZipFile('/tmp/whs_0.6.2.zip')
        >>> labels_to_read = myzip.extract("whs_0.6.2_lut.txt", "/tmp/")

        >>> ld = snap_label_description.from_txt(labels_to_read)
        >>> ld.save_txt(labels_to_read)
        >>> ld = snap_label_description.from_txt(labels_to_read)

        >>> os.remove("/tmp/whs_0.6.2.zip")
        >>> os.remove('/tmp/whs_0.6.2_lut.txt')


        """

        # When list of labels is not provided, an empty dictionary
        # is created.
        if labels:
            self._labels = dict(map(lambda x: (x.idx, x), labels))
        else:
            self._labels = {}

    def __str__(self):
        labels = sorted(self.values(), key=lambda x: x.idx)
        return ITKSNAP_DESCRIPTION_FILE_HEADER + "\n" + \
               "\n".join(map(str, labels))

    def __setitem__(self, key, value):
        assert key == value.idx, \
            "The provided key (%d) does not match the index of the label (%d)." \
            % (key, value.idx)
        self._labels[key] = value

    def __delitem__(self, key):
        del self._labels[key]
        if len(self) == 0:
            del self

    def __len__(self):
        return len(self._labels)

    def __getitem__(self, key):
        return self._labels[key]

    def keys(self):
        return self._labels.keys()

    def items(self):
        return self._labels.items()

    def values(self):
        return self._labels.values()

    def itervalues(self):
        return self._labels.itervalues()

    def iterkeys(self):
        return self._labels.iterkeys()

    def iteritems(self):
        return self._labels.iteritems()

    @classmethod
    def _read_3dbar_format(cls, filename):
        """
        :param filename: path to 3dBar label file
        :type filename: string

        :returns: segmentation object, with labels included in the file
        """

        # This is quite a simple procedure for reading labels from a
        # tab/comma/space separated file which no header.

        csvfile = open(filename)
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)

        # We will collect label in this list
        list_of_labels = []

        for row in reader:
            label = snap_label.from_row(row)
            list_of_labels.append(label)

        csvfile.close()

        return cls(list_of_labels)

    @classmethod
    def _read_native_snap_format(cls, filename):
        """
        :param filename: path to ITKSnap label file
        :type filename: string

        :returns: snap_label_description -- object with labels included in the file
        """

        csvfile = open(filename).readlines()
        csv.register_dialect("spaces", delimiter=" ")

        # Determine on which line the header ends
        first_row = len(filter(lambda x: csvfile[x][0] == "#",
                           range(len(csvfile))))
        reader = csv.reader(csvfile[first_row:], dialect="spaces")

        # We will collect label in this list
        list_of_labels = []

        for row in reader:
            # filtering out empty strings returned by csv.reader object
            row = filter(None, row)
            label = snap_label.from_row(row)
            list_of_labels.append(label)

        return cls(list_of_labels)

    @classmethod
    def from_txt(cls, filename):
        """
        Merger function that can determine which format is dealing with
        and use proper function

        :param filename: path to label file
        :type filename: string

        :returns: snap_label_description -- object with labels included in the file
        """

        header = open(filename).read(1)

        # Sometimes, the file starts with a header lines. Such lines
        # start with hash character then a slightly different procedure
        # has to be utilized.
        if header == "#":
            return cls._read_native_snap_format(filename)
        else:
            return cls._read_3dbar_format(filename)

    def save_txt(self, filename):
        """
        Creates text file with settings for each label

        :param filename: file name and desired location of export file
        :type filename: string
        """

        open(filename, "w").write(str(self))


if __name__ == 'possum.pos_segmentation_parser':

    import doctest
    print doctest.testmod()
