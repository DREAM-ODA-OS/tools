#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#  sensor metadata-extraction profiles - common common interfaces
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
    tag, text, attr,
)

class Profile(object):

    @classmethod
    def get_identifier(cls, xml):
        """ get dataset's unique identifier """
        raise NotImplementedError

    @classmethod
    def get_parent_id(cls, xml):
        """ get collections's unique identifier """
        raise NotImplementedError

    @classmethod
    def check_profile(cls, xml):
        """ check whether the profile is applicable"""
        raise NotImplementedError

    @classmethod
    def extract_range_type(cls, xml):
        """ Extract full range type definition."""
        raise NotImplementedError

    @classmethod
    def extract_range_type_sloppy(cls, xml):
        """ Extract range definition applicable to all product
            of the same type.
        """
        raise NotImplementedError

    @classmethod
    def extract_eop_metadata(cls, xml, ns_eop=None, ns_gml=None):
        """ Extract range definition applicable to all product
            of the same type.
        """
        raise NotImplementedError


class ProfileDimap(Profile):
    version = None
    profile = None

    @classmethod
    def get_dimap_profile(cls, xml):
        """ check whether the profile is applicable"""
        root = tag(xml.find("."))
        format_ = text(xml.find("//METADATA_FORMAT"))
        version = attr(xml.find("//METADATA_FORMAT"), "version")
        profile = text(xml.find("//METADATA_PROFILE"))
        if root != "Dimap_Document" or format_ != "DIMAP":
            return None #raise ValueError("Not a DIMAP XML document!")
        return (profile, version)

    @classmethod
    def check_profile(cls, xml):
        """ check whether this profile is applicable or not"""
        return (cls.profile, cls.version) == cls.get_dimap_profile(xml)
