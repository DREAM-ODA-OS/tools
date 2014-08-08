#!/usr/bin/env python
#
# extract footprint of an envistat product 
#
import sys
import traceback
import os.path 
from osgeo import gdal ; gdal.UseExceptions() 
from osgeo import ogr ; ogr.UseExceptions()
from osgeo import osr ; ogr.UseExceptions() 

import img_geom as ig 

# TODO: Proper CLI 

WGS84_SR=ig.parseSR("EPSG:4326")

#------------------------------------------------------------------------------

def usage(): 
    sys.stderr.write("USAGE: %s <.N1> [WKT|WKB] [DEBUG]\n")

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 
    FORMAT="WKB"

    try: 

        INPUT  = sys.argv[1]
        NP = 2 
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if ( arg in ig.OUTPUT_FORMATS ) : FORMAT=arg # output format
                elif ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

    except IndexError : 
        sys.stderr.write("ERROR: %s: Not enough input arguments!\n"%EXENAME) 
        usage() 
        sys.exit(1) 

    except Exception, e : 
        sys.stderr.write("ERROR: %s: %s\n"%(EXENAME,e)) 
        usage() 
        sys.exit(1) 

    #--------------------------------------------------------------------------

    # read the data 
    try: 

        ds = gdal.Open(INPUT)

        gcps = [ (p.GCPLine,p.GCPPixel,p.GCPX,p.GCPY) for p in ds.GetGCPs() ] 

        row0 = []
        row1 = []
        col0 = []
        col1 = []

        # get the grid dimension

        nc=0 
        for gcp in gcps : 
            if ( gcp[0] < 1 ) : 
                nc+=1 
            else : 
                break 

        nr = len(gcps) / nc 

        # create polygon geometry 
        lr = ogr.Geometry( ogr.wkbLinearRing ) 
            
        for i in xrange(nr-1): 
            lr.AddPoint_2D( *gcps[i*nc][2:4] ) 

        for i in xrange(nc-1): 
            lr.AddPoint_2D( *gcps[i+(nr-1)*nc][2:4] )

        for i in xrange(nr-1): 
            lr.AddPoint_2D( *gcps[(nr-i)*nc-1][2:4] )

        for i in xrange(nc-1): 
            lr.AddPoint_2D( *gcps[nc-i-1][2:4] )

        lr.CloseRings()

        geom = ogr.Geometry( ogr.wkbPolygon )
        geom.AddGeometry( lr )
        geom.AssignSpatialReference( WGS84_SR )

        # export
        sys.stdout.write(ig.dumpGeom(geom,FORMAT)) 

    except Exception as e : 
        if DEBUG : traceback.print_exc( file=sys.stderr ) 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)
