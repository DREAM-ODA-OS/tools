#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool tries to smooth mask edges by blurring and thresholding.
#   While blur makes the edges smooth the thresholding produces new binary
#   mask.
#
#   For blurring is made by the (separated) Gaussian convolution filter
#   The value of the threshold controls position of the new mask border.
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

import sys
from os.path import basename
from img import (
    FormatOptions, ImageFileReader, create_geotiff, DEF_GEOTIFF_FOPT,
    Progress, Block, execute,
)
from img.cli import error
from img.algs import threshold_values, normalize_values
from img.filters import coeff1d_gauss, filter_conv_separable, mirror_borders

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])

    def _generate_():
        yield (
            "USAGE: %s <input mask> <output mask/TIF> <threshold> <radius>"
            "" % exename
        )
        yield "EXAMPLE: %s mask_in.tif mask_out.tif 0.5 20" % exename
        yield "DESCRIPTION:"
        yield "  This tools tries to smooth edges of a binary mask by "
        yield "  blurring and consecutive threshing of the pixel values. "
        yield "  The <radius> defines size of the convolution window "
        yield "  (number of pixels surrounding the central pixel.) "
        yield "  so the that window size is <window_size> = 2 * <radius> + 1"
        yield "  The <threshold> defines the trimming threshold and it should"
        yield "  be from 0.0 to 1.0 range."

    for line in _generate_():
        print >>sys.stderr, line


def process(tile, img_in, img_out, threshold, whs, false, true):
    """ Process one tile. """
    # pylint: disable=too-many-arguments
    tile = tile & img_in # clip tile to the input image extent
    b_in = img_in.read(Block(img_in.dtype, tile.extend((whs, whs))))
    b_in = normalize_values(b_in, false, true)
    b_in = mirror_borders(b_in, img_in)
    kernel1d = coeff1d_gauss(whs)
    b_out = filter_conv_separable(b_in, kernel1d, kernel1d)
    img_out.write(threshold_values(b_out, threshold, false, true))


if __name__ == "__main__":
    MASKBG = 0x00
    MASKFG = 0xFF
    FOPTS = FormatOptions(DEF_GEOTIFF_FOPT) # default format options

    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        # trimming threshold from 0.0 to 1.0
        THRESHOLD = max(0.0, min(1.0, float(sys.argv[3])))
        # window half size >= 1
        WHS = max(1, int(sys.argv[4]))
        for opt in sys.argv[5:]:
            #anything else is treated as a format option
            FOPTS.set_option(opt)
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    # open input image
    IMG_IN = ImageFileReader(INPUT)

    # check mask properties
    if IMG_IN.size.z > 1:
        error("Multi-band masks are not supported!")
        sys.exit(1)

    if IMG_IN.dtype != 'uint8':
        error("Unsupported mask data type '%s'!" % IMG_IN.dtype)
        sys.exit(1)

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
    #TILE_SIZE = (int(FOPTS["BLOCKXSIZE"]), int(FOPTS["BLOCKYSIZE"]))
    TILE_SIZE = (512, 512) # using larger tiles

    print "Smoothing mask ..."
    execute(
        IMG_OUT.tiles(TILE_SIZE), process, (
            IMG_IN, IMG_OUT, THRESHOLD, WHS, MASKBG, MASKFG,
        ),
        progress=Progress(sys.stdout, IMG_OUT.tile_count(TILE_SIZE)),
    )
