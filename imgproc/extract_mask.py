#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool extracts a data/no-data mask from the provided raster image.
#   The input image can be in arbitrary image format supported by GDAL 
#   the output will be always produced as GeoTIFF (or TIFF if no geocoding
#   available). 
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
def extractMaskAll( bi, nodata, bg=0x00, fg=0xFF ) :
    
    # output block 
    bo = ib.ImgBlock('uint8',size=(bi.sx,bi.sy,1), offset=(bi.ox,bi.oy,0))

    # prepare list of no-data values 
    if len( nodata ) == 1 : 
        nodata = [ nodata[0] for i in xrange(bi.data.shape[2]) ] 

    # temporary array - evaluates to True for no-data values 

    tmp = np.ones( bi.data.shape[:2] , 'bool' ) 
    for i in xrange( bi.data.shape[2] ) : 
        tmp &= ( bi.data[:,:,i] == nodata[i] ) 

    # set the final array 

    bo.data[:,:,0] = tmp*bg + np.logical_not(tmp)*fg  

    return bo 

def extractMaskAny( bi, nodata, bg=0x00, fg=0xFF ) :
    
    # output block 
    bo = ib.ImgBlock('uint8',size=(bi.sx,bi.sy,1), offset=(bi.ox,bi.oy,0))

    # prepare list of no-data values 
    if len( nodata ) == 1 : 
        nodata = [ nodata[0] for i in xrange(bi.data.shape[2]) ] 

    # temporary array - evaluates to True for no-data values 

    tmp = np.zeros( bi.data.shape[:2] , 'bool' ) 
    for i in xrange( bi.data.shape[2] ) : 
        tmp |= ( bi.data[:,:,i] == nodata[i] ) 

    # set the final array 

    bo.data[:,:,0] = tmp*bg + np.logical_not(tmp)*fg  

    return bo 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 
    MODE_IS_ALL=True 
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
        NODATA0 = sys.argv[3].split(",")
        MASKBG = 0x00 
        MASKFG = 0xFF 

        #anything else treated as a format option
        for opt in sys.argv[4:] :
            if opt.upper() == "MODE=ALL" : 
                MODE_IS_ALL=True 
            elif opt.upper() == "MODE=ANY" : 
                MODE_IS_ALL=False
            else : 
                FOPTS.setOption( opt )

    except IndexError : 
        
        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input image> <output mask/TIF> <no data value or list>\n"%EXENAME) 
        sys.stderr.write("EXAMPLE: %s input.tif mask.tif 0,0,0,0\n"%EXENAME) 
        sys.stderr.write("EXAMPLE: %s input.tif mask.tif 0\n"%EXENAME) 
        sys.exit(1) 


    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # convert no-data values to the image's data type 
    NODATA = map( np.dtype(imi.dtype).type, NODATA0 ) 

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

    # mode of mask extraction - all bands equal / any band equals to no-data
    if MODE_IS_ALL : 
        extractMask = extractMaskAll
    else : 
        extractMask = extractMaskAny

    # initialize progress printer 
    prg = iu.Progress( (1+(imi.sy-1)/bsy)*(1+(imi.sx-1)/bsx) ) 

    print "Extracting data mask ..."

    for ty in xrange( 1 + (imi.sy-1)/bsy ) :
        for tx in xrange( 1 + (imi.sx-1)/bsx ) :

            # extent of the tile 
            ex_t = imi & ib.ImgExtent( (bsx,bsy,imi.sz) , (tx*bsx,ty*bsy,0) )

            # allocate input image block 
            bi = ib.ImgBlock( imi.dtype , extent = ex_t ) 

            # load image block 
            imi.read( bi ) 

            # calculate the mask 
            bo = extractMask( bi, NODATA , MASKBG, MASKFG ) 

            # save image block 
            imo.write( bo ) 

            # print progress 
            sys.stdout.write(prg.istr(1)) ; sys.stdout.flush() 

    sys.stdout.write("\n") ; sys.stdout.flush() 
