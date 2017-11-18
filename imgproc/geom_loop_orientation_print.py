#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Print geometry extent
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
# pylint: disable=invalid-name

import sys
import os.path
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements


def dump_winding(geometry, level=0, inner_loop=False):
    """ For a given Geometry print winding of the linear rings."""
    # pylint: disable=invalid-name

    geometry_name = geometry.GetGeometryName()
    if geometry_name == "LINEARRING":
        area = 0.0
        for i in xrange(geometry.GetPointCount()-1):
            x0, y0 = geometry.GetPoint_2D(i)
            x1, y1 = geometry.GetPoint_2D(i+1)
            area += x0*y1 - x1*y0
        if area < 0:
            result = "CW"
        elif area > 0:
            result = "CCW"
        elif area == 0:
            result = "0"
        else:
            result = "INVALID"
        print "%s%s(%s) %s" % (
            "  "*level, geometry_name, ("O", "I")[inner_loop], result
        )

    elif geometry_name == "POLYGON":
        print "  "*level, geometry_name
        inner_loop = False
        for i in xrange(geometry.GetGeometryCount()):
            dump_winding(geometry.GetGeometryRef(i), level+1, inner_loop)
            inner_loop = True

    elif geometry_name in ("MULTIPOLYGON", "GEOMETRYCOLLECTION"):
        print "  "*level, geometry_name
        for i in xrange(geometry.GetGeometryCount()):
            dump_winding(geometry.GetGeometryRef(i), level+1)


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
        print >>sys.stderr, "ERROR: Not enough input arguments!"
        print >>sys.stderr, "\nPrint linear ring orientation."
        print >>sys.stderr, "USAGE: %s <WKT|WKB> [DEBUG]" % EXENAME
        sys.exit(1)

    try:
        # load geometry
        fin = sys.stdin if INPUT == "-" else open(INPUT)
        geom = ig.parseGeom(fin.read(), DEBUG)

        dump_winding(geom)

    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, exc)
        sys.exit(1)
