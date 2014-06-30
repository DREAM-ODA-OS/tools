#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  sensor metadata-extraction profiles - spot4 and spot5 scene 1A products
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

from .common import (
    GDAL_TYPES, OGC_TYPE_DEFS,
    check, extract, #tag, text, attr,
)

from .interfaces import ProfileDimap

class ProfileSpotScene1a(ProfileDimap):
    version = "1.1"
    profile = "SPOTSCENE_1A"
    c_types = {(8, "UNSIGNED"): "uint8",}

    @classmethod
    def extract_range_type(cls, xml):
        """ Extract full range type definition."""
        src_type = extract(xml, "//Source_Information/SOURCE_TYPE")
        if src_type != "SCENE":
            raise ValueError("Unknown SOURCE_TYPE '%s'"%src_type)
        src_id = extract(xml, "//Source_Information/SOURCE_ID")
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")

        mname = extract(xml, "//Scene_Source/MISSION")
        mindex = extract(xml, "//Scene_Source/MISSION_INDEX")
        iname = extract(xml, "//Scene_Source/INSTRUMENT")
        iindex = extract(xml, "//Scene_Source/INSTRUMENT_INDEX")
        scode = extract(xml, "//Scene_Source/SENSOR_CODE")
        geom = extract(xml, "//Data_Processing/GEOMETRIC_PROCESSING")

        base_name = "%s%s:%s%s:%s:%s:%s"%(mname, mindex, iname, iindex, scode, geom, src_id)
        dtype = check(cls.c_types.get((nbits, dtype)), 'data type')
        gdal_dtype = check(GDAL_TYPES.get(dtype), 'data_type')
        ogc_dtype = check(OGC_TYPE_DEFS.get(dtype), 'data_type')

        nilval = []
        for elm in xml.iterfind("//Image_Display/Special_Value"):
            svalidx = extract(elm, "SPECIAL_VALUE_INDEX")
            svaltext = extract(elm, "SPECIAL_VALUE_TEXT")
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
            bname = extract(elm, "BAND_DESCRIPTION")
            bidx = int(extract(elm, "BAND_INDEX"))
            bunit = extract(elm, "PHYSICAL_UNIT")
            bgain = extract(elm, "PHYSICAL_GAIN")
            bbias = extract(elm, "PHYSICAL_BIAS")
            #cal_date = extract(elm, "PHYSICAL_CALIBRATION_DATE")
            bands.append((bidx, {
                "identifier": bname,
                "name": bname,
                "description": "\n".join([
                    "INFO: Radiance digital numbers.",
                    "BAND_INDEX: %s"%bidx,
                    "BAND: %s"%bname,
                    "UNIT: %s"%bunit,
                    "GAIN: %s"%bgain,
                    "BIAS: %s"%bbias,
                ]),
                "definition": ogc_dtype,
                "data_type": gdal_dtype,
                "gdal_interpretation": "Undefined",
                "uom": "none",
                "nil_values": nilval,
            }))

        return {
            "name": "%s:%d:%s"%(base_name, nbands, dtype),
            "bands": [obj for _, obj in sorted(bands)],
        }

    @classmethod
    def extract_range_type_sloppy(cls, xml):
        """ Extract range definition applicable to all product
            of the same type.
        """
        src_type = extract(xml, "//Source_Information/SOURCE_TYPE")
        if src_type != "SCENE":
            raise ValueError("Unknown SOURCE_TYPE '%s'"%src_type)
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")

        mname = extract(xml, "//Scene_Source/MISSION")
        mindex = extract(xml, "//Scene_Source/MISSION_INDEX")
        iname = extract(xml, "//Scene_Source/INSTRUMENT")
        iindex = extract(xml, "//Scene_Source/INSTRUMENT_INDEX")
        scode = extract(xml, "//Scene_Source/SENSOR_CODE")
        geom = extract(xml, "//Data_Processing/GEOMETRIC_PROCESSING")

        base_name = "%s%s:%s%s:%s:%s"%(mname, mindex, iname, iindex, scode, geom)
        dtype = check(cls.c_types.get((nbits, dtype)), 'data type')
        gdal_dtype = check(GDAL_TYPES.get(dtype), 'data_type')
        ogc_dtype = check(OGC_TYPE_DEFS.get(dtype), 'data_type')

        nilval = []
        for elm in xml.iterfind("//Image_Display/Special_Value"):
            svalidx = extract(elm, "SPECIAL_VALUE_INDEX")
            svaltext = extract(elm, "SPECIAL_VALUE_TEXT")
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
            bname = extract(elm, "BAND_DESCRIPTION")
            bidx = int(extract(elm, "BAND_INDEX"))
            bands.append((bidx, {
                "identifier": bname,
                "name": bname,
                "description": "\n".join([
                    "INFO: Radiance digital numbers.",
                    "BAND_INDEX: %s"%bidx,
                    "BAND: %s"%bname,
                ]),
                "definition": ogc_dtype,
                "data_type": gdal_dtype,
                "gdal_interpretation": "Undefined",
                "uom": "none",
                "nil_values": nilval,
            }))

        return {
            "name": "%s:%d:%s"%(base_name, nbands, dtype),
            "bands": [obj for _, obj in sorted(bands)],
        }
