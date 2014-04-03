#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool performs range stretch to 8 bits for given maximum and 
#   minimum values. The range is stretched beeween 1 and 255. 0 is reserved for
#   non-data value. 1 contains all values below  to min. 255 contains 
#   all values larger or eqaual to max. 
#
#   Optionally the stretching can be performed in logarithmic (dB) scale. 
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
# range stretch 

def get_nodata_mask( bi, nodata ):  


    if nodata is not None : 

        # prepare list of no-data values 
        if len( nodata ) == 1 : 
            nodata = [ nodata[0] for i in xrange(bi.data.shape[2]) ] 

        # no-data value mask 
        mask = np.ones( bi.data.shape[:2] , 'bool' ) 
        for i in xrange( bi.data.shape[2] ) : 
            mask &= ( bi.data[:,:,i] == nodata[i] ) 

    else :
        # all pixels are taken as valid 
        mask = np.zeros( bi.data.shape[:2] , 'bool' ) 

    return mask 

def add_alpha_channel( bi , mask ) : 

    # output block 
    bo = ib.ImgBlock('uint8',size=(bi.sx,bi.sy,bi.sz+1), offset=(bi.ox,bi.oy,0))

    bo.data[:,:,:-1] = bi.data 
    bo.data[:,:,-1]  = np.logical_not(mask) * 255 

    return bo 


def range_stretch_lin( bi, nodata, vmin, vmax , set_alpha = False ) :
    
    # output block 
    bo = ib.ImgBlock('uint8',size=(bi.sx,bi.sy,bi.sz), offset=(bi.ox,bi.oy,0))

    # no-data value mask 
    mask = get_nodata_mask( bi, nodata )

    # set the final array 

    # scaling 
    idx = np.logical_not(mask).nonzero()
    f   = 253.0 / ( vmax - vmin ) 
    tmp = f*( bi.data[idx] - vmin ) + 2 

    #clipping 
    tmp[ (tmp<  1).nonzero() ] =   1.
    tmp[ (tmp>255).nonzero() ] = 255. 

    #store values 
    bo.data[idx] = tmp 

    # optionally add alpha channel 
    if set_alpha : 
        bo = add_alpha_channel( bo , mask )  

    return bo 


def range_stretch_db( bi, nodata, vmin, vmax , set_alpha = False ) :

    # output block 
    bo = ib.ImgBlock('uint8',size=(bi.sx,bi.sy,bi.sz), offset=(bi.ox,bi.oy,0))

    # no-data value mask 
    mask = get_nodata_mask( bi, nodata )

    # hadle non-positive vlaues 
    for i in xrange( bi.data.shape[2] ) : 
        mask |= ( bi.data[:,:,i] <= 0 ) 

    # set the final array 

    # scaling 
    idx = np.logical_not(mask).nonzero()
    f   = 253.0 / ( vmax - vmin ) 
    tmp = f*( (10.*np.log10(bi.data[idx])) - vmin ) + 2 

    #clipping 
    tmp[ (tmp<  1).nonzero() ] =   1.
    tmp[ (tmp>255).nonzero() ] = 255. 

    #store values 
    bo.data[idx] = tmp 

    #fix the non-data values
    #idx = np.logical_not(mask).nonzero()
    #bo.data[idx] = 0

    # optionally add alpha channel 
    if set_alpha : 
        bo = add_alpha_channel( bo , mask )  

    return bo 


#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    exename = os.path.basename( sys.argv[0] ) 
    # block size 
    bsx , bsy = 256, 256 
    dbscale = False ; 
    addalpha=False

    # default format options 

    FOPTS = ib.FormatOptions() 
    FOPTS["TILED"] = "YES"
    FOPTS["BLOCKXSIZE"] = "256"
    FOPTS["BLOCKYSIZE"] = "256"
    FOPTS["COMPRESS"] = "DEFLATE"

    try: 

        INPUT  = sys.argv[1]
        OUTPUT = sys.argv[2]
        VMIN   = float(sys.argv[3])
        VMAX   = float(sys.argv[4]) 
        NODATA0 = sys.argv[5].split(",")

        #anything else than "DB" is treated as a format option
        for opt in sys.argv[6:] :
            if opt.upper() == "DB" :
                dbscale = True 
            elif opt.upper() == "ADDALPHA" :
                addalpha = True 
                FOPTS["ALPHA"] = "YES"
            else : 
                FOPTS.setOption( opt )

    except IndexError : 
        
        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input image> <output mask/TIF> <min.> <max.> <no data value or list>\n"%exename) 
        sys.stderr.write("EXAMPLE: %s input.tif output.tif 10 12000 0,0,0,0\n"%exename) 
        sys.stderr.write("EXAMPLE: %s input.tif output.tif 2 20 0\n"%exename) 
        sys.exit(1) 

    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # convert no-data values to the image's data type 

    if str(NODATA0[0]).upper() != "NONE" : 
        NODATA = map( np.dtype(imi.dtype).type, NODATA0 ) 
    else :
        NODATA = None 

    # creation parameters 
    prm = { 
        'path' :   OUTPUT,
        'nrow' :   imi.sy,
        'ncol' :   imi.sx,
        'nband' :  imi.sz + ( 1 if addalpha else 0 ) ,
        'dtype' :  'uint8',
        'options' : FOPTS.getOptions(),
        'nodata' : 0,
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

    # stretch the ranges 
    if dbscale : 
        range_stretch = range_stretch_db
    else : 
        range_stretch = range_stretch_lin

    # initialize progress printer 
    prg = iu.Progress( (1+(imi.sy-1)/bsy)*(1+(imi.sx-1)/bsx) ) 

    print "Range stretching ..."

    for ty in xrange( 1 + (imi.sy-1)/bsy ) :
        for tx in xrange( 1 + (imi.sx-1)/bsx ) :

            # extent of the tile 
            ex_t = imi & ib.ImgExtent( (bsx,bsy,imi.sz) , (tx*bsx,ty*bsy,0) )

            # allocate input image block 
            bi = ib.ImgBlock( imi.dtype , extent = ex_t ) 

            # load image block 
            imi.read( bi ) 

            # stretch the ranges 
            bo = range_stretch( bi , NODATA, VMIN, VMAX, addalpha ) 
                
            # save image block 
            imo.write( bo ) 

            # print progress 
            sys.stdout.write(prg.istr(1)) ; sys.stdout.flush() 

    sys.stdout.write("\n") ; sys.stdout.flush() 
