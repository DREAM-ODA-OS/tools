#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  sensor metadata-extraction profiles - common utilities
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

import os.path
import re

RE_ISO_8601 = re.compile(
    r"^(?P<year>\d{4,4})-?(?P<month>\d{2,2})-?(?P<day>\d{2,2})"
    r"(?:[ T](?P<hour>\d{2,2})"
    r"(?::?(?P<min>\d{2,2})(?::?(?P<sec>\d{2,2}(?:\.\d+)?))?)?"
    r"(?P<tzone>(?:(?P<tzhour>[+-]\d{2,2})(?::?(?P<tzmin>\d{2,2}))?)|(?P<tzzero>Z))?"
    r")?$"
)

def isodt(dtstr):
    """Fix ISO 8601 date-time string."""
    def _dic2str(year, month, day, hour=None, min=None, sec=None,
            tzone=None, tzhour=None, tzmin=None, tzzero=None, **kwarg):
        tzhour = tzhour or '+00'
        tzmin = tzmin or '00'
        if tzone is None or tzzero == 'Z':
            tzone = 'Z'
        elif tzhour in ('+00', '-00') and tzmin == '00':
            tzone = 'Z'
        else:
            tzone = "%s:%s"%(tzhour, tzmin)
        return "%s-%s-%sT%s:%s:%s%s"%(
            year, month, day, hour or '00', min or '00', sec or '00', tzone
        )
    m = RE_ISO_8601.match(dtstr)
    if m is None:
        raise ValueError("Invalid ISO8601 date/time '%s'!"%dtstr)
    return _dic2str(**m.groupdict())


GDAL_TYPES = {
    'uint8' : "Byte",
    'uint16' : "UInt16",
}

OGC_TYPE_DEFS = {
    'uint8': "http://www.opengis.net/def/property/netcdf/1.0/byte",
    'uint16': "http://www.opengis.net/def/property/netcdf/1.0/unsignedShort",
}

def tag(elm):
    return None if elm is None else elm.tag

def text(elm):
    return None if elm is None else elm.text

def attr(elm, key):
    return None if elm is None else elm.get(key, None)

def check(val, label):
    if val is None:
        raise ValueError("Invalid %s!"%label)
    return val

def extract(elm, path, label=None):
    return check(text(elm.find(path)), label or os.path.basename(path))

def extattr(elm, path, key, label=None):
    return check(attr(elm.find(path), key), label or os.path.basename(path))
