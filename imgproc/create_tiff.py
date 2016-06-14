#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool creates empty GeoTIFF/TIFF based on another existing master image.
#   The pixel size and geo-coding is copied from the master image. Number
#   of bands and datatype must be set by the user.
#
#   Can be use as the start image for the GDAL rasterization.
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
from os.path import basename
from img import (
    FormatOptions, ImageFileReader, create_geotiff, DT2GDT, DEF_GEOTIFF_FOPT,
)
from img.cli import error

def usage():
    """Print a short command usage help."""
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <master> <output> <pix.type> <n.bands>" % exename
    )
    print >>sys.stderr, "EXAMPLE: %s input.tif output.tif uint8 3" % exename


if __name__ == "__main__":
    FOPTS = FormatOptions(DEF_GEOTIFF_FOPT) # default format options
    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        DTYPE = sys.argv[3]
        NBAND = int(sys.argv[4])
        # anything else is treated as a format option
        FOPTS.set_options(sys.argv[5:])
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    # check the number of bands and pixel type
    if DTYPE not in DT2GDT:
        error("Invalid pixel type! DTYPE=%s" % DTYPE)
        sys.exit(1)
    if NBAND < 1:
        error("Invalid band count! NBAND=%d" % NBAND)
        sys.exit(1)

    # open input image
    IMG_IN = ImageFileReader(INPUT)

    # creation parameters
    PARAM = {
        'path': OUTPUT,
        'nrow': IMG_IN.size.y,
        'ncol': IMG_IN.size.x,
        'nband': NBAND,
        'dtype': DTYPE,
        'options': FOPTS.options,
    }
    PARAM.update(IMG_IN.geocoding) # add geo-coding

    # open output image
    create_geotiff(**PARAM)
