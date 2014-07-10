#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Ikonos metadata parser and converter - CLI tool.
#
# Project: EO Metadata Handling
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

import os.path
import sys
import traceback
from lxml import etree
from profiles.ikonos_parser import load_as_xml

XML_OPTS = {'pretty_print': True, 'xml_declaration': True, 'encoding': 'utf-8'}

if __name__ == "__main__":
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False

    try:
        INPUT = sys.argv[1]
        for arg in sys.argv[2:]:
            if arg == "DEBUG":
                DEBUG = True # dump debuging output

    except IndexError:
        print >>sys.stderr, "ERROR: %s: Not enough input arguments!"%EXENAME
        print >>sys.stderr
        print >>sys.stderr, "Convert Ikonos metadata to a simple XML."
        print >>sys.stderr
        #print >>sys.stderr, "USAGE: %s <input-xml> [DEBUG][*JSON|XML]"%EXENAME
        print >>sys.stderr, "USAGE: %s <input-xml> [DEBUG]"%EXENAME
        sys.exit(1)

    if DEBUG:
        print >>sys.stderr, "input-xml:   ", INPUT

    try:
        print etree.tostring(load_as_xml(INPUT, True), **XML_OPTS)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s "%(EXENAME, exc)
        if DEBUG:
            print >>sys.stderr, traceback.format_exc()
        sys.exit(1)

