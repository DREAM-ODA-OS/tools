#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Extract fooprint from referenceable dataset using EOxServer's reftools
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

# TODO: Output formats equivalent to footprint extractor 
# TODO: Wrap arround. 

import sys
import os.path 
import img_geom as ig 
from osgeo import gdal 

# NOTE: Make sure the eoxserver is in your path 
from eoxserver.processing.gdal import reftools as rt 

if __name__ == "__main__" : 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    FORMAT="WKB"

    try: 

        INPUT=sys.argv[1] 

        NP = 1
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if ( arg in ig.OUTPUT_FORMATS ) : FORMAT=arg # output format
                elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

    except IndexError : 
        
        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input image> [WKT|WKB]\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------
    # get the referenceable dataset's outline 

    #NOTE: It is assumed, that the outline is not wrapped arroud the date-line.

    ds   = gdal.Open( INPUT ) 
    prm  = rt.suggest_transformer( ds ) 
    geom = ig.setSR(ig.parseGeom(rt.get_footprint_wkt(ds,**prm)),ig.OSR_WGS84)

    #--------------------------------------------------------------------------
    # export 

    try: 

        sys.stdout.write(ig.dumpGeom(geom,FORMAT)) 

    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)
