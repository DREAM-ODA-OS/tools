#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# XPATH extractions
#
# Author: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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

import re
from lxml.etree import parse, XMLParser

RE_ISO8601_NAIVE = re.compile(
    r"^[0-9]{4,4}-[0-9]{2,2}-[0-9]{2,2}[ T][0-9]{2,2}:[0-9]{2,2}:[0-9]{2,2}"
    r"(?:\.[0-9]+)?$"
)
RE_ISO8601_VALID = re.compile(
    r"^[0-9]{4,4}-[0-9]{2,2}-[0-9]{2,2}[ T][0-9]{2,2}:[0-9]{2,2}:[0-9]{2,2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2,2}:[0-9]{2,2})$"
)

def _match_attributes(elm, attribs):
    """ Match the element attributes. """
    for key, value in attribs.items():
        if elm.get(key) != value:
            return False
    return True


def _text(xml, xpath, attribs):
    """ Extract element text easily. """
    for elm in xml.findall(xpath):
        if _match_attributes(elm, attribs):
            return elm.text
    else:
        return None

def _list(xml, xpath, attribs):
    """ Extract text of all matched elements. """
    return [
        elm.text for elm in xml.findall(xpath)
        if _match_attributes(elm, attribs)
    ]

def fix_datetime(value):
    """ Fix ISO-8601 date-time string. """
    if value is None:
        return None
    elif RE_ISO8601_VALID.match(value):
        return value
    elif RE_ISO8601_NAIVE.match(value):
        return "%sZ" % value
    else:
        raise ValueError("Not a valid date-time! %r" % value)


TYPE = {
    "STRING": str,
    "DATETIME": fix_datetime,
    "FLOAT2INT": lambda v: "%d" % int(float(v)),
    "GMLCOORDS": lambda v: v.replace(",", " "),
}

def extract_xpath(fobj, name, fields):
    """ Extract XPath metadata fields. """

    # parse the XML file
    xml = parse(fobj, XMLParser(remove_blank_text=True))

    results = {}
    # extract fields
    for field_def in fields:
        type_ = field_def.get('type', 'STRING')
        if type_.startswith("LIST_"):
            filter_ = TYPE[type_[5:]]
            value = ", ".join(
                filter_(value) for value
                in  _list(
                    xml, field_def['xpath'], field_def.get('attributes', {})
                )
            )
        else:
            filter_ = TYPE[type_]
            value = filter_(_text(
                xml, field_def['xpath'], field_def.get('attributes', {})
            ))
        results[field_def['name']] = value

    return results
