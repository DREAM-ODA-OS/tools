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
#from lxml import etree as et
from envisat.eheader import ProductHeader
from profiles.common import GDAL_TYPES, OGC_TYPE_DEFS

JSON_OPTS = {'sort_keys': True, 'indent': 4, 'separators': (',', ': ')}

def bands_asar_amp(header, platform='ENVISAT:ASAR'):
    def _polar(pol):
        return pol[0]+pol[2]
    bands = []
    bands.append((_polar(header.sph['MDS1_TX_RX_POLAR']), 'uint16'))
    if header.sph['MDS2_TX_RX_POLAR'] != '   ':
        bands.append((_polar(header.sph['MDS2_TX_RX_POLAR']), 'uint16'))
    name = "%s:1B:%s:%s"%(platform, header.mph["PRODUCT"][4:7], bands[0][0])
    if len(bands) > 1:
        name = "%s:%s"%(name, bands[1][0])
    return name, bands

def bands_meris_l1b(header):
    bands = []
    #nband = header.sph['NUM_BANDS']
    cnt = 0
    for ds in header.dsds:
        if ds['DS_TYPE'] != 'M':
            continue
        if ds['DS_NAME'].startswith("Radiance"):
            cnt += 1
            bands.append(('Radiance%2.2d'%cnt, 'uint16'))
        elif ds['DS_NAME'].startswith("Flags"):
            bands.append(('Flags', 'uint8'))
        else:
            raise ValueError("Unexpected dataset '%s'"%(ds['DS_NAME']))
    name = "ENVISAT:MERIS:1B:%s:%s"%(header.mph["PRODUCT"][4:7], len(bands))
    return name, bands

def bands_meris_l2(header):
    bands = []
    #nband = header.sph['NUM_BANDS']
    cnt = 0
    for ds in header.dsds:
        if ds['DS_TYPE'] != 'M':
            continue
        if ds['DS_NAME'].startswith("Norm. rho_surf"):
            cnt += 1
            bands.append(('Reflectance%2.2d'%cnt, 'uint16'))
        elif ds['DS_NAME'].startswith("Vapour Content"):
            bands.append(('Vapour', 'uint8'))
        elif ds['DS_NAME'].startswith("Chl_1, TOAVI"):
            bands.append(('Chl_1_TOAVI', 'uint8'))
        elif ds['DS_NAME'].startswith("Chl_2, BOAVI"):
            bands.append(('Chl_2_BOAVI', 'uint8'))
        elif ds['DS_NAME'].startswith("YS, SPM, Rect. Rho"):
            bands.append(('YS', 'uint8'))
            bands.append(('TSM', 'uint8'))
        elif ds['DS_NAME'].startswith("Press PAR Alb"):
            bands.append(('Press_PAR_Alb', 'uint8'))
        elif ds['DS_NAME'].startswith("Epsilon, OPT"):
            bands.append(('AAE', 'uint8'))
            bands.append(('OPT', 'uint8'))
        elif ds['DS_NAME'].startswith("Flags"):
            bands.append(('Flasg', 'uint32'))
        else:
            raise ValueError("Unexpected dataset '%s'"%(ds['DS_NAME']))
    name = "ENVISAT:MERIS:2:%s:%s"%(header.mph["PRODUCT"][4:7], len(bands))
    return name, bands


def main(fname, sloppy):

    with file(fname) as fid:
        header = ProductHeader(fid)

    pid = header.mph["PRODUCT"]
    if pid.startswith("MER_") and pid[8] == '1':
        name, bands = bands_meris_l1b(header)
    elif pid.startswith("MER_") and pid[8] == '2':
        name, bands = bands_meris_l2(header)
    elif pid.startswith("ASA_") and pid[6] in ('P', 'M', 'G') and pid[8] == '1':
        name, bands = bands_asar_amp(header)
    elif pid.startswith("SAR_") and pid[6] in ('P', 'M', 'G') and pid[8] == '1':
        name, bands = bands_asar_amp(header, platform='ERS'+pid[-1]+":AMI-SAR")
    else:
        raise ValueError("Unsupported product type %s"%pid[:9])

    nilval = []
    nilval.append({
        "reason": "http://www.opengis.net/def/nil/OGC/0/inapplicable",
        "value": 0,
    })

    bands_out = []
    for bname, btype in bands:
        bands_out.append({
            "identifier": bname,
            "name": bname,
            "description": bname,
            "definition": OGC_TYPE_DEFS[btype],
            "data_type": GDAL_TYPES[btype],
            "gdal_interpretation": "Undefined",
            "uom": "none",
            "nil_values": nilval,
        })

    rt = {
        "name": name,
        "bands": bands_out,
    }

    print json.dumps(rt, **JSON_OPTS)

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    EXENAME = os.path.basename(sys.argv[0])
    SLOPPY = False
    DEBUG = False

    try:
        INPUT = sys.argv[1]
        for arg in sys.argv[2:]:
            if arg == "DEBUG":
                DEBUG = True # dump debuging output
            elif arg == "SLOPPY":
                SLOPPY = True # dump debuging output

    except IndexError:
        print >>sys.stderr, "ERROR: %s: Not enough input arguments!"%EXENAME
        print >>sys.stderr
        print >>sys.stderr, "Extract EOxServer range-type (JSON) from N1 file."
        print >>sys.stderr
        print >>sys.stderr, "USAGE: %s <input-n1> [SLOPPY][DEBUG]"%EXENAME
        sys.exit(1)

    if DEBUG:
        print >>sys.stderr, "input-n1:   ", INPUT

    try:
        main(INPUT, SLOPPY)
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s "%(EXENAME, exc)
        if DEBUG:
            print >>sys.stderr, traceback.format_exc()
        sys.exit(1)
