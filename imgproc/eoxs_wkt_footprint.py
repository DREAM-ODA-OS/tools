#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Extract footprint from a referenceable dataset using EOxServer's reftools
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
from os.path import basename
from osgeo import gdal
from img_geom import OUTPUT_FORMATS, OSR_WGS84, setSR, parseGeom, dumpGeom
from img.cli import error

# NOTE: Make sure the eoxserver is in your Python path.
from eoxserver.processing.gdal import reftools as rt

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <input image> [%s]" % (exename, "|".join(OUTPUT_FORMATS))
    )


if __name__ == "__main__":
    DEBUG = False
    FORMAT = "WKB"
    try:
        INPUT = sys.argv[1]
        for arg in sys.argv[2:]:
            if arg in OUTPUT_FORMATS:
                FORMAT = arg # output format
            elif arg == "DEBUG":
                DEBUG = True # dump debugging output
    except IndexError:
        error("Not enough input arguments!\n")
        usage()
        sys.exit(1)

    # get the referenceable dataset outline
    #NOTE: It is assumed, that the outline is not wrapped around the date-line.
    ds = gdal.Open(INPUT)
    prm = rt.suggest_transformer(ds)
    geom = setSR(parseGeom(rt.get_footprint_wkt(ds, **prm)), OSR_WGS84)

    # print geometry
    sys.stdout.write(dumpGeom(geom, FORMAT))
