#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Convert geometry to GML (GDAL/OGR FeatureCollection) 
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
import re 
import os.path 
from lxml import etree as et
#import img_geom as ig 
#from osgeo import ogr ; ogr.UseExceptions() 
#from osgeo import osr ; ogr.UseExceptions() 
#from osgeo import gdal ; gdal.UseExceptions() 

import geom as ig 

#------------------------------------------------------------------------------
_gerexURL = re.compile(r"^http://www.opengis.net/def/crs/epsg/\d+\.?\d*/(\d+)$",re.IGNORECASE)
_gerexURN = re.compile(r"^urn:ogc:def:crs:epsg:\d*\.?\d*:(\d+)$",re.IGNORECASE) 
_gerexShortCode = re.compile(r"^epsg:(\d+)$",re.IGNORECASE) 

def fixSRSNames( e0 ) : 
    """ fix the SRS name to the URN format well understood by GDAL """

    for e in e0.getiterator()  : 
        
        srs = e.get("srsName")

        if srs is None : continue 

        m = _gerexURL.match( srs )
        if m is not None : 
            e.set("srsName","urn:ogc:def:crs:EPSG::%s"%(m.group(1)))
            continue  

        m = _gerexShortCode.match( srs ) 
        if m is not None : 
            e.set("srsName","urn:ogc:def:crs:EPSG::%s"%(m.group(1)))
            continue  

    return e0 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    PRETTY=False
    FNAME="Geometry"
    SRS=None

    try: 

        INPUT   = sys.argv[1]

        NP = 2
        for arg in sys.argv[NP:] : 
            if ( arg == "DEBUG" ) : DEBUG = True # dump debuging output
            elif ( arg == "PRETTY" ) : PRETTY = True # pretty XML print 
            elif ( arg.startswith("SRS=") ) :  
                SRS=arg.partition("=")[2]
            else : 
                FNAME = arg

    except IndexError : 
        
        sys.stderr.write("ERROR: Not enough input arguments!\n") 
        sys.stderr.write("\nConvert geometry to GML (OGR Feature Collection)\n") 
        sys.stderr.write("and dump it to the standard output.\n") 
        sys.stderr.write("NOTE: Currently limitted to gml:MultiSurface only.\n") 
        sys.stderr.write("USAGE: %s <geom> [<feature_name>] [PRETTY][DEBUG]\n"%EXENAME) 
        sys.exit(1) 

    if DEBUG: 
        print >>sys.stderr, "INPUT:      ",INPUT
        print >>sys.stderr, "PRETTY:     ",PRETTY
        
    #--------------------------------------------------------------------------
    # loading geometries 

    # read the data 
    try: 
        # open input geometry file 
        fin = sys.stdin if ( INPUT == "-" ) else open(INPUT) 

        # read the data 
        geom = ig.parseGeom( fin.read() , DEBUG ) 

        del fin

    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # create the output XML document 

    # import required namespaces 
    import ns_ogr   as ogr 
    import ns_gml32 as gml 

    srs_name = ig.dumpSR( geom.GetSpatialReference() )
    xml = gml.setSRS( gml.getMultiSurface( geom ) , srs_name , 2 ) 

    # create feature element 
    tmp = et.Element(FNAME)
    tmp.append( xml ) 
    xml = tmp 

    xml = ogr.getFeatureCollection( fixSRSNames( tmp ) ) 

    # print the output 
    print et.tostring( xml, pretty_print=PRETTY, xml_declaration=True, encoding="utf-8") 
