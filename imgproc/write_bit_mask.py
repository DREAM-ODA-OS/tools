#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool writes a single bit-mask plane (from a 'byte' mask) to a bit-flag 
#   image. 
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
def writeBitMask( bo, bi, bmask ) :

    if ( bi.sx != bo.sx ) or ( bi.sy != bo.sy ) \
        or ( bi.sz != bo.sz ) or ( 1 != bo.sz ) : 
        raise ValueError("Incompatible sizes of the input blocks.")

    # write the ooutputs 
    bo.data[:,:,:] = np.bitwise_or( bmask * ( bi.data != 0 ) , 
                                    np.bitwise_and( ~bmask, bo.data ) )

    return bo

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    def error( message ) :
        print >>sys.stderr, "ERROR: %s: %s\n" %( EXENAME, message ) 

    # block size 
    bsx , bsy = 256, 256 

    try: 

        OUTPUT = sys.argv[1]
        INPUT  = sys.argv[2]
        BMASK  = sys.argv[3]

        #anything else treated as a format option
        for opt in sys.argv[4:] :
            pass 

    except IndexError : 
        error("Not enough input arguments!") 
        sys.stderr.write("USAGE: %s <bit-flags-image> <input mask> <bit-mask>\n"%EXENAME) 
        sys.stderr.write("EXAMPLE: %s input.tif mask.tif 128\n"%EXENAME) 
        sys.exit(1) 


    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # open input image 
    imo = ib.ImgFileOut( OUTPUT ) 

    if ( imi.sz > 1 ) or ( imo.sz > 1 ) : 
        error("Multiband images not supported!") 
        sys.exit(1) 

    ALLOWED_TYPES=('uint8','uint16','uint32','int8','int16','int32')

    if imi.dtype not in ALLOWED_TYPES : 
        error("Unsupported image mask's data type '%s'!"%imi.dtype) 
        sys.exit(1) 

    if imo.dtype not in ALLOWED_TYPES : 
        error("Unsupported image bit-flag-image's data type '%s'!"%imo.dtype) 
        sys.exit(1) 

    # convert bit mask values to the image's data type 
    BMASK = np.dtype(imo.dtype).type( int(BMASK) ) 

    # check image sizes 

    if ( imi.sx != imo.sx ) or ( imi.sy != imo.sy ) : 
        sys.stderr.write("ERROR: The written mask and the target bit-flag-"
                         "image must have equal pixel sizes!\n") 
        sys.exit(1)

    # initialize progress printer 
    prg = iu.Progress( (1+(imo.sy-1)/bsy)*(1+(imo.sx-1)/bsx) ) 

    print "Writing mask as a bit flag ..."

    for ty in xrange( 1 + (imo.sy-1)/bsy ) :
        for tx in xrange( 1 + (imo.sx-1)/bsx ) :

            # extent of the tile 
            ex_t = imo & ib.ImgExtent((bsx,bsy,1),(tx*bsx,ty*bsy,0))

            # allocate image blocks
            bi = ib.ImgBlock( imi.dtype , extent = ex_t ) 
            bo = ib.ImgBlock( imo.dtype , extent = ex_t ) 

            # load image blocks  
            imi.read( bi ) 
            imo.read( bo ) 

            # calculate the mask 
            bo = writeBitMask( bo, bi, BMASK )

            # save image block 
            imo.write( bo ) 

            # print progress 
            sys.stdout.write(prg.istr(1)) ; sys.stdout.flush() 

    sys.stdout.write("\n") ; sys.stdout.flush() 

