#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool extracts a valid data mask from the provided raster image.
#   The input image can be in arbitrary image format supported by GDAL
#   The output will be always produced in  GeoTIFF (or TIFF if no geo-coding
#   available) format.
#   This version of the tool extract data mask from image having two
#   distinct no-data values.
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

import sys
from os.path import basename
from numpy import dtype
from img import (
    FormatOptions, ImageFileReader, create_geotiff, DEF_GEOTIFF_FOPT,
    Progress, Block, execute,
)
from img.algs import extract_mask_multi, replace_bool
from img.cli import error

MASKBG = 0x00
MASKFG = 0xFF

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    lines = (
        "USAGE: %s <input image> <output mask/TIF> <no data values> "
        "<no data values> [ALL_VALID|ANY_VALID]" % exename,
        "EXAMPLE: %s input.tif mask.tif 0,0,0 255,255,255" % exename,
        "EXAMPLE: %s input.tif mask.tif 0 255 MODE=ANY" % exename,
    )
    for line in lines:
        print >>sys.stderr, line


def process(tile, img_in, img_out, nodata, all_valid):
    """ Process one tile. """
    #pylint: disable=too-many-arguments
    tile = (tile & img_out).set_z(img_in) # clip tile to the image extent
    b_in = img_in.read(Block(img_in.dtype, tile))
    b_mask = extract_mask_multi(b_in, nodata, all_valid)
    b_out = replace_bool(b_mask, MASKBG, MASKFG, 'uint8')
    img_out.write(b_out)


if __name__ == "__main__":
    FOPTS = FormatOptions(DEF_GEOTIFF_FOPT) # default format options
    ALL_VALID = False
    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        NODATA1 = sys.argv[3].split(",")
        NODATA2 = sys.argv[4].split(",")
        for opt in sys.argv[5:]:
            if opt.upper() == "ALL_VALID":
                ALL_VALID = True
            elif opt.upper() == "ANY_VALID":
                ALL_VALID = False
            elif opt.upper() in ("MODE=ALL", "MODE=ANY"):
                raise ValueError("Invalid option %r!" % opt)
            else:
                #anything else is treated as a format option
                FOPTS.set_option(opt)
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    # open input image
    IMG_IN = ImageFileReader(INPUT)

    # convert no-data values to the image's data type
    if len(NODATA1) == 1 and len(IMG_IN) > 1:
        NODATA1 = NODATA1 * len(IMG_IN)
    if len(NODATA2) == 1 and len(IMG_IN) > 1:
        NODATA2 = NODATA2 * len(IMG_IN)
    NODATA = [
        tuple(dtype(dt).type(v) for v in set(nd))
        for dt, nd in zip(IMG_IN.dtypes, zip(NODATA1, NODATA2))
    ]

    DTYPE = IMG_IN.dtype

    # creation parameters
    PARAM = {
        'path' :   OUTPUT,
        'nrow' :   IMG_IN.size.y,
        'ncol' :   IMG_IN.size.x,
        'nband' :  1,
        'dtype' :  'uint8',
        'options' : FOPTS.options,
    }
    PARAM.update(IMG_IN.geocoding) # add geo-coding

    # open output image
    IMG_OUT = create_geotiff(**PARAM)

    # block size
    TILE_SIZE = (int(FOPTS["BLOCKXSIZE"]), int(FOPTS["BLOCKYSIZE"]))

    print "Extracting data mask ..."
    execute(
        IMG_OUT.tiles(TILE_SIZE), process, (IMG_IN, IMG_OUT, NODATA, ALL_VALID),
        progress=Progress(sys.stdout, IMG_OUT.tile_count(TILE_SIZE)),
    )
