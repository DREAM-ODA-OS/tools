#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   rasterize geometry
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
#pylint: disable=invalid-name, wrong-import-position

import sys
from sys import stderr
from os.path import basename
from numpy  import dtype
from osgeo import ogr; ogr.UseExceptions() #pylint: disable=multiple-statements
from osgeo import gdal; gdal.UseExceptions() #pylint: disable=multiple-statements
from img import ImageFileWriter
from img.cli import error
import img_geom as ig


def usage():
    """Print a short command usage help."""
    exename = basename(sys.argv[0])
    print >>stderr, (
        "USAGE: %s <geometry> <image> <pixel-value> [DEBUG]" % exename
    )
    print >>stderr, "Write a rasterised geometry to an existing image."

def geometry2layer(dataset, geom):
    """ Convert geometry to a virtual-memory layer. """
    # create layer
    layer = dataset.CreateLayer(
        'geom', geom.GetSpatialReference(), geom.GetGeometryType()
    )
    # add feature
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(geom)
    layer.CreateFeature(feature)
    #feature.Destroy()
    return layer

def compare_spatial_references(sr0, sr1):
    """ Return true if two spatial references are the same. """
    if sr0 is None:
        return sr1 is None
    elif sr1 is None:
        return False
    else:
        return sr0.IsSame(sr1)


if __name__ == "__main__":
    DEBUG = False
    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        VALUE = tuple(float(v) for v in sys.argv[3].split(","))
        if len(sys.argv) > 3:
            for arg in sys.argv[3:]:
                if arg == "DEBUG":
                    DEBUG = True # dump debugging output
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    # read the input geometry
    with (sys.stdin if INPUT == "-" else open(INPUT)) as fobj:
        GEOM = ig.parseGeom(fobj.read(), DEBUG)

    # open input image
    IMG_OUT = ImageFileWriter(OUTPUT)

    # convert the pixel value to a proper data type
    VALUE = [dtype(dt).type(val) for dt, val in zip(IMG_OUT.dtypes, VALUE)]
    # single value is expanded for each band
    if len(VALUE) == 1 and len(IMG_OUT) > 1:
        VALUE = VALUE * len(IMG_OUT)
    # check number of pixel values
    if len(VALUE) < len(IMG_OUT):
        error(
            "The number of pixel values is lower than the number of bands "
            "of the output image!"
        )

    # check the spatial references
    if not compare_spatial_references(
            IMG_OUT.spatial_reference, GEOM.GetSpatialReference()
        ):
        error(
            "Both the geometry and the output image must have the same "
            "spatial reference!"
        )
        sys.exit(1)

    # rasterization

    virt_ds = ogr.GetDriverByName('Memory').CreateDataSource('tmp')
    gdal.RasterizeLayer(
        IMG_OUT.dataset,
        range(1, len(IMG_OUT) + 1),
        geometry2layer(virt_ds, GEOM),
        burn_values=tuple(VALUE)
    )
