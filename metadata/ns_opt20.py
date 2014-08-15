#------------------------------------------------------------------------------
#
#   EOP-OPT v1.0 namespace
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

from lxml.builder import ElementMaker
from xml_utils import nn

import ns_eop20 as ns_eop
import ns_om20 as ns_om
import ns_ows20 as ns_ows
import ns_gml32 as ns_gml
import ns_swe10 as ns_swe
import ns_xsi as ns_xsi
import ns_xlink as ns_xlink

#------------------------------------------------------------------------------
# namespace
#------------------------------------------------------------------------------
# schema location attribute

# SchemaTron Rules
STR = "http://schemas.opengis.net/omeo/1.0/schematron_rules_for_eop.xsl"
# schema
SL = "http://www.opengis.net/opt/2.0 http://schemas.opengis.net/omeo/1.0/opt.xsd"

#------------------------------------------------------------------------------
# namespace
NS = "http://www.opengis.net/opt/2.0"
NS_MAP = {"opt": NS,
          "eop": ns_eop.NS,
          "om": ns_om.NS,
          "ows": ns_ows.NS,
          "gml": ns_gml.NS,
          "xsi": ns_xsi.NS,
          "xlink": ns_xlink.NS}

#------------------------------------------------------------------------------
# element maker
E = ElementMaker(namespace=NS, nsmap=NS_MAP)

#------------------------------------------------------------------------------
# predefined fully qualified names

# attributes

# elements
EarthObservation = nn(NS, "EarthObservation")
EarthObservationResult = nn(NS, "EarthObservationResult")
cloudCoverPercentage = nn(NS, "cloudCoverPercentage")
cloudCoverPercentageQuotationMode = nn(NS, "cloudCoverPercentageQuotationMode")
snowCoverPercentage = nn(NS, "snowCoverPercentage")
snowCoverPercentageQuotationMode = nn(NS, "snowCoverPercentageQuotationMode")

#X = nn(NS, "X")
