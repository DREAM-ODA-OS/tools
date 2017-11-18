#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  Suggest splitting of the geometry to smaller rectangular blocks
#
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
#pylint: disable=wrong-import-position,invalid-name

import sys
from math import ceil, floor
from os.path import basename
from osgeo import ogr; ogr.UseExceptions() # pylint: disable=multiple-statements
import img_geom as ig

# bounds of well known coordinate systems

DEFAULT_BOUNDS = (float('-inf'), float('-inf'), float('inf'), float('inf'))
KNOWN_BOUNDS = {
    "EPSG:4326": (-180., -90., +180., +90.),
}

def separate(geometry):
    """ Separate polygons with non-overlapping envelopes. """

    def overlap(envelope0, envelope1):
        """ check if envelopes overlap """
        return (
            (envelope0[0] <= envelope1[1]) and (envelope0[1] >= envelope1[0]) and
            (envelope0[2] <= envelope1[3]) and (envelope0[3] >= envelope1[2])
        )

    if geometry.GetGeometryName() != 'MULTIPOLYGON':
        return [geometry]

    groups = []
    geometries = ig.ungroupMultiPolygon(geometry)
    envelopes = [item.GetEnvelope() for item in geometries]
    idx_src = set(i for i in xrange(len(geometries)))

    while idx_src:
        idx = idx_src.pop()
        for item in groups: # find
            if idx in item:
                group = item
                groups.remove(item)
                break
        else:
            group = set()
            group.add(idx)

        for idy in idx_src:
            if overlap(envelopes[idx], envelopes[idy]):
                group.add(idy)
        groups.append(group)


    final_geometries = []
    for group in groups:
        if len(group) == 1:
            final_geometries.append(geometries[group.pop()].Clone())
        else:
            final_geometries.append(ig.setSR(
                ig.groupPolygons([geometries[i].Clone() for i in group]),
                geometry.GetSpatialReference()
            ))

    return final_geometries


def split(geometry, (dx_max, dy_max), (rx, ry), (bx0, by0, bx1, by1)):
    """ Cut geometry to smaller blocks. """
    #pylint: disable=invalid-name

    def _get_sizes(v0, v1, dv_max, rv, bv0, bv1):
        if rv > 0:
            dv_max *= rv
        if rv > 0:
            vr0 = vr1 = 0.5*(rv*ceil((v1-v0)/rv) - (v1-v0))
            if bv1 < (v1 + vr1):
                v1 = bv1
                vr0 = rv*ceil((v1-v0)/rv) - (v1-v0)
                vr1 = 0
            if bv0 > (v0 - vr0):
                v0 = bv0
                vr0 = 0
                vr1 = rv*ceil((v1-v0)/rv) - (v1-v0)
            v0 -= vr0
            v1 += vr1
        nv = int(ceil((v1 - v0) / dv_max))
        dv = (v1 - v0) / nv
        return v0, v1, dv, nv

    def _round(v0, v1, v_ref, rv):
        if rv > 0:
            v0 = v_ref + rv*floor((v0 - v_ref)/rv)
            v1 = v_ref + rv*ceil((v1 - v_ref)/rv)
        return v0, v1

    x0, x1, y0, y1 = geometry.GetEnvelope()
    x0, x1, dx, nx = _get_sizes(x0, x1, dx_max, rx, bx0, bx1)
    y0, y1, dy, ny = _get_sizes(y0, y1, dy_max, ry, by0, by1)

    for ix in xrange(nx):
        xx0 = x0 + ix*dx
        xx1 = xx0 + dx
        for iy in xrange(ny):
            yy0 = y0 + iy*dy
            yy1 = yy0 + dy
            gg = geometry.Intersection(ig.getRectangle((xx0, yy0, xx1, yy1)))
            if gg.IsEmpty():
                continue
            xxx0, xxx1, yyy0, yyy1 = gg.GetEnvelope()
            xxx0, xxx1 = _round(xxx0, xxx1, xx0, rx)
            yyy0, yyy1 = _round(yyy0, yyy1, yy0, ry)
            yield xxx0, yyy0, xxx1, yyy1


if __name__ == "__main__":
    EXENAME = basename(sys.argv[0])
    BUFFER = 0
    DEBUG = False
    USE_STDIN = False
    RES_X = None
    RES_Y = None

    try:
        INPUT = sys.argv[1]
        USE_STDIN = INPUT == "-"
        MAX_X_SIZE = float(sys.argv[2])
        MAX_Y_SIZE = float(sys.argv[3])

        for arg in sys.argv[4:]:
            if arg == "DEBUG":
                DEBUG = True
            elif RES_X is None:
                RES_X = abs(float(arg))
            elif RES_Y is None:
                RES_Y = abs(float(arg))
            else:
                sys.stderr.write("Invalid parameter '%s'!\n"%(arg))
                sys.exit(1)

        if RES_X is None:
            RES_X = 0
        if RES_Y is None:
            RES_Y = RES_X

    except IndexError:
        print >>sys.stderr, "Not enough input arguments!"
        print >>sys.stderr, (
            "USAGE: %s <WKT footprint> <max_x_size> <max_y_size> "
            "[<res_x> <res_y>]" % EXENAME
        )
        sys.exit(1)

    if MAX_X_SIZE <= 0 or MAX_Y_SIZE <= 0:
        sys.stderr.write("Invalid max.size (%s,%s)!\n"%(MAX_X_SIZE, MAX_Y_SIZE))
        sys.exit(1)

    # maximum rectangle size (either size or pixel size when resolution set)
    max_size = (MAX_X_SIZE, MAX_Y_SIZE)

    # pixel resolution (optional, set to 0 if not used)
    res = (RES_X, RES_Y)


    # open and read the input geometry file
    fin = sys.stdin if INPUT == "-" else open(INPUT)
    try:
        geom = ig.parseGeom(fin.read(), DEBUG)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)

    # checking presence of the mandatory spatial reference
    sr = geom.GetSpatialReference()
    if sr is None:
        print >>sys.stderr, "ERROR: %s: The geometry has no projection!" % EXENAME
        sys.exit(1)

    # projection bounds
    bounds = KNOWN_BOUNDS.get(ig.dumpSR(sr), DEFAULT_BOUNDS)

    # split geometry to clusters with non-overlapping envelope
    # and cut them to smaller blocks
    for geom in separate(geom):
        for rect in split(geom, max_size, res, bounds):
            print "%.16g %.16g %.16g %.16g" % rect
