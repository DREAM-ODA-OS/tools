#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   add/rewrite EOP footprint
#
# Project: XML Metadata Handling
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

import traceback
import sys
import os.path
from lxml import etree
from osgeo import ogr; ogr.UseExceptions()
import ns_eop20
import geom as ig
import re


XML_OPTS = {'pretty_print': True, 'xml_declaration': True, 'encoding': 'utf-8'}
RE_EarthObservation = re.compile(r'{http://www.opengis.net/\w+/2.0}EarthObservation')
XML_PARSER = etree.XMLParser(remove_blank_text=True)

def main(fname_eop, fname_footp, fname_centr):
    ns_eop = ns_eop20
    ns_om = ns_eop.ns_om

    # load inputs
    if fname_eop == '-':
        eop = etree.parse(sys.stdin, XML_PARSER)
    else:
        with file(fname_eop) as fid:
            eop = etree.parse(fid, XML_PARSER)

    if fname_footp == '-':
        footp = ig.parseGeom(sys.stdin.read())
    else:
        with file(fname_footp) as fid:
            footp = ig.parseGeom(fid.read())

    if fname_centr:
        if fname_centr == '-':
            centr = ig.parseGeom(sys.stdin.read())
        else:
            with file(fname_centr) as fid:
                centr = ig.parseGeom(fid.read())
    else:
        centr = None

    # check geometries
    if footp.GetGeometryName() == "POLYGON":
        geo_new = ogr.Geometry(ogr.wkbMultiPolygon)
        geo_new.AddGeometry(footp.Clone())
        footp = ig.setSR(geo_new, footp.GetSpatialReference())

    elif footp.GetGeometryName() != "MULTIPOLYGON":
        raise ValueError("Invalid footprint geometry type %s !"%(footp.GetGeometryName()))

    if centr and centr.GetGeometryName() != "POINT":
        raise ValueError("Invalid centroid geometry type %s !"%(centr.GetGeometryName()))

    # check root element
    if RE_EarthObservation.match(eop.find('.').tag) is None:
        raise Exception("Unexpected root element %s !"%(eop.find('.').tag))

    # find the base element
    elm = eop.find('./'+ns_om.featureOfInterest)

    # remove previous footprint
    if elm.find('./'+ns_eop.Footprint):
        elm.remove(elm.find('./'+ns_eop.Footprint))

    # append new footprint
    elm.append(ns_eop.getFootprint(footp, centr))

    # dump the output
    print etree.tostring(eop, **XML_OPTS)


if __name__ == "__main__":
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False
    CENTR = None

    try:
        INPUT = sys.argv[1]
        FOOTP = sys.argv[2]
        for arg in sys.argv[3:]:
            if arg == "DEBUG":
                DEBUG = True # dump debuging output
            else:
                CENTR = arg

    except IndexError:
        print >>sys.stderr, "ERROR: %s: Not enough input arguments!"%EXENAME
        print >>sys.stderr
        print >>sys.stderr, "Add/rewrite EOP footprint."
        print >>sys.stderr
        print >>sys.stderr, "USAGE: %s <EOP-XML> <footprint> [<center>] [DEBUG]"%EXENAME
        sys.exit(1)

    if DEBUG:
        print >>sys.stderr, "eop-xml:   ", INPUT
        print >>sys.stderr, "footprint: ", FOOTP
        print >>sys.stderr, "center:    ", CENTR

    try:
        main(INPUT, FOOTP, CENTR)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s "%(EXENAME, exc)
        if DEBUG:
            print >>sys.stderr, traceback.format_exc()
        sys.exit(1)
