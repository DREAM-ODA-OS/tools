#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool creates empty geotiff/tiff based on another existing master image.  
#   The pixel size and geo-coding is copied from the master image. Number
#   of bands and datatype must be set by the user. 
#
#   Can be use as the start image for GDAL rasterization. 
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

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    exename = os.path.basename( sys.argv[0] ) 
    # block size 
    bsx , bsy = 256, 256 

    # default format options 

    FOPTS = ib.FormatOptions() 
    FOPTS["TILED"] = "YES"
    FOPTS["BLOCKXSIZE"] = "256"
    FOPTS["BLOCKYSIZE"] = "256"
    FOPTS["COMPRESS"] = "DEFLATE"

    try: 

        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        DTYPE  = sys.argv[3]
        NBAND  = int(sys.argv[4])

        #anything else treated as a format option
        for opt in sys.argv[5:] :
            FOPTS.setOption( opt )

    except IndexError : 

        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <master image> <output TIF> <pixel type> <n.bands>\n"%exename) 
        sys.stderr.write("EXAMPLE: %s input.tif output.tif uint8 3\n"%exename) 
        sys.exit(1) 

    # check the number of bands and pixel type 

    if DTYPE not in ib.DT2GDT.keys() : 
        sys.stderr.write("ERROR: Invalid pixel type! DTYPE=%s\n"%DTYPE) 
        sys.exit(1) 

    if NBAND < 1 : 
        sys.stderr.write("ERROR: Invalid band count! NBAND=%d \n"%NBAND) 
        sys.exit(1) 

    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # creation parameters 
    prm = { 
        'path' :   OUTPUT,
        'nrow' :   imi.sy,
        'ncol' :   imi.sx,
        'nband' :  NBAND,
        'dtype' :  DTYPE,
        'options' : FOPTS.getOptions(),
    } 

    #print prm 

    # geocoding 
    if imi.ds.GetProjection() : 
        prm['proj'] = imi.ds.GetProjection()
        prm['geotrn'] = imi.ds.GetGeoTransform()
    elif imi.ds.GetGCPProjection() : 
        prm['proj'] = imi.ds.GetGCPProjection()
        prm['gcps'] = imi.ds.GetGCPs()

    # open output image 
    imo = ib.createGeoTIFF( **prm ) 

    # DONE 
