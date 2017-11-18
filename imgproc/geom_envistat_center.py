#!/usr/bin/env python
#
# extract scene centre of an Envistat product
#
import sys
import traceback
import os.path
from osgeo import gdal; gdal.UseExceptions() #pylint: disable=multiple-statements
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements
import img_geom as ig

WGS84_SR = ig.parseSR("EPSG:4326")


def interp_bilin((c, r), v):
    """ simple bilinear GCP interpolation """
    # pylint: disable=invalid-name
    ac = (c - v[0][0]) / (v[2][0] - v[0][0])
    ar = (r - v[0][1]) / (v[1][1] - v[0][1])
    n = [(1-ac)*(1-ar), (1-ac)*ar, ac*ar, ac*(1-ar)]
    x = sum(nn*vv[2] for nn, vv in zip(n, v))
    y = sum(nn*vv[3] for nn, vv in zip(n, v))
    return x, y


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

        #get centroind in pixel coordinates
        rc_cnt = 0.5*ds.RasterYSize, 0.5*ds.RasterXSize

        #find the right 4 GCPs
        for ir in xrange(nr - 1):
            if rc_cnt[0] < gcps[(ir+1)*nc][0]:
                break

        for ic in xrange(nc - 1):
            if rc_cnt[1] < gcps[ic+1][1]:
                break

        # bilinear interpolation
        xy_cnt = interp_bilin(rc_cnt, [
            gcps[(ic+0)+(ir+0)*nc], gcps[(ic+1)+(ir+0)*nc],
            gcps[(ic+1)+(ir+1)*nc], gcps[(ic+0)+(ir+1)*nc],
        ])

        # create point geometry
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint_2D(*xy_cnt)
        geom.AssignSpatialReference(WGS84_SR)

        # export
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))

    except Exception as exc:
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME, exc)
        sys.exit(1)
