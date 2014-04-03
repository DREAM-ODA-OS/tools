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

WGS84_SR=ig.parseSR("EPSG:4326")


def map_to_wgs84( geom ):

    #--------------------------------------------------------------------------

    def between(v,(v0,v1)):
        if v0 <= v1 : 
            return ((v0<=v)and(v1>=v))
        else : #v1 > v0 
            return ((v1<=v)and(v0>=v))


    def extent_contains(x0,y0):
        return ((x0_min<=x0)and(x0_max>=x0)
             and(y0_min<=y0)and(y0_max>=y0))

    def generate_polar_section(north,east): 
        eps = 1e-9 
        y00 = 89 # max. opposite pole lat.distnace from the equator 
        x0 = 0 if east else -180
        y0 = (-y00) if north else (+y00)
        y1 = (90-eps) if north else (eps-90)  

        lr = ogr.Geometry(type=ogr.wkbLinearRing)
        for i in xrange(31) :  
            lr.AddPoint_2D(i*6+x0,y0) 
        lr.AddPoint_2D(180+x0,y1) 
        lr.AddPoint_2D(x0,y1) 
        lr.AddPoint_2D(x0,y0) 
        p = ogr.Geometry(type=ogr.wkbPolygon) 
        p.AddGeometry( lr ) 
        p.AssignSpatialReference( WGS84_SR ) 

        return p 

    def fix_dateline( g , east ) : 
        """fix the +/-180dg ambiguity of the date-line nodes""" 

        # date-line pont flipers  
        def _dlflip_east( (x,y,_) ) : 
            return ( x+360.0 if x<(-179.0) else x, y ) 

        def _dlflip_west( (x,y,_) ) : 
            return ( x-360.0 if x>(+179.0) else x, y ) 

        t = ig.Transfomer( _dlflip_east if east else _dlflip_west ) 

        return t( g ) 
        
    def transform_polar( north ):  

        # generate polygon spliting the polar geometry to halves
        s1 = generate_polar_section(north,east=True)
        s2 = generate_polar_section(north,east=False)

        # transform coordinates 
        s1.Transform(ct_rev)
        s2.Transform(ct_rev)

        # split the polar geometry to halves
        g1=geom.Intersection(s1) 
        g2=geom.Intersection(s2) 

        # transform halves to the target projection 
        g1.Transform( ct_fwd ) 
        g2.Transform( ct_fwd ) 

        # fix the dateline ambiguity 
        g1 = fix_dateline( g1 , east=True ) 
        g2 = fix_dateline( g2 , east=False ) 

        # return the unified geometry 
        return g1.Union(g2)

    #--------------------------------------------------------------------------

    sr_src = geom.GetSpatialReference() 
    sr_dst = WGS84_SR

    # coordinate transformation objects
    ct_fwd = osr.CoordinateTransformation( sr_src, sr_dst ) 
    ct_rev = osr.CoordinateTransformation( sr_dst, sr_src ) 

    # envelope and centroid in the source coordinates
    x0_min, x0_max, y0_min, y0_max = geom.GetEnvelope() 

    # centroid 
    x0_cnt, y0_cnt = 0.5*(x0_min+x0_max), 0.5*(y0_min+y0_max) 

    # get coordinates of north and south pole 
    try:
        xy0_np = ct_rev.TransformPoint( 0.0 , 90.0 )[:2]
    except RuntimeError : 
        xy0_np = None 

    try:
        xy0_sp = ct_rev.TransformPoint( 0.0 , -90.0 )[:2]
    except RuntimeError : 
        xy0_sp = None 

    # case #1 - extent contains the north pole
    if xy0_np and extent_contains(*xy0_np): 
        return ig.setSR( transform_polar( north=True ) , WGS84_SR )
    
    # case #2 - extent contains the south pole
    # check whether the extent contains the south pole
    elif xy0_sp and extent_contains(*xy0_sp): 
        return ig.setSR( transform_polar( north=False ) , WGS84_SR )

    # case #3 proceed with the date-line handling 

    # perform transformation 
    geom.Transform( ct_fwd ) 

    # get extent and centroid in the target coordinates
    x1_min, _ , _ = ct_fwd.TransformPoint( x0_min, y0_cnt ) 
    x1_max, _ , _ = ct_fwd.TransformPoint( x0_max, y0_cnt ) 
    x1_cnt, _ , _ = ct_fwd.TransformPoint( x0_cnt, y0_cnt ) 

    # fix the wild easting wrap-arround
    if not between(x1_cnt,(x1_min,x1_max)): 

        print >>sys.stderr, "UNWRAPPING NODES"

        if x1_max < x1_min : 
            # axis orientation preserved
            print >>sys.stderr, "ORIENTATION: EQUAL"
            x_cnt, x_min , x_max = x1_cnt, x1_min , x1_max 

        else : # ( x1_min < x1_max )
            print >>sys.stderr, "ORIENTATION: FLIPPED"
            # flipped axis orientation
            x_cnt, x_min , x_max = x1_cnt, x1_max , x1_min

        # point unwrapping fuctions 
        if x_cnt < x_max :
            print >>sys.stderr, "EAST to WEST"
            def _dlflip(p): return (p[0]-360*(p[0]>x_max),p[1]) 

        elif x_cnt > x_min : 
            print >>sys.stderr, "WEST to EAST"
            def _dlflip(p): return (p[0]+360*(p[0]<x_min),p[1])
            
        t = ig.Transfomer( _dlflip ) 

        geom = ig.setSR( t(geom) , WGS84_SR )
        
    # perform proper wrapparround 
    return ig.setSR(ig.wrapArroundDateLine(geom,(-180,-90,180,90),1),WGS84_SR)

#------------------------------------------------------------------------------

def usage(): 
    sys.stderr.write("\nConvert the input geometry to the WGS84 coordinates\n")
    sys.stderr.write("including the north/south pole handling for polar \n") 
    sys.stderr.write("projections and the date-line wraparround for geometries\n") 
    sys.stderr.write("crossing the date-line.\n") 
    sys.stderr.write("The result is dumped as a new geometry to stdout\n") 
    sys.stderr.write("by default in WKB format.\n") 
    sys.stderr.write("USAGE: %s <WKB|WKB> [WKT|WKB] [DEBUG]\n")

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    FORMAT="WKB"

    try: 

        INPUT  = sys.argv[1]
        NP = 2 
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if ( arg in ig.OUTPUT_FORMATS ) : FORMAT=arg # output format
                elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

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
    if SOURCE_SR is None :

        geom.AssignSpatialReference( WGS84_SR ) 
   
    # 2) transform coordinates
    else: 
        
        geom = map_to_wgs84(geom)

    #--------------------------------------------------------------------------
    # export 

    try: 

        sys.stdout.write(ig.dumpGeom(geom,FORMAT)) 

    except Exception as e : 
        if DEBUG : traceback.print_exc( file=sys.stderr ) 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

