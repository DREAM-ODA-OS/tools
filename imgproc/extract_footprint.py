#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   This tool tries to extract polygon from a raster mask. 
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
import math as m 
from osgeo import ogr ; ogr.UseExceptions() 
from osgeo import osr ; ogr.UseExceptions() 
from osgeo import gdal ; gdal.UseExceptions() 

#------------------------------------------------------------------------------

from geom_simplify import simplify_polygon

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    # target spatial reference 
    sr = osr.SpatialReference() ; sr. ImportFromEPSG(4326)

    exename = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    WKT = False 
    JSON = False 

    try: 

        INPUT = sys.argv[1]
        VALUE = int( sys.argv[2] ) 
        GSLEN = float( sys.argv[3] ) # geometry simplification 
        SGLEN = float( sys.argv[4] ) # segmentization parameter
        if len(sys.argv) > 5 : 
            for arg in sys.argv[5:] : 
                if ( arg == "WKT" ) : WKT = True # produce output in WKT format
                if ( arg == "DEBUG" ) : 
                    DEBUG = True # produce to request DEBUGING output

        #OUTPUT = sys.argv[2]
        #THRSH  = max(0.0,min(1.0,float(sys.argv[3])))
        #WHS  = max(1,int(sys.argv[4] )) 
        #NREP = max(1,int(sys.argv[5] ))

    except IndexError : 
        
        sys.stderr.write("Not enough input arguments!\n") 
        sys.stderr.write("USAGE: %s <input image> <data-value> <prm.simpl.> <max.seg.len>\n"%exename) 
        #sys.stderr.write("EXAMPLE: %s mask_in.tif mask_out.tif 0.5 1 20\n"%exename) 
        sys.exit(1) 

    #--------------------------------------------------------------------------

    # open input image 
    imi = ib.ImgFileIn( INPUT ) 

    # check input image 

    if imi.sz > 1 : 
        sys.stderr.write("ERROR: Multiband images not supported!\n") 
        sys.exit(1) 

    if imi.dtype not in ('uint8','int8','uint16','int16','uint32','int32') : 
        sys.stderr.write("ERROR: Unsupported image data type '%s'!\n"%imi.dtype) 
        sys.exit(1) 

    # get gdal dataset 
    ds = imi.ds 

    # create virtual in-memory OGR datasource 
    vds = ogr.GetDriverByName('Memory').CreateDataSource('out')

    # create layer 
    ly = vds.CreateLayer( 'footprint', None, ogr.wkbPolygon )

    # add feature to hold the mask value 
    ly.CreateField( ogr.FieldDefn( 'DN', ogr.OFTInteger ) ) 

    #--------------------------------------------------------------------------

    # run the extract vector outlines 
    # NOTE: The polygons are already in the projected coordinates! 
    res = gdal.Polygonize( ds.GetRasterBand(1), None, ly , 0 ) 

    # get list of features 
    lf = [ ly.GetFeature(i) for i in xrange( ly.GetFeatureCount() ) ]

    if DEBUG: 
        print "Number of features: " , ly.GetFeatureCount()
        for i,f in enumerate( lf ) : 
            print "#%2.2i\t%s\tDN=%d"%( i , str(f) , f.GetFieldAsInteger(0) ) 

    # extract features matching the selection criteria 
    lf = filter( lambda f: ( VALUE == f.GetFieldAsInteger(0) ) , lf )

    if DEBUG: 
        print "Number of filtered features: " , len(lf)  
        for i,f in enumerate( lf ) : 
            print "#%2.2i\t%s\tDN=%d"%( i , str(f) , f.GetFieldAsInteger(0) ) 

    # extract geometries 
    lg = map( lambda f: f.GetGeometryRef() , lf ) 

    if DEBUG: 
        print "Number of initial geometries: " , len(lf)  
        for i,g in enumerate( lg ) : 
            print "#%2.2i\t"%i, g.GetGeometryType(), g.GetGeometryName(), g.Area()

    # simplify geometries 
    lg = map( lambda g: simplify_polygon( g, GSLEN ) , lg ) 

    if DEBUG: 
        print "Number of simplified geometries: " , len(lf)  
        for i,g in enumerate( lg ) : 
            print "#%2.2i\t"%i, g.GetGeometryType(), g.GetGeometryName(), g.Area()

    # remove empty geometries 
    lg = filter( lambda g: not g.IsEmpty() , lg ) 

    if DEBUG: 
        print "Number of simplified non-empty geometries: " , len(lf)  
        for i,g in enumerate( lg ) : 
            print "#%2.2i\t"%i, g.GetGeometryType(), g.GetGeometryName(), g.Area()

    # segmetize geometries 
    for g in lg : g.Segmentize( SGLEN ) 

    #--------------------------------------------------------------------------

    # unpack multi-polygons to sub-polygons 
    lp = [] 

    for g in lg : 

        # transform geometry to targed SRS 
        g.AssignSpatialReference(osr.SpatialReference(ds.GetProjection()))
        g.TransformTo( sr ) 

        if g.GetGeometryName() == "POLYGON" : 
            
            lp.append( g ) 

        elif g.GetGeometryName() == "MUTIPOLYGON"  : 

            # extract sub-geometries 
            for i in xrange( g.GetGeometryCount() ) : 

                # sub-geom
                sg = g.GetGeometryRef(i)

                if sg.GetGeometryName() == "POLYGON" :

                    lp.append( sg ) 
                else : 
                    raise Warning("Ignoring unexpected %s geometry within "
                                    "a MULTIPOLYGON!"%g.GetGeometryName())
        else: 
            raise Warning("Ignoring unexpected %s geometry!"%g.GetGeometryName())
            
    #--------------------------------------------------------------------------
    # unpack polygons to line-rings - outer ring is always the first one 

    lrl = [] # list of ring lists  

    for j,p in enumerate(lp) : 

        if p.GetGeometryCount() < 1 : 
            raise Warning("Polygon without any linear ring!")  
            continue # go for next polygon 

        # assuming the outer ring is always the first 

        lr = [] # list of rings belonging to a single polygon

        for i in xrange(p.GetGeometryCount()) :

            # extract linear ring 
            r = p.GetGeometryRef(i)

            # extrac (x,y) points 
            tmp = np.array( r.GetPoints() ) 

            lr.append( (tmp[:,0],tmp[:,1]) ) 
            
        lrl.append( lr ) 

    #--------------------------------------------------------------------------
    # output 

    format = "%.6f %.6f"

    #printWKT = True
    printWKT = WKT 

    if printWKT : 

        polygons=[] 

        for p in lrl : 
            
            rings = [] 

            for rx,ry in p : 

                rings.append("(%s)"%(", ".join(format%(x,y)for(x,y)in zip(rx,ry)))) 

            polygons.append("(%s)"%(", ".join(rings)))
        
        if len( lrl ) == 1 :  
        
            print "POLYGON%s"%( polygons[0] ) 

        else : 
            
            print "MULTIPOLYGON(%s)"%( ", ".join(polygons) ) 

    else : # printGML 

        gml = [] 
        
        gml.append('<gml:MultiSurface gml:id="multisurface_IDENTIFIER" srsName="EPSG:4326">') 

        for i,p in enumerate(lrl) : 
            
            gml.append('<gml:surfaceMember>')
            gml.append('<gml:Polygon gml:id="polygon_IDENTIFIER_%d">'%i)

            for j,(rx,ry) in enumerate(p) : 

                if j > 0 : 
                    gml.append('<gml:interior>') 
                else: 
                    gml.append('<gml:exterior>') 

                gml.append('<gml:LinearRing>') 
                gml.append('<gml:posList>')

                gml.append(" ".join( format%(y,x) for (x,y) in zip(rx,ry) ))

                gml.append('</gml:posList>')
                gml.append('</gml:LinearRing>')

                if j > 0 : 
                    gml.append('</gml:interior>') 
                else: 
                    gml.append('</gml:exterior>') 

            gml.append('</gml:Polygon>')
            gml.append('</gml:surfaceMember>')

        gml.append('</gml:MultiSurface>') 

        print "\n".join( gml ) 
