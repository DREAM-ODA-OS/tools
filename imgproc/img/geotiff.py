#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# GeoTIFF creation subroutine
#
# Author: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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

from osgeo import gdal; gdal.UseExceptions() #pylint: disable=multiple-statements
from .file_io import ImageFileWriter, DT2GDT
from .util import FormatOptions

# default GeoTIFF file-options
DEF_GEOTIFF_FOPT = {
    "TILED": "YES",
    "BLOCKXSIZE": "256",
    "BLOCKYSIZE": "256",
    "COMPRESS": "NONE",
}


def make_gcp(x, y, z, p, l, id_, info=""):
    """ Construct GDAL Ground Control Point. """
    #pylint: disable=invalid-name, too-many-arguments
    return gdal.GCP(x, y, z, p, l, info, str(id_))


def clone_gcp(gcp):
    """ Clone GCP object. """
    return gdal.GCP(
        gcp.GCPX, gcp.GCPY, gcp.GCPZ, gcp.GCPPixel, gcp.GCPLine, gcp.Info, gcp.Id
    )


def create_geotiff(path, dtype, nrow, ncol, nband=1, proj=None,
                   geotrn=None, gcps=None, nodata=None, options=None):
    """ Create a GeoTIFF image and return an instance of the ImageFileWriter
    class to access this file.
    """
    #pylint: disable=too-many-arguments, too-many-locals

    # sanitize the inputs
    nrow = max(0, int(nrow))
    ncol = max(0, int(ncol))
    nband = max(1, int(nband))
    if options is None:
        options = FormatOptions(DEF_GEOTIFF_FOPT).options

    # convert type to gdal type
    try:
        gdal_dtype = DT2GDT[dtype]
    except KeyError:
        raise ValueError("Unsupported data type! %r" % dtype)

    # get GDAL Driver
    driver = gdal.GetDriverByName("GTiff")

    # create TIFF image
    dataset = driver.Create(path, ncol, nrow, nband, gdal_dtype, options)

    if proj and geotrn:
        # set geo-transformation
        dataset.SetProjection(proj)
        dataset.SetGeoTransform(geotrn)

    elif proj and gcps:
        # copy ground control points (a.k.a. tie-points)
        dataset.SetGCPs([clone_gcp(gcp) for gcp in gcps], proj)

    # create image object
    writer = ImageFileWriter(dataset)

    #copy no-data value(s)
    if nodata is not None:
        writer.nodata = nodata

    return writer
