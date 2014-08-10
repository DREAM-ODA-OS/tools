#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  sensor metadata-extraction profiles - QuickBird products
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

from .common import (
    GDAL_TYPES, OGC_TYPE_DEFS,
    check, extract, extattr,
)

import re
from .interfaces import Profile
from lxml import etree
import ns_opt20
import numpy as np
import geom as ig
import datetime as dt

def get_footprint_and_center(xml, n=10):
    elm = None
    for _elm in xml.find("//IMFFilename"):
        if _elm.tag.startswith("BAND_"):
            elm = _elm
            break
    vlist = [
        (float(extract(elm, "./ULLon")), float(extract(elm, "./ULLat"))),
        (float(extract(elm, "./URLon")), float(extract(elm, "./URLat"))),
        (float(extract(elm, "./LRLon")), float(extract(elm, "./LRLat"))),
        (float(extract(elm, "./LLLon")), float(extract(elm, "./LLLat"))),
    ]
    lon, lat = [], []
    lon_cnt, lat_cnt = 0.0, 0.0
    for i in xrange(len(vlist)):
        lon0, lat0 = vlist[i]
        lon1, lat1 = vlist[(i+1)%len(vlist)]
        lon.append(np.linspace(lon0, lon1, n, False))
        lat.append(np.linspace(lat0, lat1, n, False))
        lon_cnt += lon0
        lat_cnt += lat0
    lon_cnt *= 0.25
    lat_cnt *= 0.25
    lon, lat = np.concatenate(lon), np.concatenate(lat)
    if hasattr(np, 'nditer'):
        wkt0 = ",".join("%.9g %.9g"%(x, y) for x, y in np.nditer([lon, lat]))
    else:
        wkt0 = ",".join("%.9g %.9g"%(x, y) for x, y in zip(lon, lat))
    wkt0 = "EPSG:4326;POLYGON((%s, %.9g %.9g))"%(wkt0, lon[0], lat[0])
    wkt1 = "EPSG:4326;POINT(%.9g %.9g)"%(lon_cnt, lat_cnt)
    return ig.parseGeom(wkt0), ig.parseGeom(wkt1)

class ProfileQuickBird(Profile):
    mode = {"Multi":"MS", "P":"PAN"}
    c_types = {8: "uint8", 16: "uint16",}
    bands = {
        "P": "PAN",
        "B": "Blue",
        "G": "Green",
        "R": "Red",
        "N": "NIR",
    }
    bands_verbose = {
        "P": "Panchromatic Band",
        "B": "Blue Band",
        "G": "Green Band",
        "R": "Red Band",
        "N": "Near Infra-Red Band",
    }
    nilval = {
        "reason": "http://www.opengis.net/def/nil/OGC/0/inapplicable",
        "value": 0,
    }
    platform = {
        "QB02": ("QuickBird", "2")
    }

    @classmethod
    def check_profile(cls, xml):
        """ check whether the profile is applicable"""
        if xml.getroot().tag != "QuickBird":
            return False

        cnt = 0
        for elm in xml.getroot():
            if elm.tag.startswith("PRODUCT_"):
                cnt += 1
        if cnt == 0:
            return False
        elif cnt > 1:
            raise ValueError("Multi-product QB products not supported!")
            #return False

        if xml.find("/PRODUCT_1/IMFFilename") is None:
            return False

        cnt = 0
        for elm in xml.find("/PRODUCT_1/IMFFilename"):
            if elm.tag.startswith("IMAGE_"):
                cnt += 1
        if cnt == 0:
            return False
        elif cnt > 1:
            raise ValueError("Multi-product QB products not supported!")
            #return False

        if xml.find("/PRODUCT_1/IMFFilename/IMAGE_1") is None:
            return False

        return True


    @classmethod
    def get_identifier(cls, xml):
        """ get dataset's unique identifier """
        satid = extract(xml, "//IMAGE_1/satId")
        prodid = extattr(xml, "//IMFFilename", "href")[:-4]
        return "%s_%s"%(satid, prodid)

    @classmethod
    def get_parent_id(cls, xml):
        """ get collections's unique identifier """
        satid = extract(xml, "//IMAGE_1/satId")
        mode = cls.mode[extract(xml, "//IMFFilename/bandId")]
        geom = "RAW"
        return "%s:%s:%s"%(satid, mode, geom)

    @classmethod
    def extract_range_type(cls, xml):
        return cls.extract_range_type_sloppy(xml)

    @classmethod
    def extract_range_type_sloppy(cls, xml):
        """ Extract range definition applicable to all product
            of the same type.
        """
        base_name = cls.get_parent_id(xml)
        dtype = cls.c_types[int(extract(xml, "//IMFFilename/bitsPerPixel"))]
        gdal_dtype = check(GDAL_TYPES.get(dtype), 'data_type')
        ogc_dtype = check(OGC_TYPE_DEFS.get(dtype), 'data_type')

        bands = []
        nbands = 0
        for elm in xml.find("//IMFFilename"):
            if not elm.tag.startswith("BAND_"):
                continue
            bandid = elm.tag.partition("_")[2]
            nbands += 1
            bands.append({
                "identifier": bandid,
                "name": cls.bands[bandid],
                "description": cls.bands_verbose[bandid],
                "nil_values": [cls.nilval],
                "definition": ogc_dtype,
                "data_type": gdal_dtype,
                "gdal_interpretation": "Undefined",
                "uom": "none",
            })

        return {
            "name": "%s:%d:%s"%(base_name, nbands, dtype),
            "bands": bands,
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

        satid = extract(xml, "//IMAGE_1/satId")
        platform, pindex = cls.platform[satid]
        time_acq_start = extract(xml, "//IMAGE_1/firstLineTime")
        nrow = int(extract(xml, "//IMFFilename/numRows"))
        trow = float(extract(xml, "//IMAGE_1/exposureDuration"))
        tstart = dt.datetime(*(int(v) for v in re.split(r'[^\d]', time_acq_start)[:-1]))
        tstop = tstart + dt.timedelta(seconds=(nrow-1)*trow)
        time_acq_stop = "%sZ"%tstop.isoformat()

        time_prod = extract(xml, "//IMFFilename/generationTime")

        eo_equipment = EOP.EarthObservationEquipment(
            ns_gml.getRandomId(),
            EOP.platform(EOP.Platform(
                EOP.shortName(platform),
                EOP.serialIdentifier(pindex),
                EOP.orbitType("LEO"),
            )),
            EOP.instrument(EOP.Instrument(
                EOP.shortName(satid),
            )),
            EOP.sensor(EOP.Sensor(
                EOP.sensorType("OPTICAL"),
            )),
            EOP.acquisitionParameters(EOP.Acquisition(
                EOP.orbitNumber(extract(xml, "//IMAGE_1/revNumber")),
                EOP.lastOrbitNumber(extract(xml, "//IMAGE_1/revNumber")),
                EOP.orbitDirection("DESCENDING"),
                EOP.illuminationAzimuthAngle(extract(xml, "//IMAGE_1/sunAz"), {"uom": "deg"}),
                EOP.illuminationElevationAngle(extract(xml, "//IMAGE_1/sunEl"), {"uom": "deg"}),
                EOP.incidenceAngle("%g"%(90.0-float(extract(xml, "//IMAGE_1/satEl"))), {"uom": "deg"}),
            )),
        )

        metadata = EOP.EarthObservationMetaData(
            EOP.identifier(cls.get_identifier(xml)),
            EOP.parentIdentifier(cls.get_parent_id(xml)),
            EOP.acquisitionType("NOMINAL"),
            EOP.productType("IMAGE"),
            EOP.status("ACQUIRED"),
        )

        result = OPT.EarthObservationResult(ns_gml.getRandomId())

        cloud_cover = float(extract(xml, "//IMAGE_1/cloudCover"))
        if 0 <= cloud_cover and cloud_cover <= 1:
            result.append(OPT.cloudCoverPercentage("%.1f"%(100.0*cloud_cover), {"uom":"%"}))

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
            OM.result(result),
            EOP.metaDataProperty(metadata),
        )

        xml_eop = etree.ElementTree(xml_eop)
        #xml_eop.getroot().addprevious(ns_eop.getSchematronPI())
        return xml_eop
