#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Generate EOxServer JSON range type from DIMAP XML.
#    This is the "sloppy" version - by leaving some of the details 
#    the produced range-type is applicable to all products of the 
#    same type. 
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
import json
from lxml import etree as et

#JSON_OPTS={}
JSON_OPTS = {'sort_keys': True, 'indent': 4, 'separators': (',', ': ')}

#------------------------------------------------------------------------------

def _tag(elm):
    return None if elm is None else elm.tag

def _text(elm):
    return None if elm is None else elm.text

def _attr(elm, key):
    return None if elm is None else elm.get(key, None)

def _check(val, label):
    if val is None:
        raise ValueError("Invalid %s!"%label)
    return val

#------------------------------------------------------------------------------

class Profile(object):
    version = None
    profile = None

    @classmethod
    def extract(cls, xml):
        raise NotImplementedError


class Profile_SPOTSCENE_1A(Profile):
    version = "1.1"
    profile = "SPOTSCENE_1A"
    gdal_types = {(8, "UNSIGNED"): "Byte",}
    c_types = {(8, "UNSIGNED"): "uint8",}

    @classmethod
    def extract(cls, xml):
        def _extract(elm, path, label=None):
            return _check(_text(elm.find(path)), label or path)
        src_type = _extract(xml, "//Source_Information/SOURCE_TYPE", "SOURCE_TYPE")
        if src_type != "SCENE":
            raise ValueError("Unknown SOURCE_TYPE '%s'"%src_type)
        #src_id = _extract(xml, "//Source_Information/SOURCE_ID", "SOURCE_ID")
        nbands = int(_extract(xml, "//Raster_Dimensions/NBANDS", "NBANDS"))
        nbits = int(_extract(xml, "//Raster_Encoding/NBITS", "NBITS"))
        dtype = _extract(xml, "//Raster_Encoding/DATA_TYPE", "DATA_TYPE")

        mname = _extract(xml, "//Scene_Source/MISSION", "MISSION")
        mindex = _extract(xml, "//Scene_Source/MISSION_INDEX", "MISSION_INDEX")
        iname = _extract(xml, "//Scene_Source/INSTRUMENT", "INSTRUMENT")
        iindex = _extract(xml, "//Scene_Source/INSTRUMENT_INDEX", "INSTRUMENT_INDEX")
        scode = _extract(xml, "//Scene_Source/SENSOR_CODE", "SENSOR_CODE")

        base_name = "%s%s:%s%s:%s"%(mname, mindex, iname, iindex, scode)
        dtype_str = _check(cls.c_types.get((nbits, dtype)), 'data type')
        data_type = _check(cls.gdal_types.get((nbits, dtype)), 'data type')

        nilval = []
        for elm in xml.iterfind("//Image_Display/Special_Value"):
            svalidx = _extract(elm, "SPECIAL_VALUE_INDEX")
            svaltext = _extract(elm, "SPECIAL_VALUE_TEXT")
            if svaltext == 'NODATA':
                nilval.append((0, {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/inapplicable",
                    "value": svalidx,
                }))
            elif svaltext == 'SATURATED':
                nilval.append((1, {
                    "reason": "http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange",
                    "value": svalidx,
                }))
        # make sure the no-data goes first
        nilval = [obj for _, obj in sorted(nilval)]

        bands = []
        for elm in xml.iterfind("//Spectral_Band_Info"):
            bname = _extract(elm, "BAND_DESCRIPTION")
            bidx = int(_extract(elm, "BAND_INDEX"))
            bunit = _extract(elm, "PHYSICAL_UNIT")
            #bgain = _extract(elm, "PHYSICAL_GAIN")
            #bbias = _extract(elm, "PHYSICAL_BIAS")
            #cal_date = _extract(elm, "PHYSICAL_CALIBRATION_DATE")
            bands.append((bidx, {
                "identifier": "%s:BAND%d:%s:%s"%(base_name, bidx, bname, dtype_str),
                "name": bname,
                "description": "\n".join([
                    "BAND_INDEX: %s"%bidx,
                    "BAND: %s"%bname,
                    "PHYSICAL_UNIT: %s"%bunit,
                    #"PHYSICAL_GAIN: %s"%bgain,
                    #"PHYSICAL_BIAS: %s"%bbias,
                    #"PHYSICAL_CALIBRATION_DATE: %s"%cal_date,
                ]),
                "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
                "data_type": data_type,
                "gdal_interpretation": "Undefined",
                "uom": "W.m-2.sr-1.nm-1",
                "nil_values": nilval,
            }))

        return {
            "name": "%s:%d:%s"%(base_name, nbands, dtype_str),
            "data_type": data_type,
            "bands": [obj for _, obj in sorted(bands)],
        }

#------------------------------------------------------------------------------

PROFILES = (
    Profile_SPOTSCENE_1A,
)

def main(fname):
    xml = et.parse(fname, et.XMLParser(remove_blank_text=True))
    profile = get_profile(xml)
    print json.dumps(profile.extract(xml), **JSON_OPTS)

def get_profile(xml):
    root = _tag(xml.find("."))
    format_ = _text(xml.find("//METADATA_FORMAT"))
    version = _attr(xml.find("//METADATA_FORMAT"), "version")
    profile = _text(xml.find("//METADATA_PROFILE"))
    if root != "Dimap_Document" or format_ != "DIMAP":
        raise ValueError("Not a DIMAP XML document!")
    for item in PROFILES:
        if item.version == version and item.profile == profile:
            return item
    raise ValueError("Unsupported %s version %s profile '%s'!"%(format_, version, profile))

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
        print >>sys.stderr, "Extract EOxServer range-type (JSON) from DIMAP"
        print >>sys.stderr, "XML metadata."
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
