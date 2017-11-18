#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Extract extent of a raster image as a rectange polygon.
#
# Author: Martin Paces <martin.paces@eox.at>
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
#pylint: disable=invalid-name, wrong-import-position

import sys
import os.path
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements
from osgeo import osr; ogr.UseExceptions() #pylint: disable=multiple-statements
from osgeo import gdal; gdal.UseExceptions() #pylint: disable=multiple-statements
from img import ImageFileReader
import img_geom as ig

if __name__ == "__main__":
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False
    FORMAT = "WKB"
    AND = False

    try:
        INPUT = sys.argv[1]
        NP = 1
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg == "DEBUG":
                    DEBUG = True # dump debuging output
    except IndexError:
        print >>sys.stderr, "ERROR: Not enough input arguments!"
        print >>sys.stderr, "\nExtract image extent as a rectange polygon."
        print >>sys.stderr, "The unsipmified geometry is dumped to stdout,"
        print >>sys.stderr, "by default in WKB format."
        print >>sys.stderr
        print >>sys.stderr, "USAGE: %s <input image> [DEBUG]"%EXENAME
        sys.exit(1)

    #--------------------------------------------------------------------------

    # open input image
    imi = ImageFileReader(INPUT)
    geocoding = imi.geocoding
    size_x, size_y = imi.size.x, imi.size.y

    if 'geotrn' in geocoding:
        # get the transformation matrix
        x0, dxx, dxy, y0, dyx, dyy = geocoding['geotrn']
        sr = osr.SpatialReference(geocoding['proj'])
    else:
        # operate in image coordinate space
        x0, dxx, dxy, y0, dyx, dyy = 0.0, 1.0, 0.0, 0.0, 0.0, 1.0
        sr = None

    # calculate the corner coordinates
    r = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in [(0, 0), (size_x, 0), (size_x, size_y), (0, size_y)]:
        r.AddPoint_2D(x0 + dxx*x + dxy*y, y0 + dyx*x + dyy*y)
    r.CloseRings()

    # create polygon
    geom = ogr.Geometry(ogr.wkbPolygon)
    geom.AddGeometry(r)

    # assign spatial reference
    geom.AssignSpatialReference(sr)

    #--------------------------------------------------------------------------
    # export

    try:
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)
