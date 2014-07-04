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

from lxml import etree
import ns_opt20
import numpy as np
import geom as ig

class SimplifiedLocationModel(object):

    def __init__(self, elm):
        lcdir = []
        for elm_coef in elm.find("./Direct_Location_Model/lc_List"):
            lcdir.append(float(elm_coef.text))
        self._lcdir = np.array(lcdir)
        pcdir = []
        for elm_coef in elm.find("./Direct_Location_Model/pc_List"):
            pcdir.append(float(elm_coef.text))
        self._pcdir = np.array(pcdir)
        lcrev = []
        for elm_coef in elm.find("./Reverse_Location_Model/lc_List"):
            lcrev.append(float(elm_coef.text))
        self._lcrev = np.array(lcrev)
        pcrev = []
        for elm_coef in elm.find("./Reverse_Location_Model/pc_List"):
            pcrev.append(float(elm_coef.text))
        self._pcrev = np.array(pcrev)

    def __call__(self, x, y, reverse=False):
        xy = x * y
        xx = x * x
        yy = y * y
        if reverse:
            lc, pc = self._lcrev, self._pcrev
        else:
            lc, pc = self._lcdir, self._pcdir
        l = lc[0];     p = pc[0]
        l += lc[1]*x;  p += pc[1]*x
        l += lc[2]*y;  p += pc[2]*y
        l += lc[3]*xy; p += pc[3]*xy
        l += lc[4]*xx; p += pc[4]*xx
        l += lc[5]*yy; p += pc[5]*yy
        return l, p

def get_footprint_and_center(xml, n=10):
    elm_slm = check(xml.find("//Simplified_Location_Model"), "Simplified_Location_Model")
    loc_mod = SimplifiedLocationModel(elm_slm)

    #ncol = int(extract(xml, "//Raster_Dimensions/NCOLS"))
    #nrow = int(extract(xml, "//Raster_Dimensions/NROWS"))

    elm = check(xml.find("//Dataset_Frame/Scene_Center"), 'Scene_Center')
    lon_cnt = float(extract(elm, "./FRAME_LON"))
    lat_cnt = float(extract(elm, "./FRAME_LAT"))

    vlist = []
    for elm in xml.iterfind("//Dataset_Frame/Vertex"):
        _lon = float(extract(elm, "./FRAME_LON"))
        _lat = float(extract(elm, "./FRAME_LAT"))
        _row = float(extract(elm, "./FRAME_ROW"))
        _col = float(extract(elm, "./FRAME_COL"))
        vlist.append((_lat, _lon, _row, _col))
    row, col = [], []
    for i in xrange(len(vlist)):
        _, _, r0, c0 = vlist[i]
        _, _, r1, c1 = vlist[(i+1)%len(vlist)]
        row.append(np.linspace(r0, r1, n, False))
        col.append(np.linspace(c0, c1, n, False))
    lon, lat = loc_mod(np.concatenate(row), np.concatenate(col))

    wkt0 = ",".join("%.9g %.9g"%(x, y) for x, y in np.nditer([lon, lat]))
    wkt0 = "EPSG:4326;POLYGON((%s, %.9g %.9g))"%(wkt0, lon[0], lat[0])
    wkt1 = "EPSG:4326;POINT(%.9g %.9g)"%(lon_cnt, lat_cnt)
    return ig.parseGeom(wkt0), ig.parseGeom(wkt1)


class ProfileSpotScene1a(ProfileDimap):
    version = "1.1"
    profile = "SPOTSCENE_1A"
    c_types = {(8, "UNSIGNED"): "uint8",}

    @classmethod
    def get_identifier(cls, xml):
        """ get dataset's unique identifier """
        src_id = extract(xml, "//Source_Information/SOURCE_ID")[:-1]
        mname = extract(xml, "//Scene_Source/MISSION")
        mindex = extract(xml, "//Scene_Source/MISSION_INDEX")
        iname = extract(xml, "//Scene_Source/INSTRUMENT")
        iindex = extract(xml, "//Scene_Source/INSTRUMENT_INDEX")
        #scode = extract(xml, "//Scene_Source/SENSOR_CODE")
        scode = ""
        for elm in xml.iterfind("//Scene_Source"):
            scode += extract(elm, "SENSOR_CODE")
        geom = extract(xml, "//Data_Processing/GEOMETRIC_PROCESSING")
        return "%s%s:%s%s:%s%s:%s"%(mname, mindex, iname, iindex, src_id, scode, geom)

    @classmethod
    def get_parent_id(cls, xml):
        """ get collections's unique identifier """
        mname = extract(xml, "//Scene_Source/MISSION")
        mindex = extract(xml, "//Scene_Source/MISSION_INDEX")
        iname = extract(xml, "//Scene_Source/INSTRUMENT")
        iindex = extract(xml, "//Scene_Source/INSTRUMENT_INDEX")
        geom = extract(xml, "//Data_Processing/GEOMETRIC_PROCESSING")
        scode = ""
        for elm in xml.iterfind("//Scene_Source"):
            scode += extract(elm, "SENSOR_CODE")
        return "%s%s:%s%s:%s:%s"%(mname, mindex, iname, iindex, scode, geom)

    @classmethod
    def extract_range_type(cls, xml):
        """ Extract full range type definition."""
        src_type = extract(xml, "//Source_Information/SOURCE_TYPE")
        if src_type != "SCENE":
            raise ValueError("Unknown SOURCE_TYPE '%s'"%src_type)
        base_name = cls.get_identifier(xml)
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")
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
        base_name = cls.get_parent_id(xml)
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")
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

    @classmethod
    def extract_eop_metadata(cls, xml, ns_opt=None, **kwarg):
        """ Extract range definition applicable to all product
            of the same type.
        """
        ns_opt = ns_opt or ns_opt20
        ns_eop = ns_opt.ns_eop
        ns_gml = ns_opt.ns_gml
        ns_om = ns_opt.ns_om
        OPT = ns_opt.E
        EOP = ns_eop.E
        OM = ns_om.E
        #GML = ns_gml.E

        time_acq_start = "%sT%sZ"%(extract(xml, "//Scene_Source/IMAGING_DATE"),
                                   extract(xml, "//Scene_Source/IMAGING_TIME"))
        time_acq_stop = time_acq_start
        time_prod = extract(xml, "//Production/DATASET_PRODUCTION_DATE")+'Z'

        grid_reference = extract(xml, "//Scene_Source/GRID_REFERENCE")
        grid_ref_lon = grid_reference[0:3]
        grid_ref_lat = grid_reference[3:6]

        eo_equipment = EOP.EarthObservationEquipment(
            ns_gml.getRandomId(),
            EOP.platform(EOP.Platform(
                EOP.shortName(extract(xml, "//Scene_Source/MISSION")),
                EOP.serialIdentifier(extract(xml, "//Scene_Source/MISSION_INDEX")),
                EOP.orbitType("LEO"),
            )),
            EOP.instrument(EOP.Instrument(
                EOP.shortName("%s%s"%(
                    extract(xml, "//Scene_Source/INSTRUMENT"),
                    extract(xml, "//Scene_Source/INSTRUMENT_INDEX"),
                )),
            )),
            EOP.sensor(EOP.Sensor(
                EOP.sensorType("OPTICAL"),
            )),
            EOP.acquisitionParameters(EOP.Acquisition(
                EOP.orbitNumber(extract(xml, "//Imaging_Parameters/REVOLUTION_NUMBER")),
                EOP.lastOrbitNumber(extract(xml, "//Imaging_Parameters/REVOLUTION_NUMBER")),
                EOP.orbitDirection("DESCENDING"),
                EOP.wrsLongitudeGrid(grid_ref_lon),
                EOP.wrsLatitudeGrid(grid_ref_lat),
                EOP.illuminationAzimuthAngle(extract(xml, "//Scene_Source/SUN_AZIMUTH"), {"uom": "deg"}),
                EOP.illuminationElevationAngle(extract(xml, "//Scene_Source/SUN_ELEVATION"), {"uom": "deg"}),
                EOP.incidenceAngle(extract(xml, "//Scene_Source/INCIDENCE_ANGLE"), {"uom": "deg"}),
            )),
        )

        metadata = EOP.EarthObservationMetaData(
            EOP.identifier(cls.get_identifier(xml)),
            EOP.parentIdentifier(cls.get_parent_id(xml)),
            EOP.acquisitionType("NOMINAL"),
            EOP.productType("IMAGE"),
            EOP.status("ACQUIRED"),
        )

        xml_eop = OPT.EarthObservation(
            ns_gml.getRandomId(),
            ns_eop.getSchemaLocation("OPT"),
            #EOP.parameter(), #optional
            OM.phenomenonTime(ns_gml.getTimePeriod(time_acq_start, time_acq_stop)),
            #OM.resultQuality(), #optional
            OM.resultTime(ns_gml.getTimeInstant(time_prod)),
            #OM.validTime(), # optional
            OM.procedure(eo_equipment),
            OM.observedProperty({"nillReason": "unknown"}),
            OM.featureOfInterest(
                ns_eop.getFootprint(*get_footprint_and_center(xml))
            ),
            OM.result(OPT.EarthObservationResult(ns_gml.getRandomId())),
            EOP.metaDataProperty(metadata),
        )

        xml_eop = etree.ElementTree(xml_eop)
        xml_eop.getroot().addprevious(ns_eop.getSchematronPI())
        return xml_eop
