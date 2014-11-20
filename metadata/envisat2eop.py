#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Generate EOxServer JSON range type from ENVISAT product
#
# Project: XML Metadata Handling
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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
from lxml import etree
from envisat.eheader import ProductHeader
import ns_opt20
import ns_sar20
import ns_xsi

XML_OPTS = {'pretty_print': True, 'xml_declaration': True, 'encoding': 'utf-8'}

def get_footprint_and_center(header):
    return []

def eop_asar(header, platform='ENVISAT:ASAR', ns_sar=None):
    ns_sar = ns_sar or ns_sar20
    ns_eop = ns_sar.ns_eop
    ns_gml = ns_sar.ns_gml
    ns_om = ns_sar.ns_om
    SAR = ns_sar.E
    EOP = ns_eop.E
    OM = ns_om.E

    def _polar(pol):
        return pol[0]+pol[2]

    time_acq_start = header.sph['FIRST_LINE_TIME'].isoformat().replace("+00:00", "Z")
    time_acq_stop = header.sph['LAST_LINE_TIME'].isoformat().replace("+00:00", "Z")
    time_prod = header.mph['PROC_TIME'].isoformat().replace("+00:00", "Z")

    if platform == "ENVISAT:ASAR":
        _platform = EOP.Platform(
            EOP.shortName("Envisat"),
            EOP.orbitType("LEO"),
        )
        _instrument = "ASAR"
        _opmode = header.mph['PRODUCT'][4:6]
        _polmode = "D" if _opmode == "AP" else "S"
        if _opmode in ("IM", "AP"):
            _wrs_code_space = "ENVISAT ASAR IM/AP"
        elif _opmode in ("WS", "GM"):
            _wrs_code_space = "ENVISAT ASAR WS"
        else:
            _wrs_code_space = "ENVISAT ASAR"
    elif platform == "ERS1:AMI-SAR":
        _platform = EOP.Platform(
            EOP.shortName("ERS"),
            EOP.serialIdentifier("1"),
            EOP.orbitType("LEO"),
        )
        _instrument = "AMI/SAR"
        _opmode = "Image"
        _polmode = "S"
        _wrs_code_space = "ERS SAR"
    elif platform == "ERS2:AMI-SAR":
        _platform = EOP.Platform(
            EOP.shortName("ERS"),
            EOP.serialIdentifier("2"),
            EOP.orbitType("LEO"),
        )
        _instrument = "AMI/SAR"
        _opmode = "Image"
        _polmode = "S"
        _wrs_code_space = "ERS SAR"

    _polchannels = [_polar(header.sph['MDS1_TX_RX_POLAR'])]
    if header.sph['MDS2_TX_RX_POLAR'] != '   ':
        _polchannels.append(_polar(header.sph['MDS2_TX_RX_POLAR']))
    if len(_polchannels) > 1:
        if _polchannels[1] == "VV":
            _polchannels = (_polchannels[1], _polchannels[0])
        if _polchannels[1] == "HH":
            _polchannels = (_polchannels[1], _polchannels[0])
    _polchannels = ", ".join(_polchannels)

    eo_equipment = EOP.EarthObservationEquipment(
        ns_gml.getRandomId(),
        EOP.platform(_platform),
        EOP.instrument(EOP.Instrument(
                EOP.shortName(_instrument)
            ),
        ),
        EOP.sensor(EOP.Sensor(
            EOP.sensorType("RADAR"),
            EOP.operationalMode(_opmode),
            EOP.swathIdentifier(header.sph['SWATH']),
        )),
        EOP.acquisitionParameters(SAR.Acquisition(
            EOP.orbitNumber("%d"%header.mph['ABS_ORBIT']),
            EOP.orbitDirection(header.sph['PASS'].strip()),
            EOP.wrsLongitudeGrid("%d"%header.mph['REL_ORBIT'],
                **{'codeSpace': _wrs_code_space}),
            SAR.polarisationMode(_polmode),
            SAR.polarisationChannels(_polchannels),
        )),
    )

    metadata = EOP.EarthObservationMetaData(
        EOP.identifier(header.mph['PRODUCT'][:-3]),
        EOP.parentIdentifier("ENVISAT:%s"%(header.mph['PRODUCT'][:9])),
        EOP.acquisitionType("NOMINAL"),
        EOP.productType(header.mph['PRODUCT'][:10]),
        EOP.status("ARCHIVED"),
        EOP.downlinkedTo(
            EOP.DownlinkInformation(
                EOP.acquisitionStation(header.mph['ACQUISITION_STATION'].strip()),
            ),
        ),
        EOP.processing(
            EOP.ProcessingInformation(
                EOP.processingCenter(header.mph['PROC_CENTER'].strip()),
                EOP.processingDate(time_prod),
                EOP.processorVersion(header.mph['SOFTWARE_VER'].strip()),
            ),
        ),
    )

    xml_eop = SAR.EarthObservation(
        ns_gml.getRandomId(),
        ns_eop.getSchemaLocation("SAR"),
        OM.phenomenonTime(ns_gml.getTimePeriod(time_acq_start, time_acq_stop)),
        #OM.resultQuality(), #optional
        OM.resultTime(ns_gml.getTimeInstant(time_acq_stop)),
        #OM.validTime(), # optional
        OM.procedure(eo_equipment),
        OM.observedProperty({ns_xsi.nil: "true", "nilReason": "inapplicable"}),
        OM.featureOfInterest(
            #ns_eop.getFootprint(*get_footprint_and_center(header))
        ),
        OM.result(EOP.EarthObservationResult(ns_gml.getRandomId())),
        EOP.metaDataProperty(metadata),
    )
    xml_eop = etree.ElementTree(xml_eop)
    #xml_eop.getroot().addprevious(ns_eop.getSchematronPI())
    return xml_eop

def eop_meris(header, ns_opt=None):
    ns_opt = ns_opt or ns_opt20
    ns_eop = ns_opt.ns_eop
    ns_gml = ns_opt.ns_gml
    ns_om = ns_opt.ns_om
    OPT = ns_opt.E
    EOP = ns_eop.E
    OM = ns_om.E

    time_acq_start = header.sph['FIRST_LINE_TIME'].isoformat().replace("+00:00", "Z")
    time_acq_stop = header.sph['LAST_LINE_TIME'].isoformat().replace("+00:00", "Z")
    time_prod = header.mph['PROC_TIME'].isoformat().replace("+00:00", "Z")

    if header.sph['FIRST_MID_LAT'] > header.sph['LAST_MID_LAT']:
        _pass = "DESCENDING"
    else:
        _pass = "ASCENDING"

    eo_equipment = EOP.EarthObservationEquipment(
        ns_gml.getRandomId(),
        EOP.platform(EOP.Platform(
            EOP.shortName("Envisat"),
            EOP.orbitType("LEO"),
        )),
        EOP.instrument(EOP.Instrument(
                EOP.shortName("MERIS")
            ),
        ),
        EOP.sensor(EOP.Sensor(
            EOP.sensorType("OPTICAL"),
            EOP.operationalMode(header.mph['PRODUCT'][4:6]),
        )),
        EOP.acquisitionParameters(EOP.Acquisition(
            EOP.orbitNumber("%d"%header.mph['ABS_ORBIT']),
            EOP.orbitDirection(_pass),
            EOP.wrsLongitudeGrid("%d"%header.mph['REL_ORBIT'],
                **{'codeSpace': "ENVISAT MERIS"}),
        )),
    )

    metadata = EOP.EarthObservationMetaData(
        EOP.identifier(header.mph['PRODUCT'][:-3]),
        EOP.parentIdentifier("ENVISAT:%s"%(header.mph['PRODUCT'][:9])),
        EOP.acquisitionType("NOMINAL"),
        EOP.productType(header.mph['PRODUCT'][:10]),
        EOP.status("ARCHIVED"),
        EOP.downlinkedTo(
            EOP.DownlinkInformation(
                EOP.acquisitionStation(header.mph['ACQUISITION_STATION'].strip()),
            ),
        ),
        EOP.processing(
            EOP.ProcessingInformation(
                EOP.processingCenter(header.mph['PROC_CENTER'].strip()),
                EOP.processingDate(time_prod),
                EOP.processorVersion(header.mph['SOFTWARE_VER'].strip()),
            ),
        ),
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
        OM.observedProperty({ns_xsi.nil: "true", "nilReason": "inapplicable"}),
        OM.featureOfInterest(
            #ns_eop.getFootprint(*get_footprint_and_center(header))
        ),
        OM.result(OPT.EarthObservationResult(ns_gml.getRandomId())),
        EOP.metaDataProperty(metadata),
    )
    xml_eop = etree.ElementTree(xml_eop)
    #xml_eop.getroot().addprevious(ns_eop.getSchematronPI())
    return xml_eop



def main(fname):
    with file(fname) as fid:
        header = ProductHeader(fid)

    #print header.mph
    #print "----------------------"
    #print header.sph

    pid = header.mph["PRODUCT"]
    if pid.startswith("MER_") and pid[8] == '1':
        eop = eop_meris(header)
    elif pid.startswith("MER_") and pid[8] == '2':
        eop = eop_meris(header)
    elif pid.startswith("ASA_") and pid[6] in ('P', 'M', 'G') and pid[8] == '1':
        eop = eop_asar(header)
    elif pid.startswith("SAR_") and pid[6] in ('P', 'M', 'G') and pid[8] == '1':
        eop = eop_asar(header, platform='ERS'+pid[-1]+":AMI-SAR")
    else:
        raise ValueError("Unsupported product type %s"%pid[:9])

    print etree.tostring(eop, **XML_OPTS)

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
        print >>sys.stderr, "Extract EOxServer range-type (JSON) from N1 file."
        print >>sys.stderr
        print >>sys.stderr, "USAGE: %s <input-n1> [DEBUG]"%EXENAME
        sys.exit(1)

    if DEBUG:
        print >>sys.stderr, "input-n1:   ", INPUT

    try:
        main(INPUT)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s "%(EXENAME, exc)
        if DEBUG:
            print >>sys.stderr, traceback.format_exc()
        sys.exit(1)
