import csv
import colorsys


def int_colour_to_float(color, max_value=255., min_value=0.):
    """
    Convert colors provided as tuple of (r,g,b) components to tuple of floats
    ranging from 0 to 1. Only values ranging from 0 to 255 are mapped properly.
    Providing values from outside this range will cause an excepton.

    :param color: tuple of (r,g,b) components provided as
                  integers from 0 to 255
    :type color: (int, int, int)

    :return: tuple of (r,g,b) float components.

    An example of a good usage:

    >>> res = int_colour_to_float((128,100,200))
    >>> tuple(map(lambda x: round(x, 3), res))
    (0.502, 0.392, 0.784)

    Tests:

    >>> int_colour_to_float #doctest: +ELLIPSIS
    <function int_colour_to_float at 0x...>

    >>> int_colour_to_float()
    Traceback (most recent call last):
    TypeError: int_colour_to_float() takes at least 1 argument (0 given)

    >>> int_colour_to_float(100, 100, 100)
    Traceback (most recent call last):
    TypeError: 'int' object is not iterable

    >>> res = int_colour_to_float((128, 100))
    >>> tuple(map(lambda x: round(x, 3), res))
    (0.502, 0.392)

    >>> int_colour_to_float((128, 100, "x"))
    Traceback (most recent call last):
    AssertionError: A tuple of three integers ranging from 0 to 255 is required.

    >>> int_colour_to_float((128))
    Traceback (most recent call last):
    TypeError: 'int' object is not iterable

    >>> int_colour_to_float((0,0,0))
    (0.0, 0.0, 0.0)

    >>> int_colour_to_float((0, 255, 0))
    (0.0, 1.0, 0.0)

    >>> int_colour_to_float((0, 256, 0))
    Traceback (most recent call last):
    AssertionError: A tuple of three integers ranging from 0 to 255 is required.

    """
    assert all([min_value <= x <= max_value for x in color]) is True, \
        "A tuple of three integers ranging from 0 to 255 is required."

    return tuple(x / max_value for x in color)


def float_colour_to_int(color, maxValue=255.):
    """
    Convert (r,g,b) color tuple provided as integers to tuple of floats ranging
    from 0 to 1.

    :param color: tuple of (r,g,b) components ranging from 0 to 1.
    :type color: (float, float, float)

    :return: tuple of (r,g,b) integer components.

    An example of a good usage:

    >>> float_colour_to_int((0.4,0.01,0.9))
    (102, 2, 229)

    Tests:

    >>> float_colour_to_int()
    Traceback (most recent call last):
    TypeError: float_colour_to_int() takes at least 1 argument (0 given)

    >>> float_colour_to_int #doctest: +ELLIPSIS
    <function float_colour_to_int at 0x...>

    >>> float_colour_to_int()
    Traceback (most recent call last):
    TypeError: float_colour_to_int() takes at least 1 argument (0 given)

    >>> float_colour_to_int(0.4, 0.01, 0.9)
    Traceback (most recent call last):
    TypeError: float_colour_to_int() takes at most 2 arguments (3 given)

    >>> float_colour_to_int((0,0,0))
    (0, 0, 0)

    >>> float_colour_to_int((1,1,1))
    (255, 255, 255)

    >>> float_colour_to_int((0.5, 0.5, 0.5))
    (127, 127, 127)

    >>> float_colour_to_int((0.5))
    Traceback (most recent call last):
    TypeError: 'float' object is not iterable

    >>> float_colour_to_int((0.5, 0.2))
    (127, 51)

    >>> float_colour_to_int((0.5, 0.2,4))
    Traceback (most recent call last):
    AssertionError: A tuple of three float numbers ranging from 0 to 1 is required.
    """

    assert all([0 <= x <= 1 for x in color]) is True, \
        "A tuple of three float numbers ranging from 0 to 1 is required."

    return tuple(int(x * maxValue) for x in color)


class pos_color(object):
    """
    Color object. Class representing a color :) A versatile way of manipulating
    color information.

    An example of a good usage:

    >>> print pos_color((0.5,0.2,1.0)).rgb
    (127, 51, 255)

    >>> print pos_color.from_int((50,150,40)).rgb
    (50, 150, 40)

    >>> print pos_color.from_int((50,150,40)).html
    #329628

    >>> map(lambda x: "%0.2f" % x,pos_color.from_int((50,150,40)).hsv)
    ['0.32', '0.73', '0.59']

    >>> print pos_color.from_html("#44ff23").html
    #44FF23

    Testing all output formats:

    >>> p=pos_color.from_html("#1155ff")
    >>> map(lambda x: "%0.2f" % x, p.c) == ['0.07', '0.33', '1.00']
    True

    >>> p.gnuplot == ' rgb "#1155FF"'
    True

    >>> map(lambda x: "%0.2f" % x, p.hsv) == ['0.62', '0.93', '1.00']
    True

    >>> p.rgb == (17, 85, 255)
    True

    >>> p.html == '#1155FF'
    True

    Tests:

    >>> pos_color()
    Traceback (most recent call last):
    TypeError: __init__() takes exactly 2 arguments (1 given)

    >>> pos_color((0.5,0.2,1.0)) #doctest: +ELLIPSIS
    <__main__.pos_color object at 0x...>

    >>> p=pos_color((0.5,0.2,1.0))
    >>> print map(lambda x: "%0.2f" % x, p.c)
    ['0.50', '0.20', '1.00']
    """

    def __init__(self, (r, g, b)):
        """
        :param r: Red component of given color.
        :type r:  float from 0 to 1
        :param g: Green component of given color.
        :type g:  float from 0 to 1.
        :param b: Blue component of given color.
        :type b:  float from 0 to 1.

        Note that no argument validation is performed. Your are responsible
        for what you pass to the class.
        """

        # Just store the color components. Yes, it's just so simple.
        # Note that no argument validation is performed. Your are responsible
        # for what you pass to the class
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    def from_int(pos_color, (rInt, bInt, gInt)):
        """
        Create pos_color objects from tuple of integers from (0 to 255) instead
        of floats.

        :param rInt: Red component of given color, Integer from 0 to 255.
        :type rInt: int
        :param gInt: Green component of given color, Integer from 0 to 255.
        :type gInt: int
        :param bInt: Blue component of given color, Integer from 0 to 255.
        :type bInt: int

        :return: :class:`pos_color` object

        >>> pos_color.from_int()
        Traceback (most recent call last):
        TypeError: from_int() takes exactly 2 arguments (1 given)

        >>> pos_color.from_int(("3",3,0.1))
        Traceback (most recent call last):
        AssertionError: A tuple of three integers ranging from 0 to 255 is required.

        >>> pos_color.from_int((45,40,99)).rgb == (45,40,99)
        True

        >>> pos_color.from_int((0,0,0)).rgb == (45,40,0)
        False
        """

        (r, g, b) = int_colour_to_float((rInt, bInt, gInt))
        return pos_color((r, g, b))

    @classmethod
    def from_html(cls, colorstring):
        """
        Create pos_color object from html color string. String can be in form of
        either "#rrggbb" or just "rrggbb".

        :param colorstring: html color string.
        :type colorstring: str

        :return: :class:`pos_color` object

        >>> pos_color.from_html()
        Traceback (most recent call last):
        TypeError: from_html() takes exactly 2 arguments (1 given)

        >>> pos_color.from_html("#55hh66")
        Traceback (most recent call last):
        ValueError: invalid literal for int() with base 16: 'hh'

        >>> pos_color.from_html("#55ee66").html.lower() == "#55ee66"
        True

        >>> pos_color.from_html("#55ee66").rgb == (85, 238, 102)
        True
        """

        colorstring = colorstring.strip()

        # Check if the colorstring starts from "#"
        if colorstring[0] == '#':
            colorstring = colorstring[1:]

        if len(colorstring) != 6:
            raise ValueError, \
                "input #%s is not in #RRGGBB format" % colorstring

        # Extract individual color components and convert them to integers.
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]

        return cls.from_int((r, g, b))

    @classmethod
    def fromHSVTuple(cls, (h, s, v)):
        """
        Create color object from hue, saturation, value tuple.

        :return: :class:`pos_color` object
        """
        return cls(colorsys.hsv_to_rgb(h, s, v))

    def __str__(self):
        return str(self())

    def __call__(self):
        return self._getValues()

    def _getInt(self, x):
        return int(x * 255.)

    def _getIntTuple(self):
        return tuple(map(self._getInt, self()))

    def _getHTMLcolor(self):
        return '#%02X%02X%02X' % self.rgb

    def _getValues(self):
        return (self.r, self.g, self.b)

    def _getHSVTuple(self):
        return colorsys.rgb_to_hsv(*self())

    def _get_gnuplot_color_format(self):
        return ' rgb "' + self.html + '"'

    rgb = property(_getIntTuple)
    html = property(_getHTMLcolor)
    hsv = property(_getHSVTuple)
    c = property(_getValues)
    gnuplot = property(_get_gnuplot_color_format)


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
        <class '__main__.snap_label'>

        >>> snap_label()
        Traceback (most recent call last):
        TypeError: __init__() takes exactly 7 arguments (1 given)

        >>> snap_label(34, (30, 150, 244), 0.5, True, False, "Desc") #doctest: +ELLIPSIS
        <__main__.snap_label object at 0x...>

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
        assert type(value) == type(0), "Integer value expected"
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
        assert type(value) == type(True), "Boolean value expected"
        self._visibility = value

    def _get_mesh_visibility(self):
        return self._mesh_visibility

    def _set_mesh_visibility(self, value):
        assert type(value) == type(True), "Boolean value expected"
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


class snap_label_description(object):

    def __init__(self, labels=None):
        """
        TODO: Labels are to to snap labels
        #TODO: What is labels?
        """

        if labels:
            self._labels = dict(map(lambda x: (x.idx, x), labels))
        else:
            self._labels = {}

    def __str__(self):
        labels = sorted(self.values(), key=lambda x: x.idx)
        return "\n".join(map(str, labels))

    def __setitem__(self, key, value):
        """
        #TODO: Print warning when the key already
        # exists
        """
        self._labels[key] = value
        self._labels[key].color = self._color

    def __delitem__(self, key):
        del self[key]
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


if __name__ == "__main__":

#   l = snap_label(2, (24, 13, 43), 0.5, False, True, "sdfsd")
#   s1 = snap_label_description.from_txt("mbisc_11_lut_.txt")
#   print s1

    import doctest
    print doctest.testmod()
