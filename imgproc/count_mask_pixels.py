#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Extract pixel count.
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
import math as m 
from osgeo import ogr ; ogr.UseExceptions() 
from osgeo import osr ; ogr.UseExceptions() 
from osgeo import gdal ; gdal.UseExceptions() 

#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# pixel counters 

def countPixelsEQL( bi, value ):
    return np.sum( bi.data[:,:,0] == value ) 

def countPixelsAND( bi, value ):
    return np.sum( ( bi.data[:,:,0] & value ) != 0 ) 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    OPERATOR="EQL"
    OPERATORS=("EQL","AND","ALL")

    try: 

        INPUT = sys.argv[1]
        VALUE = int( sys.argv[2] ) 
        NP = 2 
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if ( arg in OPERATORS ) : OPERATOR = arg # match operator 
                elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

    except IndexError : 
        
        sys.stderr.write("\nCount pixels.\n\n") 
        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input image> <data-value> [AND|EQL*] [DEBUG]\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------

    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # check input image 

    if imi.sz > 1 : 
        sys.stderr.write( "ERROR: %s: Multiband images not supported!" \
                          "\n"%(EXENAME) ) 
        sys.exit(1) 

    if imi.dtype not in ('uint8','int8','uint16','int16','uint32','int32') : 
        sys.stderr.write( "ERROR: %s: Unsupported image data type '%s'!" \
                          "\n"%(EXENAME,imi.dtype) ) 
        sys.exit(1) 

    #--------------------------------------------------------------------------

    if DEBUG:
        print >>sys.stderr, "OPERATOR:" , OPERATOR 
        print >>sys.stderr, "VALUE:   " , VALUE

    if OPERATOR == "EQL" :
        countPixels = countPixelsEQL
    elif OPERATOR == "AND" :
        countPixels = countPixelsAND
    elif OPERATOR == "ALL" :
        print ( imi.sx * imi.sy ) 
        sys.exit(0) 
    else: 
        sys.stderr.write( "ERROR: %s: Unsupported operator! OPERATOR='%s'!" \
                          "\n"%(EXENAME,OPERATOR) ) 
        sys.exit(1) 

    #--------------------------------------------------------------------------
    bsx , bsy = 256,256 

    count = 0 

    for ty in xrange( 1 + (imi.sy-1)/bsy ) :
        for tx in xrange( 1 + (imi.sx-1)/bsx ) :

            if DEBUG:
                sys.stderr.write("#")
                sys.stderr.flush() 

            # extent of the tile 
            ex_t = imi & ib.ImgExtent( (bsx,bsy,imi.sz) , (tx*bsx,ty*bsy,0) )

            # allocate input image block 
            bi = ib.ImgBlock( imi.dtype , extent = ex_t ) 

            # load image block 
            imi.read( bi ) 

            # count pixels
            count += countPixels( bi, VALUE ) 

            # save image block 
            #imo.write( bo ) 

        if DEBUG:
            sys.stderr.write("\n")
            sys.stderr.flush() 

    print count 
