#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Vector Geometry Manipulations 
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
import math as m 
import numpy as np 
from osgeo import ogr ; ogr.UseExceptions()
from osgeo import osr ; osr.UseExceptions()

#-------------------------------------------------------------------------------
# spatial references 

# the most common spatial references

def createSRFromEPSG( epsg ):
    """ Create OSR Spatial Reference from EPSG number code"""
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(epsg)
    return sr 

OSR_WGS84 = createSRFromEPSG(4326) 
OSR_USP_N = createSRFromEPSG(32661)
OSR_USP_N = createSRFromEPSG(32761) 

OSR_UTM_N = tuple( createSRFromEPSG(32601+i) for i in xrange(60) ) 
OSR_UTM_S = tuple( createSRFromEPSG(32701+i) for i in xrange(60) ) 


def setSR( geom , sr ) : 
    """Assing spatial reference to a geometry and return it."""
    geom.AssignSpatialReference( sr ) 
    return geom 


def parseSR( srs , debug = False ) : 

    if debug: print >>sys.stderr, "SRS: ",srs

    if ( srs[:5] == "EPSG:" ) : 
        sr = createSRFromEPSG( int(srs.split(":")[-1]) ) 

    elif ( srs[:7] == "PROJCS[" ):  
        sr = osr.SpatialReference( srs ) 

    elif srs in ( None , "" , "NONE" ) : 
        sr = None 

    else : 
        raise ValueError("Failed to parse the spatial reference! SRS='%s'"%(srs))

    return sr 

def dumpSR( sr , delimiter = "",  debug = False ): 

    # check whether geometry has a spatial reference 
    if sr is not None : 
        an,ac = (sr.GetAuthorityName(None),sr.GetAuthorityCode(None))
        if an == "EPSG" and ac > 0 : 
            out = "%s:%s%s"%( an , ac , delimiter ) 
        else : 
            out = "%s%s"%( sr.ExportToWkt() , delimiter ) 
    else : 
        out = ""

    return out 

#-------------------------------------------------------------------------------
# File I/O subroutines  

def parseGeom( buf , debug = False ): 
    """ parse geometry from a source buffer """ 

    # parse prefix 
    if buf.startswith("EPSG:") or buf.startswith("PROJCS[") :
        srs , _ , buf  = buf.partition(';')
        sr = parseSR(srs) 
    else : 
        sr = None ; 
    
    # create the geometry 
    for loader in ( ogr.CreateGeometryFromWkb, 
                    ogr.CreateGeometryFromWkt,
                    ogr.CreateGeometryFromGML,
                    ogr.CreateGeometryFromJson ) : 
        try :
            if debug: print >>sys.stderr, "LOADER: ",loader,
            geom = loader( buf )  
        except Exception as e : 
            if debug: print >>sys.stderr, e 
            continue 

        if debug: print >>sys.stderr, "OK"
        break 

    else : 
        raise ValueError("ERROR: Failed to parse the source geometry!") 

    if sr is not None : 
        geom.AssignSpatialReference( sr ) 

    return geom 

#OUTPUT_FORMATS=("WKB","WKT","JSON","GML","KML")
OUTPUT_FORMATS=("WKB","WKT","JSON","KML")

def dumpGeom( geom , format="WKB", debug = False ): 
    """ dump geometry to a buffer possible formats are: WKB(*)|WKT|JSON|GML|KML """ 

    # dump SRS prefix 
    prefix = dumpSR( geom.GetSpatialReference() , ";" , debug ) 

    if format == "WKB" : 
        data = geom.ExportToWkb()
        if prefix : data = "%s%s"%(prefix,data)  
    elif format == "WKT" : 
        data = "%s%s\n"%(prefix,geom.ExportToWkt())
    elif format == "JSON" : 
        data = geom.ExportToJson() 
# the GML needs to be verified 
#    elif format == "GML" : 
#        data = geom.ExportToGML() 
    elif format == "KML" : 
        data = geom.ExportToKML() 
    else : 
        raise ValueError("Invalid format specification! FORMAT='%s'"%(format)) 

    return data

#-------------------------------------------------------------------------------

def wrapArroundDateLine( geom , (xmin,ymin,xmax,ymax) , nstep = 200 ) : 
    """ 
        wrap (split) geometry arround the date-line 

        nstep controls the split border segmentation ( dy = (ymax-ymin)/nstep )
    """ 

    xdif = xmax - xmin 
    step = ( ymax - ymin ) / nstep 

    x0, x1, _, _ = geom.GetEnvelope() 

    p_start = int(m.floor((x0-xmin)/xdif))
    p_stop  = int(m.ceil((x1-xmin)/xdif))

    # skip geometries falling to a regular domain
    if ( p_start == 0 ) and ( p_stop == 1 ) : 
        return geom

    # wrap-arround 
    lgeom = []
    for p in xrange(p_start,p_stop) : 
        offset = p*xdif 
        clip = getRectangle((xmin+offset,ymin,xmax+offset,ymax),step) 
        tmp  = geom.Intersection(clip) 
        tmp  = shiftGeom( tmp, (-offset,0.0) ) 
        lgeom.extend( extractPolygons(tmp) )  

    return groupPolygons( lgeom )


def wrapArroundWGS84( geom , nstep = 200 ): 
    """ 
        logitude wrap-arround of geometry in WGS84 

        nstep controls the split border segmentation ( dy = (ymax-ymin)/nstep )

        eqivalent to: 
            wrapArroundDateLine(geom,(-180.,-90.,+180.,+90.),nstep)
    """ 

    return wrapArroundDateLine( geom , (-180.,-90.,+180.,+90.) , nstep ) 

#-------------------------------------------------------------------------------

def groupPolygons( plist ):  
    """ group polygons to a multi-polygon """ 

    m = ogr.Geometry(ogr.wkbMultiPolygon)

    for p in plist : 
        m.AddGeometry( p ) 

    return m 

#-------------------------------------------------------------------------------

def ungroupMultiPolygon( mpol ): 
    """ un-group multi-polygon to a list of multi-polygons """ 

    return [ mpol.GetGeometryRef(i) for i in xrange(mpol.GetGeometryCount()) ]  


#-------------------------------------------------------------------------------

def extractPolygons( geom ): 

    if geom.GetGeometryName() == "GEOMETRYCOLLECTION" :

        l = []
        for i in xrange(mpol.GetGeometryCount()): 
            l.extend(extractPolygons(mpol.GetGeometryRef(i)))
        return l 

    elif geom.GetGeometryName() == "MULTIPOLYGON" : 

        return ungroupMultiPolygon() 

    elif geom.GetGeometryName() == "POLYGON" : 

        return [ geom ]

    else : 

        return []

#-------------------------------------------------------------------------------

def getRectangle( (x_min,y_min,x_max,y_max) , step = 1.0 ) : 
    """ Create rectangle polygon with the edges broken to smaller 
        line segments. The size of the lenght line segments is approx. 
        the value of the step parameter
    """ 

    # stepping 
    n_x = max(1,int(m.ceil((max(x_min,x_max)-min(x_min,x_max))/float(step)))) 
    n_y = max(1,int(m.ceil((max(y_min,y_max)-min(y_min,y_max))/float(step)))) 

    lx = []
    ly = [] 

    # generate polygon
    lx.append( np.linspace(x_min,x_max,n_x,False) ) 
    ly.append( np.ones(n_x)*y_min ) 

    lx.append( np.ones(n_y)*x_max ) 
    ly.append( np.linspace(y_min,y_max,n_y,False) ) 
    
    lx.append( np.linspace(x_max,x_min,n_x,False) ) 
    ly.append( np.ones(n_x)*y_max ) 

    lx.append( np.ones(n_y)*x_min ) 
    ly.append( np.linspace(y_max,y_min,n_y,False) ) 

    # close ring 
    lx.append( np.array([x_min]) ) 
    ly.append( np.array([y_min]) ) 

    # concatenate arrays 
    x = np.concatenate( lx ) 
    y = np.concatenate( ly )

    # convert to polygon
    r = ogr.Geometry(ogr.wkbLinearRing)

    for xx,yy in zip(x,y) : 
        r.AddPoint_2D( xx , yy ) 

    p = ogr.Geometry(ogr.wkbPolygon)
    p.AddGeometry( r ) 

    return p 

#------------------------------------------------------------------------------

def shiftGeom( g , (dx,dy) ) : 
    """ shift geometry by a given offset """ 

    def _shift( p , (dx,dy) ) : 
        return ( p[0]+dx, p[1]+dy ) 

    t = Transfomer( _shift ) 

    return t( g, (dx,dy) ) 

#------------------------------------------------------------------------------

class Transfomer: 

    def __init__( self , f ): 
        self.__f = f 

    def __call__( self, g0, *prm , **kw ) : 
        return self._geometry( g0 , *prm, **kw ) 

    def _geometry( self, g0, *prm, **kw ): 
        #print g0.GetGeometryName(), g0.GetGeometryType()
        if g0.GetGeometryName() == "MULTIPOLYGON" : 
            return self._multi_polygon( g0 , *prm, **kw )

        elif g0.GetGeometryName() == "POLYGON" : 
            return self._polygon( g0 , *prm, **kw )

        elif g0.GetGeometryName() == "LINEARRING" : 
            return self._linear_ring( g0 , *prm, **kw )

        else : 
            return None


    def _linear_ring( self, r0 , *prm, **kw ): 
        #print r0.GetGeometryName(), r0.GetGeometryType()
        if r0.GetGeometryName() != "LINEARRING" : return None 
        r1 = ogr.Geometry(ogr.wkbLinearRing)
        for i in xrange( r0.GetPointCount() ): 
            rv = (self.__f)( r0.GetPoint(i) , *prm , **kw ) 
            if rv is not None : r1.AddPoint(*rv) 
        return r1 
        
    def _polygon( self, p0, *prm, **kw ): 
        #print p0.GetGeometryName(), p0.GetGeometryType()
        if p0.GetGeometryName() != "POLYGON" : return None 
        p1 = ogr.Geometry(ogr.wkbPolygon)
        for i in xrange( p0.GetGeometryCount() ) : 
            rv = self._linear_ring( p0.GetGeometryRef(i), *prm, **kw ) 
            if rv is not None : p1.AddGeometry(rv) 
        return p1 

    def _multi_polygon( self, m0, *prm, **kw ): 
        #print m0.GetGeometryName(), m0.GetGeometryType()
        if p0.GetGeometryName() != "MULTIPOLYGON" : return None 
        m1 = ogr.Geometry(ogr.wkbMultiPolygon)
        for i in xrange( m0.GetGeometryCount() ) :
            rv = self._polygon( p0.GetGeometryRef(i), *prm, **kw ) 
            if rv is not None : m1.AddGeometry(p1) 
        return m1 


