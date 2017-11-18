#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  get list of MGRS 100km tiles matching the images
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
# pylint: disable=wrong-import-position, redefined-outer-name

import sys
from math import floor, ceil
from os.path import basename
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements
import img_geom as ig
import utm
import mgrs


def chop2mgrs(geom, utmz):
    """ chop geometry to MGRS 100km squares """
    # pylint: disable=invalid-name

    # convert footprint to utm coordinates
    geom.TransformTo(ig.OSR_UTM_N[utmz-1])

    # get the bounds
    x0, x1, y0, y1 = geom.GetEnvelope()

    i0, i1 = int(floor(x0*1e-5)), int(ceil(x1*1e-5))
    j0, j1 = int(floor(y0*1e-5)), int(ceil(y1*1e-5))

    sqids = []
    for j in xrange(j0, j1):
        for i in xrange(i0, i1):
            x, y = i*1e5+5e4, j*1e5+5e4
            clip = ig.getRectangle((x - 5e4, y - 5e4, x + 5e4, y + 5e4), 2e5)
            if not geom.Intersect(clip):
                continue
            mgrs_sqid = mgrs.getUTM2MGRSSqId(x, y, utmz, True, 0)
            sqids.append(mgrs_sqid)

    return sqids


if __name__ == "__main__":
    EXENAME = basename(sys.argv[0])
    BUFFER = 0
    DEBUG = False
    USE_STDIN = False

    try:
        INPUT = sys.argv[1]
        USE_STDIN = (INPUT == "-")

        if len(sys.argv) > 2 and sys.argv[2] == "DEBUG":
            DEBUG = True

    except IndexError:
        sys.stderr.write("Not enough input arguments!\n")
        sys.stderr.write("USAGE: %s <WKT footprint>\n"%EXENAME)
        sys.exit(1)

    # open input geometry file
    fin = sys.stdin if INPUT == "-" else open(INPUT)

    # read the data
    try:
        geom = ig.parseGeom(fin.read(), DEBUG)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)

    # checking spatial reference
    # NOTE: The geometry is expected to be projected in WGS84.
    sref = geom.GetSpatialReference()
    if (sref is not None) and (ig.dumpSR(sref) != "EPSG:4326"):
        print >>sys.stderr, (
            "ERROR: %s: The input geometry must be projected"\
            " to WGS84 geographic coordinate system!" % EXENAME
        )
        sys.exit(1)

    # wrap-around the geometry to fit the WGS84 bounds
    geom = ig.wrapArroundWGS84(geom)

    # get intersections with the UTM zones
    #l = []
    for zone in xrange(1, 61):

        # get the UTM zone polygon with buffer
        zg = utm.getUTMZoneAsGeom(zone, True, True, BUFFER)

        # wrap it around
        zg = ig.setSR(ig.wrapArroundWGS84(zg), zg.GetSpatialReference())

        # check intersection
        if not geom.Intersect(zg):
            continue

        # get the footprint subset intersecting the UTM zone
        geom_utm = ig.setSR(zg.Intersection(geom), zg.GetSpatialReference())

        if DEBUG:
            print >>sys.stderr, geom_utm

        # get list of MGRS squares
        lsq = chop2mgrs(geom_utm, zone)

        for sqid in lsq:
            s = mgrs.MGRS(sqid)
            x0, y0 = s.getCornerSW()
            x1, y1 = s.getCornerNE()
            print "%s\tEPSG:%d\t%d,%d,%d,%d" % (sqid, s.epsg, x0, y0, x1, y1)

        #debug print
        if DEBUG:
            # convert list of square ID to polygons
            mp = ig.groupPolygons(mgrs.MGRS(s).asPolygonWGS84() for s in lsq)
            print >>sys.stderr, mp
