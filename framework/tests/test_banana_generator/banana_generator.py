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

import os, sys
import Image
import ImageDraw
from math import radians, sin, cos
import numpy as np


image_size = 256
initial_banana_size = 32
slice_number = 16*1
starting_sine_angle = 45.
end_sine_angle = 135.

for i in range(slice_number):
    deg = (end_sine_angle - starting_sine_angle) /slice_number * i + starting_sine_angle
    d2 = float(i) / float(slice_number) * 180.

    r = initial_banana_size * sin(radians(d2)) + 0.25 * initial_banana_size
    x = image_size/2
    y = image_size + 4.*initial_banana_size*cos(radians(deg*2)) - 0.25 * image_size

    img = Image.new('RGB', size = (image_size, image_size), color = (0, 0, 0))
    canvas = ImageDraw.Draw(img)

    canvas.ellipse((x-r, y-r, x+r, y+r), fill=(255, 255, 255))
    img.save('f/%04d.png' % i)

    # -----------------------------------------------------

    mu, sigma, n = image_size/2, image_size/16, slice_number
    x_samples = np.random.normal(mu, sigma, size=1)
    y_samples = np.random.normal(mu, sigma, size=1)

    r_mu, r_std = 1.0, 0.1
    r_samples = np.random.normal(r_mu, r_std, size=1)
    x_samples = np.random.normal(r_mu, r_std, size=1)
    y_samples = np.random.normal(r_mu, r_std, size=1)

    x*= x_samples[0]
    y*= y_samples[0]
    r*= r_samples[0]

    img = Image.new('RGB', size = (image_size, image_size), color = (0, 0, 0))
    canvas = ImageDraw.Draw(img)

    canvas.ellipse((x-r, y-r, x+r, y+r), fill=(255, 255, 255))
    img.save('m/%04d.png' % i)
