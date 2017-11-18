#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool performs range stretch to 8 bits for given maximum and
#   minimum values. The number of output band is restricted to 1 or 3 colour
#   bands to produce either gray-scale or RGB images. Optionally an alpha
#   band generated for the given no-data value can be added.
#
#   The range is stretched between 1 and 255.
#   0 is reserved for the non-data value.
#   1 contains all values below the minimum value.
#   255 contains all values larger equal to the maximum value.
#
#   Optionally the stretching can be performed in the logarithmic scale.
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
    FormatOptions, create_geotiff, DEF_GEOTIFF_FOPT,
    Block, ImageFileReader, Progress, execute,
)
from img.cli import error
from img.algs import range_stretch_uint8, extract_mask

def usage():
    """Print a short command usage help."""
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <input image> <output image> <min.value> <max.value> "
        "<no data value>|NONE [LOGSCALE] [DBSCALE] [ADDALPHA]" % exename
    )
    print >>sys.stderr, (
        "USAGE: %s <input image> <output image> NOSCALE "
        "<no data value>|NONE [ADDALPHA]" % exename
    )
    print >>sys.stderr, (
        "EXAMPLE: %s input.tif output.tif 10 12000 0,0,0,0" % exename
    )
    print >>sys.stderr, "EXAMPLE: %s input.tif output.tif 2 20 0" % exename


def process(tile, img_in, img_out, vmin, vmax, nodata, scale, add_alpha):
    """ Process one tile. """
    # pylint: disable=too-many-arguments
    tile = tile & img_out # clip tile to the image extent
    b_in = Block(img_in.dtype, tile.set_z(img_out.size.z - add_alpha))
    b_in = img_in.read(b_in)
    b_mask = extract_mask(b_in, nodata, all_valid=True)
    b_out = range_stretch_uint8(b_in, b_mask, vmin, vmax, scale, add_alpha)
    img_out.write(b_out)


if __name__ == "__main__":
    FOPTS = FormatOptions(DEF_GEOTIFF_FOPT) # default format options
    FOPTS['INTERLEAVE'] = 'PIXEL'
    ADDALPHA = False
    SCALE = "linear"
    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        if sys.argv[3] == "NOSCALE":
            SCALE = "identity"
            POS = 4
        else:
            VMIN = sys.argv[3]
            VMAX = sys.argv[4]
            POS = 5
        NODATA = sys.argv[POS]
        for opt in sys.argv[POS+1:]:
            if opt.upper() == "LOGSCALE":
                SCALE = "logarithmic"
            elif opt.upper() in ("DB", "DBSCALE"):
                SCALE = "decibel"
            elif opt.upper() == "NOSCALE":
                SCALE = "identity"
            elif opt.upper() == "ADDALPHA":
                ADDALPHA = True
                FOPTS["ALPHA"] = "YES"
            else:
                #anything else is treated as a format option
                FOPTS.set_option(opt)
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    if SCALE == "identity":
        VMIN = "2"
        VMAX = "255"

    # open input image
    IMG_IN = ImageFileReader(INPUT)
    NBANDS = 1 if len(IMG_IN) < 3 else 3

    VMIN = [float(v) for v in VMIN.split(",")]
    VMAX = [float(v) for v in VMAX.split(",")]
    # expand values if needed
    if len(VMIN) == 1 and NBANDS > 1:
        VMIN = VMIN * NBANDS
    if len(VMAX) == 1 and NBANDS > 1:
        VMAX = VMAX * NBANDS

    # convert no-data values to the image's data type
    if NODATA != "NONE":
        NODATA = NODATA.split(",")
        if len(NODATA) == 1 and NBANDS > 1:
            NODATA = NODATA * NBANDS
        NODATA = [dtype(dt).type(nd) for dt, nd in zip(IMG_IN.dtypes, NODATA)]
    else:
        NODATA = None

    DTYPE = IMG_IN.dtype

    # creation parameters
    PARAM = {
        'path' :   OUTPUT,
        'nrow' :   IMG_IN.size.y,
        'ncol' :   IMG_IN.size.x,
        'nband' :  NBANDS + ADDALPHA,
        'dtype' :  'uint8',
        'options' : FOPTS.options,
    }
    if not ADDALPHA:
        PARAM['nodata'] = [0] * PARAM['nband']
    PARAM.update(IMG_IN.geocoding) # add geo-coding

    # open output image
    IMG_OUT = create_geotiff(**PARAM)

    # block size
    TILE_SIZE = (int(FOPTS["BLOCKXSIZE"]), int(FOPTS["BLOCKYSIZE"]))

    print "Range stretching ..."
    execute(
        IMG_OUT.tiles(TILE_SIZE), process, (
            IMG_IN, IMG_OUT, VMIN, VMAX, NODATA, SCALE, ADDALPHA,
        ),
        progress=Progress(sys.stdout, IMG_OUT.tile_count(TILE_SIZE)),
    )
