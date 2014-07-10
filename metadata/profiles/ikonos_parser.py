#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Ikonos metadata parser and converter - library.
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
#import sys
import os.path
from lxml import etree

RE_WS = re.compile(r"\s+")
RE_INV = re.compile(r"[/,]")
RE_LINE = re.compile(r"^(?P<ind>\s*)(?P<key>[^:^(]*)(?:\((?P<info>.*)\))?(?::\s*(?P<val>.*))?\s*")


def load_as_xml(fname, resolve_references=False, element=None):
    """ Load QuickBird metadata as a single XML tree."""

    with file(fname) as fid:
        xml = _parse(fid, fname, element)

    if resolve_references:
        #locate header files
        headers = etree.SubElement(xml, "Headers")
        for elm in xml.iterfind("./Product_Component_Metadata/Component_File_Name"):
            for fname_img in elm.text.split(" "):
                fname_hdr = os.path.splitext(fname_img)[0]+".hdr"
                elm_hdr = etree.SubElement(headers, "Header", {"href": fname_hdr})
                load_as_xml(_set_path(fname_hdr, fname), False, elm_hdr)
                fname_rpc = os.path.splitext(fname_img)[0]+"_rpc.txt"
                elm_rpc = etree.SubElement(elm_hdr, "RPC", {"href": fname_rpc})
                load_as_xml(_set_path(fname_rpc, fname), False, elm_rpc)

        shapes = etree.SubElement(xml, "Shapes")
        fname_md = os.path.basename(fname)
        if fname_md.endswith("_metadata.txt"):
            fname_base = fname_md[:-len("_metadata.txt")]
            fname_aoi = fname_base + "_aoi.shp"
            fname_cmp = fname_base + "_component.shp"
            fname_img = fname_base + "_image.shp"
            etree.SubElement(shapes, "Shape", {"href": fname_aoi, "type": "AOI"})
            etree.SubElement(shapes, "Shape", {"href": fname_cmp, "type": "COMPONENT"})
            etree.SubElement(shapes, "Shape", {"href": fname_img, "type": "IMAGE"})

    if element is None:
        headers = etree.SubElement(xml, "Headers")

    return xml


def _set_path(dst, src=None):
    dname = "." if src is None else os.path.dirname(src)
    return os.path.join(dname, dst)

def _parse(fid, fname, element=None):
    """ Parse Ikonos metadata document."""

    def _parse_value(val):
        tmp = RE_WS.sub(" ", val.strip()).split(" ")
        if len(tmp) > 1:
            #if tmp[-3:] in Bits_per_Pixel_per_Band
            if len(tmp) > 3 and tmp[-3:] == ["bits", "per", "pixel"]:
                return " ".join(tmp[:-3]), " ".join(tmp[-3:])
            if tmp[-1] in ("degrees", "meters", "pixels"):
                return " ".join(tmp[:-1]), tmp[-1]
            if tmp[-1] == "GMT":
                return "T".join(tmp[:-1])+"Z", None
        return val, None

    line_count = [0]
    indent_last = 0
    estack = []
    text = None
    text_buffer = []
    if element is None:
        element = etree.Element("Ikonos", {"href": os.path.basename(fname)})
    root = element

    for src_line in fid:
        line_count[0] += 1
        src_line = src_line.rstrip().expandtabs()
        line = RE_LINE.match(src_line).groupdict()
        if indent_last > len(line['ind']) and estack:
            element = estack.pop() # exit group
        if text is not None:
            if src_line.startswith("="):
                text.text = "\n".join(text_buffer)
                text = None
                text_buffer = []
            else:
                text_buffer.append(src_line[indent_last:])
                continue
        indent_last = len(line['ind'])
        if len(line['key']) == 0:
            continue  # skip empty lines and separators
        if line['key'].startswith("="):
            while estack:
                element = estack.pop()
            continue  # skip empty lines and separators
        tag = line['key'].strip()
        tag = RE_WS.sub("_", tag)
        tag = RE_INV.sub("", tag)
        if line['val'] is not None:
            if len(line['val']) == 0:
                line['val'] = fid.next().strip()
                line_count[0] += 1
            elm = etree.SubElement(element, tag)
            if line['info'] is not None:
                elm.set('info', line['info'])
            val, uom = _parse_value(line['val'])
            if uom is not None:
                elm.set('uom', uom)
            elm.text = val
        else:
            estack.append(element)
            elm = etree.SubElement(element, tag)
            if line['info'] is not None:
                elm.set('info', line['info'])
            element = elm
            if tag == "Company_Information":
                text = element
    return root


