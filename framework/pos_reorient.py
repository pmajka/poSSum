#!/usr/bin/python
# -*- coding: utf-8 -*
###############################################################################
#                                                                             #
#    This file is part of Multimodal Atlas of Monodelphis Domestica           #
#                                                                             #
#    Copyright (C) 2011-2012 Piotr Majka                                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is free software: you can redistribute      #
#    it and/or modify it under the terms of the GNU General Public License    #
#    as published by the Free Software Foundation, either version 3 of        #
#    the License, or (at your option) any later version.                      #
#                                                                             #
#    3d Brain Atlas Reconstructor is distributed in the hope that it          #
#    will be useful, but WITHOUT ANY WARRANTY; without even the implied       #
#    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.         #
#    See the GNU General Public License for more details.                     #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along  with  3d  Brain  Atlas  Reconstructor.   If  not,  see            #
#    http://www.gnu.org/licenses/.                                            #
#                                                                             #
###############################################################################

import sys, os
import datetime, logging
from optparse import OptionParser, OptionGroup
import itk

from pos_slice_volume import autodetect_file_type, setup_logging

# Dictionary below copied from (Sun Apr  7 14:04:28 CEST 2013)
# http://code.google.com/p/medipy/source/browse/lib/medipy/itk/types.py?name=default&r=0da35e1099e5947151dee239f7a09f405f4e105c
io_component_type_to_type = {
        itk.ImageIOBase.UCHAR : itk.UC,
        itk.ImageIOBase.CHAR : itk.SC,
        itk.ImageIOBase.USHORT : itk.US,
        itk.ImageIOBase.SHORT : itk.SS,
        itk.ImageIOBase.UINT : itk.UI,
        itk.ImageIOBase.INT : itk.SI,
        itk.ImageIOBase.ULONG : itk.UL,
        itk.ImageIOBase.LONG : itk.SL,
        itk.ImageIOBase.FLOAT : itk.F,
        itk.ImageIOBase.DOUBLE : itk.D,
        }

# And this is my own invention: a dictionary that converts tuple of specific
# image parameters into itk image type. We all love ITK heavy templated code
# style!
io_component_string_name_to_image_type = {
        ('scalar', 'short', 3) : itk.Image.SS3,
        ('scalar', 'unsigned_short', 3) : itk.Image.US3,
        ('scalar', 'unsigned_char', 3) : itk.Image.UC3,
        ('vector', 'unsigned_char', 3) : itk.Image.RGBUC3,
        ('scalar', 'short', 2) : itk.Image.SS2,
        ('scalar', 'unsigned_short', 2) : itk.Image.US2,
        ('vector', 'unsigned_char', 2) : itk.Image.RGBUC2,
        ('scalar', 'unsigned_char', 2) : itk.Image.UC2,
        ('scalar', 'float', 3) : itk.Image.F3
        }

# Another quite clever dictionary. This one converts given image type to the
# same type but with number of dimensions reduced by one (e.g. 3->2).
types_reduced_dimensions = {
        itk.Image.SS3 : itk.Image.SS2,
        itk.Image.US3 : itk.Image.US2,
        itk.Image.UC3 : itk.Image.UC2,
        itk.Image.RGBUC3 : itk.Image.RGBUC2,
        itk.Image.F3 : itk.Image.F2
    }

CoordinateMajornessTerms = {
    'ITK_COORDINATE_PrimaryMinor' : 0,
    'ITK_COORDINATE_SecondaryMinor' : 8,
    'ITK_COORDINATE_TertiaryMinor' : 16
}

CoordinateTerms = {
     'ITK_COORDINATE_UNKNOWN': 0,
     'ITK_COORDINATE_Right': 2,
     'ITK_COORDINATE_Left': 3,
     'ITK_COORDINATE_Posterior': 4,
     'ITK_COORDINATE_Anterior': 5,
     'ITK_COORDINATE_Inferior': 8,
     'ITK_COORDINATE_Superior': 9
}

ValidCoordinateOrientationFlags = {
    'ITK_COORDINATE_ORIENTATION_INVALID': CoordinateTerms['ITK_COORDINATE_UNKNOWN'],
    'ITK_COORDINATE_ORIENTATION_RIP': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LIP': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_RSP': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LSP': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_RIA': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LIA': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_RSA': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LSA': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),

    'ITK_COORDINATE_ORIENTATION_IRP': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ILP': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SRP': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SLP': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_IRA': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ILA': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SRA': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SLA': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),

    'ITK_COORDINATE_ORIENTATION_RPI': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LPI': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_RAI': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LAI': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_RPS': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LPS': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_RAS': ( CoordinateTerms['ITK_COORDINATE_Right']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_LAS': ( CoordinateTerms['ITK_COORDINATE_Left']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),

    'ITK_COORDINATE_ORIENTATION_PRI': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_PLI': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ARI': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ALI': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_PRS': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_PLS': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ARS': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ALS': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),

    'ITK_COORDINATE_ORIENTATION_IPR': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SPR': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_IAR': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SAR': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_IPL': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SPL': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Posterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_IAL': ( CoordinateTerms['ITK_COORDINATE_Inferior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_SAL': ( CoordinateTerms['ITK_COORDINATE_Superior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Anterior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),

    'ITK_COORDINATE_ORIENTATION_PIR': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_PSR': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_AIR': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ASR': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Right'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_PIL': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_PSL': ( CoordinateTerms['ITK_COORDINATE_Posterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_AIL': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Inferior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] ),
    'ITK_COORDINATE_ORIENTATION_ASL': ( CoordinateTerms['ITK_COORDINATE_Anterior']
    << CoordinateMajornessTerms['ITK_COORDINATE_PrimaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Superior'] << CoordinateMajornessTerms['ITK_COORDINATE_SecondaryMinor'] )
    + ( CoordinateTerms['ITK_COORDINATE_Left'] << CoordinateMajornessTerms['ITK_COORDINATE_TertiaryMinor'] )
}

ValidOriginFlags =  {
   'ITK_ORIGIN_IRP' : 0,
   'ITK_ORIGIN_IRA' : 1,
   'ITK_ORIGIN_ILP' : 2,
   'ITK_ORIGIN_ILA' : 3,
   'ITK_ORIGIN_SRP' : 4,
   'ITK_ORIGIN_SRA' : 5,
   'ITK_ORIGIN_SLP' : 6,
   'ITK_ORIGIN_SLA' : 7
}


setup_logging(log_filename=None, log_level='DEBUG')

input_filename = sys.argv[1]
output_filename = sys.argv[2]

input_image_type = autodetect_file_type(input_filename)
output_image_type = input_image_type

image_reader = itk.ImageFileReader[input_image_type].New()
image_reader.SetFileName(input_filename)
image_reader.Update()

flipper = itk.FlipImageFilter[input_image_type].New(image_reader)
flipper.FlipAboutOriginOff()
flipper.SetFlipAxes([0, 0, 1])
flipper.Update()

permute = itk.PermuteAxesImageFilter[input_image_type].New(flipper)
permute.SetOrder([0,1,2])

change_info = itk.ChangeInformationImageFilter[input_image_type].New(permute)

cast = itk.CastImageFilter[input_image_type, output_image_type].New(change_info)

#   reorient = itk.OrientImageFilter[input_image_type, input_image_type].New(image_reader)
#   print image_reader.GetOutput().GetDirection().GetVnlMatrix().get(0,0)
#   print image_reader.GetOutput().GetDirection().GetVnlMatrix().get(1,1)
#   print image_reader.GetOutput().GetDirection().GetVnlMatrix().get(2,2)
#   #reorient.SetGivenCoordinateOrientation(ValidCoordinateOrientationFlags['ITK_COORDINATE_ORIENTATION_RAI'])
#   reorient.UseImageDirectionOn()
#   #reorient.SetDesiredCoordinateOrientation(ValidCoordinateOrientationFlags['ITK_COORDINATE_ORIENTATION_RAS'])
#   #reorient.SetDesiredCoordinateOrientationToSagittal()
#   print reorient.GetFlipAxes()
#   print reorient.GetPermuteOrder()
#   reorient.Update()
#   print reorient.GetOutput().GetDirection().GetVnlMatrix().get(0,0)
#   print reorient.GetOutput().GetDirection().GetVnlMatrix().get(1,1)
#   print reorient.GetOutput().GetDirection().GetVnlMatrix().get(2,2)

image_writer = itk.ImageFileWriter[output_image_type].New()
image_writer.SetInput(permute.GetOutput())
image_writer.SetFileName(output_filename)
image_writer.Update()
