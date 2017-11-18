#!/usr/bin/env python
#
# extract footprint of an envistat product
#
import sys
import traceback
import os.path
from osgeo import gdal; gdal.UseExceptions() #pylint: disable=multiple-statements
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements
import img_geom as ig

WGS84_SR = ig.parseSR("EPSG:4326")


def usage():
    print >>sys.stderr, "USAGE: %s <.N1> [WKT|WKB] [DEBUG]"


if __name__ == "__main__":
    # TODO: to improve CLI
    EXENAME = os.path.basename(sys.argv[0])
    DEBUG = False
    FORMAT = "WKB"

    try:
        INPUT = sys.argv[1]
        NP = 2
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg == "DEBUG":
                    DEBUG = True # dump debuging output

    except IndexError:
        print >>sys.stderr, "ERROR: %s: Not enough input arguments!" % EXENAME
        usage()
        sys.exit(1)

    except Exception, exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        usage()
        sys.exit(1)


    try:
        ds = gdal.Open(INPUT)
        gcps = [(p.GCPLine, p.GCPPixel, p.GCPX, p.GCPY) for p in ds.GetGCPs()]

        row0, row1 = [], []
        col0, col1 = [], []

        if len(gcps) == 0:
            raise ValueError("Source image has not GCP!")

        # get the grid dimension
        nc = 0
        for gcp in gcps:
            if gcp[0] < 1:
                nc += 1
            else:
                break
        nr = len(gcps) / nc

        # collect points
        xy = []
        for i in xrange(nr-1):
            xy.append(gcps[i*nc][2:4])
        for i in xrange(nc-1):
            xy.append(gcps[i+(nr-1)*nc][2:4])
        for i in xrange(nr-1):
            xy.append(gcps[(nr-i)*nc-1][2:4])
        for i in xrange(nc-1):
            xy.append(gcps[nc-i-1][2:4])
        xy.append(xy[0])

        # create polygon geometry
        lr = ogr.Geometry(ogr.wkbLinearRing)
        for p in xy:
            lr.AddPoint_2D(*p)
        geom = ogr.Geometry(ogr.wkbPolygon)
        geom.AddGeometry(lr)
        geom.AssignSpatialReference(WGS84_SR)

        # export
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))

    except Exception as exc:
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, exc)
        sys.exit(1)
