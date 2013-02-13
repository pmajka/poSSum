#!/usr/bin/python

import sys
import os
import colorsys
from scipy.interpolate import interp1d

"""
Directory with all the available palettes, Palettes are stored as gnuplot
palette files which are basicly csv files in form of:
value red_component(0-1) green_component(0-1)  blue_component(0-1)
"""
DIRECTORY_PALLETES = 'palettes/'


def int_colour_to_float(color, max_value=255., min_value=0.):
    """
    Convert colors provided as tuple of (r,g,b) components to tuple of floats
    ranging from 0 to 1. Only values ranging from 0 to 255 are mapped properly.
    Providing values from outside this range will cause an excepton.

    :param color: tuple of (r,g,b) components provided as integers from 0 to 255
    :type color: (int, int, int)

    :return: tuple of (r,g,b) float components.

    An example of a good usage:

    >>> int_colour_to_float((128,100,200))
    (0.50196078431372548, 0.39215686274509803, 0.78431372549019607)

    Tests:

    >>> int_colour_to_float #doctest: +ELLIPSIS
    <function int_colour_to_float at 0x...>

    >>> int_colour_to_float()
    Traceback (most recent call last):
    TypeError: int_colour_to_float() takes at least 1 argument (0 given)

    >>> int_colour_to_float(100,100,100)
    Traceback (most recent call last):
    TypeError: 'int' object is not iterable

    >>> int_colour_to_float((128,100))
    (0.50196078431372548, 0.39215686274509803)

    >>> int_colour_to_float((128,100,"x"))
    Traceback (most recent call last):
    AssertionError: A tuple of three integers ranging from 0 to 255 is required.

    >>> int_colour_to_float((128))
    Traceback (most recent call last):
    TypeError: 'int' object is not iterable

    >>> int_colour_to_float((0,0,0))
    (0.0, 0.0, 0.0)

    >>> int_colour_to_float((0,255,0))
    (0.0, 1.0, 0.0)

    >>> int_colour_to_float((0,256,0))
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
    :tyepe color: (float, float, float)

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

    >>> float_colour_to_int(0.4,0.01,0.9)
    Traceback (most recent call last):
    TypeError: float_colour_to_int() takes at most 2 arguments (3 given)

    >>> float_colour_to_int((0,0,0))
    (0, 0, 0)

    >>> float_colour_to_int((1,1,1))
    (255, 255, 255)

    >>> float_colour_to_int((0.5,0.5,0.5))
    (127, 127, 127)

    >>> float_colour_to_int((0.5))
    Traceback (most recent call last):
    TypeError: 'float' object is not iterable

    >>> float_colour_to_int((0.5,0.2))
    (127, 51)

    >>> float_colour_to_int((0.5,0.2,4))
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
            raise ValueError, "input #%s is not in #RRGGBB format" % colorstring

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


class pos_palette(object):
    """
    An very flexible object for managing color palettes and lookup tables.

    :param mapping: {float: (float, float, float), ...}. A mapping from a value
        to the corensponding color provided by float r,g,b components ranging from
        0 to 1. The mapping can be either continous (with lot of entries) or
        discrete (with just a few entries). In both cases continous palette is
        built and color for any value within min,max range can be calculated.
    :type mapping: dict

    :param min: Lower bound of the palette
    :type min: int of float
    :param max: Upper bound of the lookup table.
    :type max: int of float

    An example of a good usage:

    >>> p=pos_palette({0.5:(0,0,0),2:(1,1,1)})
    >>> p(0.5).rgb
    (0, 0, 0)
    >>> p(2).html
    '#FFFFFF'
    >>> p(1.245).html
    '#7E7E7E'

    >>> p.from_gnuplot_file('palettes/bb.gpf') #doctest: +ELLIPSIS
    <__main__.pos_palette object at 0x...>
    >>> p(0.9).html
    '#444444'

    >>> p.lib('bb') #doctest: +ELLIPSIS
    <__main__.pos_palette object at 0x...>
    >>> p(0.9).html
    '#444444'

    >>> p.piecewise_function() #doctest: +ELLIPSIS
    <libvtkFilteringPython.vtkPiecewiseFunction vtkobject at 0x...>

    >>> p.color_transfer_function() #doctest: +ELLIPSIS
    <libvtkFilteringPython.vtkColorTransferFunction vtkobject at 0x...>

    """

    def __init__(self, mapping, min=0.0, max=1.0):
        """
        Tests

        >>> pos_palette()
        Traceback (most recent call last):
        TypeError: __init__() takes at least 2 arguments (1 given)

        >>> pos_palette
        <class '__main__.pos_palette'>

        >>> pos_palette({0:(0.4,0.6,0.1)})
        Traceback (most recent call last):
        ValueError: x and y arrays must have at least 2 entries

        >>> pos_palette({0:(0.4,0.6,0.1), 1:(0,0,0)}) #doctest: +ELLIPSIS
        <__main__.pos_palette object at 0x...>

        >>> p=pos_palette({0:(0.0,0.5,0.0), 1:(1,0,1)})
        >>> print p #doctest: +ELLIPSIS
        <__main__.pos_palette object at 0x...>

        >>> p.scale == 1.0
        True

        >>> p.offset == 0.0
        True

        >>> p(0) #doctest: +ELLIPSIS
        <__main__.pos_color object at 0x...>

        >>> p(0).html == "#007F00"
        True

        >>> p(-1)
        Traceback (most recent call last):
        ValueError: A value in x_new is below the interpolation range.

        >>> p(2)
        Traceback (most recent call last):
        ValueError: A value in x_new is above the interpolation range.

        >>> p=pos_palette({1:(0,0,0),0:(1,1,1)}, min=-1.0, max=5.0)
        >>> p.scale, p.offset
        (6.0, -1.0)

        >>> p(-1).html, p(5).html
        ('#FFFFFF', '#000000')

        >>> p=pos_palette({5:(0,0,0),-1:(1,1,1)})
        >>> p(-1).html, p(5).html
        ('#FFFFFF', '#000000')
        """

        # First thing to check :P
        assert max > min

        # Calculate scaling and offset mapping range (0,1) to (min,max)
        # and store them within the class
        self.scale, self.offset = float(max - min), float(min)

        # Define mappings and then define interpolation function between the
        # mapping entries.
        self._define_mapping(mapping)
        self._define_interpolation()

    def _define_mapping(self, mapping):
        # Initialize empty mapping
        self._mapping = {}

        # For every mapping entry create internal entry
        # scaled to min,max range
        for value, color in mapping.iteritems():
            transformed = self._shift_scale(value)
            self._mapping[transformed] = pos_color(color)

    def _define_interpolation(self, kind='linear'):
        """
        Define interpolation function for discrete mapping.

        :param kind: Kind of interpolation. See scipy interp1d function for list
        of available interpolation types (http://docs.scipy.org/doc/scipy/reference/interpolate.html)
        :type kind: str

        """
        # Get all the mapping values and sort them
        # Then get all the colors preserving their order
        m = sorted(self._mapping)
        r = map(lambda x: self._mapping[x].r, m)
        g = map(lambda x: self._mapping[x].g, m)
        b = map(lambda x: self._mapping[x].b, m)

        # Create three interpolation functions. Each interpolation function
        # interpolates single color channel thus we need three eof them. Perhaps
        # this step could be implemented in a better way (e.g. using numpy
        # arrays) but this implementation also works fine.
        # TODO: Implement using numpy arrays.
        ic = \
            tuple(map(lambda x: interp1d(m, x, kind=kind), [r, g, b]))

        # Store all the three interpolation functions.
        self._intepolated = ic

    def _shift_scale(self, value):
        """
        A trivial helper function that affinely transforms provided value.

        :param value: value to be scaled
        :type value: int or float
        """

        return value * self.scale + self.offset

    def _interpolate(self, value):
        """
        Return color corresponding to the provided value. The value can be any number within
        boundaries. If the value is not match any of the explicit mapping
        entries, it is interpolated.

        :param value: a number within table's boundaries.
        :return: pos_color
        """
        ci = map(lambda x: self._intepolated[x](value), range(3))

        return pos_color(tuple(map(float, ci)))

    def __call__(self, value):
        return self._interpolate(value)

    def _get_vtk_color_map_preprocess(self, additional_mapping=None):

        # If additional mapping is provided, execute this mapping.
        # Otherwise use the identity mapping.
        if additional_mapping:
            xpts = map(lambda p: p[0], additional_mapping)
            ypts = map(lambda p: p[1], additional_mapping)
        else:
            xpts = sorted(self._mapping.keys())
            ypts = xpts

        # Create intepolation function for the 'additional_mapping'
        interpolator = interp1d(xpts, ypts)

        return interpolator, xpts, ypts

    def _get_vtk_color_transfer_function(self, additional_mapping=None):
        # First off all, check if the python vtk binding is installed. If it's
        # not, the function cannot proceed.
        try:
            import vtk
        except:
            print >>sys.stderr, "Cannot import vtk. exiting"
            return None

        interpolator, xpts, ypts = \
            self._get_vtk_color_map_preprocess(additional_mapping)

        # Finally, create and fill the colot transfer function
        ctf = vtk.vtkColorTransferFunction()

        for xpt in xpts:
            value = float(interpolator(xpt))
            ctf.AddRGBPoint(value, *self(xpt).c)

        return ctf

    def color_transfer_function(self, additional_mapping=None):
        """
        Generate vtk 'vtkColorTransferFunction object' with exactly the same
        mapping as defined in the table.

        :param additional_mapping: [(x,y),(x,y),.....]. An additional mapping
            trough which source lookup table will be mapped (sic!). It sounds awful
            but works really cool. The 'additional_mapping' parameter is a piecewise
            linear (discrete) mapping.

        :return: :class:`vtk.vtkColorTransferFunction`

        An example usage:

        >>> p=pos_palette({5:(0,0,0),-1:(1,1,1)})
        >>> f=p.color_transfer_function()
        >>> f.GetColor(-1) == (1.0, 1.0, 1.0)
        True

        >>> f.GetColor(5) == (0.0, 0.0, 0.0)
        True

        >>> f.GetRange() == (-1.0, 5.0)
        True

        >>> f=p.color_transfer_function([(-1,0),(5,10)])
        >>> f.GetRange()
        (0.0, 10.0)
        >>> f.GetColor(0)
        (1.0, 1.0, 1.0)
        >>> f.GetColor(10)
        (0.0, 0.0, 0.0)
        >>> f.GetColor(5)
        (0.5, 0.5, 0.5)
        >>> p(0).c == f.GetColor(9)
        False

        >>> f=p.color_transfer_function([(-1,0),(0,9),(5,10)])
        >>> p(-1).c == f.GetColor(0)
        True
        >>> p(5).c == f.GetColor(10)
        True
        >>> p(0).c == f.GetColor(9)
        True
        """

        return self._get_vtk_color_transfer_function(additional_mapping)

    def _get_vtk_piecewise_function(self, additional_mapping=None):
        # First off all, check if the python vtk binding is installed. If it's
        # not, the function cannot proceed.
        try:
            import vtk
        except:
            print >>sys.stderr, "Cannot import vtk. exiting"
            return None

        interpolator, xpts, ypts = \
            self._get_vtk_color_map_preprocess(additional_mapping)

        # Finally, create and fill the colot transfer function
        ctf = vtk.vtkPiecewiseFunction()

        for xpt in xpts:
            value = float(interpolator(xpt))
            ctf.AddPoint(value, self(xpt).c[0])

        return ctf

    def piecewise_function(self, additional_mapping=None):
        """
        Generate vtk 'vtk.vtkPiecewiseFunction object' with exactly the same
        mapping as the first color component of the palette.

        :param additional_mapping: [(x,y),(x,y),.....]. An additional mapping
            trough which source lookup table will be mapped (sic!). It sounds awful
            but works really cool. The 'additional_mapping' parameter is a piecewise
            linear (discrete) mapping.

        :return: :class:`vtk.vtkPiecewiseFunction`

        An example usage:

        >>> p=pos_palette({5:(0,0,0),-1:(1,1,1)})
        >>> f=p.piecewise_function()
        >>> f.GetValue(-1) == 1.0
        True

        >>> f.GetValue(5) == 0.0
        True

        >>> f.GetRange() == (-1.0, 5.0)
        True

        >>> f=p.piecewise_function([(-1,0),(5,10)])
        >>> f.GetRange()
        (0.0, 10.0)
        >>> f.GetValue(0)
        1.0
        >>> f.GetValue(10)
        0.0
        >>> f.GetValue(5)
        0.5
        >>> p(0).c[0] == f.GetValue(9)
        False

        >>> f=p.color_transfer_function([(-1,0),(0,9),(5,10)])
        >>> p(-1).c == f.GetColor(0)
        True
        >>> p(5).c == f.GetColor(10)
        True
        >>> p(0).c == f.GetColor(9)
        True
        """
        return self._get_vtk_piecewise_function(additional_mapping)

    @classmethod
    def from_gnuplot_file(cls, filename, delimiter=" ", min=0.0, max=1.0):
        """
        Create lookup table based on given file containing gnuplot color
        palette.

        :param filename: path to file with the palette.
        :type filename: str

        :param delimiter: use custom delimiter instead of the default (space).
        Just in case when the file is stored in some unusual manner.
        :type delimiter: str

        :param min: Use custom lower boundary. Default is 0.
        :type min: int
        :param max: Use custom upper boundary. Default is 1.
        :type max: int

        :return: :class:`pos_palette`

        Tests:

        >>> pos_palette.from_gnuplot_file('palettes/bb.gpf') #doctest: +ELLIPSIS
        <__main__.pos_palette object at 0x...>

        >>> p = pos_palette.from_gnuplot_file('palettes/bb.gpf', min=0, max=100)
        >>> p(0).html == '#000000'
        True
        >>> p(1).html == '#050000'
        True
        >>> p(100).html == '#FFFFFF'
        True
        >>> p.scale == 100.0
        True

        >>> p.color_transfer_function().GetRange() == (0.0, 100.0)
        True

        >>> p.piecewise_function().GetRange() == (0.0, 100.0)
        True
        """

        # Initialize empty dictionary fo the mapping. Open provided file and
        # read the entry line by line.
        mapping = {}
        for sourceLine in open(filename):
            if sourceLine.strip().startswith('#') or sourceLine.strip() == "":
                continue

            line = sourceLine.split("#")[0].strip().split(delimiter)
            value = float(line[0])

            r, g, b = map(lambda x: float(line[x]), range(1, 4))
            mapping[value] = (r, g, b)

        return cls(mapping, min=min, max=max)

    @classmethod
    def lib(cls, name, min=0.0, max=1.0):
        """
        Load provided palette from the library of palettes within this
        framework.

        :param name: name of the palette,

        :param min: Use custom lower boundary. Default is 0.
        :param max: Use custom upper boundary. Default is 1.

        :return: pos_palette

        >>> p = pos_palette.lib('bb', min=0, max=100)
        >>> p(0).html == '#000000'
        True
        >>> p(1).html == '#050000'
        True
        >>> p(100).html == '#FFFFFF'
        True
        >>> p.scale == 100.0
        True

        >>> p.color_transfer_function().GetRange() == (0.0, 100.0)
        True

        >>> p.piecewise_function().GetRange() == (0.0, 100.0)
        True

        """
        execution_path = os.path.dirname(__file__)
        return cls.from_gnuplot_file(os.path.join(
            execution_path, DIRECTORY_PALLETES, name + '.gpf'),
            min=min, max=max)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
