#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool calculates the image histogram for a given number of equidistant
#   bins. Additional two border bins are added for the values laying outside
#   the covered interval. No data or invalid values are ignored.
#
#   For multi-band images, for each band a separate histogram is calculated
#
#   Optionally dB scale histogram can be calculated.
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
    ImageFileReader, Progress, Block, aggregate, Point3,
)
from img.algs import extract_mask, scale_values
from img.cli import error

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <input image> <output histogram file> <min.> <max.> <nbins> "
        "<no data values>|NONE [ALL_VALID|ANY_VALID] "
        " [LOGSCALE|DBSCALE] [IGNORE_ALPHA]" % exename
    )
    print >>sys.stderr, (
        "EXAMPLE: %s input.tif histogram.txt 0.5 255.0 255 0,0,0,0" % exename
    )
    print >> sys.stderr, (
        "EXAMPLE: %s input.tif histogram.txt 0.0 2.0 20 0 ALL_VALID" % exename
    )


def process(tile, image, scale, vmin, vmax, nbin, nodata, all_valid,
            ignore_alpha):
    """ Process one tile. """
    # pylint: disable=too-many-arguments
    tile = tile & image # clip tile to the image extent
    if ignore_alpha:
        tile = tile.set_z(tile.size.z - 1)
    b_data = image.read(Block(image.dtype, tile))
    b_mask = extract_mask(b_data, nodata, all_valid)
    if scale != "linear":
        b_data, b_mask = scale_values(b_data, b_mask, scale)
    return b_data.histogram(vmin, vmax, nbin, b_mask.data[..., 0])


if __name__ == "__main__":
    ALL_VALID = False
    IGNORE_ALPHA = False
    SCALE = "linear"
    MASKBG = 0x00
    MASKFG = 0xFF
    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        VMIN = float(sys.argv[3])
        VMAX = float(sys.argv[4])
        NBIN = max(1, int(sys.argv[5]))
        NODATA = sys.argv[6]
        for opt in sys.argv[7:]:
            if opt.upper() == "ALL_VALID":
                ALL_VALID = True
            elif opt.upper() == "ANY_VALID":
                ALL_VALID = False
            elif opt.upper() == "LOGSCALE":
                SCALE = "logarithmic"
            elif opt.upper() in ("DB", "DBSCALE"):
                SCALE = "decibel"
            elif opt.upper() == "IGNORE_ALPHA":
                IGNORE_ALPHA = True
            else:
                raise ValueError("Invalid option %r!" % opt)
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    OUTPUT_STREAM = sys.stderr if OUTPUT == "-" else sys.stdout

    # open input image
    IMG_IN = ImageFileReader(INPUT)

    # convert no-data values to the image's data type
    if NODATA != "NONE":
        NODATA = NODATA.split(",")
        if len(NODATA) == 1 and len(IMG_IN) > 1:
            NODATA = NODATA * len(IMG_IN)
        NODATA = [dtype(dt).type(nd) for dt, nd in zip(IMG_IN.dtypes, NODATA)]
        if IGNORE_ALPHA:
            NODATA = NODATA[:-1]
    else:
        NODATA = None

    # print short summary
    print >>OUTPUT_STREAM, "Calculating histogram ..."
    print >>OUTPUT_STREAM, "scale:          ", SCALE
    print >>OUTPUT_STREAM, "value range:    ", (VMIN, VMAX)
    print >>OUTPUT_STREAM, "number of bins: ", NBIN
    print >>OUTPUT_STREAM, "image size:     ", tuple(
        IMG_IN.size - Point3(0, 0, IGNORE_ALPHA)
    )
    print >>OUTPUT_STREAM, "no-data:        ", NODATA
    print >>OUTPUT_STREAM, "no-data-type:   ", ("ANY", "ALL")[ALL_VALID]

    TILE_SIZE = (256, 256)

    HISTOGRAM = aggregate(
        IMG_IN.tiles(TILE_SIZE), process,
        lambda value, memo: value + memo, None, (
            IMG_IN, SCALE, VMIN, VMAX, NBIN, NODATA, ALL_VALID, IGNORE_ALPHA,
        ),
        progress=Progress(OUTPUT_STREAM, IMG_IN.tile_count(TILE_SIZE)),
    )

    with sys.stdout if OUTPUT == "-" else open(OUTPUT, "w") as fout:
        HISTOGRAM.write(fout, {"file": INPUT, "scale": SCALE})
