#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Raster geometry vectorization.
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

from osgeo import ogr; ogr.UseExceptions() # pylint: disable=multiple-statements
from osgeo import gdal; gdal.UseExceptions() # pylint: disable=multiple-statements

def vectorize(band, filter_function):
    """ Vectorize GDAL raster band."""
    # create virtual in-memory OGR data-source
    ogr_ds = ogr.GetDriverByName('Memory').CreateDataSource('_in_memory_')
    # create geometry layer
    layer = ogr_ds.CreateLayer('footprint', None, ogr.wkbPolygon)
    # add feature to hold the mask value
    layer.CreateField(ogr.FieldDefn('DN', ogr.OFTInteger))
    # extract vector outlines
    # NOTE: The polygons are already in the projected coordinates!
    gdal.Polygonize(band, None, layer, 0)
    # extract geometries and DNs
    geometries = [
        (feature.GetGeometryRef().Clone(), feature.GetFieldAsInteger(0))
        for feature in (
            layer.GetFeature(idx) for idx in xrange(layer.GetFeatureCount())
        ) if filter_function(feature.GetFieldAsInteger(0))
    ]
    if len(geometries) == 1: # polygon
        return geometries[0][0]
    else: # multi-polygon
        wrapper = ogr.Geometry(ogr.wkbMultiPolygon)
        dn_set = set()
        for geometry, dn in geometries:
            wrapper.AddGeometry(geometry)
            dn_set.add(dn)
        # if there are multiple NDs perform union
        if len(dn_set) > 1:
            wrapper = wrapper.UnionCascaded()
        return wrapper
