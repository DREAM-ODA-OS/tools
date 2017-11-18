#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Extract geometry from a feature collection.
#
# Author: Martin Paces <martin.paces@eox.at>
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
#pylint: disable=wrong-import-position, invalid-name

import sys
from os.path import basename
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements
from osgeo import gdal; gdal.UseExceptions() #pylint: disable=multiple-statements
import img_geom as ig


if __name__ == "__main__":
    # TODO: to improve CLI
    EXENAME = basename(sys.argv[0])
    DEBUG = False
    FORMAT = "WKB"
    OPERATOR = "EQL"
    OPERATORS = ("EQL", "AND", "ALL")
    try:
        INPUT = sys.argv[1]
        VALUE = int(sys.argv[2])
        NP = 2
        if len(sys.argv) > NP:
            for arg in sys.argv[NP:]:
                if arg in ig.OUTPUT_FORMATS:
                    FORMAT = arg # output format
                elif arg in OPERATORS:
                    OPERATOR = arg # match operator
                elif arg == "DEBUG":
                    DEBUG = True # dump debuging output
    except IndexError:
        print >>sys.stderr, "ERROR: Not enough input arguments!"
        print >>sys.stderr, "\nExtract geometry from a feature collection."
        print >>sys.stderr, (
            "USAGE: %s <feature-collection> <data-value> [WKT|WKB*] "
            "[ALL|AND|EQL*] [DEBUG]" % EXENAME
        )
        sys.exit(1)

    dataset = ogr.Open(INPUT)
    layer = dataset.GetLayer(0)
    sref = layer.GetSpatialRef()
    if sref is not None:
        sref.AutoIdentifyEPSG()

    # get list of features
    features = [layer.GetFeature(idx) for idx in xrange(layer.GetFeatureCount())]

    if DEBUG:
        print >>sys.stderr, "Number of features: ", len(features)
        for idx, feature in enumerate(features):
            print >>sys.stderr, "#%2.2i\t%s\tDN=%d" % (
                idx, str(feature), feature.GetFieldAsInteger(0)
            )

    # extract features matching the selection criteria
    if OPERATOR == "EQL": # (V == DN)
        predicate = lambda f: VALUE == f.GetFieldAsInteger(0)
    elif OPERATOR == "AND": # (0 != (V&DN))
        predicate = lambda f: (VALUE & f.GetFieldAsInteger(0)) != 0
    elif OPERATOR == "ALL": # (0 != (V&DN))
        predicate = lambda f: True
    else:
        raise RuntimeError("Invalid operator! OPERATOR=%s"%OPERATOR)

    features = [feature for feature in features if predicate]

    if DEBUG:
        print >>sys.stderr, "Number of filtered features: ", len(features)
        for idx, feature in enumerate(features):
            print >>sys.stderr, "#%2.2i\t%s\tDN=%d" % (
                idx, str(feature), feature.GetFieldAsInteger(0)
            )

    # collect unique list of matched digital numbers
    dn_set = set(feature.GetFieldAsInteger(0) for feature in features)

    # extract geometries
    geometries = [feature.GetGeometryRef() for feature in features]

    if DEBUG:
        print >>sys.stderr, "Number of initial geometries: ", len(geometries)
        for idx, geometry in enumerate(geometries):
            print >>sys.stderr, "#%2.2i\t%s\t%s\t%s" % (
                idx, geometry.GetGeometryType(), geometry.GetGeometryName(),
                geometry.Area()
            )

    # remove empty geometries
    geometries = [geometry for geometry in geometries if not geometry.IsEmpty()]

    if DEBUG:
        print >>sys.stderr, "Number of non-empty geometries: ", len(geometries)
        for idx, geometry in enumerate(geometries):
            print >>sys.stderr, "#%2.2i\t%s\t%s\t%s" % (
                idx, geometry.GetGeometryType(), geometry.GetGeometryName(),
                geometry.Area()
            )

    # NOTE: no geometry optimisations performed

    # merge the individual geometries
    # NOTE: We assume that all geometries are polygons which can be joined
    # to a multi-polygon.

    if len(geometries) > 1: # multiple polygons
        geom = ig.groupPolygons(geometries)
        if len(dn_set) > 0: # perform union if multiple DN matched
            geom = geom.UnionCascaded()

    elif len(geometries) == 1: # single polygon
        geom, = geometries

    else: # no match -> empty multi-polygon
        geom = ogr.Geometry(ogr.wkbMultiPolygon)

    # assign spatial reference
    geom.AssignSpatialReference(sref)

    # export
    try:
        sys.stdout.write(ig.dumpGeom(geom, FORMAT))
    except Exception as exc:
        print >>sys.stderr, "ERROR: %s: %s" % (EXENAME, exc)
        sys.exit(1)
