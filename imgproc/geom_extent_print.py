#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Print geometry extent (envelope).
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
# pylint: disable=invalid-name

import sys
import os.path
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements


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
        print >>sys.stderr, "ERROR: Not enough input arguments!"
        print >>sys.stderr, "\nDump geometry extent:"
        print >>sys.stderr, "    <x_min>, <y_min>, <x_max>, <y_max>"
        print >>sys.stderr, " and its spatial reference."
        print >>sys.stderr, "USAGE: %s <WKT|WKB> [DEBUG]" % EXENAME
        sys.exit(1)

    try:
        # load geometry
        fin = sys.stdin if INPUT == "-" else open(INPUT)
        geom = ig.parseGeom(fin.read(), DEBUG)

        sref = geom.GetSpatialReference()
        envelope = geom.GetEnvelope()

        print "%s%.6g,%.6g,%.6g,%.6g" % (
            ig.dumpSR(sref, ";"), envelope[0], envelope[2], envelope[1],
            envelope[3]
        )

    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)
