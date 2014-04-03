#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool calculates the image histogram for a given number of equidistant
#   bins. Additional two border bins are added for the values laying outside
#   the covered interval. No data or invalid values are ignored. 
# 
#   For multi-band images, for each band a separate histogram is calculated 
#
#   Optionally dB scale histogram can be calculated. 
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

#------------------------------------------------------------------------------
# range stretch 

def get_nodata_mask( bi, nodata ):  

    # prepare list of no-data values 
    if len( nodata ) == 1 : 
        nodata = [ nodata[0] for i in xrange(bi.data.shape[2]) ] 

    # no-data value mask 

    mask = np.ones( bi.data.shape[:2] , 'bool' ) 
    for i in xrange( bi.data.shape[2] ) : 
        mask &= ( bi.data[:,:,i] == nodata[i] ) 

    return mask 

class Histogram:

    def __init__(self,nband,vmin,vmax,nbin,dbscale):

        self.dbscale = bool(dbscale) 
        self.vmin = float( vmin ) 
        self.vmax = float( vmax ) 
        self.nbin = max( 1 , int(nbin) ) 
        self.step = ( self.vmax - self.vmin ) / self.nbin 

        # histogram accumulator
        self.accum = np.zeros((nband,nbin+2),'uint64')
        self.count = np.zeros(nband,'uint64')

    def add( self, bi, nodata ) :

        if self.dbscale : 
            return self._add_hist_db( bi, nodata ) 
        else:
            return self._add_hist_lin( bi, nodata ) 

    def _add_hist( self, data): 

        nbin = self.nbin + 2 
        vrange = ( self.vmin - self.step , self.vmax + self.step ) 

        # clip the outliers 
        data[ (data<self.vmin).nonzero() ] = self.vmin - 0.5*self.step ;  
        data[ (data>self.vmax).nonzero() ] = self.vmax + 0.5*self.step ;  

        # calculate the histograms 
        for i in xrange( self.accum.shape[0] ) : 

            band_hist , _ = np.histogram(data[:,i],nbin,vrange)

            self.accum[i,:] += band_hist 
            self.count[i]   += data.shape[0]


    def _add_hist_lin( self, bi, nodata ) : 

        # no-data value mask 
        mask = get_nodata_mask( bi, nodata )

        # extract valid values and pass it to histogrammer
        self._add_hist( bi.data[np.logical_not(mask).nonzero()] ) 


    def _add_hist_db( self, bi, nodata ) : 

        # no-data value mask 
        mask = get_nodata_mask( bi, nodata )

        # hadle non-positive vlaues 
        for i in xrange( bi.data.shape[2] ) : 
            mask |= ( bi.data[:,:,i] <= 0 ) 

        # extract valid values and pass it to histogrammer
        self._add_hist( 10*np.log10( bi.data[np.logical_not(mask).nonzero()] ) ) 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    exename = os.path.basename( sys.argv[0] ) 
    # block size 
    bsx , bsy = 256, 256 
    dbscale = False 
    gnuplot = False  

    # default format options 

    try: 

        INPUT  = sys.argv[1]
        OUTPUT = sys.argv[2]
        VMIN   = float(sys.argv[3])
        VMAX   = float(sys.argv[4]) 
        NBIN   = int(sys.argv[5]) 
        NODATA0 = sys.argv[6].split(",")

        #anything else than "DB" is treated as a format option
        for opt in sys.argv[7:] :
            if opt.upper() == "DB" :
                dbscale = True 
            elif opt.upper() == "GNUPLOT" : 
                gnuplot = True 
            else : 
                pass

    except IndexError : 
        
        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input image> <output text file> <min.> <max.> <nbins> <no data value or list>\n"%exename) 
        sys.stderr.write("EXAMPLE: %s input.tif histogram.txt 10 120 110 0,0,0,0\n"%exename) 
        sys.stderr.write("EXAMPLE: %s input.tif histogram.txt 0.0 2.0 20 0\n"%exename) 
        sys.exit(1) 



    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # convert no-data values to the image's data type 
    NODATA = map( np.dtype(imi.dtype).type, NODATA0 ) 

    #create histogram object 
    hist = Histogram(imi.sz,VMIN,VMAX,NBIN,dbscale)

    print "RANGE: " , VMIN , VMAX 
    print "NBIN:  " , NBIN 
    print "IMG:   " , (imi.sx,imi.sy,imi.sz) 
    print "NODATA:" , NODATA
    print imi.dtype

    for ty in xrange( 1 + (imi.sy-1)/bsy ) :
        for tx in xrange( 1 + (imi.sx-1)/bsx ) :

            sys.stdout.write("#") ; sys.stdout.flush() 

            # extent of the tile 
            ex_t = imi & ib.ImgExtent( (bsx,bsy,imi.sz) , (tx*bsx,ty*bsy,0) )

            # allocate input image block 
            bi = ib.ImgBlock( imi.dtype , extent = ex_t ) 

            # load image block 
            imi.read( bi ) 

            # accumulate current tile
            hist.add( bi, NODATA ) 

        sys.stdout.write("\n") ; sys.stdout.flush() 

    # write histogram 

    with open(OUTPUT,"w") as fid : 

        fid.write("#HISTOGRAM: %s\n"%INPUT)
        fid.write("#vmin=%g\n"%hist.vmin)
        fid.write("#vmax=%g\n"%hist.vmax)
        fid.write("#nbin=%g\n"%hist.nbin)
        fid.write("#scale=%s\n"%( "dB" if dbscale else "linear"  ) )
        fid.write("#nband=%d\n"%( len( hist.count ) ) )
        fid.write("#count=%s\n"%(",".join(map(lambda v:"%d"%v,hist.count))))

 
        for i in xrange( hist.accum.shape[1] ) : 
            x = (i-0.5)*hist.step + hist.vmin 
            fid.write("%g\t%s\n"%(x,"\t".join(map(str,hist.accum[:,i]))))


