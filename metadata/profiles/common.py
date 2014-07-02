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
