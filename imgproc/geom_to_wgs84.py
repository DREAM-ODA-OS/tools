#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Coordinate transformation.
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
import traceback
import os.path
import img_geom as ig
from osgeo import ogr ; ogr.UseExceptions()
#from osgeo import osr ; ogr.UseExceptions()
#from osgeo import gdal ; gdal.UseExceptions()

WGS84_SR = ig.parseSR("EPSG:4326")

def usage():
    sys.stderr.write("\nConvert the input geometry to the WGS84 coordinates\n")
    sys.stderr.write("including the north/south pole handling for polar \n")
    sys.stderr.write("projections and the date-line wraparround for geometries\n")
    sys.stderr.write("crossing the date-line.\n")
    sys.stderr.write("The result is dumped as a new geometry to stdout\n")
    sys.stderr.write("by default in WKB format.\n")
    sys.stderr.write("USAGE: %s <WKB|WKB> [WKT|WKB] [DEBUG]\n")

if __name__ == "__main__":
    # TODO: to improve CLI
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False
    FORMAT = "WKB"

    try:
        INPUT = sys.argv[1]
        NP = 2
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg == "DEBUG":
                    DEBUG = True # dump debuging output

    except IndexError:
        sys.stderr.write("ERROR: %s: Not enough input arguments!\n"%EXENAME)
        usage()
        sys.exit(1)

    except Exception, e:
        sys.stderr.write("ERROR: %s: %s\n"%(EXENAME, e))
        usage()
        sys.exit(1)

    #--------------------------------------------------------------------------
    # import

    # open input geometry file
    fin = sys.stdin if INPUT == "-" else open(INPUT)

    # read the data
    try:
        geom = ig.parseGeom(fin.read(), DEBUG)
    except Exception as e:
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, e)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # project geometry

    SOURCE_SR = geom.GetSpatialReference()

    # assing the default spatial reference (WGS84)
    if SOURCE_SR is None:
        geom.AssignSpatialReference(WGS84_SR)

    # process the coordinates
    geom = ig.mapToWGS84(geom)

    #--------------------------------------------------------------------------
    # export

    try:
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))
    except Exception as e:
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, e)
        sys.exit(1)
