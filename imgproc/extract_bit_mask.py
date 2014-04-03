#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool extracts a single bit-mask plane (as a 'byte' mask) from
#   a bit-flasg image. 
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
import img_util as iu
import numpy as np 

#------------------------------------------------------------------------------
# mask extractor 
def extractBitMask( bi, bmask, bg=0x00, fg=0xFF ) :

    if ( bi.sz != 1 ) : 
        raise RuntimeError("Invalid band count! sz=%d ",bi.sz) 

    # output block 
    bo = ib.ImgBlock('uint8',size=(bi.sx,bi.sy,1), offset=(bi.ox,bi.oy,0))

    tmp = ( 0 == np.bitwise_and( bi.data[:,:,0] , bmask ) ) 

    bo.data[:,:,0] = tmp*bg + np.logical_not(tmp)*fg  

    return bo 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    def error( message ) :
        print >>sys.stderr, "ERROR: %s: %s\n" %( EXENAME, message ) 

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
        BMASK  = sys.argv[3]
        MASKBG = 0x00 
        MASKFG = 0xFF 

        #anything else treated as a format option
        for opt in sys.argv[4:] :
            FOPTS.setOption( opt )

    except IndexError : 
        error("Not enough input arguments!") 
        sys.stderr.write("USAGE: %s <input image> <output mask/TIF> <bit-wise and mask>\n"%EXENAME) 
        sys.stderr.write("EXAMPLE: %s input.tif mask.tif 128\n"%EXENAME) 
        sys.exit(1) 


    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    if imi.sz > 1 : 
        error("ERROR: Multiband images not supported!") 
        sys.exit(1) 

    if imi.dtype not in ('uint8','uint16','uint32','int8','int16','int32') : 
        error("ERROR: Unsupported image data type '%s'!"%imi.dtype) 
        sys.exit(1) 

    # convert bit mask values to the image's data type 
    BMASK = map( np.dtype(imi.dtype).type, BMASK ) 

    # creation parameters 
    prm = { 
        'path' :   OUTPUT,
        'nrow' :   imi.sy,
        'ncol' :   imi.sx,
        'nband' :  1,
        'dtype' :  'uint8',
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

    # initialize progress printer 
    prg = iu.Progress( (1+(imi.sy-1)/bsy)*(1+(imi.sx-1)/bsx) ) 

    print "Extracting bit flag as a mask ..."

    for ty in xrange( 1 + (imi.sy-1)/bsy ) :
        for tx in xrange( 1 + (imi.sx-1)/bsx ) :

            # extent of the tile 
            ex_t = imi & ib.ImgExtent( (bsx,bsy,imi.sz) , (tx*bsx,ty*bsy,0) )

            # allocate input image block 
            bi = ib.ImgBlock( imi.dtype , extent = ex_t ) 

            # load image block 
            imi.read( bi ) 

            # calculate the mask 
            bo = extractBitMask( bi, BMASK , MASKBG, MASKFG ) 

            # save image block 
            imo.write( bo ) 

            # print progress 
            sys.stdout.write(prg.istr(1)) ; sys.stdout.flush() 

    sys.stdout.write("\n") ; sys.stdout.flush() 
