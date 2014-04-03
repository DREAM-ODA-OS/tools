#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Validate XML document against given schema. 
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

# NOTE: whenever possible use local schemes 
# export XML_CATALOG_FILES=" ... /schemas/catalog.xml"
#

import sys 
import re 
import os.path 
from lxml import etree as et
import ns_xsi as xsi

try: 
    # try the new API 
    from lxml import isoschematron
    HAS_ISOSCHEMATRON=True 
except ImportError :
    # default to the old API 
    HAS_ISOSCHEMATRON=False

#------------------------------------------------------------------------------

_rec_pi=re.compile(r"<\?([a-zA-Z_\-]*) *(.*) *\?>")
_rec_type=re.compile(r'^(?:.* )?type="(.*?)"')
_rec_href=re.compile(r'^(?:.* )?href="(.*?)"')


#def parseSchematronPI( pi ): 
#    
#    # parse the processing instruction 
#    m = _rec_pi.match(pi)
#    name, text = None,"" if ( m is None ) else m.groups()
#
#    if name != "xml-stylesheet" : return None 
#
#    # type 
#    m = _rec_type.match( text ) 
#    type = None if ( m is None ) else m.group(1)
#
#    if type != "text/xsl" : return None 
#
#    # href 
#    m = _rec_href.match( text ) 
#    href = None if ( m is None ) else m.group(1)
#
#    return href



#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # NOTE: 
    #       profile defines namespace 
    #       namespace defines schema 
    #       user provided profile overrides document namespace 
    #       user provided namespace overrides document namespace 
    #       user provided scheeme overrides document namespace 
    #

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    PRETTY=False
    PROFILE=None
    NS=None 
    SCHEMA=None     # exlicit schema specification 
    SCHEMATRON=None # additional schematron check 
    SCHEMA_ROOT=None # schema location (overiding the indicated location)  
    NS2SCHEMA={ 
        "http://www.opengis.net/eop/2.0" : "http://schemas.opengis.net/omeo/1.0/eop.xsd",
        "http://www.opengis.net/alt/2.0" : "http://schemas.opengis.net/omeo/1.0/alt.xsd",
        "http://www.opengis.net/atm/2.0" : "http://schemas.opengis.net/omeo/1.0/atm.xsd",
        "http://www.opengis.net/lmb/2.0" : "http://schemas.opengis.net/omeo/1.0/lmb.xsd",
        "http://www.opengis.net/opt/2.0" : "http://schemas.opengis.net/omeo/1.0/opt.xsd",
        "http://www.opengis.net/sar/2.0" : "http://schemas.opengis.net/omeo/1.0/sar.xsd",
        "http://www.opengis.net/sen1/2.0" : "http://schemas.opengis.net/omeo/1.0/sen1.xsd",
        "http://www.opengis.net/ssp/2.0" : "http://schemas.opengis.net/omeo/1.0/ssp.xsd",
    } 

    PROFILE2NS = { 
       "EOP"  : "http://www.opengis.net/eop/2.0" ,
       "ALT"  : "http://www.opengis.net/alt/2.0" ,
       "ATM"  : "http://www.opengis.net/atm/2.0" ,
       "LMB"  : "http://www.opengis.net/lmb/2.0" ,
       "OPT"  : "http://www.opengis.net/opt/2.0" ,
       "SAR"  : "http://www.opengis.net/sar/2.0" ,
       "SEN1" : "http://www.opengis.net/sen1/2.0" ,
       "SSP"  : "http://www.opengis.net/ssp/2.0" ,
    } 

    try: 

        XML     = sys.argv[1]

        NP = 1 
        for arg in sys.argv[NP:] : 
            if ( arg == "DEBUG" ) : DEBUG = True # dump debuging output
            elif ( arg == "PRETTY" ) : PRETTY = True # pretty XML print 
            elif arg.startswith("SCHEMA=" ) :
                SCHEMA=arg.partition("=")[2]
            elif arg.startswith("SCHEMATRON=" ) :
                SCHEMATRON=arg.partition("=")[2]
            elif arg.startswith("SCHEMA_ROOT=" ) :
                SCHEMA_ROOT=arg.partition("=")[2]
            elif arg.startswith("NS=" ) :
                NS=arg.partition("=")[2]
            elif ( arg in PROFILE2NS ) : 
                PROFILE=arg 

    except IndexError : 
        
        sys.stderr.write("ERROR: Not enough input arguments!\n") 
        sys.stderr.write("\nValidate EO-O&M XML document.\n\n") 
        sys.stderr.write("USAGE: %s <xml> [DEBUG]\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------
    # load XML document which is being validated 

    if DEBUG : 
        print >>sys.stderr, "xml-doc.:   %s"%( XML ) 

    if XML == "-" : XML=sys.stdin 

    try: 
        xml = et.parse( XML ) # 
    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: Failed to parse the input XML! " \
                            "INPUT=%s"%(EXENAME,XML)
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

    #--------------------------------------------------------------------------
    # handle schema locations 

    # map profile to namespace 
    if PROFILE is not None : 
        try: 
            NS = PROFILE2NS[PROFILE]
        except KeyError : 
            print >>sys.stderr, "ERROR: %s: Invalid profile! " \
                                "PROFILE=%s\n"%(EXENAME,PROFILE)
            sys.exit(1)

    # extract schema location
    if NS is None : 
        schmloc = xml.getroot().get( xsi.schemaLocation )
        if schmloc is not None : 
            tmp = schmloc.strip().partition(" ") 
            NS=tmp[0].strip() 
            if SCHEMA is None : 
                SCHEMA=tmp[2].strip() 
            if len(SCHEMA)==0 : SCHEMA=None 

    # if no schema available gueess one from the namespace 
    if SCHEMA is None : 
        if NS is None : NS = PROFILE2NS["EOP"]
        try: 
            SCHEMA = NS2SCHEMA[NS]
        except KeyError : 
            print >>sys.stderr, "ERROR: %s: Invalid namespace!" \
                                " NS=\n"%(EXENAME,NS)
            sys.exit(1)

    # get schematron rules 
    for pi in xml.getroot().xpath('preceding-sibling::node()') : 
        if pi.get("type").lower() == "text/xsl" : 
            SCHEMATRON=pi.get("href")
            if SCHEMATRON is not None : 
                break

    # in case of explicit root input the schemes are re-rooted
    if SCHEMA_ROOT is not None : 

        SCHEMA=os.path.join( SCHEMA_ROOT, os.path.basename( SCHEMA ) ) 
        SCHEMATRON=os.path.join( SCHEMA_ROOT, os.path.basename( SCHEMATRON ) ) 
        
    if DEBUG : 
        print >>sys.stderr, "namespace:  %s"%( NS ) 
        print >>sys.stderr, "schema:     %s"%( SCHEMA ) 
        print >>sys.stderr, "schematron: %s"%( SCHEMATRON ) 

    #--------------------------------------------------------------------------

    if SCHEMA is not None : 
        if DEBUG : 
            print >>sys.stderr, "XML schema validation ... "

        xmlschema = et.XMLSchema( et.parse(SCHEMA) ) 

        xmlschema.assertValid( xml ) 

        if DEBUG : 
            print >>sys.stderr, "XML schema validation PASSED "
    else : 

        if DEBUG : 
            print >>sys.stderr, "XML schema validation SKIPPED "


    # TODO: Fix schematron validation!
    SCHEMATRON=None
    if SCHEMATRON is not None : 
        if DEBUG : 
            print >>sys.stderr, "schematron validation ... "
    
        if HAS_ISOSCHEMATRON :

            schmtrn = isoschematron.Schematron( et.parse(SCHEMATRON) ) 

        else :

            schmtrn = et.Schematron( et.parse(SCHEMATRON) ) 

        schmtrn.assertValid( xml )

        if DEBUG : 
            print >>sys.stderr, "schematron validation PASSED "
    else : 
        if DEBUG : 
            print >>sys.stderr, "schematron validation SKIPPED "

    #--------------------------------------------------------------------------
    # print the valid xml 

    print et.tostring( xml, pretty_print=PRETTY, xml_declaration=True, encoding="utf-8") 
