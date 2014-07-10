#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   calculate possible >gdaladdo< overview levels
#
#   Optionally the stretching can be performed in logarithmic (dB) scale.
#
# Project: Image Processing Tools
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

import sys
import os.path
import img_block as ib
import numpy as np

if __name__ == "__main__":
    # TODO: to improve CLI
    exename = os.path.basename(sys.argv[0])
    # block size
    bsx, bsy = 256, 256
    dbscale = False

    try:
        INPUT = sys.argv[1]
        STOP_MAX = int(sys.argv[2])
        STOP_MIN = int(sys.argv[3])

    except IndexError:
        sys.stderr.write("Not enough input arguments!\n")
        sys.stderr.write("USAGE: %s <input image> <stop_size_max> <stop_size_min>\n"%exename)
        sys.stderr.write("EXAMPLE: %s input.tif 256 16\n"%exename)
        sys.exit(1)

    level = []
    factor = 1
    imi = ib.ImgFileIn(INPUT)
    size = np.array([imi.sy, imi.sx], "int32")

    while np.all(size >= STOP_MIN) and np.any(size > STOP_MAX):
        factor *= 2
        level.append(factor)
        size = (size + 1) / 2

    print " ".join("%d"%v for v in level)
