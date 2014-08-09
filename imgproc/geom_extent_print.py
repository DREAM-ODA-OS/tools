#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Print geometry extent (envelope).
#
# Project: Image Processing Tools
# Authors: Martin Paces <martin.paces@eox.at>
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

import sys
import os.path
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions()
#from osgeo import osr; ogr.UseExceptions()
#from osgeo import gdal; gdal.UseExceptions()

if __name__ == "__main__":
    # TODO: to improve CLI
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False

    try:
        INPUT = sys.argv[1]
        NP = 1
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg == "DEBUG":
                    DEBUG = True # dump debuging output

    except IndexError:
        sys.stderr.write("ERROR: Not enough input arguments!\n")
        sys.stderr.write("\nDump geometry extent:\n")
        sys.stderr.write("    <x_min>, <y_min>, <x_max>, <y_max>\n")
        sys.stderr.write(" and its spatial reference.\n")
        sys.stderr.write("USAGE: %s <WKT|WKB> [DEBUG]\n"%EXENAME)
        sys.exit(1)

    try:
        # load geometry
        fin = sys.stdin if INPUT == "-" else open(INPUT)
        geom = ig.parseGeom(fin.read(), DEBUG)

        sr = geom.GetSpatialReference()
        env = geom.GetEnvelope()

        print "%s%.6g,%.6g,%.6g,%.6g"%(
            ig.dumpSR(sr, ";"), env[0], env[2], env[1], env[3]
        )

    except Exception as e:
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, e)
        sys.exit(1)

