#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   QuickBird metadata parser and converter - library.
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

import re
import os.path
import sys
from lxml import etree
try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

RE_WS = re.compile(r"[,\s]+")


def load_as_xml(fname, resolve_references=False, element=None):
    """ Load QuickBird metadata as a single XML tree."""
    if fname.endswith("COMMERCIAL.TXT"):
        return None
    with file(fname) as fid:
        try:
            md = _parse(fid, fname)
        except ValueError as e:
            if element is None:
                raise
            else:
                print >>sys.stderr, "WARNING: %s!"%e
                return None
    xml = _to_xml(md, fname, resolve_references, element)
    if element is None:
        xml = etree.ElementTree(xml)
    return xml


def _to_xml(obj, fname, resolve_references=False, element=None):
    """ Convert parsed metadata to an XML documents."""
    gstack = []
    estack = []
    group = obj.iteritems()
    if element is None:
        element = etree.Element("QuickBird", {"href": os.path.basename(fname)})
    while True:
        try:
            key, val = group.next()
        except StopIteration:
            if len(gstack) == 0:
                break
            group = gstack.pop()
            element = estack.pop()
            continue
        if isinstance(val, dict):
            gstack.append(group)
            estack.append(element)
            element = etree.SubElement(element, key)
            group = val.iteritems()
        elif isinstance(val, list):
            _elm = etree.SubElement(element, key)
            for item in val:
                etree.SubElement(_elm, "arrayItem").text = item
        else:
            if key.endswith("Filename"):
                _elm = etree.SubElement(element, key, {"href": val})
                if resolve_references:
                    load_as_xml(_set_path(val, fname), False, _elm)
            else:
                etree.SubElement(element, key).text = val
    return element

def _set_path(dst, src=None):
    dname = "." if src is None else os.path.dirname(src)
    return os.path.join(dname, dst)

def _parse(fid, fname):
    """ Parse QuickBird metadata document."""
    def _strip_indent(val):
        tmp = val.lstrip()
        return tmp, len(val)-len(tmp)

    def _parse_type(val):
        if val[0] == '"' and val[-1] == '"':
            return val[1:-1]
        if val[0] == '(' and val[-1] == ')':
            return RE_WS.sub(" ", val[1:-1]).strip()
#        for type_ in (int, float):
#            try:
#                return type_(val)
#            except ValueError:
#                pass
        return val.strip()

    def _read_array(fid):
        for src_line in fid:
            line_count[0] += 1
            line = src_line.strip()
            if line.endswith(","):
                yield _parse_type(line[:-1].rstrip())
            elif line.endswith(");"):
                yield _parse_type(line[:-2].rstrip())
                break
            else:
                raise ValueError("%s: Invalid array item at line nr.%d: %r"%(fname, line_count[0], src_line))

    gstack = []
    bstack = []
    group = OrderedDict()
    block = None
    level = 0
    line_count = [0]

    for src_line in fid:
        line_count[0] += 1
        line = src_line.rstrip()
        has_semicolon = line[-1] == ';'
        if has_semicolon:
            line = line[:-1]
        if len(line) == 0:  # skip empty lines
            continue
        line, lev = _strip_indent(line)
        key, sep, val = line.partition(" = ")
        if len(sep) and has_semicolon:
            if level != lev:
                raise ValueError("%s: Invalid indentation at line nr.%d: %r"%(fname, line_count[0], src_line))
            group[key] = _parse_type(val)
        elif len(sep) and not has_semicolon:
            if val == "(":
                arr = []
                for item in _read_array(fid):
                    arr.append(item)
                group[key] = arr
            elif key == "BEGIN_GROUP":
                gstack.append(group)
                bstack.append(block)
                group = OrderedDict()
                block = val
                level += 1
            elif key == "END_GROUP":
                if block != val:
                    raise ValueError("%s: Invalid group end at line nr.%d: %r"%(fname, line_count[0], src_line))
                gstack[-1][val] = group
                group = gstack.pop()
                block = bstack.pop()
                level -= 1
            else:
                raise ValueError("%s: Invalid line no.%d: %r"%(fname, line_count[0], src_line))
        elif key == "END" and len(sep) == 0 and len(val) == 0 and has_semicolon:
            break
        else:
            raise ValueError("%s: Invalid line no.%d: %r"%(fname, line_count[0], src_line))
    return group
