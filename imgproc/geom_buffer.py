#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   buffer geometry
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
import os.path
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements


if __name__ == "__main__":

    # TODO: to improve CLI

    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False
    FORMAT = "WKB"

    try:
        INPUT = sys.argv[1]
        BFLEN = float(sys.argv[2]) # geometry simplification parameter
        NP = 2
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg == "DEBUG":
                    DEBUG = True # dump debugging output

    except IndexError:
        sys.stderr.write("ERROR: Not enough input arguments!\n")
        sys.stderr.write("\nBuffer geometry and dump new geometry to stdout\n")
        sys.stderr.write("by default in WKB format.\n\n")
        sys.stderr.write("USAGE: %s <WKB|WKB> <prm.sgm.> [WKT|WKB] [DEBUG]\n"%EXENAME)
        sys.exit(1)

    # open input geometry file
    fin = sys.stdin if INPUT == "-" else open(INPUT)

    # read the data
    try:
        geom = ig.parseGeom(fin.read(), DEBUG)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)

    # create the buffer
    geom = ig.setSR(geom.Buffer(BFLEN), geom.GetSpatialReference())

    # export
    try:
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)
