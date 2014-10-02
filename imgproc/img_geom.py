#-------------------------------------------------------------------------------
#
#  Vector Geometry Manipulations
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

import re
import sys
import math as m
import numpy as np
from collections import Iterable
from osgeo import ogr ; ogr.UseExceptions()
from osgeo import osr ; osr.UseExceptions()

_gerexURL = re.compile(r"^http://www.opengis.net/def/crs/epsg/\d+\.?\d*/(\d+)$", re.IGNORECASE)
_gerexURN = re.compile(r"^urn:ogc:def:crs:epsg:\d*\.?\d*:(\d+)$", re.IGNORECASE)
_gerexShortCode = re.compile(r"^epsg:(\d+)$", re.IGNORECASE)

#-------------------------------------------------------------------------------
# coordinate transformation
RO = ['readonly']
WO = ['writeonly', 'allocate']

class CTransform(object):
    """GDAL/SRS coordinate transformation."""

    def __init__(self, sr_src, sr_dst):
        self._ct = osr.CoordinateTransformation(sr_src, sr_dst)

    def __call__(self, xarr, yarr):
        if hasattr(np, 'nditer') and isinstance(xarr, np.ndarray) and isinstance(yarr, np.ndarray):
            # NumPy array
            if xarr.shape != yarr.shape:
                raise ValueError("Array shape mismatch!")
            itr = np.nditer([xarr, yarr, None, None], [], [RO, RO, WO, WO])
            for x, y, u, v in itr:
                u[...], v[...], _ = self._ct.TransformPoint(float(x), float(y))
            return itr.operands[2], itr.operands[3]
        elif isinstance(xarr, Iterable) and isinstance(xarr, Iterable):
            # generic iterables + NumPy prior 'np.nditer'
            u, v = [], []
            for x, y in zip(xarr, yarr):
                _u, _v, _ = self._ct.TransformPoint(float(x), float(y))
                u.append(_u)
                v.append(_v)
            return u, v
        else: # assuming scalar values
            return self._ct.TransformPoint(float(xarr), float(yarr))[0:2]


class GTMTransform(object):
    """GDAL Geo-Transformation Matrix based (affine) transformation."""

    def __init__(self, gtm):
        self._gtm = gtm

    def __transform(self, col, row):
        gtm = self._gtm
        x = gtm[0] + gtm[1]*col + gtm[2]*row
        y = gtm[3] + gtm[4]*col + gtm[5]*row
        return x, y

    def __call__(self, xarr, yarr):
        if hasattr(np, 'nditer') and isinstance(xarr, np.ndarray) and isinstance(yarr, np.ndarray):
            # NumPy array
            if xarr.shape != yarr.shape:
                raise ValueError("Array shape mismatch!")
            itr = np.nditer([xarr, yarr, None, None], [], [RO, RO, WO, WO])
            for x, y, u, v in itr:
                u[...], v[...] = self.__transform(float(x), float(y))
            return itr.operands[2], itr.operands[3]
        elif isinstance(xarr, Iterable) and isinstance(xarr, Iterable):
            # generic iterables + NumPy prior 'np.nditer'
            u, v = [], []
            for x, y in zip(xarr, yarr):
                _u, _v = self.__transform(float(x), float(y))
                u.append(_u)
                v.append(_v)
            return u, v
        else: # assuming scalar values
            return self.__transform(float(xarr), float(yarr))


#-------------------------------------------------------------------------------
# spatial references

# the most common spatial references

def createSRFromEPSG(epsg):
    """ Create OSR Spatial Reference from EPSG number code"""
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(epsg)
    return sr

OSR_WGS84 = createSRFromEPSG(4326)
OSR_USP_N = createSRFromEPSG(32661)
OSR_USP_N = createSRFromEPSG(32761)

OSR_UTM_N = tuple(createSRFromEPSG(32601+i) for i in xrange(60))
OSR_UTM_S = tuple(createSRFromEPSG(32701+i) for i in xrange(60))


def setSR(geom, sr):
    """Assing spatial reference to a geometry and return it."""
    geom.AssignSpatialReference(sr)
    return geom

def parseSR(srs, debug=False):
    if debug:
        print >>sys.stderr, "SRS: ", srs
    for regex in (_gerexShortCode, _gerexURN, _gerexURL):
        match = regex.match(srs)
        if match is not None:
            return createSRFromEPSG(int(match.group(1)))
    if srs[:7] in ("PROJCS[", "GEOGCS["):
        return osr.SpatialReference(srs)
    if srs in (None, "", "NONE"):
        return None
    raise ValueError("Failed to parse the spatial reference! SRS='%s'"%(srs))


def dumpSR(sr, delimiter="", debug=False):
    # check whether geometry has a spatial reference
    if sr is not None:
        an, ac = (sr.GetAuthorityName(None), sr.GetAuthorityCode(None))
        if an == "EPSG" and ac > 0:
            out = "%s:%s%s"%(an, ac, delimiter)
        else:
            out = "%s%s"%(sr.ExportToWkt(), delimiter)
    else:
        out = ""
    return out

#-------------------------------------------------------------------------------
# File I/O subroutines

def parseGeom(buf, debug=False):
    """ parse geometry from a source buffer """
    # parse prefix
    if buf.startswith("EPSG:") or buf.startswith("PROJCS["):
        srs, _, buf = buf.partition(';')
        sr = parseSR(srs)
    else:
        sr = None

    # create the geometry
    for loader in (ogr.CreateGeometryFromWkb,
                    ogr.CreateGeometryFromWkt,
                    ogr.CreateGeometryFromGML,
                    ogr.CreateGeometryFromJson):
        try:
            if debug:
                print >>sys.stderr, "LOADER: ", loader,
            geom = loader(buf)
        except Exception as e:
            if debug:
                print >>sys.stderr, e
            continue

        if debug:
            print >>sys.stderr, "OK"
        break

    else:
        raise ValueError("ERROR: Failed to parse the source geometry!")

    if sr is not None:
        geom.AssignSpatialReference(sr)

    return geom


#OUTPUT_FORMATS = ("WKB", "WKT", "JSON", "GML", "KML")
OUTPUT_FORMATS = ("WKB", "WKT", "JSON", "KML")

def dumpGeom(geom, format="WKB", debug=False):
    """ dump geometry to a buffer possible formats are: WKB(*)|WKT|JSON|GML|KML """
    # dump SRS prefix
    prefix = dumpSR(geom.GetSpatialReference(), ";", debug)

    if format == "WKB":
        data = geom.ExportToWkb()
        if prefix:
            data = "%s%s"%(prefix, data)
    elif format == "WKT":
        data = "%s%s\n"%(prefix, geom.ExportToWkt())
    elif format == "JSON":
        data = geom.ExportToJson()
# the GML needs to be verified
#    elif format == "GML":
#        data = geom.ExportToGML()
    elif format == "KML":
        data = geom.ExportToKML()
    else:
        raise ValueError("Invalid format specification! FORMAT='%s'"%(format))

    return data

#-------------------------------------------------------------------------------

def wrapArroundDateLine(geom, (xmin, ymin, xmax, ymax), nstep=200):
    """
        wrap (split) geometry arround the date-line

        nstep controls the split border segmentation (dy = (ymax-ymin)/nstep)
    """
    xdif = xmax - xmin
    step = (ymax - ymin) / nstep

    x0, x1, _, _ = geom.GetEnvelope()

    p_start = int(m.floor((x0-xmin)/xdif))
    p_stop = int(m.ceil((x1-xmin)/xdif))

    # skip geometries falling to a regular domain
    if (p_start == 0) and (p_stop == 1):
        return geom

    # wrap-arround
    lgeom = []
    for p in xrange(p_start, p_stop):
        offset = p*xdif
        clip = getRectangle((xmin+offset, ymin, xmax+offset, ymax), step)
        tmp = geom.Intersection(clip)
        tmp = shiftGeom(tmp, (-offset, 0.0))
        lgeom.extend(extractPolygons(tmp))

    return groupPolygons(lgeom)


def wrapArroundWGS84(geom, nstep=200):
    """
        logitude wrap-arround of geometry in WGS84

        nstep controls the split border segmentation (dy = (ymax-ymin)/nstep)

        eqivalent to:
            wrapArroundDateLine(geom, (-180., -90., +180., +90.), nstep)
    """
    return wrapArroundDateLine(geom, (-180., -90., +180., +90.), nstep)

#-------------------------------------------------------------------------------

def mapToWGS84(geom):

    def between(v, (v0, v1)):
        if v0 <= v1:
            return (v0 <= v)and(v1 >= v)
        else: #v1 > v0
            return (v1 <= v)and(v0 >= v)

    def extent_contains(x0, y0):
        return ((x0_min <= x0)and(x0_max >= x0)
             and(y0_min <= y0)and(y0_max >= y0))

    def generate_polar_section(north, east):
        eps = 1e-9
        y00 = 89 # max. opposite pole lat.distnace from the equator
        x0 = 0 if east else -180
        y0 = (-y00) if north else (+y00)
        y1 = (90-eps) if north else (eps-90)

        lr = ogr.Geometry(type=ogr.wkbLinearRing)
        for i in xrange(31):
            lr.AddPoint_2D(i*6+x0, y0)
        lr.AddPoint_2D(180+x0, y1)
        lr.AddPoint_2D(x0, y1)
        lr.AddPoint_2D(x0, y0)
        p = ogr.Geometry(type=ogr.wkbPolygon)
        p.AddGeometry(lr)
        p.AssignSpatialReference(OSR_WGS84)
        return p

    def fix_dateline(geom, east):
        """fix the +/-180dg ambiguity of the date-line nodes"""
        def _dlflip_east((x, y, _)): # date-line point flipper
            return (x+360.0 if x < -179.0 else x, y)
        def _dlflip_west((x, y, _)): # date-line point flipper
            return (x-360.0 if x > (+179.0) else x, y)
        return Transfomer(_dlflip_east if east else _dlflip_west)(geom)

    def transform_polar(north):
        # generate polygon spliting the polar geometry to halves
        s1 = generate_polar_section(north, east=True)
        s2 = generate_polar_section(north, east=False)

        # transform coordinates
        s1.Transform(ct_rev)
        s2.Transform(ct_rev)

        # split the polar geometry to halves
        g1 = geom.Intersection(s1)
        g2 = geom.Intersection(s2)

        # transform halves to the target projection
        g1.Transform(ct_fwd)
        g2.Transform(ct_fwd)

        # fix the dateline ambiguity
        g1 = fix_dateline(g1, east=True)
        g2 = fix_dateline(g2, east=False)

        # return the unified geometry
        return g1.Union(g2)

    #--------------------------------------------------------------------------

    sr_src = geom.GetSpatialReference()
    sr_dst = OSR_WGS84

    # coordinate transformation objects
    ct_fwd = osr.CoordinateTransformation(sr_src, sr_dst)
    ct_rev = osr.CoordinateTransformation(sr_dst, sr_src)

    # envelope and centroid in the source coordinates
    x0_min, x0_max, y0_min, y0_max = geom.GetEnvelope()

    # centroid
    x0_cnt, y0_cnt = 0.5*(x0_min+x0_max), 0.5*(y0_min+y0_max)

    # try to get coordinates of the north and south pole in the source CRS
    try:
        xy0_np = ct_rev.TransformPoint(0.0, 90.0)[:2]
    except RuntimeError:
        xy0_np = None

    try:
        xy0_sp = ct_rev.TransformPoint(0.0, -90.0)[:2]
    except RuntimeError:
        xy0_sp = None

    # case #1 - extent contains the north pole
    if xy0_np and extent_contains(*xy0_np):
        return setSR(transform_polar(north=True), OSR_WGS84)

    # case #2 - extent contains the south pole
    # check whether the extent contains the south pole
    elif xy0_sp and extent_contains(*xy0_sp):
        return setSR(transform_polar(north=False), OSR_WGS84)

    # case #3 proceed with the date-line handling

    # perform transformation
    geom.Transform(ct_fwd)

    # get extent and centroid in the target coordinates
    x1_min, _, _ = ct_fwd.TransformPoint(x0_min, y0_cnt)
    x1_max, _, _ = ct_fwd.TransformPoint(x0_max, y0_cnt)
    x1_cnt, _, _ = ct_fwd.TransformPoint(x0_cnt, y0_cnt)

    # fix the wild easting wrap-arround
    if not between(x1_cnt, (x1_min, x1_max)):
        if x1_max < x1_min: # axis orientation preserved
            x_cnt, x_min, x_max = x1_cnt, x1_min, x1_max
        else: # (x1_min < x1_max) # flipped axis orientation
            x_cnt, x_min, x_max = x1_cnt, x1_max, x1_min

        # point unwrapping fuctions
        if x_cnt < x_max: # EAST to WEST
            def _dlflip(p):
                return (p[0]-360*(p[0] > x_max), p[1])
        elif x_cnt > x_min: # WEST to EAST
            def _dlflip(p):
                return (p[0]+360*(p[0] < x_min), p[1])

        geom = setSR(Transfomer(_dlflip)(geom), OSR_WGS84)

    # perform proper wrapparround
    return setSR(wrapArroundDateLine(geom, (-180, -90, 180, 90), 1), OSR_WGS84)

#-------------------------------------------------------------------------------

def groupPolygons(plist):
    """ group polygons to a multi-polygon """
    mp = ogr.Geometry(ogr.wkbMultiPolygon)
    for p in plist:
        mp.AddGeometry(p)
    return mp


def ungroupMultiPolygon(mpol):
    """ un-group multi-polygon to a list of multi-polygons """
    return [mpol.GetGeometryRef(i) for i in xrange(mpol.GetGeometryCount())]


def extractPolygons(geom):
    if geom.GetGeometryName() == "GEOMETRYCOLLECTION":
        l = []
        for i in xrange(geom.GetGeometryCount()):
            l.extend(extractPolygons(geom.GetGeometryRef(i)))
        return l
    elif geom.GetGeometryName() == "MULTIPOLYGON":
        return ungroupMultiPolygon(geom)
    elif geom.GetGeometryName() == "POLYGON":
        return [geom]
    else:
        return []


def getRectangle((x_min, y_min, x_max, y_max), step=1.0):
    """ Create rectangle polygon with the edges broken to smaller
        line segments. The size of the lenght line segments is approx.
        the value of the step parameter
    """
    n_x = max(1, int(m.ceil((max(x_min, x_max)-min(x_min, x_max))/float(step))))
    n_y = max(1, int(m.ceil((max(y_min, y_max)-min(y_min, y_max))/float(step))))

    lx = []
    ly = []

    # generate polygon
    lx.append(np.linspace(x_min, x_max, n_x, False))
    ly.append(np.ones(n_x)*y_min)
    lx.append(np.ones(n_y)*x_max)
    ly.append(np.linspace(y_min, y_max, n_y, False))
    lx.append(np.linspace(x_max, x_min, n_x, False))
    ly.append(np.ones(n_x)*y_max)
    lx.append(np.ones(n_y)*x_min)
    ly.append(np.linspace(y_max, y_min, n_y, False))

    # close ring
    lx.append(np.array([x_min]))
    ly.append(np.array([y_min]))

    # concatenate arrays
    x = np.concatenate(lx)
    y = np.concatenate(ly)

    # convert to polygon
    r = ogr.Geometry(ogr.wkbLinearRing)

    for xx, yy in zip(x, y):
        r.AddPoint_2D(xx, yy)

    p = ogr.Geometry(ogr.wkbPolygon)
    p.AddGeometry(r)
    return p


def shiftGeom(g, (dx, dy)):
    """ shift geometry by a given offset """
    def _shift(p, (dx, dy)):
        return (p[0]+dx, p[1]+dy)
    t = Transfomer(_shift)
    return t(g, (dx, dy))

#------------------------------------------------------------------------------

class Transfomer(object):

    def __init__(self, f):
        self.__f = f

    def __call__(self, g0, *prm, **kw):
        return self._geometry(g0, *prm, **kw)

    def _geometry(self, g0, *prm, **kw):
        #print g0.GetGeometryName(), g0.GetGeometryType()
        if g0.GetGeometryName() == "MULTIPOLYGON":
            return self._multi_polygon(g0, *prm, **kw)

        elif g0.GetGeometryName() == "POLYGON":
            return self._polygon(g0, *prm, **kw)

        elif g0.GetGeometryName() == "LINEARRING":
            return self._linear_ring(g0, *prm, **kw)

        else:
            return None

    def _linear_ring(self, r0, *prm, **kw):
        #print r0.GetGeometryName(), r0.GetGeometryType()
        if r0.GetGeometryName() != "LINEARRING":
            return None
        r1 = ogr.Geometry(ogr.wkbLinearRing)
        for i in xrange(r0.GetPointCount()):
            rv = (self.__f)(r0.GetPoint(i), *prm, **kw)
            if rv is not None:
                r1.AddPoint_2D(*rv)
        return r1

    def _polygon(self, p0, *prm, **kw):
        #print p0.GetGeometryName(), p0.GetGeometryType()
        if p0.GetGeometryName() != "POLYGON":
            return None
        p1 = ogr.Geometry(ogr.wkbPolygon)
        for i in xrange(p0.GetGeometryCount()):
            rv = self._linear_ring(p0.GetGeometryRef(i), *prm, **kw)
            if rv is not None:
                p1.AddGeometry(rv)
        return p1

    def _multi_polygon(self, m0, *prm, **kw):
        #print m0.GetGeometryName(), m0.GetGeometryType()
        if m0.GetGeometryName() != "MULTIPOLYGON":
            return None
        m1 = ogr.Geometry(ogr.wkbMultiPolygon)
        for i in xrange(m0.GetGeometryCount()):
            rv = self._polygon(m0.GetGeometryRef(i), *prm, **kw)
            if rv is not None:
                m1.AddGeometry(rv)
        return m1

