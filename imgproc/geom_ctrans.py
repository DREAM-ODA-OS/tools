#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Coordinate transformation.
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
import traceback
import os.path 
import img_geom as ig 
from osgeo import ogr ; ogr.UseExceptions() 
from osgeo import osr ; ogr.UseExceptions() 
#from osgeo import gdal ; gdal.UseExceptions() 

#TODO: remove date-line handling moved to the 'geom_to_wgs84.py' 

#------------------------------------------------------------------------------
# bounds of well known coordinate systems 

KNOWN_BOUNDS={ 
    "EPSG:4326" : (-180.,-90.,+180.,+90.) ,
}

#------------------------------------------------------------------------------

def usage(): 
    sys.stderr.write("\nPerform coordinate transformation of the \n")
    sys.stderr.write("geometry and dump new geometry to stdout\n") 
    sys.stderr.write("by default in WKB format.\n") 
    sys.stderr.write("The projection is to be provided as an EPSG code\n") 
    sys.stderr.write("(EPSG:4326) or as a WTK string.\n\n") 
    sys.stderr.write("USAGE: %s <WKB|WKB> <projection> [DLXFIX] [DLXWRAP] ")
    sys.stderr.write("[BOUNDS:<xmin>,<ymin>,<xmax>,<ymax>] [WKT|WKB] [DEBUG]\n") 

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    FORMAT="WKB"
    DLXFIX=False  # fix easting wraparroud by providig SR bounds 
    DLXWRAP=False  # perform proper easting wraparround
    BOUNDS=None  #  projection bounds -> needed by wraparround handling

    try: 

        INPUT    = sys.argv[1]
        TARGET_SR = ig.parseSR(sys.argv[2]) # target spatial reference  
        BOUNDS = KNOWN_BOUNDS.get(sys.argv[2],None) 
        NP = 2 
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if ( arg in ig.OUTPUT_FORMATS ) : FORMAT=arg # output format
                elif ( arg == "DLXFIX" ) :          DLXFIX="True" 
                elif ( arg == "DLXWRAP" ) :         DLXWRAP="True"
                elif ( arg.startswith("BOUNDS:") ): 
                    BOUNDS=arg.split(":")[-1] 
                    BOUNDS=map(float,BOUNDS.split(",")) 
                elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

        # check bounds 
        if BOUNDS is not None : 
            if len(BOUNDS) != 4 : 
                raise ValueError("Invalid projection bounds!") 

            if DLXWRAP: DLXFIX=True 
        else: 
            if DLXFIX or DLXWRAP : 
                raise ValueError("SR bounds required by date-line wrap handling!") 

    except IndexError : 
        sys.stderr.write("ERROR: %s: Not enough input arguments!\n"%EXENAME) 
        usage() 
        sys.exit(1) 

    except Exception, e : 
        sys.stderr.write("ERROR: %s: %s\n"%(EXENAME,e)) 
        usage() 
        sys.exit(1) 

    #--------------------------------------------------------------------------
    # import 

    # open input geometry file 
    fin = sys.stdin if INPUT == "-" else open(INPUT) 

    # read the data 
    try: 
        geom = ig.parseGeom( fin.read() , DEBUG ) 
    except Exception as e : 
        if DEBUG : traceback.print_exc( file=sys.stderr ) 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # project geometry 

    SOURCE_SR = geom.GetSpatialReference() 

    # 1) geometry either source or target SR is None -> assign the target 
    if ( SOURCE_SR is None ) or ( TARGET_SR is None ):
        geom.AssignSpatialReference( TARGET_SR )  
   
    # 2) transform coordinates
    else: 

        # envelope and centroid in the source coordinates
        x0_min, x0_max, y0_min, y0_max = geom.GetEnvelope() 
        x0_cnt, y0_cnt = 0.5*(x0_min+x0_max), 0.5*(y0_min+y0_max) #centroid
        
        # coordinate transformation object 
        ct = osr.CoordinateTransformation( SOURCE_SR, TARGET_SR ) 

        # perform transformation 
        geom.Transform( ct ) 

        # get envelope and centroid in the target coordinates
        x1_min, _ , _ = ct.TransformPoint( x0_min, y0_cnt ) 
        x1_max, _ , _ = ct.TransformPoint( x0_max, y0_cnt ) 
        _ , y1_min, _ = ct.TransformPoint( x0_cnt, y0_min ) 
        _ , y1_max, _ = ct.TransformPoint( x0_cnt, y0_max ) 
        x1_cnt, y1_cnt, _ = ct.TransformPoint( x0_cnt, y0_cnt ) 

        # fix the wraparroud issues 
    
        if DLXFIX : # fix the wild wraparround (unwrapp coordinates)

            # flip axis and projection span 
            xx = 0.5*(x1_min+x1_max)
            dd = BOUNDS[2]-BOUNDS[0]

            if   (x1_cnt<x1_max)and(x1_max<x1_min) : # fix needed 

                t = ig.Transfomer( lambda p: (p[0]-dd*(p[0]>xx),p[1]) )
                geom = ig.setSR(t(geom),geom.GetSpatialReference())

            elif (x1_cnt>x1_min)and(x1_max<x1_min) : # fix needed 

                t = ig.Transfomer( lambda p: (p[0]+dd*(p[0]<xx),p[1]) )
                geom = ig.setSR(t(geom),geom.GetSpatialReference())

        if DLXWRAP : # perform proper wrapparround 

            geom = ig.setSR( ig.wrapArroundDateLine(geom,BOUNDS,1), geom.GetSpatialReference()) 

        # fix the overlapping edges 
        if geom.GetGeometryName() == "MULTIPOLYGON" : 
            geom = ig.setSR( geom.UnionCascaded(), geom.GetSpatialReference() )

        geom = ig.setSR( geom.Buffer(0), geom.GetSpatialReference() )

    #--------------------------------------------------------------------------
    # export 

    try: 

        sys.stdout.write(ig.dumpGeom(geom,FORMAT)) 

    except Exception as e : 
        if DEBUG : traceback.print_exc( file=sys.stderr ) 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

