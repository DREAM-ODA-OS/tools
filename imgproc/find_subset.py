#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  This tool takes the mask claculated by the extract_mask tool
#  and calculates the offset ans size of the image subset
#  without the no-data borders and containing the original
#  valid data.
#
#  As output the command writes 4 comma separated integers values:
#
#   <col. offset>, <row offset>, <number of cols.>, <number of rows>
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
import os.path
import img_block as ib
import numpy as np

def getDataExtent( bi, nodata ) :

    #--------------------------------------------------------------------------
    # X coordinate

    xmin = bi.ux
    xmax = bi.ox

    # find X minimum
    for i in xrange( bi.sx ) :

        # get count of valid pixels
        s = np.sum( bi.data[:,i,0] != nodata )

        if ( s > 0 ) :
            xmin = bi.ox + i
            break

    # find X maximum
    for i in xrange( bi.sx-1 , xmin-bi.ox-1 , -1 ) :

        # get count of valid pixels
        s = np.sum( bi.data[:,i,0] != nodata )

        if ( s > 0 ) :
            xmax = bi.ox + i + 1
            break

    if xmax < xmin : xmax = xmin + 1
    if xmax > bi.ux : xmax = bi.ux

    #--------------------------------------------------------------------------

    if xmin >= bi.ux : # no data found - the image is empty
        return ib.ImgExtent((0,0,imi.sz),(bi.ox,bi.oy,0))

    #--------------------------------------------------------------------------
    # Y coordinate

    ymin = bi.uy
    ymax = bi.oy

    # find Y minimum
    for i in xrange( bi.sy ) :

        # get count of valid pixels
        s = np.sum( bi.data[i,:,0] != nodata )

        if ( s > 0 ) :
            ymin = bi.oy + i
            break

    # find Y maximum
    for i in xrange( bi.sy-1 , ymin-bi.oy-1 , -1 ) :

        # get count of valid pixels
        s = np.sum( bi.data[i,:,0] != nodata )

        if ( s > 0 ) :
            ymax = bi.oy + i + 1
            break

    if ymax < ymin : ymax = ymin + 1
    if ymax > bi.uy : ymax = bi.uy

    #--------------------------------------------------------------------------

    return ib.ImgExtent((xmax-xmin,ymax-ymin,imi.sz),(xmin,ymin,0))


#------------------------------------------------------------------------------

if __name__ == "__main__" :

    # TODO: block processing 
    # TODO: to improve CLI

    exename = os.path.basename( sys.argv[0] )
    # block size
    bsx , bsy = 256, 256

    try:

        INPUT = sys.argv[1]
        NODATA = sys.argv[2]

    except IndexError :

        sys.stderr.write("Not enough input arguments!\n")
        sys.stderr.write("USAGE: %s <input image mask> <no data value>\n"%exename)
        sys.stderr.write("EXAMPLE: %s mask.tif 0\n"%exename)
        sys.exit(1)

    # open input image
    imi = ib.ImgFileIn( INPUT )

    # convert no-data values to the image's data type
    NODATA = np.dtype(imi.dtype).type( NODATA )

    # load the mask as single image
    bi = ib.ImgBlock( 'uint8' , (imi.sx,imi.sy,1) )

    # load image block
    imi.read( bi )

    #--------------------------------------------------------------------------
    # extract subset

    subset = getDataExtent( bi, NODATA )

    # print the subset

    print  "%d,%d,%d,%d"%( subset.ox, subset.oy, subset.sx, subset.sy )
