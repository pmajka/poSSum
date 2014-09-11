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
    <possum.pos_color.pos_color object at 0x...>

    >>> p=pos_color((0.5,0.2,1.0))
    >>> print map(lambda x: "%0.2f" % x, p.c)
    ['0.50', '0.20', '1.00']

    >>> str(p) == '(0.5, 0.2, 1.0)'
    True
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

        >>> pos_color.from_html("#55ee66X")
        Traceback (most recent call last):
        ValueError: input #55ee66X is not in #RRGGBB format
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
    def from_hsv(cls, (h, s, v)):
        """
        Create color object from hue, saturation, value tuple.

        :return: :class:`pos_color` object

        >>> pos_color.from_hsv((0.2, 0.3, 0.4)).rgb
        (95, 102, 71)

        >>> pos_color.from_hsv((0.2, 0.3, 0.4, 4))
        Traceback (most recent call last):
        ValueError: too many values to unpack
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

if __name__ == 'possum.pos_color':
    import doctest
    print doctest.testmod()
