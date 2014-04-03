#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Extract geometry outline from a raster image. 
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
import img_geom as ig 
#import numpy as np 
#import math as m 
from osgeo import ogr ; ogr.UseExceptions() 
from osgeo import osr ; ogr.UseExceptions() 
from osgeo import gdal ; gdal.UseExceptions() 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    FORMAT="WKB"
    OPERATOR="EQL"
    OPERATORS=("EQL","AND","ALL")

    try: 

        INPUT = sys.argv[1]
        VALUE = int( sys.argv[2] ) 
        NP = 2 
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if   ( arg in ig.OUTPUT_FORMATS ) : FORMAT=arg # output format
                elif ( arg in OPERATORS ) : OPERATOR = arg # match operator 
                elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

    except IndexError : 
        
        sys.stderr.write("ERROR: Not enough input arguments!\n") 
        sys.stderr.write("\nExtract single colour raster patches outline as gemetry.\n") 
        sys.stderr.write("The unsipmified geometry is dumped to stdout,\n") 
        sys.stderr.write("by default in WKB format.\n\n") 
        sys.stderr.write("USAGE: %s <input image> <data-value> [WKT|WKB*] [AND|EQL*] [DEBUG]\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------

#    # open input image 
#    imi = ib.ImgFileIn( INPUT ) 
#
#    # check input image 
#
#    if imi.sz > 1 : 
#        sys.stderr.write("ERROR: Multiband images not supported!\n") 
#        sys.exit(1) 
#
#    if imi.dtype not in ('uint8','int8','uint16','int16','uint32','int32') : 
#        sys.stderr.write("ERROR: Unsupported image data type '%s'!\n"%imi.dtype) 
#        sys.exit(1) 
#
#    # get gdal dataset 
#    ds = imi.ds 
#
#    # has geocoding?
#    if imi.ds.GetProjection() : 
#        sr = osr.SpatialReference( imi.ds.GetProjection() ) 
#    else : 
#        sr = None 
#
#    # create virtual in-memory OGR datasource 
#    vds = ogr.GetDriverByName('Memory').CreateDataSource('out')
#
#    # create layer 
#    ly = vds.CreateLayer( 'footprint', None, ogr.wkbPolygon )
#
#    # add feature to hold the mask value 
#    ly.CreateField( ogr.FieldDefn( 'DN', ogr.OFTInteger ) ) 

    ds = ogr.Open( INPUT )

    ly = ds.GetLayer(0)

    sr = ly.GetSpatialRef()
    
    if sr is not None : sr.AutoIdentifyEPSG()

    #--------------------------------------------------------------------------

    # run the extract vector outlines 
    # NOTE: The polygons are already in the projected coordinates! 
#    res = gdal.Polygonize( ds.GetRasterBand(1), None, ly , 0 ) 

    # get list of features 
    lf = [ ly.GetFeature(i) for i in xrange( ly.GetFeatureCount() ) ]

    if DEBUG: 
        print >>sys.stderr,"Number of features: " , ly.GetFeatureCount()
        for i,f in enumerate( lf ) : 
            print >>sys.stderr,"#%2.2i\t%s\tDN=%d"%( i , str(f) , f.GetFieldAsInteger(0) ) 

    # extract features matching the selection criteria 
    if OPERATOR == "EQL" : # ( V == DN )
        _filter = lambda f: ( VALUE == f.GetFieldAsInteger(0) ) 
    elif OPERATOR == "AND" : # ( 0 != (V&DN) )  
        _filter = lambda f: ( 0 != (VALUE&f.GetFieldAsInteger(0)) ) 
    elif OPERATOR == "ALL" : # ( 0 != (V&DN) )  
        _filter = lambda f: True
    else : 
        raise RuntimeError( "Invalid operator! OPERATOR=%s"%OPERATOR ) 

    lf = filter( _filter , lf ) ; del _filter 

    if DEBUG: 
        print >>sys.stderr,"Number of filtered features: " , len(lf)  
        for i,f in enumerate( lf ) : 
            print >>sys.stderr,"#%2.2i\t%s\tDN=%d"%( i , str(f) , f.GetFieldAsInteger(0) ) 

    # collect set of matched digital numbers  
    dn_set = set() 
    for f in lf : dn_set.add( f.GetFieldAsInteger(0) ) 

    # extract geometries 
    lg = map( lambda f: f.GetGeometryRef() , lf ) 

    if DEBUG: 
        print >>sys.stderr,"Number of initial geometries: " , len(lf)  
        for i,g in enumerate( lg ) : 
            print >>sys.stderr,"#%2.2i\t"%i, g.GetGeometryType(), g.GetGeometryName(), g.Area()

    # remove empty geometries 
    lg = filter( lambda g: not g.IsEmpty() , lg ) 

    if DEBUG: 
        print >>sys.stderr,"Number of simplified non-empty geometries: " , len(lf)  
        for i,g in enumerate( lg ) : 
            print >>sys.stderr,"#%2.2i\t"%i, g.GetGeometryType(), g.GetGeometryName(), g.Area()

    # NOTE: no geometry optiomisations performed 

    #--------------------------------------------------------------------------
    # pack the individual geometries 

    # NOTE: At this point we assume that all geometries are polygons 
    #       and thus they can be joined to a multi-polygon.
   
    if ( len(lg)  > 1 ) : # mutiple polygons

        geom = ig.groupPolygons( lg )

        # perform union if mutiple DN matched
        if len(dn_set) > 0 : 
            geom = geom.UnionCascaded()
    
    elif ( len(lg) == 1 ) : # single polygon

        geom = lg[0]

    else : # no match -> empty polygon 

        geom = ogr.Geometry( ogr.wkbPolygon ) 
    
    # assign spatial reference 
    geom.AssignSpatialReference( sr )  

    #--------------------------------------------------------------------------
    # export 

    try: 

        sys.stdout.write(ig.dumpGeom(geom,FORMAT)) 

    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)
