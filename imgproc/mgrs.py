#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  NATO Military Grid Reference System (MGSS) conversion tools.
#
# NOTE: polar (USP-North, USP-South) coordinates are not handled
# TODO: implmenent handling of polar (USP-North, USP-South) coordinates
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
import re
from math import floor
import img_geom as ig
from osgeo import osr ; osr.UseExceptions()

# allowed zone overlap (40km)
ALLOWED_OVERLAP = 40000

# false northing used for south hemishere
FALSE_NORTHING_NORTH = 0
FALSE_NORTHING_SOUTH = 10000000

# false easting at central meridian
FALSE_EASTING = 500000

# wrap lattitudes in dg
MGRS_LAT_WRAP = (18.0887089, 36.1447181, 54.1481041, 72.0992225)

# bounds of the latitude UTM zones
BASE_NORTHING = (
    -8881586, -7988933, -7097015, -6206080, -5316301, -4427758, -3540436,
    -2654227, -1768936, -884298, 0, 884297, 1768935, 2654226, 3540435, 4427757,
    5316300, 6206079, 7097014, 7988932, 9328093
)

#number to character conversion (allowed zone characters)

N2C = "ABCDEFGHJKLMNPQRSTUVWXYZ"
NCN = 20
NCE = 24

#character to number conversion
C2N = dict((c, i) for i, c in enumerate(N2C))

#------------------------------------------------------------------------------
# regular expressions to match MGRS 100km square ID (non-polar)

# UTM zone match
_RE_UTMZ = r"(?P<utmz>0?[1-9]|[1-5][0-9]|60)"

# MGRS latitude zone
_RE_LATZ = r"(?P<latz>[CDEFGHJKLMNPQRSTUVWX])"

# MGRS 100 km square northing
_RE_N0 = r"(?P<n0>[ABCDEFGHJKLMNPQRSTUV])"

# MGRS 100 km square easting
_RE_E0 = r"(?P<e0>[ABCDEFGHJKLMNPQRSTUVWXYZ])"

# MGRS sub 100 km precision
_RE_SUBPREC = r"(?P<subprec>([0-9][0-9]){0,5})"

RE_MGRS = re.compile(
    r"^%s\s*%s\s*%s%s%s$" % (_RE_UTMZ, _RE_LATZ, _RE_E0, _RE_N0, _RE_SUBPREC),
    re.IGNORECASE
)

#------------------------------------------------------------------------------

PREC2STR = ("100km", "10km", "1km", "100m", "10m", "1m")
PREC2DST = (100000, 10000, 1000, 100, 10, 1)

#------------------------------------------------------------------------------

def getUTM2MGRSSqId(east, north, utmz, is_north=True, precision=0,
                    leading_zero=True):
    """
        For a given UTM coordinate return square ID!

            east       easting
            north      northing
            utmz       UTM zone number
            is_north   if False southern hemishpere false northig
                       is substracted from the northing value

            precision  precision level:
                        0 ... 100km (default)
                        1 ... 10km
                        2 ... 1km
                        3 ... 100m
                        4 ... 10m
                        5 ... 1m
            leading_zero  if True leading zero will be added to one digit zones
                          e.g., "01" instead of "1"
    """
    # check zone
    if (utmz < 1) or (utmz > 60):
        raise ValueError("Invalid UTM zone %s !" % utmz)

    # substract false northing and easting
    east -= FALSE_EASTING
    north -= FALSE_NORTHING_NORTH if is_north else FALSE_NORTHING_SOUTH

    # floor the easting and norting to meters
    east = int(floor(east))
    north = int(floor(north))

    # get the UTM lateral zone
    for idx, lat_band_border in enumerate(BASE_NORTHING[1:]):
        if north < lat_band_border:
            break
    utm_lat_zone = N2C[idx+2]

    # MGRS letter easting offset of the central meridian
    off_cmr = 4+((utmz-1)%3)*8

    # MGRS letter northing offset to equator
    off_eqt = ((utmz-1)%2)*5

    # 100 km square easting/northing coordinates
    e_tmp, n_tmp = int(floor(east*1e-5)), int(floor(north*1e-5))

    e_ref, n_ref = e_tmp*100000, n_tmp*100000

    # 100km square letter symbols
    cn100km = N2C[(n_tmp+off_eqt)%NCN]
    ce100km = N2C[(e_tmp+off_cmr)%NCE]

    # encode the sub 100km integer reminder

    e_str = ("%+5.5d"%(east-e_ref))[-5:]
    n_str = ("%+5.5d"%(north-n_ref))[-5:]

    prec_str = "".join(v for t in zip(e_str, n_str) for v in t)

    # zone string
    zstr = "%2.2d"%utmz if leading_zero else "%d"%utmz

    # return the MGRS location code
    return "%s%s%s%s%s" % (
        zstr, utm_lat_zone, ce100km, cn100km, prec_str[:precision*2]
    )

#------------------------------------------------------------------------------

class MGRS(object):
    """ Class representing an MGRS location.

        obj_mgrt = MGRS(<MGRS string>)
    """

    mgrs = property(lambda self: self.__mgrs, doc="MGRS grid reference")
    utmz = property(lambda self: self.__utmz, doc="UTM zone")
    utmlb = property(lambda self: self.__latz, doc="UTM latitude band")
    sqide = property(lambda self: self.__e0, doc="MGRS 100km square ID - easting")
    sqidn = property(lambda self: self.__n0, doc="MGRS 100km square ID - northing")
    precision = property(lambda self: self.__prec, doc="""precision:
                        0 ... 100km
                        1 ... 10km
                        2 ... 1km
                        3 ... 100m
                        4 ... 10m
                        5 ... 1m
        """)

    @property
    def epsg(self):
        "Get EPSG code of the UTM zone."
        if self.isNorthHemisphere():
            return 32600 + self.utmz
        else:
            return 32700 + self.utmz

    def __init__(self, sqid):
        """ Initialize class by a MGRS square ID """
        match = RE_MGRS.match(sqid) # parse MGRS square ID
        if match is None:
            raise ValueError("Invalid MGRS 100km Square ID!")
        prm = match.groupdict()
        self.__mgrs = sqid
        self.__utmz = int(prm['utmz'])
        self.__latz = prm['latz'].upper()
        self.__e0 = prm['e0'].upper()
        self.__n0 = prm['n0'].upper()
        self.__prec = len(prm['subprec'])/2
        self.__subprec = prm['subprec']
        # detect invalid zones
        if (self.utmlb == "X") and (self.utmz in (32, 34, 36)):
            raise ValueError("Invalid UTM Zone %d%s !"%(self.utmz, self.utmlb))
        self.__setEN() # set base easting and northing

    def __setEN(self):
        " calculate the base easting and northing values"
        # offset of the central meridian
        off_cmr = 4+((self.utmz-1)%3)*8
        # offset to equator
        off_eqt = ((self.utmz-1)%2)*5
        n0 = (C2N[self.sqidn] - off_eqt)*100000
        nb = 0
        # min. and max. northing for given UTM-zone + allowed overlap
        i = C2N[self.utmlb] - 2
        n_min = BASE_NORTHING[i] - n0 - ALLOWED_OVERLAP - 100000
        n_max = BASE_NORTHING[i+1] - n0 + ALLOWED_OVERLAP
        #TODO: find more elegant unwrapping algorithm
        while n_max < nb:
            nb -= 2000000
        while n_min > nb:
            nb += 2000000
        if n_max < nb: # the square is not within he UTM zone
            raise ValueError(
                "The 100x100km square does not match the UTM zone!"
            )
        #---------------------------------------------------
        # calculate the SW corner easting and northing
        # easting - 100km base
        e = (C2N[self.sqide] - off_cmr)*100000 + FALSE_EASTING
        # northing - 100km base
        n = (C2N[self.sqidn] - off_eqt)*100000 + nb + self.getFalseNorthing()
        # easting and northing - sub-100km base
        s = self.__subprec
        g = ((int(s[i]), int(s[i+1])) for i in xrange(0, len(s), 2))
        for i, (ve, vn) in enumerate(g):
            d = PREC2DST[i+1]
            e += ve * d
            n += vn * d
        # set the final values as properties
        self.__e, self.__n = (e, n)

    def zone2lat(self):
        "Get tuple of minimal and maximal latitude (WGS84)."
        lat0 = C2N[self.utmlb]*8 - 96
        if lat0 < -80:
            return (-90, -80)
        elif lat0 > +72:
            return (+84, +90)
        elif lat0 == 72:
            return (+72, +84)
        else:
            return (lat0, lat0+8)

    def zone2lon(self):
        "Get tuple of minimal and maximal longitude (WGS84)."
        lon0 = self.utmz*6 - 186
        tmp = (self.utmz, self.utmlb)
        # handle exceptions
        if tmp == (31, "V"):
            return (lon0, lon0+3)
        elif tmp == (31, "X"):
            return (lon0, lon0+9)
        elif tmp in ((32, "V"), (37, "X")):
            return (lon0-3, lon0+6)
        elif tmp in ((33, "X"), (35, "X")):
            return (lon0-3, lon0+9)
        else:
            return (lon0, lon0+6)

    def isNorthHemisphere(self):
        "Does the square lie the norther hemishere?"
        return C2N[self.utmlb] > 11

    def getFalseNorthing(self):
        "Get false northing base on the hemishere."
        if self.isNorthHemisphere():
            return FALSE_NORTHING_NORTH
        else:
            return FALSE_NORTHING_SOUTH

    def getCornerSW(self):
        """Get the UTM coordinates of the west-south square corner."""
        return (self.__e, self.__n)

    def getCornerNW(self):
        """Get the UTM coordinates of the west-north square corner."""
        return (self.__e, self.__n + PREC2DST[self.__prec])

    def getCornerSE(self):
        """Get the UTM coordinates of the west-south square corner."""
        return (self.__e + PREC2DST[self.__prec], self.__n)

    def getCornerNE(self):
        """Get the UTM coordinates of the west-north square corner."""
        d = PREC2DST[self.__prec]
        return (self.__e + d, self.__n + d)

    def __getSR(self):
        """ get spatial reference of the UTM zone """
        if self.isNorthHemisphere():
            return ig.OSR_UTM_N[self.utmz-1]
        else:
            return ig.OSR_UTM_S[self.utmz-1]

    def convertEN2LL(self, (e, n)):
        """Convert WGS84/UTM easting/northing to WGS84 longitude/latitude."""
        ct = osr.CoordinateTransformation(self.__getSR(), ig.OSR_WGS84)
        x, y, _ = ct.TransformPoint(float(e), float(n))
        return (x, y)

    def asPolygonWGS84(self, step=1.0e5):
        """Get outline in the WGS84 coordinates as an OGR polygon."""
        # get corner coordinates
        x0, y0 = self.getCornerSW()
        x1, y1 = self.getCornerNE()
        # outline polygon in UTM coordinates
        ol = ig.setSR(ig.getRectangle((x0, y0, x1, y1), step), self.__getSR())
        # transform to WGS84
        ol.TransformTo(ig.OSR_WGS84)
        # handle coordinates crossing the date-line
        if self.utmz < 2:
            t = ig.Transfomer(lambda p: (p[0] - 360.0*(p[0] > 0), p[1]))
            ol = ig.setSR(t(ol), p0.GetSpatialReference())
        elif self.utmz > 59:
            t = ig.Transfomer(lambda p: (p[0] + 360.0*(p[0] < 0), p[1]))
            ol = ig.setSR(t(ol), p0.GetSpatialReference())
        return ol

#    def asWKT(self, n = 1):
#        """Get square outline in WGS84 coordinates as WKT (corners only)."""
#        #_format = "%.6f %.6f"
#        _format = "%.3f %.3f"
#        coords = ( self.getCornerSW(), self.getCornerNW(),
#                    self.getCornerNE(), self.getCornerSE())
#
#        def _segment(c0, c1):
#            x0, y0 =  c0
#            dx = float(c1[0] - c0[0]) / n
#            dy = float(c1[1] - c0[1]) / n
#            ll = [self.convertEN2LL((x0+dx*i, y0+dy*i)) for i in xrange(n)]
#            return ll
#
#        cc = []
#        cc.extend(_segment(coords[0], coords[1]))
#        cc.extend(_segment(coords[1], coords[2]))
#        cc.extend(_segment(coords[2], coords[3]))
#        cc.extend(_segment(coords[3], coords[0]))
#        cc.append(cc[0])
#
#        s = []
#        ll = [self.convertEN2LL(c) for c in coords]
#        if (ll[0][0] > ll[3][0]) or (ll[1][0] > ll[2][0]):
#            cc0 = [(x-360*(x>0), y) for (x, y) in cc]
#            cc1 = [(x+360, y) for (x, y) in cc0]
#            #s.append("MULTIPOLYGON(")
#            s.append("((")
#            s.append(", ".join(_format%c for c in cc0))
#            s.append(")), ")
#            s.append("((")
#            s.append(", ".join(_format%c for c in cc1))
#            s.append(")), ")
#            #s.append(")")
#        else:
#            #s.append("POLYGON(")
#            s.append("((")
#            s.append(", ".join(_format%c for c in cc))
#            s.append(")), ")
#            #s.append(")")
#        return "".join(s)


    def __str__(self):
        """ Convert object to string. """
        utm = "%d%s" % (self.utmz, self.utmlb)
        def __corner(label, (e, n)):
            lat, lon = self.convertEN2LL((e, n))
            return "   - %s: %s %dmE %dmN (%+.6fdg %+.6fdg) "%(label, utm, e, n, lat, lon)
        utm_zone = "%d%s" % (self.utmz, self.utmlb)
        s = []
        s.append("Location: %s" % (self.mgrs))
        s.append(" - precision: %s"%(PREC2STR[self.precision]))
        s.append(" - UTM Zone: %s [EPSG:%d]" % (utm_zone, self.epsg))
        s.append("   - lon: from %+ddg to %+ddg"%self.zone2lon())
        s.append("   - lat: from %+ddg to %+ddg"%self.zone2lat())
        s.append(" - square 100km: %s%s" % (self.sqide, self.sqidn))
        s.append(__corner("Corner-SW", self.getCornerSW()))
        s.append(__corner("Corner-SE", self.getCornerSE()))
        s.append(__corner("Corner-NE", self.getCornerNE()))
        s.append(__corner("Corner-NW", self.getCornerNW()))
        return "\n".join(s)


#------------------------------------------------------------------------------
# CLI test

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "USAGE: %s <MGRS square ID>" % sys.argv[0]
        print "\n\t Convert MGRS square ID to UTM and WGS84 coordinates."
        sys.exit(1)

    # parse MGRS grid reference
    mgrs = MGRS(sys.argv[1])

    # generate MGRS grid reference from a location

    # get UTM coordinates of the centre of the square
    d = 0.5*PREC2DST[mgrs.precision]
    e, n = mgrs.getCornerSW(); e += d; n += d

    # get the the square ID
    sqid = getUTM2MGRSSqId(
        e, n, mgrs.utmz, mgrs.isNorthHemisphere(), mgrs.precision
    )

    print "-----------------------"
    print "CODE:    ", sqid
    print mgrs

