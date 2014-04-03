#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   Convert Spot4-Take5 metadata to EO-O&M
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

import sys 
import re 
import os.path 
from lxml import etree as et
#import img_geom as ig 
#from osgeo import ogr ; ogr.UseExceptions() 
#from osgeo import osr ; ogr.UseExceptions() 
#from osgeo import gdal ; gdal.UseExceptions() 

import geom as ig 

#------------------------------------------------------------------------------

def load_geometry( fname , debug = False ): 

    # open input geometry file 
    fin = sys.stdin if ( fname == "-" ) else open(fname) 

    # read the data 
    return ig.parseGeom( fin.read() , debug ) 


#------------------------------------------------------------------------------

re_date=r"(?P<date>\d{4,4}-\d{2,2}-\d{2,2})"
re_time=r"(?P<time>\d{2,2}:\d{2,2}:\d{2,2}(.\d{1,6})?)"
re_zone=r"(?P<zone>Z|[+\-]\d{2,2}(:\d{2,2})?)"
rec_dt=re.compile(r"^%s([ T]%s(%s)?)?$"%(re_date,re_time,re_zone))

def fix_time( s ): 
    """ fix date/time string """

    m = rec_dt.match( s ) 

    if ( m is None ) :
        d = {'date':None,'time':None,'zone':None}
    else : 
        d = m.groupdict()

    if d['date'] is None:
        raise ValueError( "Invalid date-time specification! DT='%s'" % s ) 
    
    if d['time'] is None : 
        d['time'] = "00:00:00"

    if d['zone'] is None : 
        d['zone'] = "Z"

    return "%sT%s%s"%(d['date'],d['time'],d['zone']) 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    PRETTY=False
    CMASK_GEOM=None 
    CMASK_RAS_URL=None
    CMASK_VEC_URL=None
    CMASK_RAS_SRS=None
    CMASK_VEC_SRS=None
    CC_PERCNT=None

    try: 

        ID      = sys.argv[1]
        XML     = sys.argv[2]
        OUTLINE = sys.argv[3]
        #DIM     = sys.argv[4]

        NP = 3 
        for arg in sys.argv[NP:] : 
            if ( arg == "DEBUG" ) : DEBUG = True # dump debuging output
            elif ( arg == "PRETTY" ) : PRETTY = True # pretty XML print 
            elif ( arg.startswith("CMASK_GEOM=") ) :  
                CMASK_GEOM=arg.partition("=")[2]
            elif ( arg.startswith("CMASK_RAS_URL=") ) :  
                CMASK_RAS_URL=arg.partition("=")[2]
            elif ( arg.startswith("CMASK_VEC_URL=") ) :  
                CMASK_VEC_URL=arg.partition("=")[2]
            elif ( arg.startswith("CMASK_RAS_SRS=") ) :  
                CMASK_RAS_SRS=arg.partition("=")[2]
            elif ( arg.startswith("CMASK_VEC_SRS=") ) :  
                CMASK_VEC_SRS=arg.partition("=")[2]
            elif ( arg.startswith("CC_PERCNT=") ) :  
                CC_PERCNT=arg.partition("=")[2]

    except IndexError : 
        
        sys.stderr.write("ERROR: Not enough input arguments!\n") 
        sys.stderr.write("\nConvert Spot4-Take5 metadata to EO-O&M\n") 
        sys.stderr.write("and dump it to std-out.\n") 
        sys.stderr.write("USAGE: %s <identifier> <xml-md> <geom> [DEBUG]\n"%EXENAME) 
        sys.exit(1) 


    if DEBUG: 
        print >>sys.stderr, "identifier:   ",ID
        print >>sys.stderr, "xml-metadata: ",XML
        print >>sys.stderr, "footprint:    ",OUTLINE


    if CC_PERCNT is not None : 
        try : 
            tmp = float(CC_PERCNT) 
            if tmp < 0.0 or tmp > 100.0 : 
                raise ValueError("Percentage does not fit the allowed range.")
            CC_PERCNT = "%.2f"%tmp
        except Exception as e : 
            print >>sys.stderr, "ERROR: %s: Invalid cloud cover percentage! "\
                                "CC_PERCNT=%s"%(EXENAME,CC_PERCNT)
            print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
            sys.exit(1)

    #--------------------------------------------------------------------------
    # loading geometries 

    # read the data 
    try: 
        outline = load_geometry( OUTLINE, DEBUG ) 

        if CMASK_GEOM is not None : 
            geom_cmask = load_geometry( CMASK_GEOM, DEBUG )
        else : 
            geom_cmask = None 

    except Exception as e : 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

    # check projection or assign when missing 
    if outline.GetSpatialReference() is None : 
        outline.AssignSpatialReference( ig.OSR_WGS84 )
    
    if not ig.OSR_WGS84.IsSame( outline.GetSpatialReference() ) : 
        print >>sys.stderr,"ERROR: %s: Geometry must be in WGS84 CRS!"%(EXENAME)
        sys.exit(1)

    # check projection of the cloud mask 
    if geom_cmask is not None : 
        if not ig.dumpSR(geom_cmask.GetSpatialReference()).startswith("EPSG") :
            print >>sys.stderr,"ERROR: %s: Geometry does not have a supported"\
                " spatial reference!"%(EXENAME) 
            sys.exit(1)

    #--------------------------------------------------------------------------
    # parse the XML metadata

    xml_in = et.parse(XML)  

    profile    = "OPT"
    platform   = xml_in.find("HEADER/PLATEFORM").text
    instrument = xml_in.find("HEADER/SENSOR").text
    sensor     = "OPTICAL"
    level      = xml_in.find("HEADER/LEVEL").text
    time_acq   = fix_time( xml_in.find("HEADER/DATE_PDV").text ) 
    time_prod  = fix_time( xml_in.find("HEADER/DATE_PROD").text ) 
    collection = (xml_in.find("HEADER/ZONE_GEO").text).replace("D0000B0000","")

    acq_type   = "NOMINAL" 
    prod_type  = "Spot4Take5_%s"%(level) 
    prod_stat  = "ARCHIVED"

    # get name of the original product 
    orig_prod  = xml_in.find("CTN_HISTORY/TASKS/TASK/INPUT_PRODUCTS/FILE").text

    # locate the source metadata 
    #orid_dim  = os.path.join(DIMDIR,os.path.basename(orig_prod),"METADATA.DIM") 

    #--------------------------------------------------------------------------
    # parse original DIM metadata 

    #xml_dim = et.parse( orid_dim ) 
    #xml_dim = et.parse( DIM ) 

    #dim_scene_source = xml_dim.find("Dataset_Sources/Source_Information/Scene_Source")
    #print "dim_scene_source =", dim_scene_source

    platform_name = "SPOT"
    platform_idx  = "4"
    #platform_name = dim_scene_source.find("MISSION").text
    #platform_idx  = dim_scene_source.find("MISSION_INDEX").text
    platfotm_orbit = "LEO"

    #instrument_name = "%s%s"%( dim_scene_source.find("INSTRUMENT").text , 
    #                           dim_scene_source.find("INSTRUMENT_INDEX").text ) 

    #time_acq = "%sT%sZ" % ( dim_scene_source.find("IMAGING_DATE").text ,
    #                        dim_scene_source.find("IMAGING_TIME").text ) 

    angles = xml_in.find("RADIOMETRY/ANGLES") 

    angle_incidence = "%+.8f"%(float(angles.find("THETA_V").text))
    angle_sun_azim  = "%+.8f"%(float(angles.find("PHI_S").text))
    angle_sun_elev  = "%+.8f"%(90-float(angles.find("THETA_S").text))

    orbit_direction = "DESCENDING"

    grid_reference  = os.path.basename(orig_prod).split("_")[2:4]
    grid_ref_lon    = "%d"%( int(grid_reference[0]) )
    grid_ref_lat    = "%d"%( int(grid_reference[1]) )

    #--------------------------------------------------------------------------
    # create output EO-O&M document 

    # import required namespaces 
    import ns_xlink as xlink 
    import ns_om20  as om
    import ns_ows20 as ows
    import ns_gml32 as gml 
    import ns_eop20 as eop
    import ns_opt20 as opt
 
    equipment = [ gml.getId() , 
        eop.E.platform( eop.E.Platform( 
#            eop.E.shortName( platform ), 
            eop.E.shortName(platform_name), 
            eop.E.serialIdentifier(platform_idx), 
            eop.E.orbitType(platfotm_orbit),
        )),
        eop.E.instrument( eop.E.Instrument(
            eop.E.shortName( instrument ), 
        )),
        eop.E.sensor( eop.E.Sensor(
            eop.E.sensorType( sensor ),
        )),
        eop.E.acquisitionParameters( eop.E.Acquisition( 
            eop.E.orbitDirection( orbit_direction ),
            eop.E.wrsLongitudeGrid( grid_ref_lon ),
            eop.E.wrsLatitudeGrid( grid_ref_lat ),
            eop.E.illuminationAzimuthAngle( angle_sun_azim, {"uom":"deg"} ), 
            eop.E.illuminationElevationAngle( angle_sun_elev, {"uom":"deg"} ), 
            eop.E.incidenceAngle( angle_incidence, {"uom":"deg"} ), 
        )),
    ]  

    result = [ gml.getId(),
    ] 

    # append optional vector cloud mask 
    if ( geom_cmask is not None ) : 
        rsi = ig.dumpSR( geom_cmask.GetSpatialReference() )
        result.append( eop.getMask("CLOUD","VECTOR",rsi,geom=geom_cmask) )

    # append optional referenced vector cloud mask 
    if ( CMASK_VEC_URL is not None ) : 
        result.append( eop.getMask("CLOUD","VECTOR",CMASK_VEC_SRS,url=CMASK_VEC_URL) ) 

    # append optional referenced raster cloud mask 
    if ( CMASK_RAS_URL is not None ) : 
        result.append( eop.getMask("CLOUD","RASTER",CMASK_RAS_SRS,url=CMASK_RAS_URL) ) 

    if CC_PERCNT is not None : 
        result.append( opt.E.cloudCoverPercentage(CC_PERCNT,{"uom":"%"}) )
        # NOTE: following does not pass the validation
        #result.append( opt.E.cloudCoverPercentageQuotationMode("AUTOMATIC") )


    # add cloud percentage 
    metadata = [
        eop.E.identifier(ID),
        eop.E.parentIdentifier(collection),
        eop.E.acquisitionType(acq_type),
        eop.E.productType(prod_type),
        eop.E.status(prod_stat),
    ] 

    xml = et.ElementTree( eop.E.EarthObservation( 
        gml.getRandomId(), eop.schemaLocation(profile),
        om.E.phenomenonTime( gml.getTimePeriod( time_acq, time_acq ) ), 
        om.E.resultTime( gml.getTimeInstant( time_prod ) ), 
        om.E.procedure( eop.E.EarthObservationEquipment( *equipment ) ),
        #om.E.observedProperty( {"nillReason":"inapplicable"} ),
        om.E.observedProperty( xlink.getHRef("#dummy") ),
        om.E.featureOfInterest( eop.getFootprint( outline ) ), 
        #om.E.result( eop.E.EarthObservationResult( *result ) ), 
        om.E.result( opt.E.EarthObservationResult( *result ) ), 
        eop.E.metaDataProperty( eop.E.EarthObservationMetaData( *metadata ) ), 
    )) 

    xml.getroot().addprevious( eop.getSchematronPI() ) 

    print et.tostring( xml, pretty_print=PRETTY, xml_declaration=True, encoding="utf-8") 



