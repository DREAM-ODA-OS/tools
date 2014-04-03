#------------------------------------------------------------------------------
# 
#   GML v3.2 namespace
#
# Project: XML Metadata Handling 
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

# swapped EPSG codes 
from epsg_swapped_axes import EPSG_AXES_REVERSED 

from lxml.builder import ElementMaker
from xml_utils import nn 
import uuid 

#------------------------------------------------------------------------------
# get random GML identifier 
def getRandomId() : return { ID : "uuid_%s"%( uuid.uuid4() ) }  

def getId(id=None) : 
    if id is None :
        return getRandomId() 
    else : 
        return { ID : str(id) } 

#------------------------------------------------------------------------------
# namespace 

NS="http://www.opengis.net/gml/3.2"
NS_MAP={ "gml" : NS }

#------------------------------------------------------------------------------
# element maker 

E = ElementMaker(namespace=NS,nsmap=NS_MAP) 

#------------------------------------------------------------------------------
# predefined fully qualified names 

# attributes 
id=nn(NS,"id") ; ID=id 
srsName=nn(None,"srsName")
srsName=nn(None,"srsDimension")
axisLabels=nn(None,"axisLabels")
uomLabels=nn(None,"uomLabels")

# elements 
TimeInstant     = nn(NS,"TimeInstant") 
TimePeriod      = nn(NS,"TimePeriod") 
MultiSurface    = nn(NS,"MultiSurface") 
Polygon         = nn(NS,"Polygon") 
LinearRing      = nn(NS,"LinearRing") 

beginPosition   = nn(NS,"beginPosition") 
endPosition     = nn(NS,"endPosition") 
timePosition    = nn(NS,"timePosition") 
surfaceMember   = nn(NS,"surfaceMember") 
exterior        = nn(NS,"exterior") 
interior        = nn(NS,"interior") 
posList         = nn(NS,"posList") 

#X=nn(NS,"X") 

#------------------------------------------------------------------------------
# element factories 

def getTimeInstant( time , id = None ) : 
    return E.TimeInstant( getId(id), E.timePosition( str(time) ) )

def getTimePeriod( begin , end , id = None ) : 
    return E.TimePeriod( getId(id), E.beginPosition( str(begin) ) ,
                                    E.endPosition( str(end) ) ) 

def getTime( begin, end = None , id = None ): 
    if end is None : 
        return getTimeInstant( begin, id ) 
    else : 
        return getTimePeriod( begin , end , id )

#------------------------------------------------------------------------------

def setSRSName( e , srs_name ): 
    if srs_name : e.set("srsName",str(srs_name))
    return e 

def setSRSDimension( e , srs_dim ): 
    srs_dim = int( srs_dim ) 
    if ( srs_dim > 0 ) : e.set("srsDimension",str(srs_dim))
    return e 


def setSRS( e , srs_name , srs_dim = None ) : 
    
    return setSRSDimension( setSRSName( e , srs_name ) , srs_dim ) 

def getPointList2D( geom , sr = None ) : 

    if sr is None : 
        sr = geom.GetSpatialReference() 
    
    # check the spatial reference, adjust format and swap coordinates if needed 

    if sr is None : 
        sr = geom.GetSpatialReference() 

    # check if geographic of projected 
    if ( sr is not None ) and ( sr.IsProjected() ): 
        # setting precision to meters
        _frm = "%.2f %.2f"
    else : 
        # setting precision to degrees
        _frm = "%.8f %.8f"

    # check whether swap coordinates or not 
    _cswap = ( sr is not None ) and ( sr.GetAuthorityName(None) == "EPSG" ) \
                and ( int( sr.GetAuthorityCode(None) ) in EPSG_AXES_REVERSED ) 

    if _cswap : 
        _str = lambda p: _frm%( p[1], p[0] ) 
    else : 
        _str = lambda p: _frm%( p[0], p[1] ) 

    pl = " ".join(_str(geom.GetPoint(i)) for i in xrange(geom.GetPointCount())) 

    return E.posList(pl) 


def getLinearRing( geom , sr = None ) : 

    if sr is None : 
        sr = geom.GetSpatialReference() 

    if geom.GetGeometryName() != "LINEARRING" : 
        raise ValueError( "Invalid input: %s" % geom ) 

    return E.LinearRing( getPointList2D( geom , sr ) )


def getPolygon( geom , sr = None ) : 

    if sr is None : 
        sr = geom.GetSpatialReference() 

    if geom.GetGeometryName() != "POLYGON" : 
        raise ValueError( "Invalid input: %s" % geom ) 
        
    l = [ getId() ] 
    cnt = 0 
    for i in xrange(geom.GetGeometryCount()) :  
        g = geom.GetGeometryRef(i) 
        if g.GetGeometryName() == "LINEARRING" :
            e =  E.exterior if cnt == 0 else E.interior 
            l.append( e( getLinearRing(g,sr) ) ) 
            cnt += 1 

    return E.Polygon( *l )


def getMultiSurface( geom , sr = None ) : 

    if sr is None : 
        sr = geom.GetSpatialReference() 

    l = [ getId() ] 

    if geom.GetGeometryName() == "POLYGON" : 

        l.append( E.surfaceMember( getPolygon(geom,sr) ) ) 

    elif geom.GetGeometryName() == "MULTIPOLYGON" : 

        for i in xrange(geom.GetGeometryCount()) :  
            g = geom.GetGeometryRef(i) 
            if g.GetGeometryName() == "POLYGON" :
                l.append( E.surfaceMember( getPolygon(g,sr) ) ) 

    # geometry collection is meant to represent empty geometry
    # non-empty collections are not supported
    elif geom.GetGeometryName() == "GEOMETRYCOLLECTION" :
        if 0 != geom.GetGeometryCount() :
            raise ValueError( "Invalid input: %s" % geom )
        pass

    else:
        raise ValueError( "Invalid input: %s" % geom )

    return E.MultiSurface( *l )


def getSurface( geom ) : 

    if geom.GetGeometryName() == "POLYGON" : 
        return getPolygon( geom )  

    elif geom.GetGeometryName() == "MULTIPOLYGON" : 
        return getMultiSurface( geom )  

    # geometry collection is meant to represent empty geometry
    # non-empty collections are not supported
    elif geom.GetGeometryName() == "GEOMETRYCOLLECTION" :
        return getMultiSurface( geom )
    
    else :
        raise ValueError( "Invalid input: %s" % geom ) 
