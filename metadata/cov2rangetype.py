#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Generate EOxServer JSON range type from Coverage (XML+image)
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
from osgeo import gdal
from profiles.common import attr
#import ns_opt20
import ns_gmlcov10

GCI_TO_NAME = {
    gdal.GCI_Undefined: "Undefined",
    gdal.GCI_GrayIndex: "GrayIndex",
    gdal.GCI_PaletteIndex: "PaletteIndex",
    gdal.GCI_RedBand: "RedBand",
    gdal.GCI_GreenBand: "GreenBand",
    gdal.GCI_BlueBand: "BlueBand",
    gdal.GCI_AlphaBand: "AlphaBand",
    gdal.GCI_HueBand: "HueBand",
    gdal.GCI_SaturationBand: "SaturationBand",
    gdal.GCI_LightnessBand: "LightnessBand",
    gdal.GCI_CyanBand: "CyanBand",
    gdal.GCI_MagentaBand: "MagentaBand",
    gdal.GCI_YellowBand: "YellowBand",
    gdal.GCI_BlackBand: "BlackBand",
    gdal.GCI_YCbCr_YBand: "YBand",
    gdal.GCI_YCbCr_CbBand: "CbBand",
    gdal.GCI_YCbCr_CrBand: "CrBand",
}

GDT_TO_NAME = {
    gdal.GDT_Byte: "Byte",
    gdal.GDT_UInt16: "UInt16",
    gdal.GDT_Int16: "Int16",
    gdal.GDT_UInt32: "UInt32",
    gdal.GDT_Int32: "Int32",
    gdal.GDT_Float32: "Float32",
    gdal.GDT_Float64: "Float64",
    gdal.GDT_CInt16: "CInt16",
    gdal.GDT_CInt32: "CInt32",
    gdal.GDT_CFloat32: "CFloat32",
    gdal.GDT_CFloat64: "CFloat64",
}

JSON_OPTS = {'sort_keys': True, 'indent': 4, 'separators': (',', ': ')}

def float_or_int(v):
    """ cast to int if possible or to float """
    vf = float(v)
    try:
        vi = int(vf)
        if vi == vf:
            return vi
    except:
        return vf

def add_nodata(nilval, nodata):
    values = [float(nv['value']) for nv in nilval]
    if nodata is not None and nodata not in values:
        nilval.append({
            "reason": "http://www.opengis.net/def/nil/OGC/0/inapplicable",
            "value": float_or_int(nodata),
        })
    return nilval

def main(rt_name, fname_xml, fname_data):
    ns_gmlcov = ns_gmlcov10
    ns_swe = ns_gmlcov10.ns_swe

    xml = et.parse(fname_xml, et.XMLParser(remove_blank_text=True))
    img = gdal.Open(fname_data)

    bands = []
    for idx, elm_dr in enumerate(xml.iterfind("//%s/%s/%s"%(ns_gmlcov.rangeType,
                                            ns_swe.DataRecord, ns_swe.field))):
        img_band = img.GetRasterBand(idx+1)
        bname = elm_dr.get("name")
        nilval = []
        for elm_nv in elm_dr.iterfind(".//%s"%ns_swe.nilValue):
            nilval.append({
                "reason": elm_nv.get("reason"),
                "value": float_or_int(elm_nv.text),
            })

        elm_q = elm_dr.find("./%s"%ns_swe.Quantity)
        if elm_q is None:
            raise ValueError("Invalid range-type. Missing the swe:Quality elememnt!")
        bdef = elm_q.get('definition')
        bdscr = elm_q.findtext("./%s"%ns_swe.description)
        buom = attr(elm_q.find("./%s"%ns_swe.uom), 'code')
        band = {
            "identifier": bname,
            "name": bname,
            "description": bdscr or "",
            "definition": bdef,
            "data_type": GDT_TO_NAME[img_band.DataType],
            "gdal_interpretation": GCI_TO_NAME[img_band.GetColorInterpretation()],
            "nil_values": add_nodata(nilval, img_band.GetNoDataValue()),
        }
        if buom:
            band['uom'] = buom
        bands.append(band)

    rt = {
        "name": rt_name,
        "bands": bands,
    }

    print json.dumps(rt, **JSON_OPTS)


#------------------------------------------------------------------------------

if __name__ == "__main__":
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False

    try:
        XML = sys.argv[1]
        DATA = sys.argv[2]
        NAME = sys.argv[3]
        for arg in sys.argv[4:]:
            if arg == "DEBUG":
                DEBUG = True # dump debuging output

    except IndexError:
        print >>sys.stderr, "ERROR: %s: Not enough input arguments!"%EXENAME
        print >>sys.stderr
        print >>sys.stderr, "Extract EOxServer range-type (JSON) from a coverage"
        print >>sys.stderr, "XML and data-file."
        print >>sys.stderr
        print >>sys.stderr, "USAGE: %s <input-xml> <input-data> <rt-name> [DEBUG]"%EXENAME
        sys.exit(1)

    if DEBUG:
        print >>sys.stderr, "input-xml:      ", XML
        print >>sys.stderr, "input-data:     ", DATA
        print >>sys.stderr, "rangetype-name: ", DATA

    try:
        main(NAME, XML, DATA)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s "%(EXENAME, exc)
        if DEBUG:
            print >>sys.stderr, traceback.format_exc()
        sys.exit(1)

