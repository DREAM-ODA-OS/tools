#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Simplify geometry
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
#from osgeo import gdal ; gdal.UseExceptions()

#------------------------------------------------------------------------------

def simplify_geometry(src_geom, gslen):
    """ Recursively simplify complex 2D geometry (linear-ring, polygon or
    multi-polygon).
    """
    # NOTE: The Geometry.GetGeometryType() method is not reliable.
    # To get the true geometry type always use string names returned
    # by Geometry.GetGeometryName() method.

    # -----------------------------------------------
    if src_geom.GetGeometryName() == "LINEARRING":

        # note simplification works on polygons only
        polygon = ogr.Geometry(ogr.wkbPolygon)
        polygon.AddGeometry(src_geom)
        geom_simplified = polygon.Simplify(gslen)

        rings = [] # list of simplified rings

        # parse the output and decompose it to linear rings
        if geom_simplified.IsEmpty():
            pass

        elif geom_simplified.GetGeometryName() == "POLYGON":
            rings.append(
                #clone to avoid segfaults
                geom_simplified.GetGeometryRef(0).Clone()
            )

        elif geom_simplified.GetGeometryName() == "MULTIPOLYGON":
            rings.extend(
                #clone to avoid segfaults
                geom_simplified.GetGeometryRef(i).GetGeometryRef(0).Clone()
                for i in xrange(geom_simplified.GetGeometryCount())
            )

        else:
            raise ValueError(
                "Unexpected simplified geometry type %s! "
                "Expected POLYGON or MULTIPOLYGON." %
                geom_simplified.GetGeometryName()
            )

        return rings

    # -----------------------------------------------
    elif src_geom.GetGeometryName() == "POLYGON":

        polygon = ogr.Geometry(ogr.wkbPolygon)

        for i in xrange(src_geom.GetGeometryCount()):
            ring = src_geom.GetGeometryRef(i)
            if ring.GetGeometryName() != "LINEARRING":
                raise ValueError(
                    "Unexpected geometry type %s! Expected LINEARRING." %
                    geom_simplified.GetGeometryName()
                )

            simplified_rings = simplify_geometry(ring, gslen)

            if i == 0: # first ring is the outer ring
                if len(simplified_rings) > 1:
                    raise ValueError(
                        "Polygon outer ring split into multiple polygons!"
                    )

                elif len(simplified_rings) == 0:
                    # outer ring got removed -> return empty multi-polygon
                    return ogr.Geometry(ogr.wkbMultiPolygon)

                else:
                    polygon.AddGeometry(simplified_rings[0])

            else: # inner rings
                for ring in simplified_rings:
                    polygon.AddGeometry(ring)

        return polygon

    # -----------------------------------------------
    elif src_geom.GetGeometryName() == "MULTIPOLYGON":
        multi_polygon = ogr.Geometry(ogr.wkbMultiPolygon)
        for i in xrange(src_geom.GetGeometryCount()):
            polygon = src_geom.GetGeometryRef(i)
            if polygon.GetGeometryName() != "POLYGON":
                raise ValueError(
                    "Unexpected geometry type %s! Expected POLYGON." %
                    geom_simplified.GetGeometryName()
                )

            # simplify polygon
            simplified_polygon = simplify_geometry(polygon, gslen)

            # if non-empty add to multi-polygon
            if not simplified_polygon.IsEmpty():
                multi_polygon.AddGeometry(simplified_polygon)

        return multi_polygon

    # -----------------------------------------------
    else:
        # any other geometry is passed trough unchanged
        return src_geom

#------------------------------------------------------------------------------

if __name__ == "__main__":

    # TODO: to improve CLI

    EXENAME = os.path.basename(sys.argv[0])

    DEBUG = False
    FORMAT = "WKB"

    try:

        INPUT = sys.argv[1]
        GSLEN = float(sys.argv[2]) # geometry simplification parameter
        NP = 2
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg == "DEBUG":
                    DEBUG = True # dump debuging output

    except IndexError:

        sys.stderr.write("ERROR: Not enough input arguments!\n")
        sys.stderr.write("\nSimplify geometry and dump new geometry to stdout\n")
        sys.stderr.write("by default in WKB format.\n\n")
        sys.stderr.write("USAGE: %s <WKB|WKB> <prm.simpl.> [WKT|WKB] [DEBUG]\n"%EXENAME)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # import

    # open input geometry file
    fin = sys.stdin if INPUT == "-" else open(INPUT)

    # read the data
    try:
        geom = ig.parseGeom(fin.read(), DEBUG)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # simplify geometry

    geom = ig.setSR(simplify_geometry(geom, GSLEN), geom.GetSpatialReference())

    #--------------------------------------------------------------------------
    # export

    try:

        sys.stdout.write(ig.dumpGeom(geom, FORMAT))

    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)
