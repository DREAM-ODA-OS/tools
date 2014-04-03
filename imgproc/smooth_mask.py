#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool tries to smooth mask edges by bluring and thresholding.
#   While blur makes the edges smooth the thresholding generates new 
#   mask. 
#
#   
#   For bluring (separated) Gaussian convolution filter is applied. 
#   The value of the threshold controls position of the new mask border. 
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
import math as m 

#------------------------------------------------------------------------------
# mask extractor 

# erf function approximation [src: http://en.wikipedia.org/wiki/Error_function] 
c=np.array([-1.26551223,+1.00002368,+0.37409196,+0.09678418,-0.18628806,
             +0.27886807,-1.13520398,+1.48851587,-0.82215223,+0.17087277])

def _erf( x ) : 
    t = 1.0 / ( 1.0 + 0.5*np.abs(x) ) 
    p=c[0]+t*(c[1]+t*(c[2]+t*(c[3]+t*(c[4]+t*(c[5]+t*(c[6]+t*(c[7]+t*(c[8]+t*c[9]))))))))
    y = np.sign(x)*( 1.0 - t*np.exp( p - x**2 ) ) 
    return y 
    

def convCoef1D_GaussBlur( whs ) : 
    """ evaluate coeficients of 1D Gaussian filter (convolution matrix)""" 

    c0 = 3.0 / m.sqrt(2.0) 
    f0 = 0.5 / _erf(c0) 
    
    a = f0*_erf( c0*np.linspace( -1 , 1 , 2*whs+2 ) ) 

    return a[1:]-a[:-1]


def gaussianBlur( bb , whs = 1 ) : 
    
    coef = convCoef1D_GaussBlur( whs ) 

    nn = 2*whs+1 ;

    # PASS 1 

    # temporary buffer (already set to zero)
    t1 = ib.ImgBlock('float32',(bb.sx-2*whs,bb.sy,1),(bb.ox+whs,bb.oy,0)) 

    for i in xrange( nn ) : 
        t1.data[:,:,0] += coef[i] * bb.data[:,i:(i+t1.sx),0] 

    # PASS 2 

    bb = ib.ImgBlock('float32',(t1.sx,t1.sy-2*whs,1),(t1.ox,t1.oy+whs,0)) 

    for i in xrange( nn ) : 
        bb.data[:,:,0] += coef[i] * t1.data[i:(i+bb.sy),:,0] 

    return bb 


def boxCar( bb, whs = 1 ) :

    nn = 2*whs+1 ;

    # PASS 1 

    # temporary buffer (already set to zero)
    t1 = ib.ImgBlock('float32',(bb.sx-2*whs,bb.sy,1),(bb.ox+whs,bb.oy,0)) 

    for i in xrange( nn ) : 
        t1.data[:,:,0] += bb.data[:,i:(i+t1.sx),0] 

    t1.data *= 1.0/nn

    # PASS 2 

    bb = ib.ImgBlock('float32',(t1.sx,t1.sy-2*whs,1),(t1.ox,t1.oy+whs,0)) 

    for i in xrange( nn ) : 
        bb.data[:,:,0] += t1.data[i:(i+bb.sy),:,0] 

    bb.data *= 1.0/nn

    return bb 

 
def boxCarN( bb , whs = 1 , nrep = 1 ) : 

    for i in xrange( nrep ) : 
        bb = boxCar( bb , whs ) 

    return bb 

#------------------------------------------------------------------------------

def mirrorBorder( bb , im ) : 

    if bb.ox < im.ox : 
        o = im.ox - bb.ox
        for i in xrange( o ) : 
            bb.data[:,i,:] = bb.data[:,(2*o-i-1),:]

    if bb.ux > im.ux : 
        n = bb.ux - im.ux
        o = im.ux - bb.ox
        for i in xrange( n ) : 
            bb.data[:,(o+i),:] = bb.data[:,(o-i-1),:]

    if bb.oy < im.oy : 
        o = im.oy - bb.oy
        for i in xrange( o ) : 
            bb.data[i,:,:] = bb.data[(2*o-i-1),:,:]

    if bb.uy > im.uy : 
        n = bb.uy - im.uy
        o = im.uy - bb.oy
        for i in xrange( n ) : 
            bb.data[(o+i),:,:] = bb.data[(o-i-1),:,:]

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 
    # block size 
    #bsx , bsy =  4000 , 4000  # using larger windows 
    #bsx , bsy =  1024 , 1024  # using larger windows 
    bsx , bsy =  1000 , 1000  # using larger windows 
    #bsx , bsy =  256 , 256  # using larger windows 

    FOPTS = ib.FormatOptions() 
    FOPTS["TILED"] = "YES"
    FOPTS["BLOCKXSIZE"] = "256"
    FOPTS["BLOCKYSIZE"] = "256"
    FOPTS["COMPRESS"] = "DEFLATE"

    try: 

        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        THRSH  = max(0.0,min(1.0,float(sys.argv[3])))
        WHS  = max(1,int(sys.argv[4] )) 
        #NREP = max(1,int(sys.argv[5] ))
        MASKBG = 0x00 
        MASKFG = 0xFF 

        #anything else treated as a format option
        #for opt in sys.argv[6:] :
        for opt in sys.argv[5:] :
            FOPTS.setOption( opt )

    except IndexError : 
        
        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input mask> <output mask/TIF> <threshold> <radius>\n"%EXENAME) 
        sys.stderr.write("EXAMPLE: %s mask_in.tif mask_out.tif 0.5 20\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------

    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # check input image 

    if imi.sz > 1 : 
        sys.stderr.write("ERROR: Multiband images not supported!\n") 
        sys.exit(1) 

    if imi.dtype != 'uint8' : 
        sys.stderr.write("ERROR: Unsupported image data type '%s'!\n"%imi.dtype) 
        sys.exit(1) 

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

    #--------------------------------------------------------------------------

    #nn = WHS * NREP 
    nn = WHS 

    # initialize progress printer 
    prg = iu.Progress( (1+(imi.sy-1)/bsy)*(1+(imi.sx-1)/bsx) ) 

    print "Smoothing mask ..."

    for ty in xrange( 1 + (imi.sy-1)/bsy ) :
        for tx in xrange( 1 + (imi.sx-1)/bsx ) :

            # extent of the tile 
            ex_t = imi & ib.ImgExtent( (bsx,bsy,1) , (tx*bsx,ty*bsy,0) )

            # extended tile extent 
            ex_t2 = ib.ImgExtent( (ex_t.sx+2*nn,ex_t.sy+2*nn,1),
                                  (ex_t.ox-nn,ex_t.oy-nn,0))

            # allocate input image block (already filled by zero)
            bb = ib.ImgBlock( 'float32' , extent = ex_t2 ) 

            # load image block 
            imi.read( bb ) 

            # mirror the borders 
            mirrorBorder( bb , imi )  

            # scale 
            bb.data *= (1.0/MASKFG)

            # apply boxcar filter 

            #bb = boxCarN( bb , WHS , NREP ) 
            bb = gaussianBlur( bb , WHS ) 

            # apply threshold
            bb.data[:,:,:] = ( bb.data > THRSH ) 
            
            # scale 
            bb.data *= MASKFG

            # save image block 
            imo.write( bb ) 

            # print progress 
            sys.stdout.write(prg.istr(1)) ; sys.stdout.flush() 

    sys.stdout.write("\n") ; sys.stdout.flush() 
