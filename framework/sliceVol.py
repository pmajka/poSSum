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
from optparse import OptionParser, OptionGroup
import itk


INPUT_IMAGE_TYPE=itk.Image.UC3
OUTPUT_IMAGE_TYPE=itk.Image.UC2

r = itk.ImageFileReader[INPUT_IMAGE_TYPE].New()
r.SetFileName('/home/pmajka/fixed.nii.gz')
r.Update()

full_region = r.GetOutput().GetLargestPossibleRegion()

new_region = itk.ImageRegion[3]()
new_region.SetSize([175, 255, 0])
new_region.SetIndex([0,0,50])

w = itk.ImageFileWriter[OUTPUT_IMAGE_TYPE].New()

ef=itk.ExtractImageFilter[itk.Image.UC3,itk.Image.UC2].New()
ef.SetInput(r.GetOutput())
ef.SetExtractionRegion(new_region)
ef.SetDirectionCollapseToSubmatrix()
ef.Update()

w.SetFileName('/home/pmajka/x.nii.gz')
w.SetInput(ef.GetOutput())
w.Update()


class slice_vol():
    pass

