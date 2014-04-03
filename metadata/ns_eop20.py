#------------------------------------------------------------------------------
# 
#   EOP v2.0 namespace
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

from lxml import etree 
from lxml.builder import ElementMaker
from xml_utils import nn 

import ns_om20 as om 
import ns_ows20 as ows
import ns_gml32 as gml 
import ns_swe10 as swe
import ns_xsi as xsi
import ns_xlink as xlink

#------------------------------------------------------------------------------
# schema location attribute 

#LIMB
#RADAR
#OPTICAL
#ALTIMETRIC
#ATMOSPHERIC

# SchemaTron Rules
STR="http://schemas.opengis.net/omeo/1.0/schematron_rules_for_eop.xsl"

SL= {
    "OPT" : "http://www.opengis.net/opt/2.0 http://schemas.opengis.net/omeo/1.0/opt.xsd",
    "SAR" : "http://www.opengis.net/sar/2.0 http://schemas.opengis.net/omeo/1.0/sar.xsd",
    "ATM" : "http://www.opengis.net/atm/2.0 http://schemas.opengis.net/omeo/1.0/atm.xsd",
    "ALT" : "http://www.opengis.net/alt/2.0 http://schemas.opengis.net/omeo/1.0/alt.xsd",
    "LMB" : "http://www.opengis.net/lmb/2.0 http://schemas.opengis.net/omeo/1.0/lmb.xsd",
    "SEN1" : "http://www.opengis.net/sen1/2.0 http://schemas.opengis.net/omeo/1.0/sen1.xsd",
    "SPP" : "http://www.opengis.net/ssp/2.0 http://schemas.opengis.net/omeo/1.0/ssp.xsd",
} 

def schemaLocation(profile) : return xsi.getSchemaLocation(SL[profile])

#------------------------------------------------------------------------------
# namespace 

NS="http://www.opengis.net/eop/2.0"

NS_MAP={ "eop" : NS , 
         "om"  : om.NS , 
         "ows" : ows.NS , 
         "gml" : gml.NS , 
         "swe" : swe.NS ,
         "xsi" : xsi.NS ,
         "xlink" : xlink.NS } 

#------------------------------------------------------------------------------
# add processing instructions to the root element 

def getSchematronPI() : 
    payload='type="text/xsl" href="%s"'%( STR ) 
    return etree.ProcessingInstruction( 'xml-stylesheet', payload )

#------------------------------------------------------------------------------
# element maker 

E = ElementMaker(namespace=NS,nsmap=NS_MAP) 

#------------------------------------------------------------------------------
# predefined fully qualified names 

# attributes 

# elements 

EarthObservation=nn(NS,"EarthObservation") 
EarthObservationEquipment=nn(NS,"EarthObservationEquipment") 
platform=nn(NS,"platform") 
Platform=nn(NS,"Platform") 
instrument=nn(NS,"instrument") 
Instrument=nn(NS,"Instrument") 
sensor=nn(NS,"sensor") 
Sensor=nn(NS,"Sensor") 
Footprint=nn(NS,"Footprint") 
multiExtentOf=nn(NS,"multiExtentOf") 
identifier=nn(NS,"identifier") 
acquisitionType=nn(NS,"acquisitionType") 
productType=nn(NS,"productType") 
status=nn(NS,"status") 
downlinkedTo=nn(NS,"downlinkedTo") 
acquisitionStation=nn(NS,"acquisitionStation") 
DownlinkInformation=nn(NS,"DownlinkInformation") 
processing=nn(NS,"processing") 
ProcessingInformation=nn(NS,"ProcessingInformation") 
processingCenter=nn(NS,"processingCenter") 
EarthObservationMetaData=nn(NS,"EarthObservationMetaData") 
metaDataProperty=nn(NS,"metaDataProperty")
identifier=nn(NS,"identifier") 
acquisitionType=nn(NS,"acquisitionType") 
productType=nn(NS,"productType") 
status=nn(NS,"status") 
parentIdentifier=nn(NS,"parentIdentifier") 
MaskInformation=nn(NS,"MaskInformation") 
type=nn(NS,"type") 
mask=nn(NS,"mask") 
format=nn(NS,"format") 
referenceSystemIdentifier=nn(NS,"referenceSystemIdentifier") 

#X=nn(NS,"X")

#------------------------------------------------------------------------------
# element factories 

def getMultiExtentOf( geom , srs_name="" ):
    return E.multiExtentOf(gml.setSRS(gml.getMultiSurface(geom),srs_name,2))

def getFootprint( geom ):  
    """ convert geometry to Footprint element """ 

    # TODO: orientation, centerOf 
    # check projection 

    return E.Footprint(gml.getId(),getMultiExtentOf(geom,"EPSG:4326")) 

def getBrowse( type, srs, url, subtype=None): 

    tmp = [
        E.type( type ) ,
    ]

    if subtype : 
        tmp.append(E.subType(subtype))

    ex_srs = "urn:ogc:def:crs:EPSG:6.3:%s"%( srs.split(':')[-1] )
    tmp.append( E.referenceSystemIdentifier(ex_srs,{"codeSpace":"EPSG"}) )

    tmp.append(E.fileName(ows.getServiceReference(url)))

    return E.browse( E.BrowseInformation( *tmp ) )


def getProduct( srs, url, version=None, size=None, timeliness=None ):
    
    tmp = [] 

    if srs  : 
        ex_srs = "urn:ogc:def:crs:EPSG:6.3:%s"%( srs.split(':')[-1] )
        tmp.append( E.referenceSystemIdentifier(ex_srs,{"codeSpace":"EPSG"}) )

    if version : 
        tmp.append( E.version( version ) ) 

    if size : 
        tmp.append( E.size( size ) ) 

    if timeliness : 
        tmp.append( E.timeliness( timeliness ) ) 

    tmp.append(E.fileName(ows.getServiceReference(url)))

    return E.product( E.ProductInformation( *tmp ) )


def getMask( type, format, srs=None, geom=None, url=None, post=None, subtype=None ): 

    tmp = [
        E.type( type ) ,
        E.format( format ) ,
    ]

    if subtype : 
        tmp.append(E.subType(subtype))
    if srs  : 
        ex_srs = "urn:ogc:def:crs:EPSG:6.3:%s"%( srs.split(':')[-1] )
        tmp.append( E.referenceSystemIdentifier(ex_srs,{"codeSpace":"EPSG"}) )
    # NOTE: Following is a backported feature. It does not validate
    #       with the current schemas
    if geom : tmp.append(getMultiExtentOf(geom,srs)) 
    if url  : tmp.append(E.fileName(ows.getServiceReference(url)))

    return E.mask( E.MaskInformation( *tmp ))

#------------------------------------------------------------------------------
