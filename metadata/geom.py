#------------------------------------------------------------------------------
# 
#   geometry utilities 
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

#def setSR( geom , sr ) : 
#    """Assing spatial reference to a geometry and return it."""
#    geom.AssignSpatialReference( sr ) 
#    return geom 

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

#-------------------------------------------------------------------------------

def dumpSR( sr ): 

    # check whether geometry has a spatial reference 
    if sr is not None : 
        an,ac = (sr.GetAuthorityName(None),sr.GetAuthorityCode(None))
        if an == "EPSG" and ac > 0 : 
            #out = "%s:%s%s"%( an , ac , delimiter ) 
            out = "urn:ogc:def:crs:%s::%s"%( an , ac ) 
        else : 
            print >>sys.stderr , "WARNING: Unsupported projection! %s"%(sr.ExportToWkt())
            out = ""
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

#-------------------------------------------------------------------------------
