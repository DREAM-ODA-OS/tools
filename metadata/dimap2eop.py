#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Extract O&M-EOP metadata document.
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

import traceback
import sys
import os.path
from lxml import etree as et

from profiles.interfaces import ProfileDimap
from profiles.spot6_ortho import ProfileSpot6Ortho
from profiles.spot_view import ProfileSpotView
from profiles.spot_scene_1a import ProfileSpotScene1a
from profiles.pleiades1_ortho import ProfilePleiades1Ortho

XML_OPTS = {'pretty_print': True, 'xml_declaration': True, 'encoding': 'utf-8'}

PROFILES = (
    ProfileSpotScene1a, ProfileSpotView,
    ProfileSpot6Ortho, ProfilePleiades1Ortho,
)

def main(fname):
    xml = et.parse(fname, et.XMLParser(remove_blank_text=True))
    profile = get_profile(xml)
    print et.tostring(profile.extract_eop_metadata(xml, file_name=fname), **XML_OPTS)

def get_profile(xml):
    for item in PROFILES:
        if item.check_profile(xml):
            return item
    prf = ProfileDimap.get_dimap_profile(xml)
    if prf is None:
        raise ValueError("Not a DIMAP XML document!")
    profile, version = prf
    raise ValueError("Unsupported DIMAP version %s profile '%s'!"%(version, profile))

#------------------------------------------------------------------------------

if __name__ == "__main__":
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False

    try:
        XML = sys.argv[1]
        for arg in sys.argv[2:]:
            if arg == "DEBUG":
                DEBUG = True # dump debuging output

    except IndexError:
        print >>sys.stderr, "ERROR: %s: Not enough input arguments!"%EXENAME
        print >>sys.stderr
        print >>sys.stderr, "Extract EOP XML metadata from DIMAP XML metadata."
        print >>sys.stderr
        print >>sys.stderr, "USAGE: %s <input-xml> [DEBUG]"%EXENAME
        sys.exit(1)

    if DEBUG:
        print >>sys.stderr, "input-xml:   ", XML

    try:
        main(XML)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s "%(EXENAME, exc)
        if DEBUG:
            print >>sys.stderr, traceback.format_exc()
        sys.exit(1)
