#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Tiny block-based API build on top of GDAL and Numpy.
#
# Project: Image Processing Tools
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

from osgeo import gdal; gdal.UseExceptions()
import numpy as np

#------------------------------------------------------------------------------
# datatype mapping

GDT2DT = {
    gdal.GDT_Byte: "uint8",
    gdal.GDT_UInt16: "uint16",
    gdal.GDT_Int16: "int16",
    gdal.GDT_UInt32: "uint32",
    gdal.GDT_Int32: "int32",
    gdal.GDT_Float32: "float32",
    gdal.GDT_Float64: "float63"}

DT2GDT = dict((v, k) for (k, v) in GDT2DT.items())

def getGdalDataType(dtype):
    gdtype = DT2GDT.get(str(dtype).lower(), None)
    if gdtype is None:
        raise ValueError("Unsupported data type '%s'!"%(str(dtype)))
    return gdtype

def getNumpyDataType(gdtype):
    dtype = GDT2DT.get(gdtype, None)
    if dtype is None:
        raise ValueError("Unsupported data type %s!"%(str(gdtype)))
    return dtype

#------------------------------------------------------------------------------

class FormatOptions(object):
    _fopts = {}

    def __init__(self, options=None):
        for opt in options or []:
            self.setOption(opt)

    def setOption(self, opt):
        k, v = opt.split("=")
        k, v = k.strip(), v.strip()
        self[k] = v

    def getOptions(self):
        return ["%s=%s"%(k, v) for k, v in self.items()]

    def __setitem__(self, key, value):
        self._fopts[key] = value

    def __getitem__(self, key):
        return self._fopts[key]

    def __delitem__(self, key):
        del self._fopts[key]

    def get(self, key, default=None):
        return self._fopts.get(key, default)

    def items(self):
        return self._fopts.items()

#------------------------------------------------------------------------------

class ImgExtent(object):
    """ Image Extent

            &   - area intersection (maximum common area)
            |   - area expansion (minimum area contaning both boxes)
            +   - offset translation (adding vector to current value)
            -   - offset translation (substracting vector from current value)
    """

    # offset manipulation
    def move_to(self, ox, oy, oz=0):
        self.__ox = ox
        self.__oy = oy
        self.__oz = oz

    def move_by(self, ox, oy, oz=0):
        self.__ox += ox
        self.__oy += oy
        self.__oz += oz

    # upper corrner
    ox = property(lambda s: s.__ox, doc="x offset/lower coord. (ro)")
    oy = property(lambda s: s.__oy, doc="y offset/lower coord. (ro)")
    oz = property(lambda s: s.__oz, doc="z offset/lower coord. (ro)")

    sx = property(lambda s: s.__sx, doc="x size (RO)")
    sy = property(lambda s: s.__sy, doc="y size (RO)")
    sz = property(lambda s: s.__sz, doc="y size (RO)")

    ux = property(lambda s: s.__ox + s.__sx, doc="x upper coord. (RO)")
    uy = property(lambda s: s.__oy + s.__sy, doc="y upper coord. (RO)")
    uz = property(lambda s: s.__oz + s.__sz, doc="y upper coord. (RO)")

    # extent
    ext = property(lambda s: s.__sx * s.__sy * s.__sz, doc="extent/box area (RO)")
    off = property(lambda s: (s.ox, s.oy, s.oz), doc="offset tuple (RO)")
    upp = property(lambda s: (s.ux, s.uy, s.uz), doc="upper corner tuple (RO)")
    size = property(lambda s: (s.sx, s.sy, s.sz), doc="size tuple (RO)")

    offset = off
    upper = upp

    #--------------------------------------------------------------------------

    def equal_2d(self, other):
        """Compare 2D (x,y only) extents and returns True if equal."""
        return (
            (self.ox == other.ox) and
            (self.oy == other.oy) and
            (self.sx == other.sx) and
            (self.sy == other.sy))

    def non_equal_2d(self, other):
        """Compare 2D (x,y only) extents and returns True if not equal."""
        return not self.equal_2d(other)

    def __eq__(self, other):
        return (
            (self.ox == other.ox) and
            (self.oy == other.oy) and
            (self.oz == other.oz) and
            (self.sx == other.sx) and
            (self.sy == other.sy) and
            (self.sz == other.sz))

    def __ne__(self, other):
        return not self.__eq__(other)

    #--------------------------------------------------------------------------

    def as_tuple(self):
        """ Get bbounding box as (sx.sy,ox,oy) tuple """
        return (self.sx, self.sy, self.sz, self.ox, self.oy, self.oz)

    def __str__(self):
        return "ImgExtent%s"%str(self.as_tuple())

    def __init__(self, size=(None, None, None), offset=(0, 0, 0),
                     upper=(0, 0, 0), extent=None):
        if extent:
            size = extent.size
            offset = extent.offset
            upper = (0, 0, 0)

        sx, sy, sz = size
        ox, oy, oz = offset
        ux, uy, uz = upper

        self.__ox = ox
        self.__oy = oy
        self.__oz = oz
        self.__sx = max(0, (ux - ox) if sx is None else sx)
        self.__sy = max(0, (uy - oy) if sy is None else sy)
        self.__sz = max(0, (uz - oz) if sz is None else sz)

    # area operators
    def __and__(self, other):
        """ operator - intersection """
        return ImgExtent(offset=(max(self.ox, other.ox), max(self.oy, other.oy),
                                  max(self.oz, other.oz)),
                          upper=(min(self.ux, other.ux), min(self.uy, other.uy),
                                  min(self.uz, other.uz)))

    def __or__(self, other):
        """ operator - expansion """
        return ImgExtent(offset=(min(self.ox, other.ox), min(self.oy, other.oy),
                                  min(self.oz, other.oz)),
                          upper=(max(self.ux, other.ux), max(self.uy, other.uy),
                                  max(self.uz, other.uz)))

    # box operator - offset translation
    def __add__(self, (ox, oy, oz)):
        """ operator - offset translation """
        return ImgExtent(size=self.size, offset=(self.ox+ox, self.oy+oy, self.oz+oz))

    def __sub__(self, (ox, oy, oz)):
        """ operator - offset translation """
        return ImgExtent(size=self.size, offset=(self.ox-ox, self.oy-oy, self.oz-oz))

    # box operator - offset translation
    def __iadd__(self, (ox, oy, oz)):
        """ operator - offset translation """
        self.__ox += ox
        self.__oy += oy
        self.__oz += oz

    def __isub__(self, (ox, oy, oz)):
        """ operator - offset translation """
        self.__ox -= ox
        self.__oy -= oy
        self.__oz -= oz

#------------------------------------------------------------------------------

class ImgBlock(ImgExtent):

    def __str__(self):
        return "ImgBlock%s (dtype=%s)"%(str(self.as_tuple()), self.data.dtype)

    def __init__(self, dtype='float64', size=(None, None, None),
                    offset=(0, 0, 0), upper=(0, 0, 0), extent=None):
        ImgExtent.__init__(self, size, offset, upper, extent)
        self.data = np.zeros((self.sy, self.sx, self.sz), dtype)

    def fill(self, v):
        """ fill by a constant value """
        self.data[:, :, :] = v

    dtype = property(lambda s: s.data.dtype, doc="data type(RO)")
    shape = property(lambda s: s.data.shape, doc="array shape(RO)")

#------------------------------------------------------------------------------

class ImgFile(ImgExtent):

    def __str__(self):
        return "ImgFile%s"%str(self.as_tuple())

    def _get_dtype(self):
        # extract band types
        gdt = [self.ds.GetRasterBand(b+1).DataType for b in xrange(self.ds.RasterCount)]

        # check if all band types equal
        # MP: check disabled to allow reading of MERIS N1 files
        #for t in gdt[1:]:
        #    if (t != gdt[0]):
        #        raise RuntimeError("Datasets with mixed band types not supported!")

        return getNumpyDataType(gdt[0])

    @property
    def dtype(self):
        """ dataset's datatype """
        return self.__dtype

    @property
    def nodata(self):
        """ get a tuple of band's no-data values """
        return tuple(self.ds.GetRasterBand(i+1).GetNoDataValue()
                                        for i in xrange(self.ds.RasterCount))

    @nodata.setter
    def nodata(self, val):
        """ set band's no-data values by a sequence or single value """
        try:
            len(val)
        except TypeError:
            val = [val for i in xrange(self.ds.RasterCount)]

        if len(val) < self.ds.RasterCount:
            raise ValueError("Not enough items in the value list!")

        for i, v in enumerate(val[:self.ds.RasterCount]):
            if v is not None:
                self.ds.GetRasterBand(i+1).SetNoDataValue(float(v))


    def __init__(self, ds, subds=None, band_subset=None):
        if subds:
            raise RuntimeError("Subdataset handling not implemented!")

        if band_subset:
            raise RuntimeError("Band subsetting not implemented!")

        self.ds = ds
        self.__dtype = self._get_dtype()

        ImgExtent.__init__(self, (self.ds.RasterXSize, self.ds.RasterYSize,
                                    self.ds.RasterCount))

#------------------------------------------------------------------------------

# mix in reader class
class _ImgFileIn(object):

    def read(self, block):
        ol = self & block #calculate overlap
        if ol.ext == 0:
            return
        for i in xrange(0, ol.sz): # load the raster bands
            rb = self.ds.GetRasterBand(ol.oz-self.oz+i+1)
            block.data[
                (ol.oy-block.oy):(ol.oy-block.oy+ol.sy),
                (ol.ox-block.ox):(ol.ox-block.ox+ol.sx),
                (ol.oz-block.oz+i),
            ] = rb.ReadAsArray(ol.ox-self.ox, ol.oy-self.oy, ol.sx, ol.sy)
        return block

#------------------------------------------------------------------------------

class ImgFileIn(ImgFile, _ImgFileIn):

    def __str__(self):
        return "ImgFileIn%s"%str(self.as_tuple())

    def __init__(self, path_or_ds, subds=None, band_subset=None):
        if not isinstance(path_or_ds, gdal.Dataset):
            path_or_ds = gdal.Open(path_or_ds, gdal.GA_ReadOnly)
        ImgFile.__init__(self, path_or_ds, subds, band_subset)


#------------------------------------------------------------------------------

class ImgFileOut(ImgFile, _ImgFileIn):

    def __str__(self):
        return "ImgFileOut%s"%str(self.as_tuple())


    def __init__(self, path_or_ds, subds=None, band_subset=None):
        if not isinstance(path_or_ds, gdal.Dataset):
            path_or_ds = gdal.Open(path_or_ds, gdal.GA_Update)
        ImgFile.__init__(self, path_or_ds, subds, band_subset)

#    def close():
#        """ commit write to the dataset - NOTE: Renders the class unusable!"""
#        self.ds = None

    def write(self, block):
        ol = (self & block) #calculate overlap
        if ol.ext == 0:
            return
        for i in xrange(0, ol.sz): # save the raster bands
            rb = self.ds.GetRasterBand(ol.oz-self.oz+i+1)
            rb.WriteArray(
                block.data[(ol.oy-block.oy):(ol.oy-block.oy+ol.sy),
                            (ol.ox-block.ox):(ol.ox-block.ox+ol.sx),
                            (ol.oz-block.oz+i)],
                ol.ox-self.ox, ol.oy-self.oy)

#------------------------------------------------------------------------------

def createGeoTIFF(path, dtype, nrow, ncol, nband=1, proj=None,
        geotrn=None, gcps=None, nodata=None, options=None):
    """Return ImgFileOut object poiting to a newly created GeoTIFF """

    nrow = max(0, int(nrow))
    ncol = max(0, int(ncol))
    nband = max(1, int(nband))

    # convert type to gdal type
    gdtype = getGdalDataType(dtype)

    # get GDAL Driver
    drv = gdal.GetDriverByName("GTiff")

    # create TIFF image
    ds = drv.Create(path, ncol, nrow, nband, gdtype, options)

    if proj and geotrn:
        # set geotransfromation
        ds.SetProjection(proj)
        ds.SetGeoTransform(geotrn)

    elif proj and gcps:
        # set ground control points (a.k.a. tie-points)
        def _gcp(i, p):
            if type(p) == gdal.GCP:
                p = gdal.GCP(p.GCPX, p.GCPY, p.GCPZ, p.GCPPixel, p.GCPLine, p.Info, p.Id)
            else:
                p = gdal.GCP(p[0], p[1], p[2], p[3], p[4], "", "%d"%(i+1))
            return p
        ds.SetGCPs([_gcp(_i, _p) for _i, _p in enumerate(gcps)], proj)

    # create image object
    ifo = ImgFileOut(ds)

    #set no-data value(s)
    ifo.nodata = nodata

    return ifo
