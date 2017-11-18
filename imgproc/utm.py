#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  Universal Transversal Mercator (UTM) tools.
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
import sys
import img_geom as ig

STEP = 1.0

# FIXME
#def clipByUTMZone(geom, utmz, south=True, north=True, buffer=0.0):
#    """ Clip geometry in WGS84 to the extent of the UTM zone extended
#        by the given buffer.
#    """
#    zone = getUTMZoneAsGeom(utmz, south, north, buffer)
#    return zone

def getUTMZoneAsGeom(utmz, south=True, north=True, buffer=0.0, phase=0):
    """ Get UTM zone as GDAL/OGR polygon (WGS84)
    Parameters:
        utmz    [integer] UTM zone (1-60)
        south   [boolean] set True to include the southern hemisphere
        north   [boolean] set True to include the northern hemisphere
        buffer  [float]   buffer in km
        phase   [integer] set longitude offset to (phase*360) degrees
    """
    if (utmz < 1) or (utmz > 60):
        raise ValueError("Invalid UTM zone!")
    if not (south or north):
        raise ValueError("No hemisphere selected!")
    offset = phase * 360.0
    # basic shape bounds

    # latitude bounds
    lat_min = -80.0 if south else 0.0
    lat_max = +84.0 if north else 0.0
    if north and utmz in (32, 34, 36):
        lat_max = +72.0

    # longitude bounds
    lon_min = (utmz - 1)*6.0 - 180.0
    lon_max = lon_min + 6.0

    # create regular shape
    geom = ig.getRectangle((lon_min, lat_min, lon_max, lat_max), STEP)

    # handle northern irregularities
    if north and utmz in (31, 32, 33, 35, 37):
        if utmz == 31:
            geom = geom.Union(
             ig.getRectangle((lon_min, 72.0, lon_max+3.0, 84.0), STEP)
            )
            geom = geom.Difference(
                ig.getRectangle((lon_min+3.0, 56.0, lon_max, 64.0), STEP)
            )
        elif utmz == 32:
            geom = geom.Union(
                ig.getRectangle((lon_min-3.0, 56.0, lon_max, 64.0), STEP)
            )
        elif utmz in (33, 35):
            geom = geom.Union(
                ig.getRectangle((lon_min-3.0, 72.0, lon_max+3.0, 84.0), STEP)
            )
        elif utmz == 37:
            geom = geom.Union(
                ig.getRectangle((lon_min-3.0, 72.0, lon_max, 84.0), STEP)
            )

    # assing the spatial reference
    geom.AssignSpatialReference(ig.OSR_WGS84)

    if buffer != 0.0: # buffer requested
        # transform to UTM coordinates
        geom.TransformTo(ig.OSR_UTM_N[utmz-1])
        # enlarege by given buffer distance
        geom = ig.setSR(geom.Buffer(buffer*1e3), geom.GetSpatialReference())
        # convert back to WGS84
        geom.TransformTo(ig.OSR_WGS84)
        #NOTE: transformation wraps the coordinates arround date-line
        if utmz < 2:
            trn = ig.Transfomer(lambda p: (p[0] - 360.0*(p[0] > 0), p[1]))
            geom = ig.setSR(trn(geom), geom.GetSpatialReference())
        elif utmz > 59:
            trn = ig.Transfomer(lambda p: (p[0] + 360.0*(p[0] < 0), p[1]))
            geom = ig.setSR(trn(geom), geom.GetSpatialReference())

    if phase != 0:
        geom = ig.setSR(ig.shiftGeom(geom, (offset, 0.0)), ig.OSR_WGS84)

    return geom


if __name__ == "__main__":
    # print UTM zone extended by overlap buffer
    # parse UTM zone
    UTMZ = 31 if len(sys.argv) < 2 else int(sys.argv[1])
    # parse buffer
    BUFFER = 0.0 if len(sys.argv) < 3 else float(sys.argv[2])
    GEOM = getUTMZoneAsGeom(UTMZ, True, True, BUFFER, 0)
    GEOM = ig.wrapArroundWGS84(GEOM)
    print GEOM.ExportToWkt()
