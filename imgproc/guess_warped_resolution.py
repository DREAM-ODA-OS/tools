#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  Guess resolution of the warped image using the same method
#  as the one used by GDAL warp (length from the top-left to bottom-right edge).
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

import sys
from os.path import basename
from img_geom  import GTMTransform, CTransform, parseSR
from img import Point2, ImageFileReader
from img.cli import error

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, "USAGE: %s <img> <target-srs>\n" % exename


def get_resolution_rectified(size, geotrn, sr_in, sr_out):
    """ Calculate the output resolution. """
    # prepare transformations objects
    pixel2sr_in = GTMTransform(geotrn)
    sr_in2sr_out = CTransform(sr_in, sr_out)
    # transform coordinates
    x_pix, y_pix = [0, size.x], [0, size.y]
    x_src, y_src = pixel2sr_in(x_pix, y_pix)
    x_dst, y_dst = sr_in2sr_out(x_src, y_src)
    # evaluate distances between the corners in the pixels and output map
    # coordinate systems
    l_pix = (Point2(x_pix[1], y_pix[1]) - Point2(x_pix[0], y_pix[0])).length()
    l_dst = (Point2(x_dst[1], y_dst[1]) - Point2(x_dst[0], y_dst[0])).length()
    # target resolution
    return l_dst / l_pix


if __name__ == "__main__":
    try:
        INPUT = sys.argv[1]
        PROJECTION = sys.argv[2]
    except IndexError:
        error("Not enough input arguments!\n")
        usage()
        sys.exit(1)

    # open input image
    IMG_IN = ImageFileReader(INPUT)
    SR_IN = IMG_IN.spatial_reference
    SR_OUT = parseSR(PROJECTION)
    GEO_PRM = IMG_IN.geocoding

    if SR_IN:
        if 'geotrn' in GEO_PRM:
            print get_resolution_rectified(
                IMG_IN.size, GEO_PRM['geotrn'], SR_IN, SR_OUT
            )
        else:
            error("The GCP geocoded imagery is not supported!")
            sys.exit(1)
    else:
        error("The image is not geocoded!")
        sys.exit(1)
