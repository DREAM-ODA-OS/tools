#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Simplify geometry 
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

def simplify_polygon( g0 , gslen ): 
    
    # NOTE: The Geometry.GetGeometryType() method is not 
    #       reliable. To get the true geometry type always 
    #       use string names returned by 
    #       Geometry.GetGeometryName() method. 
    # -----------------------------------------------
    if g0.GetGeometryName() == "LINEARRING" :
        
        # note simplyfication works on polygons only 
        pg0 = ogr.Geometry(ogr.wkbPolygon)
        pg0.AddGeometry( g0 ) 

        # simplify lienear ring 
        pg1 = pg0.Simplify( gslen )

        rl = [] 
    
        # parse the output and decompose it to linear rings
        if pg1.IsEmpty() : 
            pass 

        elif pg1.GetGeometryName() == "POLYGON" : 
            rl.append(pg1.GetGeometryRef(0).Clone()) #clone to avoid segfaults

        elif pg1.GetGeometryName() == "MULTIPOLYGON" :
            for i in xrange(pg1.GetGeometryCount()) :
                p = pg1.GetGeometryRef(1) 
                rl.append(p.GetGeometryRef(0).Clone()) #clone to avoid segfaults

        else : 
            raise ValueError("Unexpected geometry %s"%(pg1.GetGeometryName())) 

        return rl

    # -----------------------------------------------
    elif g0.GetGeometryName() == "POLYGON" :
    
        pg = ogr.Geometry(ogr.wkbPolygon)

        for i in xrange(g0.GetGeometryCount()) : 

            g = g0.GetGeometryRef(i)
    
            # ignore anything but the linear rings  
            if g.GetGeometryName() != "LINEARRING" : 
                continue 

            # simplify linear ring  
            for lr in simplify_polygon( g, gslen ) : 

                # if non-empty add to polygon 
                if not lr.IsEmpty() : 
                    pg.AddGeometry( lr ) 

        return pg

    # -----------------------------------------------
    elif g0.GetGeometryName() == "MULTIPOLYGON" :
        
        mp = ogr.Geometry(ogr.wkbMultiPolygon)

        for i in xrange(g0.GetGeometryCount()) : 

            g = g0.GetGeometryRef(i)
            
            # ignore anything but the polygons 
            if g.GetGeometryName() != "POLYGON" : 
                continue 

            # simplify polygon
            pg = simplify_polygon( g, gslen ) 
            
            # if non-empty add to multi-polygon 
            if not pg.IsEmpty() : 
                mp.AddGeometry( pg ) 

        return mp 
            
    # -----------------------------------------------
    else :

        # ignore anything else 
        return g0 
        
#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    FORMAT="WKB"

    try: 

        INPUT = sys.argv[1]
        GSLEN = float( sys.argv[2] ) # geometry simplification parameter
        NP = 2 
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if ( arg in ig.OUTPUT_FORMATS ) : FORMAT=arg # output format
                elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

    except IndexError : 
        
        sys.stderr.write("ERROR: Not enough input arguments!\n") 
        sys.stderr.write("\nSimplify geometry and dump new geometry to stdout\n") 
        sys.stderr.write("by default in WKB format.\n\n") 
        sys.stderr.write("USAGE: %s <WKB|WKB> <prm.simpl.> [WKT|WKB] [DEBUG]\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------
    # import 

    # open input geometry file 
    fin = sys.stdin if INPUT == "-" else open(INPUT) 

    # read the data 
    try: 
        geom = ig.parseGeom( fin.read() , DEBUG ) 
    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # simplify geometry 

    geom = ig.setSR(simplify_polygon(geom,GSLEN),geom.GetSpatialReference())

    #--------------------------------------------------------------------------
    # export 

    try: 

        sys.stdout.write(ig.dumpGeom(geom,FORMAT)) 

    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)
