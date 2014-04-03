#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#  perform union of a list of geometries
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
import img_geom as ig 
from osgeo import ogr ; ogr.UseExceptions() 
from osgeo import osr ; ogr.UseExceptions() 
#from osgeo import gdal ; gdal.UseExceptions() 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    FORMAT="WKB"
    HELP=False
    INPUTS=[]  

    for arg in sys.argv[1:] : 

        # reserved keywords 
        if arg in ( "WKT", "WKB", "JSON", "KML", "DEBUG" , "HELP" ) : 
            if ( arg in ig.OUTPUT_FORMATS ) : FORMAT=arg # output format
            elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output
            elif ( arg == "HELP" ) : HELP = True # print help on useage and exit 
            continue 

        INPUTS.append( arg ) 

    if HELP or ( len(sys.argv) == 1 ) :
        
        sys.stderr.write("\nUnite muptiple geometries and dump new geometry to stdout\n") 
        sys.stderr.write("by default in WKB format.\n\n") 
        sys.stderr.write("USAGE: %s <WKB|WKB> ... [WKT|WKB] [HELP] [DEBUG]\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------

    # start with an empty polygon 
    geom = ogr.Geometry( ogr.wkbPolygon )
    sr = None 

    for i,input in enumerate(INPUTS) : 
    
        if DEBUG : print >>sys.stderr, "#%d\t%s"%(i,input) 

        # open input geometry file 
        fin = sys.stdin if input == "-" else open(input) 

        # read the data 
        try: 
            gsrc = ig.parseGeom( fin.read() , DEBUG ) 
        except Exception as e : 
            print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
            sys.exit(1)
    
        if ( sr is None ) and ( gsrc.GetSpatialReference() is not None ) : 
            sr = gsrc.GetSpatialReference().Clone() 
        
        # unite geometries 
        geom = geom.Union( gsrc ) 

    # assign spatial reference 
    geom.AssignSpatialReference( sr ) 

    #--------------------------------------------------------------------------
    # export 

    try: 

        sys.stdout.write(ig.dumpGeom(geom,FORMAT)) 

    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)
