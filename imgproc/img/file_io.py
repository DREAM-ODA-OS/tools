#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Image File I/O classes
#
# Project: Image Processing Tools
# Authors: Martin Paces <martin.paces@eox.at>
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
from osgeo import osr; osr.UseExceptions() #pylint: disable=multiple-statements
from .extent import Extent

# data type mappings
GDT2DT = {
    gdal.GDT_Byte: "uint8",
    gdal.GDT_UInt16: "uint16",
    gdal.GDT_Int16: "int16",
    gdal.GDT_UInt32: "uint32",
    gdal.GDT_Int32: "int32",
    gdal.GDT_Float32: "float32",
    gdal.GDT_Float64: "float63"
}

DT2GDT = dict((v, k) for (k, v) in GDT2DT.items())


def pixel_offset(geocoding, offset):
    """ Add pixel offset to the image geo-coding. """
    offx, offy = tuple(offset)[:2]
    geocoding_new = {}
    for key, value in geocoding.iteritems():
        if key == 'geotrn':
            # calculate the new offset of the origin
            mtx = value
            ogx = mtx[0] + mtx[1] * offx + mtx[2] * offy
            ogy = mtx[3] + mtx[4] * offx + mtx[5] * offy
            value = (ogx, mtx[1], mtx[2], ogy, mtx[4], mtx[5])
        elif key == 'gcps':
            # translate GCPs
            _offset_gcp = lambda p: gdal.GCP(
                p.GCPX, p.GCPY, p.GCPZ,
                p.GCPPixel - offx, p.GCPLine - offy, p.Info, p.Id
            )
            value = [_offset_gcp(gcp) for gcp in value]
        geocoding_new[key] = value
    return geocoding_new


class BaseImageFile(Extent):
    """ Base GDAL-based image file class. """

    def __init__(self, dataset):
        self._ds = dataset
        super(BaseImageFile, self).__init__((
            dataset.RasterXSize, dataset.RasterYSize, dataset.RasterCount
        ))

    dataset = property(lambda s: s._ds, doc="GDAL dataset(RO)")

    def __str__(self):
        return "%s(size=%s, offset=%s, dtypes=%s)" % (
            self.__class__.__name__, self.size, self.offset, self.dtypes
        )

    def __len__(self):
        """ Get number of bands easily. """
        return self._ds.RasterCount

    def __getitem__(self, idx):
        """ Get band by index """
        return self._ds.GetRasterBand(idx + 1)

    @property
    def bands(self):
        """ Bands as a list. """
        return [self[idx] for idx in xrange(len(self))]

    @property
    def dtype(self):
        """ Get data type able to represent all the contained band data-types."""
        # TODO: fix the type selection
        return GDT2DT[self[0].DataType]

    @property
    def dtypes(self):
        """ Get list of band data-types. """
        return tuple(GDT2DT[band.DataType] for band in self.bands)

    @property
    def nodata(self):
        """ Get a tuple of band's no-data values """
        return tuple(band.GetNoDataValue() for band in self.bands)

    @nodata.setter
    def nodata(self, values):
        """ Set band's no-data values by a sequence or single value """
        if not hasattr(values, '__len__'):
            values = (values,) * len(self)

        if len(values) < len(self):
            raise ValueError("Not enough values in the list! %r" % values)

        for band, value in zip(self.bands, values):
            band.SetNoDataValue(float(value))

    @property
    def geocoding(self):
        """ Get the image geo-coding parameters. """
        prm = {}
        if self._ds.GetProjection():
            prm['proj'] = self._ds.GetProjection()
            prm['geotrn'] = self._ds.GetGeoTransform()
        elif self._ds.GetGCPProjection():
            prm['proj'] = self._ds.GetGCPProjection()
            prm['gcps'] = self._ds.GetGCPs()
        return prm

    @property
    def spatial_reference(self):
        """ Get OSR spatial reference of the projection. """
        proj = self._ds.GetProjection() or self._ds.GetGCPProjection()
        return osr.SpatialReference(proj) if proj else None


class ImageReaderMixIn(object):
    """ Image reader mix-in. """
    #pylint: disable=too-few-public-methods

    def read(self, block):
        """ Read data to a block from the image file. """
        overlap = self & block # calculate overlap of the block and the image
        if overlap.extent > 0:
            doffs = overlap.offset - self.offset
            doffb = overlap.offset - block.offset
            size = overlap.size
            if doffs.z == 0 and size.z == self.size.z and size.z > 1:
                block.data[
                    doffb.y:doffb.y + size.y, doffb.x:doffb.x + size.x, :
                ] = self.dataset.ReadAsArray(
                    doffs.x, doffs.y, size.x, size.y
                ).transpose((1, 2, 0))
            else:
                for idx in xrange(size.z):
                    band = self[doffs.z + idx]
                    block.data[
                        doffb.y:doffb.y + size.y,
                        doffb.x:doffb.x + size.x,
                        doffb.z + idx
                    ] = band.ReadAsArray(doffs.x, doffs.y, size.x, size.y)
        return block


class ImageWriterMixIn(object):
    """ Image writer mix-in. """
    #pylint: disable=too-few-public-methods

    def write(self, block):
        """ Write data from a block to the image file. """
        overlap = self & block # calculate overlap of the block and the image
        if overlap.extent > 0:
            doffs = overlap.offset - self.offset
            doffb = overlap.offset - block.offset
            size = overlap.size
            for idx in xrange(size.z):
                self[doffs.z + idx].WriteArray(
                    block.data[
                        doffb.y:doffb.y + size.y,
                        doffb.x:doffb.x + size.x,
                        doffb.z + idx
                    ], doffs.x, doffs.y
                )
        return block


class ImageFileReader(BaseImageFile, ImageReaderMixIn):
    """ GDAL-based image file reader class. """

    def __init__(self, path_or_ds):
        if not isinstance(path_or_ds, gdal.Dataset):
            path_or_ds = gdal.Open(path_or_ds, gdal.GA_ReadOnly)
        super(ImageFileReader, self).__init__(path_or_ds)


class ImageFileWriter(BaseImageFile, ImageReaderMixIn, ImageWriterMixIn):
    """ GDAL-based image file reader class. """

    def __init__(self, path_or_ds):
        if not isinstance(path_or_ds, gdal.Dataset):
            path_or_ds = gdal.Open(path_or_ds, gdal.GA_Update)
        super(ImageFileWriter, self).__init__(path_or_ds)
