#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  Guess resolution of the warped image using the GDAL method.
#  (lenght from the top-left to bottom-right edge)
#
# Project: Image Processing Tools
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

import math as m
import sys
import os.path
import img_block as ib
import img_geom as ig

def dist((x0, x1), (y0, y1)):
    dx, dy = (x1 - x0), (y1 - y0)
    return m.sqrt(dx*dx + dy*dy)

if __name__ == "__main__":
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False

    try:
        INPUT = sys.argv[1]
        PROJECTION = sys.argv[2]

        for arg in sys.argv[3:]:
            if arg == "DEBUG":
                DEBUG = True
            else:
                sys.stderr.write("Invalid parameter '%s'!\n"%(arg))
                sys.exit(1)

        if len(sys.argv) > 4 and sys.argv[4] == "DEBUG":
            DEBUG = True

    except IndexError:
        sys.stderr.write("Not enough input arguments!\n")
        sys.stderr.write("USAGE: %s <img> <srs>\n"%EXENAME)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # open input image
    imi = ib.ImgFileIn(INPUT)

    # geocoding
    if imi.ds.GetProjection():
        gtm = ig.GTMTransform(imi.ds.GetGeoTransform())
        ctr = ig.CTransform(ig.parseSR(imi.ds.GetProjection()), ig.parseSR(PROJECTION))

        x_pix, y_pix = [0, imi.sx], [0, imi.sy]
        x_src, y_src = gtm(x_pix, y_pix)
        x_dst, y_dst = ctr(x_src, y_src)

    elif imi.ds.GetGCPProjection():
        sys.stderr.write("Support for GCP encoded imagery not supported!")

    l_pix = dist(x_pix, y_pix)
    #l_src = dist(x_src, y_src)
    l_dst = dist(x_dst, y_dst)

    #print l_src / l_pix
    print l_dst / l_pix
