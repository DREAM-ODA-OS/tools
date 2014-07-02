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
    check, extract, extattr,
)

import os.path
from .interfaces import ProfileDimap
from lxml import etree
import ns_opt20
#import numpy as np
import geom as ig
from osgeo import ogr; ogr.UseExceptions()

# segmentation threshold
SGLEN = 10000.0 # 10km

def get_mask_element(xml, mtype="Area_Of_Interest (ROI)"):
    for elm in xml.iterfind("//Quality_Assessment/Imaging_Quality_Measurement"):
        if mtype == extract(elm, "./MEASURE_NAME"):
            return elm
    return None

def get_multipolygon(fname, sr=None):
    #NOTE: GDAL is not able to detect the spatial reference!
    geom = ogr.Geometry(ogr.wkbMultiPolygon)
    ds = ogr.Open(fname)
    if ds is not None and ds.GetLayerCount() > 0:
        ly = ds.GetLayer(0)
        for ft in (ly.GetFeature(i) for i in xrange(ly.GetFeatureCount())):
            _geom = ft.GetGeometryRef()
            if "POLYGON" == _geom.GetGeometryName():
                if sr is None and _geom.GetSpatialReference() is not None:
                    sr = _geom.GetSpatialReference()
                geom.AddGeometry(_geom.Clone())
        geom.Segmentize(SGLEN)
    return ig.setSR(geom, sr)

def get_mask(xml, type_="ROI", fname=None):
    dname = "." if fname is None else os.path.dirname(fname)
    prod_crs = extract(xml, "//Coordinate_Reference_System/Projected_CRS/PROJECTED_CRS_CODE")
    title = {
       "ROI": "Area_Of_Interest (ROI)",
       "CLOUD": "Cloud_Cotation (CLD)",
       "SNOW": "Snow_Cotation (SNW)",
       "WATER": "Water_Cotation (DTM)",
       "VISIBLE": "Visibility_Cotation (VIS)",
    }[type_]
    msk_elm = check(get_mask_element(xml, title), title)
    msk_fname = extattr(msk_elm, "./Quality_Mask/Component/COMPONENT_PATH", "href")
    msk_fname = os.path.join(dname, msk_fname)
    return get_multipolygon(msk_fname, ig.parseSR(prod_crs))

def get_footprint_and_center(xml, fname=None):
    footprint = get_mask(xml, "ROI", fname)
    centroid = ig.setSR(footprint.Centroid(), footprint.GetSpatialReference())
    return ig.mapToWGS84(footprint), ig.mapToWGS84(centroid)

def get_mask_and_relcover(xml, type_, fname=None):
    try:
        mask = get_mask(xml, type_, fname)
    except ValueError:
        return None, None
    extn = get_mask(xml, "ROI", fname)
    ratio = mask.Area() / extn.Area()
    return ig.mapToWGS84(mask), ratio

class ProfileSpot6Ortho(ProfileDimap):
    version = "2.0"
    profile = "S6_ORTHO"
    c_types = {("INTEGER", 16, "UNSIGNED"): "uint16",}

    @classmethod
    def get_identifier(cls, xml):
        """ get dataset's unique identifier """
        #pname = extract(xml, "//Dataset_Identification/DATASET_NAME")
        mname = extract(xml, "//Source_Identification/Strip_Source/MISSION")
        mindex = extract(xml, "//Source_Identification/Strip_Source/MISSION_INDEX")
        scode = extract(xml, "//Product_Settings/SPECTRAL_PROCESSING")
        idate = extract(xml, "//Source_Identification/Strip_Source/IMAGING_DATE")
        itime = extract(xml, "//Source_Identification/Strip_Source/IMAGING_TIME")
        dtstr = "".join([idate[0:4], idate[5:7], idate[8:10],
                         itime[0:2], itime[3:5], itime[6:8], itime[9:10]])
        jobid = extract(xml, "//Delivery_Identification/JOB_ID")
        return "%s%s_%s_%s_ORT_%s"%(mname, mindex, scode, dtstr, jobid)

    @classmethod
    def get_parent_id(cls, xml):
        """ get collections's unique identifier """
        mname = extract(xml, "//Source_Identification/Strip_Source/MISSION")
        mindex = extract(xml, "//Source_Identification/Strip_Source/MISSION_INDEX")
        iname = extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT")
        iindex = extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT_INDEX")
        scode = extract(xml, "//Product_Settings/SPECTRAL_PROCESSING")
        geom = "ORTHO"
        #geom = extract(xml, "//Product_Settings/Geometric_Settings/GEOMETRIC_PROCESSING")
        return "%s%s:%s%s:%s:%s"%(mname, mindex, iname, iindex, scode, geom)

    @classmethod
    def extract_range_type(cls, xml):
        subprof = extract(xml, "//Metadata_Identification/METADATA_SUBPROFILE")
        if subprof != "PRODUCT":
            raise ValueError("Unknown METADATA_SUBPROFILE '%s'"%subprof)
        base_name = cls.get_identifier(xml)
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")
        dtsgn = extract(xml, "//Raster_Encoding/SIGN")

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
        base_name = cls.get_parent_id(xml)
        nbands = int(extract(xml, "//Raster_Dimensions/NBANDS"))
        nbits = int(extract(xml, "//Raster_Encoding/NBITS"))
        dtype = extract(xml, "//Raster_Encoding/DATA_TYPE")
        dtsgn = extract(xml, "//Raster_Encoding/SIGN")

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

    @classmethod
    def extract_eop_metadata(cls, xml, ns_opt=None, file_name=None, **kwarg):
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

        time_acq_start = "%sT%sZ"%(
            extract(xml, "//Source_Identification/Strip_Source/IMAGING_DATE"),
            extract(xml, "//Source_Identification/Strip_Source/IMAGING_TIME"))
        time_acq_stop = time_acq_start
        time_prod = extract(xml, "//Delivery_Identification/PRODUCTION_DATE")

        # extracting angles
        for elm in xml.iterfind("//Geometric_Data/Use_Area/Located_Geometric_Values"):
            if "Center" != extract(elm, "./LOCATION_TYPE"):
                continue
            #cnt_row = int(extract(elm, "./ROW"))
            #cnt_col = int(extract(elm, "./COL"))
            angle_incidence = extract(elm, "./Acquisition_Angles/INCIDENCE_ANGLE")
            angle_inc_acrst = extract(elm, "./Acquisition_Angles/INCIDENCE_ANGLE_ACROSS_TRACK")
            angle_inc_alngt = extract(elm, "./Acquisition_Angles/INCIDENCE_ANGLE_ALONG_TRACK")
            angle_sol_azim = extract(elm, "./Solar_Incidences/SUN_AZIMUTH")
            angle_sol_elev = extract(elm, "./Solar_Incidences/SUN_ELEVATION")
            break


        eo_equipment = EOP.EarthObservationEquipment(
            ns_gml.getRandomId(),
            EOP.platform(EOP.Platform(
                EOP.shortName(extract(xml, "//Source_Identification/Strip_Source/MISSION")),
                EOP.serialIdentifier(extract(xml, "//Source_Identification/Strip_Source/MISSION_INDEX")),
                EOP.orbitType("LEO"),
            )),
            EOP.instrument(EOP.Instrument(
                EOP.shortName("%s%s"%(
                    extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT"),
                    extract(xml, "//Source_Identification/Strip_Source/INSTRUMENT_INDEX"),
                )),
            )),
            EOP.sensor(EOP.Sensor(
                EOP.sensorType("OPTICAL"),
            )),
            EOP.acquisitionParameters(EOP.Acquisition(
                EOP.orbitDirection("DESCENDING"),
                EOP.illuminationAzimuthAngle(angle_sol_azim, {"uom": "deg"}),
                EOP.illuminationElevationAngle(angle_sol_elev, {"uom": "deg"}),
                EOP.incidenceAngle(angle_incidence, {"uom": "deg"}),
                EOP.acrossTrackIncidenceAngle(angle_inc_acrst, {"uom": "deg"}),
                EOP.alongTrackIncidenceAngle(angle_inc_alngt, {"uom": "deg"}),
            )),
        )

        metadata = EOP.EarthObservationMetaData(
            EOP.identifier(cls.get_identifier(xml)),
            EOP.parentIdentifier(cls.get_parent_id(xml)),
            EOP.acquisitionType("NOMINAL"),
            EOP.productType("IMAGE"),
            EOP.status("ACQUIRED"),
        )

        result = OPT.EarthObservationResult(
            ns_gml.getRandomId(),
        )

        mask_cloud, ratio_cloud = get_mask_and_relcover(xml, "CLOUD", file_name)
        mask_snow, ratio_snow = get_mask_and_relcover(xml, "SNOW", file_name)

        if mask_cloud is not None:
            result.append(ns_eop.getMask("CLOUD", "VECTOR", geom=mask_cloud))

        if mask_snow is not None:
            result.append(ns_eop.getMask("SNOW", "VECTOR", geom=mask_snow))

        if ratio_cloud is not None:
            result.append(OPT.cloudCoverPercentage("%.4f"%(ratio_cloud*100), {"uom":"%"}))

        if ratio_snow is not None:
            result.append(OPT.snowCoverPercentage("%.4f"%(ratio_snow*100), {"uom":"%"}))

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
                ns_eop.getFootprint(*get_footprint_and_center(xml, file_name))
            ),
            OM.result(result),
            EOP.metaDataProperty(metadata),
        )

        xml_eop = etree.ElementTree(xml_eop)
        xml_eop.getroot().addprevious(ns_eop.getSchematronPI())
        return xml_eop
