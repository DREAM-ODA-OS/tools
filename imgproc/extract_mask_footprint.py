#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool tries to extract polygon footprint from a raster mask.
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
# TODO: merge with geom_raster_outline.py

import sys
from os.path import basename
from osgeo import ogr; ogr.UseExceptions() # pylint: disable=multiple-statements
from osgeo import osr; ogr.UseExceptions() # pylint: disable=multiple-statements
from osgeo import gdal; gdal.UseExceptions() # pylint: disable=multiple-statements
from img import ImageFileReader
from img.cli import error
from img_geom import OUTPUT_FORMATS, setSR, dumpGeom
from img_vectorize import vectorize

def usage():
    """ Print simple usage help. """
    print >>sys.stderr, (
        "USAGE: %s <input image> <value> [%s]" %
        (basename(sys.argv[0]), "|".join(OUTPUT_FORMATS))
    )


if __name__ == "__main__":
    ALLOWED_DTYPES = ('uint8', 'uint16', 'uint32', 'int8', 'int16', 'int32')
    FORMAT = "WKB"
    try:
        INPUT = sys.argv[1]
        VALUE = int(sys.argv[2])
        for arg in sys.argv[3:]:
            if arg in OUTPUT_FORMATS:
                FORMAT = arg # output format
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    # open the mask image
    IMG_MASK = ImageFileReader(INPUT)

    # check mask properties
    if IMG_MASK.size.z > 1:
        error("Multi-band masks are not supported!")
        sys.exit(1)

    if IMG_MASK.dtype not in ALLOWED_DTYPES:
        error("Unsupported mask data type '%s'!" % IMG_MASK.dtype)
        sys.exit(1)

    GEOCODING = IMG_MASK.geocoding
    if 'geotrn' not in GEOCODING:
        error("The mask must be rectified and geocoded!")
        sys.exit(1)

    # vectorize geometry, fix the spatial reference and print the output
    sys.stdout.write(dumpGeom(setSR(
        vectorize(IMG_MASK[0], lambda v: v == VALUE),
        osr.SpatialReference(GEOCODING['proj'])
    ), FORMAT))
