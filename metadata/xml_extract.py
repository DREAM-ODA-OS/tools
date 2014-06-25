#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Extract part of an XML document
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
import os.path
from lxml import etree as et
import ns_ogr
from geom2gml import fixSRSNames

#------------------------------------------------------------------------------

if __name__ == "__main__":

    # TODO: to improve CLI

    EXENAME = os.path.basename(sys.argv[0])

    DEBUG = False
    PRETTY = False
    ATTRIB = None
    TEXT = False
    GML = False
    TAG = False
    MULTI = False

    try:
        XML = sys.argv[1]
        XPATH = sys.argv[2]
        for arg in sys.argv[3:]:
            if arg == "DEBUG":
                DEBUG = True # dump debuging output
            elif arg.startswith("ATTRIB="):
                ATTRIB = arg.partition('=')[2] # pretty XML print
            elif arg == "PRETTY":
                PRETTY = True # pretty XML print
            elif arg == "TEXT":
                TEXT = True # pretty XML print
            elif arg == "GML":
                GML = True # print GML as GDAL feature collection
            elif arg == "TAG":
                TAG = True # element name print
            elif arg == "MULTI":
                MULTI = True # pretty XML print

    except IndexError:
        sys.stderr.write("ERROR: %s: Not enough input arguments!\n"%EXENAME)
        sys.stderr.write("\nExtract subset of an XML document\n")
        sys.stderr.write("and dump it to the standard output.\n")
        sys.stderr.write("USAGE: %s <input-xml> <xpath> [PRETTY][TEXT][GML][DEBUG]\n"%EXENAME)
        sys.exit(1)

    if DEBUG:
        print >>sys.stderr, "input-xml:   ", XML
        print >>sys.stderr, "x-path:      ", XPATH
        print >>sys.stderr, "TEXT:        ", TEXT
        print >>sys.stderr, "PRETTY:      ", PRETTY
        print >>sys.stderr, "ATTRIB:      ", ATTRIB
        print >>sys.stderr, "TAG:         ", TAG
        print >>sys.stderr, "MULTI:       ", MULTI

#------------------------------------------------------------------------------

    if XPATH.endswith("/name()"): # lxml XPATH 1.0 does not support name()
        XPATH = XPATH[0:-len("/name()")] or "/"
        TAG = True

    try:
        xml_in = et.parse(XML, et.XMLParser(remove_blank_text=True))
        #elm = xml_in.find(XPATH)
        etxp_expr = et.ETXPath(XPATH)
        result = etxp_expr(xml_in)
    except Exception as e:
        print >>sys.stderr, "ERROR: %s: %s "%(EXENAME, e)
        sys.exit(1)

    if not isinstance(result, list):
        print result
    else:
        if len(result) == 0:
            print >>sys.stderr, "ERROR: %s: No result found!"%EXENAME
            sys.exit(1)
        elif not MULTI and len(result) > 1:
            print >>sys.stderr, "ERROR: %s: Multiple results found!"%EXENAME
            sys.exit(1)
        for item in result:
            if not isinstance(item, et._Element):
                print item
            elif TAG:
                print item.tag
            elif ATTRIB: # extract text
                print item.get(ATTRIB, "")
            elif TEXT: # extract text
                print item.text
            else: # extrac XML subtree
                if GML: # wrap the GML so that it can be loaded by QGIS
                    item = ns_ogr.getFeatureCollection(fixSRSNames(item))
                print et.tostring(item, pretty_print=PRETTY, xml_declaration=True, encoding="utf-8")
