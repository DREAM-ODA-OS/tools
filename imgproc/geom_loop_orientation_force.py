#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   orientation (clock-wise / counter-clock-wise) of the linear rings
#
# Project: Image Processing Tools
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions()
#from osgeo import osr; ogr.UseExceptions()
#from osgeo import gdal; gdal.UseExceptions()

def force_winding(geom, is_cw, level=0, inner_loop=False):

    gname = geom.GetGeometryName()
    if gname == "LINEARRING":
        if inner_loop: # reversed ordering for innner loop
            is_cw = not is_cw

        xy = [geom.GetPoint_2D(0)]
        area = 0.0
        for i in xrange(geom.GetPointCount()-1):
            x0, y0 = geom.GetPoint_2D(i)
            x1, y1 = geom.GetPoint_2D(i+1)
            xy.append((x1, y1))
            area += x0*y1 - x1*y0

        if (is_cw and area > 0) or (not is_cw and area < 0):
            # change orientations (point's order)
            gout = ogr.Geometry(ogr.wkbLinearRing)
            for x, y in reversed(xy):
                gout.AddPoint_2D(x, y)

        else:
            # nothig's to be changed
            gout = geom.clone()

    elif gname == "POLYGON":
        gout = ogr.Geometry(ogr.wkbPolygon)
        inner_loop = False
        for i in xrange(geom.GetGeometryCount()):
            gout.AddGeometry(force_winding(geom.GetGeometryRef(i), is_cw, level+1, inner_loop))
            inner_loop = True

    elif gname == "MULTIPOLYGON":
        gout = ogr.Geometry(ogr.wkbMultiPolygon)
        for i in xrange(geom.GetGeometryCount()):
            gout.AddGeometry(force_winding(geom.GetGeometryRef(i), is_cw, level+1))

    elif gname == "GEOMETRYCOLLECTION":
        gout = ogr.Geometry(ogr.wkbGeometryCollection)
        for i in xrange(geom.GetGeometryCount()):
            gout.AddGeometry(force_winding(geom.GetGeometryRef(i), is_cw, level+1))

    else:
        gout = geom.Clone()

    return gout


if __name__ == "__main__":
    # TODO: to improve CLI
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False
    IS_CW = False
    FORMAT = "WKB"

    try:
        INPUT = sys.argv[1]
        ORIENT = sys.argv[2]
        NP = 2
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg == "DEBUG":
                    DEBUG = True # dump debuging output
                elif arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg == "CW":
                    ORIENT = "CW"
                elif arg == "CCW":
                    ORIENT = "CCW"
        IS_CW = ORIENT == "CW"

    except IndexError:
        sys.stderr.write("ERROR: Not enough input arguments!\n")
        sys.stderr.write("\nForce linear ring orientation.\n")
        sys.stderr.write("USAGE: %s <WKT|WKB> CW|CCW [WKT|WKB][DEBUG]\n"%EXENAME)
        sys.exit(1)

    try:
        fin = sys.stdin if INPUT == "-" else open(INPUT)
        geom = ig.parseGeom(fin.read(), DEBUG)
        geom = ig.setSR(force_winding(geom, IS_CW), geom.GetSpatialReference())
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))

    except Exception as e:
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, e)
        sys.exit(1)

