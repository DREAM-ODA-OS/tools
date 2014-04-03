#!/usr/bin/env python 
#------------------------------------------------------------------------------
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

# tiepoint offset - higher order function                                         
def tiepointOffsetter( ( ox , oy ) ) :                                                         
    def function( p ) :                                                              
        return gdal.GCP( p.GCPX, p.GCPY, p.GCPZ, p.GCPPixel - ox, 
                         p.GCPLine - oy, p.Info, p.Id )                                                  
    return function                                                                  
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
        SUBSET = map( int , sys.argv[3].split(",") ) 
        NODATA = 0 # TODO: make it parameter

        #anything else treated as a format option
        for opt in sys.argv[4:] :
            FOPTS.setOption( opt )

    except IndexError : 

        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input image> <output TIF> <subset spec>\n"%exename) 
        sys.stderr.write("EXAMPLE: %s input.tif subset.tif 10,20,200,200\n"%exename) 
        sys.exit(1) 

    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # convert subset to extent and trim it by the image extent 
    ss = imi&ib.ImgExtent((SUBSET[2],SUBSET[3],imi.sz),(SUBSET[0],SUBSET[1],0))

    # creation parameters 
    prm = { 
        'path' :   OUTPUT,
        'nrow' :   ss.sy,
        'ncol' :   ss.sx,
        'nband' :  imi.sz,
        'dtype' :  imi.dtype,
        'nodata' :  imi.nodata,
        'options' : FOPTS.getOptions(),
    } 

    #print prm 

    # geocoding 
    if imi.ds.GetProjection() : 

        # get the original transformation matrix
        tmtx0 = imi.ds.GetGeoTransform()

        # calculate the new offset of the origin
        ox = tmtx0[0] + tmtx0[1] * ss.ox + tmtx0[2] * ss.ox  
        oy = tmtx0[3] + tmtx0[4] * ss.oy + tmtx0[5] * ss.oy  

        # new transformation matrix 
        tmtx1 = [ ox, tmtx0[1], tmtx0[2], oy, tmtx0[4], tmtx0[5] ] 
        
        prm['proj'] = imi.ds.GetProjection()
        prm['geotrn'] = tmtx1

    elif imi.ds.GetGCPProjection() : 

        # instantiate tiepoint offsetter function for current offset value 
        tpOff = tiepointOffsetter( ( ss.ox , ss.oy ) )                                                          

        prm['proj'] = imi.ds.GetGCPProjection()
        prm['gcps'] = [ tpOff(p) for p in imi.ds.GetGCPs() ]


    # open output image 
    imo = ib.createGeoTIFF( **prm ) 

    #--------------------------------------------------------------------------

    BSX=256 # X block size 
    BSY=256 # Y block size 

    # allocate image block 
    bi = ib.ImgBlock( imi.dtype , (BSX,BSY,imi.sz) ) 

    # initialize progress printer 
    prg = iu.Progress( (1+(imo.sy-1)/BSY)*(1+(imo.sx-1)/BSX) ) 

    print "Extracting image subset..."

    for tr in xrange( 1 + (imo.sy-1)/BSY ) :
        for tc in xrange( 1 + (imo.sx-1)/BSX ) :

            bi.fill( NODATA ) # fill block by no-data value 

            # load image block 
            bi.move_to( tc*BSX + ss.ox , tr*BSY + ss.oy ) # input image offset 
            imi.read( bi ) 

            # save image block 
            bi.move_to( tc*BSX , tr*BSY ) # output image offset 
            imo.write( bi ) 

            # print progress 
            sys.stdout.write(prg.istr(1)) ; sys.stdout.flush() 

    sys.stdout.write("\n") ; sys.stdout.flush() 
