#!/usr/bin/pythoN

import sys
import os
import colorsys
import numpy as np
from scipy.interpolate import interp1d

DIRECTORY_PALLETES='palettes/'

def int_colour_to_float(colour, maxValue = 255.):
    return tuple(x / maxValue for x in colour)

def float_colour_to_int(colour, maxValue = 255):
    return tuple(int(x * maxValue) for x in colour)

class pos_color(object):
    """
    """
    def __init__(self, (r, g, b)):
        self.r = r
        self.g = g
        self.b = b
    
    @classmethod
    def from_int(pos_color, (rInt, bInt, gInt)):
        (r,g,b) = int_colour_to_float((rInt, bInt, gInt))
        return pos_color((r,g,b))
    
    @classmethod
    def from_html(pos_color, colorstring):
        colorstring = colorstring.strip()
        if colorstring[0] == '#': colorstring = colorstring[1:]
        if len(colorstring) != 6:
            raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        return pos_color.from_int((r, g, b))
     
    @classmethod
    def fromHSVTuple(cls, (h,s,v)):
        return cls(colorsys.hsv_to_rgb(h,s,v))
    
    def __str__(self):
        return str(self())
    
    def __call__(self):
        return self.__getValues()
    
    def __getInt(self, x):
        return int(x*255.)
    
    def __getIntTuple(self):
        return tuple(map(self.__getInt, self()))
    
    def __getHTMLcolor(self):
        return '#%02X%02X%02X' % self.rgb
    
    def __getValues(self):
        return (self.r, self.g, self.b)
    
    def __getHSVTuple(self):
        return colorsys.rgb_to_hsv(*self())

    def __get_gnuplot_color_format(self):
        return ' rgb "' + self.html + '"'
     
    rgb = property(__getIntTuple)
    html= property(__getHTMLcolor)
    hsv = property(__getHSVTuple)
    c   = property(__getValues)
    gnuplot = property(__get_gnuplot_color_format)

class pos_palette(object):
    """
    """
    def __init__(self, mapping, min = 0.0, max = 1.0):
        """
        mapping: {float: (float, float, float)i, ...}
        """
        
        assert max > min
        scale, offset = (max - min), min
        
        self._mapping = {}
        self.scale = float(scale)
        self.offset = float(offset)
        
        for val, color in mapping.iteritems():
            transformed = self._shift_scale(val)
            self._mapping[transformed] = pos_color(color)
        
        self._define_interpolation()
    
    def _define_interpolation(self, kind = 'linear'):
        m = sorted(self._mapping)
        r = map(lambda x: self._mapping[x].r, m)
        g = map(lambda x: self._mapping[x].g, m)
        b = map(lambda x: self._mapping[x].b, m)
        
        ic = \
           tuple(map(lambda x: interp1d(m, x, kind = kind), [r,g,b]))
        
        self._intepolated = ic
    
    def _shift_scale(self, value):
        return value * self.scale + self.offset
    
    def _interpolate(self, value):
        ci = map(lambda x: self._intepolated[x](value), range(3))
         
        return pos_color(tuple(map(float,ci)))
    
    def __call__(self, value):
        return self._interpolate(value)
    
    def _get_vtk_color_transfer_function(self, additional_mapping = None):
        try:
            import vtk
        except:
            print >>sys.stderr, "Cannot import vtk. exiting"
            return None
        
        if additional_mapping:
            xx = map(lambda p: p[0], additional_mapping)
            yy = map(lambda p: p[1], additional_mapping)
            print xx, yy 
            interpolator = interp1d(xx, yy)
        else:
            xx = sorted(self._mapping.keys())
            yy = xx
            interpolator = interp1d(xx, yy)
             
        ctf = vtk.vtkColorTransferFunction()
        
        for pt in xx:
            val = float(interpolator(pt))
            print pt, val, self(pt).c
            ctf.AddRGBPoint(val, *self(pt).c)
        
        return ctf
    
    def color_transfer_function(self, additional_mapping = None):
        return self._get_vtk_color_transfer_function(additional_mapping)
    
    @classmethod
    def from_gnuplot_file(cls, filename, delimiter=" ", min=0.0, max=1.0):
        """
        """
        
        mapping = {}
        for sourceLine in open(filename):
            if sourceLine.strip().startswith('#') or sourceLine.strip() == "":
                continue
            
            line = sourceLine.split("#")[0].strip().split(delimiter)
            value = float(line[0])
            
            r, g, b = map(lambda x: float(line[x]), range(1,4))
            mapping[value] = (r, g, b)
        
        return cls(mapping, min = min, max = max)
    
    @classmethod
    def lib(cls, name, min=0.0, max=1.0):
        return cls.from_gnuplot_file(os.path.join(DIRECTORY_PALLETES, name+'.gpf'), \
                                     min = min, max = max)

if __name__ == '__main__':
    pass
