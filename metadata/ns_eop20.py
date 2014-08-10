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
import geom as ig

import ns_om20 as ns_om
import ns_ows20 as ns_ows
import ns_gml32 as ns_gml
import ns_swe10 as ns_swe
import ns_xsi as ns_xsi
import ns_xlink as ns_xlink

#------------------------------------------------------------------------------
# schema location attribute

#LIMB
#RADAR
#OPTICAL
#ALTIMETRIC
#ATMOSPHERIC

# SchemaTron Rules
STR = "http://schemas.opengis.net/omeo/1.0/schematron_rules_for_eop.xsl"

SL = {
    "OPT": "http://www.opengis.net/opt/2.0 http://schemas.opengis.net/omeo/1.0/opt.xsd",
    "SAR": "http://www.opengis.net/sar/2.0 http://schemas.opengis.net/omeo/1.0/sar.xsd",
    "ATM": "http://www.opengis.net/atm/2.0 http://schemas.opengis.net/omeo/1.0/atm.xsd",
    "ALT": "http://www.opengis.net/alt/2.0 http://schemas.opengis.net/omeo/1.0/alt.xsd",
    "LMB": "http://www.opengis.net/lmb/2.0 http://schemas.opengis.net/omeo/1.0/lmb.xsd",
    "SEN1": "http://www.opengis.net/sen1/2.0 http://schemas.opengis.net/omeo/1.0/sen1.xsd",
    "SPP": "http://www.opengis.net/ssp/2.0 http://schemas.opengis.net/omeo/1.0/ssp.xsd",
}

def getSchemaLocation(profile):
    return ns_xsi.getSchemaLocation(SL[profile])

#------------------------------------------------------------------------------
# namespace

NS = "http://www.opengis.net/eop/2.0"

NS_MAP = {
         "eop": NS,
         "om": ns_om.NS,
         "ows": ns_ows.NS,
         "gml": ns_gml.NS,
         "swe": ns_swe.NS,
         "xsi": ns_xsi.NS,
         "xlink": ns_xlink.NS
}

#------------------------------------------------------------------------------
# add processing instructions to the root element

def getSchematronPI():
    payload = 'type="text/xsl" href="%s"'%(STR)
    return etree.ProcessingInstruction('xml-stylesheet', payload)

#------------------------------------------------------------------------------
# element maker

E = ElementMaker(namespace=NS, nsmap=NS_MAP)

#------------------------------------------------------------------------------
# predefined fully qualified names

# attributes

# elements

EarthObservation = nn(NS, "EarthObservation")
EarthObservationEquipment = nn(NS, "EarthObservationEquipment")
platform = nn(NS, "platform")
Platform = nn(NS, "Platform")
instrument = nn(NS, "instrument")
Instrument = nn(NS, "Instrument")
sensor = nn(NS, "sensor")
Sensor = nn(NS, "Sensor")
Footprint = nn(NS, "Footprint")
multiExtentOf = nn(NS, "multiExtentOf")
identifier = nn(NS, "identifier")
acquisitionType = nn(NS, "acquisitionType")
productType = nn(NS, "productType")
status = nn(NS, "status")
downlinkedTo = nn(NS, "downlinkedTo")
acquisitionStation = nn(NS, "acquisitionStation")
DownlinkInformation = nn(NS, "DownlinkInformation")
processing = nn(NS, "processing")
ProcessingInformation = nn(NS, "ProcessingInformation")
processingCenter = nn(NS, "processingCenter")
EarthObservationMetaData = nn(NS, "EarthObservationMetaData")
metaDataProperty = nn(NS, "metaDataProperty")
identifier = nn(NS, "identifier")
acquisitionType = nn(NS, "acquisitionType")
productType = nn(NS, "productType")
status = nn(NS, "status")
parentIdentifier = nn(NS, "parentIdentifier")
MaskInformation = nn(NS, "MaskInformation")
type = nn(NS, "type")
mask = nn(NS, "mask")
format = nn(NS, "format")
referenceSystemIdentifier = nn(NS, "referenceSystemIdentifier")
codeSpace = nn(NS, "codeSpace")

#X=nn(NS, "X")

#------------------------------------------------------------------------------
# element factories

def getMultiExtentOf(geom, srs_name=""):
    return E.multiExtentOf(ns_gml.setSRS(ns_gml.getMultiSurface(geom), srs_name, 2))

def getCenterOf(geom, srs_name=""):
    return E.centerOf(ns_gml.setSRS(ns_gml.getPoint(geom), srs_name, 2))

def getFootprint(outline, centroid=None):
    """ convert geometry to Footprint element """
    # TODO: orientation,
    # TODO: check projection
    elm = E.Footprint(ns_gml.getId(), getMultiExtentOf(outline, "EPSG:4326"))
    if centroid is not None:
        elm.append(getCenterOf(centroid, "EPSG:4326"))
    return elm


def getBrowse(type, srs, url, subtype=None):
    tmp = [E.type(type)]
    if subtype:
        tmp.append(E.subType(subtype))
    ex_srs = "urn:ogc:def:crs:EPSG:6.3:%s"%(srs.split(':')[-1])
    tmp.append(E.referenceSystemIdentifier(ex_srs, {"codeSpace":"EPSG"}))
    tmp.append(E.fileName(ns_ows.getServiceReference(url)))
    return E.browse(E.BrowseInformation(*tmp))


def getProduct(srs, url, version=None, size=None, timeliness=None):

    tmp = []

    if srs:
        ex_srs = "urn:ogc:def:crs:EPSG:6.3:%s"%(srs.split(':')[-1])
        tmp.append(E.referenceSystemIdentifier(ex_srs, {"codeSpace":"EPSG"}))

    if version:
        tmp.append(E.version(version))

    if size:
        tmp.append(E.size(size))

    if timeliness:
        tmp.append(E.timeliness(timeliness))

    tmp.append(E.fileName(ns_ows.getServiceReference(url)))

    return E.product(E.ProductInformation(*tmp))


def getMask(type, format, srs=None, geom=None, url=None, post=None, subtype=None):

    tmp = [
        E.type(type),
        E.format(format),
    ]

    if srs is None and geom and geom.GetSpatialReference():
        srs = ig.dumpSR(geom.GetSpatialReference())
    if subtype:
        tmp.append(E.subType(subtype))
    if srs:
        ex_srs = "urn:ogc:def:crs:EPSG:6.3:%s"%(srs.split(':')[-1])
        tmp.append(E.referenceSystemIdentifier(ex_srs, {"codeSpace":"EPSG"}))
    # NOTE: Following is a backported feature. It does not validate
    #       with the current schemas
    if geom:
        tmp.append(getMultiExtentOf(geom, srs))
    if url:
        tmp.append(E.fileName(ns_ows.getServiceReference(url)))

    return E.mask(E.MaskInformation(*tmp))

#------------------------------------------------------------------------------
