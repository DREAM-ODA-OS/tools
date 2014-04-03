#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool clips data to mask. Based on the mask value, the code 
#   performs folloging pixel operations:
#       mask no-data value (0x00) -> sets pixel to a given no-data value
#       mask data value (0xFF)    -> copies pixel from the original image 
#
#   This tool extracts subset of the image specified by the row/column 
#   offset of the upper-left corenr and row/column size of extracted 
#   block. The tool takes care about preserving the geo-metadata.
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

def clipToMask( bi , bm , mask_fg , nodata ) : 
    
    if bi.non_equal_2d( bm ) : 
        raise RuntimeError( "Equal blocks' extents required!" ) 

    # prepare list of no-data values 
    if len( nodata ) == 1 : 
        nodata = [ nodata[0] for i in xrange(bi.data.shape[2]) ] 

    fg = ( bm.data[:,:,0] == mask_fg ) 
    bg = ( bm.data[:,:,0] != mask_fg ) 

    for i in xrange( bi.data.shape[2] ) : 
        bi.data[:,:,i] = bg * nodata[i] + fg * bi.data[:,:,i] 

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
        MASK  = sys.argv[2]
        OUTPUT = sys.argv[3]
        NODATA = sys.argv[4].split(",")
        MASKBG = 0x00 
        MASKFG = 0xFF 

        #anything else treated as a format option
        for opt in sys.argv[5:] :
            FOPTS.setOption( opt )

    except IndexError : 

        error("Not enough input arguments!") 
        sys.stderr.write("USAGE: %s <input image> <mask> <output TIF> <no data value or list>\n"%EXENAME) 
        sys.stderr.write("EXAMPLE: %s input.tif mask.tif output.tif 255,255,255\n"%EXENAME) 
        sys.stderr.write("EXAMPLE: %s input.tif mask.tif output.tif 0\n"%EXENAME) 
        sys.exit(1) 

    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # convert no-data values to the image's data type 
    NODATA = map( np.dtype(imi.dtype).type, NODATA ) 

    if len(NODATA) < imi.sz : 
        NODATA=[ NODATA[0] for i in xrange(imi.sz) ]

    # open input mask
    imm = ib.ImgFileIn( MASK ) 

    # check mask properties  

    if imm.sz > 1 : 
        error("Multiband mask not supported!")
        sys.exit(1) 

    if imm.dtype != 'uint8' : 
        error("Unsupported mask data type '%s'!"%imi.dtype)
        sys.exit(1) 

    if not imm.equal_2d( imi ) : 
        error("Input mask and image must have the same pixel"
                " size! image: (%d x %d)  mask: (%d x %d)" %( 
                            imi.sy , imi.sx, imm.sy , imm.sx ) )  
        sys.exit(1) 

    # creation parameters 
    prm = { 
        'path' :   OUTPUT,
        'nrow' :   imi.sy,
        'ncol' :   imi.sx,
        'nband' :  imi.sz,
        'dtype' :  imi.dtype,
        'options' : FOPTS.getOptions(),
        'nodata' : NODATA,
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

    #--------------------------------------------------------------------------

    # initialize progress printer 
    prg = iu.Progress( (1+(imi.sy-1)/bsy)*(1+(imi.sx-1)/bsx) ) 

    print "Clipping image by a mask ..."

    for ty in xrange( 1 + (imi.sy-1)/bsy ) :
        for tx in xrange( 1 + (imi.sx-1)/bsx ) :

            # extent of the tile 
            ex_ti = imi & ib.ImgExtent( (bsx,bsy,imi.sz) , (tx*bsx,ty*bsy,0) )
            ex_tm = imi & ib.ImgExtent( (bsx,bsy,1) , (tx*bsx,ty*bsy,0) )

            # allocate input image block 
            bi = ib.ImgBlock( imi.dtype , extent = ex_ti ) 

            # allocate mask block  
            bm = ib.ImgBlock( imm.dtype , extent = ex_tm ) 

            # load image block 
            imi.read( bi ) 

            # load mask block 
            imm.read( bm ) 

            # clip image block to mask 
            clipToMask( bi , bm , MASKFG , NODATA ) 

            # save image block 
            imo.write( bi ) 

            # print progress 
            sys.stdout.write(prg.istr(1)) ; sys.stdout.flush() 

    sys.stdout.write("\n") ; sys.stdout.flush() 
