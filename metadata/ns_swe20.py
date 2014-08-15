#------------------------------------------------------------------------------
#
#   SWE v2.0 namespace
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

#------------------------------------------------------------------------------
# namespace

NS = "http://www.opengis.net/swe/2.0"
NS_MAP = {"swe": NS}

#------------------------------------------------------------------------------
# element maker

E = ElementMaker(namespace=NS, nsmap=NS_MAP)

#------------------------------------------------------------------------------
# predefined fully qualified names

# attributes

# elements
DataRecord = nn(NS, 'DataRecord')
AllowedValues = nn(NS, 'AllowedValues')
NilValues = nn(NS, 'NilValues')
field = nn(NS, 'field')
Quantity = nn(NS, 'Quantity')
description = nn(NS, 'description')
nilValues = nn(NS, 'nilValues')
nilValue = nn(NS, 'nilValue')
uom = nn(NS, 'uom')
constraint = nn(NS, 'constraint')
interval = nn(NS, 'interval')
significantFigures = nn(NS, 'significantFigures')

