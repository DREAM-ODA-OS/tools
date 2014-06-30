#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  sensor metadata-extraction profiles - spot6 ortho-product
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

class ProfileSpot6Ortho(ProfileDimap):
    version = "2.0"
    profile = "S6_ORTHO"
    c_types = {("INTEGER", 16, "UNSIGNED"): "uint16",}

    @classmethod
    def extract_range_type(cls, xml):
        subprof = extract(xml, "//Metadata_Identification/METADATA_SUBPROFILE")
        if subprof != "PRODUCT":
            raise ValueError("Unknown METADATA_SUBPROFILE '%s'"%subprof)
        pname = extract(xml, "//Dataset_Identification/DATASET_NAME")
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")
        dtsgn = extract(xml, "//Raster_Encoding/SIGN")

        mname = extract(xml, "//Source_Identification/Strip_Source/MISSION")
        mindex = extract(xml, "//Source_Identification/Strip_Source/MISSION_INDEX")
        #iname = extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT")
        #iindex = extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT_INDEX")
        scode = extract(xml, "//Product_Settings/SPECTRAL_PROCESSING")
        geom = extract(xml, "//Product_Settings/Geometric_Settings/GEOMETRIC_PROCESSING")

        base_name = "%s%s:%s:%s:%s"%(mname, mindex, scode, geom, pname)

        dtype = check(cls.c_types.get((dtype, nbits, dtsgn)), 'data type')
        gdal_dtype = check(GDAL_TYPES.get(dtype), 'data_type')
        ogc_dtype = check(OGC_TYPE_DEFS.get(dtype), 'data_type')

        nilval = []
        for elm in xml.iterfind("//Raster_Display/Special_Value"):
            svalidx = extract(elm, "SPECIAL_VALUE_COUNT")
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

        band_data = {}
        band_ids = []
        idx = 0
        for elm in xml.find("//Instrument_Calibration/Band_Measurement_List"):
            bid = extract(elm, 'BAND_ID')
            band = band_data.get(bid)
            if band is None:
                idx += 1
                band = {"bid": bid, "idx": idx}
                band_ids.append(bid)

            prop = {
                'cal_data': extract(elm, "CALIBRATION_DATE"),
                'desc': extract(elm, "MEASURE_DESC"),
                'unit': extract(elm, "MEASURE_UNIT"),
                'uncert': extract(elm, "MEASURE_UNCERTAINTY"),
            }
            if elm.tag == 'Band_Spectral_Range':
                prop.update({
                    'min': extract(elm, "MIN"),
                    'max': extract(elm, "MAX"),
                })
                band['spectral_range'] = prop
            elif elm.tag == 'Band_Radiance':
                prop.update({
                    'gain': extract(elm, "GAIN"),
                    'bias': extract(elm, "BIAS"),
                })
                band['radiance'] = prop
            elif elm.tag == 'Band_Solar_Irradiance':
                prop.update({
                    'value': extract(elm, "VALUE"),
                })
                band['solar_irradiance'] = prop

            band_data[bid] = band

        bands = []
        for band in (band_data[id_] for id_ in band_ids):
            bands.append((band['idx'], {
                "identifier": band['bid'],
                "name": band['bid'],
                "description": "\n".join([
                    "INFO: Radiance digital numbers.",
                    "BAND: %s"%band['bid'],
                    #"BAND_SPECTRAL_RANGE: from %s to %s +/-%s %s"%(
                    "BAND_SPECTRAL_RANGE: from %s to %s %s"%(
                        band['spectral_range']['min'],
                        band['spectral_range']['max'],
                        #band['spectral_range']['uncert'],
                        band['spectral_range']['unit'],
                    ),
                    #"SOLAR_IRRADIANCE: %s +/-%s %s"%(
                    "SOLAR_IRRADIANCE: %s %s"%(
                        band['solar_irradiance']['value'],
                        #band['solar_irradiance']['uncert'],
                        band['solar_irradiance']['unit'],
                    ),
                    "UNIT: %s"%band['radiance']['unit'],
                    "GAIN: %s"%band['radiance']['gain'],
                    "BIAS: %s"%band['radiance']['bias'],
                    #"UNCERTAINITY: %s"%band['radiance']['uncert'],
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
        subprof = extract(xml, "//Metadata_Identification/METADATA_SUBPROFILE")
        if subprof != "PRODUCT":
            raise ValueError("Unknown METADATA_SUBPROFILE '%s'"%subprof)
        #pname = extract(xml, "//Dataset_Identification/DATASET_NAME")
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")
        dtsgn = extract(xml, "//Raster_Encoding/SIGN")

        mname = extract(xml, "//Source_Identification/Strip_Source/MISSION")
        mindex = extract(xml, "//Source_Identification/Strip_Source/MISSION_INDEX")
        #iname = extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT")
        #iindex = extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT_INDEX")
        scode = extract(xml, "//Product_Settings/SPECTRAL_PROCESSING")
        geom = extract(xml, "//Product_Settings/Geometric_Settings/GEOMETRIC_PROCESSING")

        base_name = "%s%s:%s:%s"%(mname, mindex, scode, geom)

        dtype = check(cls.c_types.get((dtype, nbits, dtsgn)), 'data type')
        gdal_dtype = check(GDAL_TYPES.get(dtype), 'data_type')
        ogc_dtype = check(OGC_TYPE_DEFS.get(dtype), 'data_type')

        nilval = []
        for elm in xml.iterfind("//Raster_Display/Special_Value"):
            svalidx = extract(elm, "SPECIAL_VALUE_COUNT")
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

        band_data = {}
        band_ids = []
        idx = 0
        for elm in xml.find("//Instrument_Calibration/Band_Measurement_List"):
            bid = extract(elm, 'BAND_ID')
            band = band_data.get(bid)
            if band is None:
                idx += 1
                band = {"bid": bid, "idx": idx}
                band_ids.append(bid)

            prop = {
                'cal_data': extract(elm, "CALIBRATION_DATE"),
                'desc': extract(elm, "MEASURE_DESC"),
                'unit': extract(elm, "MEASURE_UNIT"),
                'uncert': extract(elm, "MEASURE_UNCERTAINTY"),
            }
            if elm.tag == 'Band_Spectral_Range':
                prop.update({
                    'min': extract(elm, "MIN"),
                    'max': extract(elm, "MAX"),
                })
                band['spectral_range'] = prop
            elif elm.tag == 'Band_Radiance':
                prop.update({
                    'gain': extract(elm, "GAIN"),
                    'bias': extract(elm, "BIAS"),
                })
                band['radiance'] = prop
            elif elm.tag == 'Band_Solar_Irradiance':
                prop.update({
                    'value': extract(elm, "VALUE"),
                })
                band['solar_irradiance'] = prop

            band_data[bid] = band

        bands = []
        for band in (band_data[id_] for id_ in band_ids):
            bands.append((band['idx'], {
                "identifier": band['bid'],
                "name": band['bid'],
                "description": "\n".join([
                    "INFO: Radiance digital numbers.",
                    "BAND: %s"%band['bid'],
                    "BAND_SPECTRAL_RANGE: from %s to %s %s"%(
                        band['spectral_range']['min'],
                        band['spectral_range']['max'],
                        band['spectral_range']['unit'],
                    ),
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
