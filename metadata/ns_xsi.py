#------------------------------------------------------------------------------
# 
#   XSI namespace 
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

#from lxml.builder import ElementMaker
from xml_utils import nn 

#------------------------------------------------------------------------------
# schema location attribute 
def getSchemaLocation( sl ) : return { schemaLocation : sl } 

#------------------------------------------------------------------------------
# namespace 

NS="http://www.w3.org/2001/XMLSchema-instance"
NS_MAP={ "xsi" : NS }

#------------------------------------------------------------------------------
# element maker 

#E = ElementMaker(namespace=NS,nsmap=NS_MAP) 

#------------------------------------------------------------------------------
# predefined fully qualified names 

# attributes 
schemaLocation = nn(NS, "schemaLocation") 
nil = nn(NS, "nil")

# elements 
