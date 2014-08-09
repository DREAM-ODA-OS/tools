#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Print geometry extent
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
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions()
#from osgeo import osr; ogr.UseExceptions()
#from osgeo import gdal; gdal.UseExceptions()

def dump_winding(geom, level=0, inner_loop=False):
    gname = geom.GetGeometryName()
    if gname == "LINEARRING":
        area = 0.0
        for i in xrange(geom.GetPointCount()-1):
            x0, y0 = geom.GetPoint_2D(i)
            x1, y1 = geom.GetPoint_2D(i+1)
            area += x0*y1 - x1*y0
        if area < 0:
            result = "CW"
        elif area > 0:
            result = "CCW"
        elif area == 0:
            result = "0"
        else:
            result = "INVALID"
        print "%s%s(%s) %s"%("  "*level, gname, ("O", "I")[inner_loop], result)

    elif gname == "POLYGON":
        print "  "*level, gname
        inner_loop = False
        for i in xrange(geom.GetGeometryCount()):
            dump_winding(geom.GetGeometryRef(i), level+1, inner_loop)
            inner_loop = True

    elif gname in ("MULTIPOLYGON", "GEOMETRYCOLLECTION"):
        print "  "*level, gname
        for i in xrange(geom.GetGeometryCount()):
            dump_winding(geom.GetGeometryRef(i), level+1)


if __name__ == "__main__":
    # TODO: to improve CLI
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False

    try:
        INPUT = sys.argv[1]
        NP = 1
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg == "DEBUG":
                    DEBUG = True # dump debuging output

    except IndexError:
        sys.stderr.write("ERROR: Not enough input arguments!\n")
        sys.stderr.write("\nPrint linear ring orientation.\n")
        sys.stderr.write("USAGE: %s <WKT|WKB> [DEBUG]\n"%EXENAME)
        sys.exit(1)

    try:
        # load geometry
        fin = sys.stdin if INPUT == "-" else open(INPUT)
        geom = ig.parseGeom(fin.read(), DEBUG)

        dump_winding(geom)

    except Exception as e:
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, e)
        sys.exit(1)
