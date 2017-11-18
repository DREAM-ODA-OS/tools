#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  change winding (clock-wise / counter-clock-wise) of linear rings
#
# Author: Martin Paces <martin.paces@eox.at>
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
# pylint: disable=invalid-name

import sys
import os.path
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements


def force_winding(geometry, is_cw, level=0, inner_loop=False):
    """ For given Geometry change winding of the coordinate loops."""
    # pylint: disable=invalid-name
    geometry_name = geometry.GetGeometryName()
    if geometry_name == "LINEARRING":
        if inner_loop: # reversed ordering for inner loop
            is_cw = not is_cw

        xy = [geometry.GetPoint_2D(0)]
        area = 0.0
        for idx in xrange(1, geometry.GetPointCount()):
            x0, y0 = xy[-1]
            x1, y1 = geometry.GetPoint_2D(idx)
            xy.append((x1, y1))
            area += x0*y1 - x1*y0

        if (is_cw and area > 0) or (not is_cw and area < 0):
            # change orientations (point's order)
            output_geometry = ogr.Geometry(ogr.wkbLinearRing)
            for x, y in reversed(xy):
                output_geometry.AddPoint_2D(x, y)

        else:
            # nothing is to be changed
            output_geometry = geometry.clone()

    elif geometry_name == "POLYGON":
        output_geometry = ogr.Geometry(ogr.wkbPolygon)
        inner_loop = False
        for idx in xrange(geometry.GetGeometryCount()):
            output_geometry.AddGeometry(force_winding(
                geometry.GetGeometryRef(idx), is_cw, level+1, inner_loop
            ))
            inner_loop = True

    elif geometry_name == "MULTIPOLYGON":
        output_geometry = ogr.Geometry(ogr.wkbMultiPolygon)
        for idx in xrange(geometry.GetGeometryCount()):
            output_geometry.AddGeometry(force_winding(
                geometry.GetGeometryRef(idx), is_cw, level+1
            ))

    elif geometry_name == "GEOMETRYCOLLECTION":
        output_geometry = ogr.Geometry(ogr.wkbGeometryCollection)
        for idx in xrange(geometry.GetGeometryCount()):
            output_geometry.AddGeometry(force_winding(
                geometry.GetGeometryRef(idx), is_cw, level+1
            ))

    else:
        output_geometry = geometry.Clone()

    return output_geometry


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
        print >>sys.stderr, "ERROR: Not enough input arguments!"
        print >>sys.stderr, "\nForce linear ring orientation."
        print >>sys.stderr, "USAGE: %s <WKT|WKB> CW|CCW [WKT|WKB][DEBUG]" % EXENAME
        sys.exit(1)

    try:
        fin = sys.stdin if INPUT == "-" else open(INPUT)
        geom = ig.parseGeom(fin.read(), DEBUG)
        geom = ig.setSR(force_winding(geom, IS_CW), geom.GetSpatialReference())
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))

    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, exc)
        sys.exit(1)
