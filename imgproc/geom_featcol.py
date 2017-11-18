#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Extract geometry from as feature collection
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
# pylint: disable=invalid-name

import sys
import os.path
import img_geom as ig
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements


if __name__ == "__main__":
    # TODO: to improve CLI
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False
    FORMAT = "WKB"
    SELECT = []

    try:
        INPUT = sys.argv[1]
        NP = 2
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg == "DEBUG":
                    DEBUG = True # dump debugging output
                else:
                    try:
                        arg = int(arg) # if possible convert value to integer
                    except:
                        pass # or keep string otherwise
                    SELECT.append(arg)

    except IndexError:
        print >>sys.stderr, "ERROR: Not enough input arguments!\n"
        print >>sys.stderr, "Extract geometry from a feature collection,"
        print >>sys.stderr, "OGR GML/Fature collection or shape file."
        print >>sys.stderr, "The non-simplified geometry is dumped to stdout,"
        print >>sys.stderr, "by default in WKB format.\n"
        print >>sys.stderr, (
            "USAGE: %s <input image> [<layer>] [<feature>] [WKT|WKB*] "
            "[AND|EQL*] [DEBUG]" % EXENAME
        )
        sys.exit(1)

    # by default export the first layer and first feature
    if len(SELECT) < 1:
        SELECT.append(0)
    if len(SELECT) < 2:
        SELECT.append(0)

    # extract geometry
    dataset = ogr.Open(INPUT)
    layer = dataset.GetLayer(SELECT[0])
    feature = layer.GetFeature(SELECT[1])
    geom = feature.GetGeometryRef()

    # export geometry
    try:
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)
