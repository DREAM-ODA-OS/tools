#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool clips data to mask. Based on the mask value, the code
#   performs following pixel operations:
#       mask no-data value (0x00) -> sets pixel to a given no-data value
#       mask data value (0xFF)    -> copies pixel from the original image
#
#   This tool extracts subset of the image specified by the row/column
#   offset of the upper-left corner and row/column size of extracted
#   block. The tool takes care of preserving the geo-metadata.
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
from numpy import dtype
from img import (
    FormatOptions, ImageFileReader, create_geotiff, DEF_GEOTIFF_FOPT,
    Progress, Block, execute, Point2,
)
from img.algs import clip_to_mask
from img.cli import error

def usage():
    """Print a short command usage help."""
    exe = basename(sys.argv[0])
    out = sys.stderr
    print >>out, (
        "USAGE: %s <input image> <mask> <output TIF> <no data value or list>"
        % exe
    )
    print >>out, "EXAMPLE: %s input.tif mask.tif output.tif 255,255,255" % exe
    print >>out, "EXAMPLE: %s input.tif mask.tif output.tif 0" % exe


def process(tile, img_in, img_mask, img_out, nodata, clipped_mask_value=0):
    """ Process one tile. """
    # pylint: disable=too-many-arguments
    tile = tile & img_out # clip tile to the image extent
    b_in = img_in.read(Block(img_in.dtype, tile))
    b_mask = img_mask.read(Block(img_mask.dtype, tile))
    b_out = clip_to_mask(b_in, b_mask, nodata, clipped_mask_value)
    img_out.write(b_out)


if __name__ == "__main__":
    FOPTS = FormatOptions(DEF_GEOTIFF_FOPT) # default format options
    MASKBG = 0x00
    MASKFG = 0xFF
    try:
        INPUT = sys.argv[1]
        MASK = sys.argv[2]
        OUTPUT = sys.argv[3]
        NODATA = sys.argv[4].split(",")
        #anything else treated as a format option
        FOPTS.set_options(sys.argv[5:])
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    # open input image
    IMG_IN = ImageFileReader(INPUT)

    # convert no-data values to the image's data type
    if len(NODATA) == 1 and len(IMG_IN) > 1:
        NODATA = NODATA * len(IMG_IN)
    NODATA = [dtype(dt).type(nd) for dt, nd in zip(IMG_IN.dtypes, NODATA)]

    # open the mask image
    IMG_MASK = ImageFileReader(MASK)

    # check mask properties
    if IMG_MASK.size.z > 1:
        error("Multi-band masks are not supported!")
        sys.exit(1)

    if IMG_MASK.dtype != 'uint8':
        error("Unsupported mask data type '%s'!" % IMG_MASK.dtype)
        sys.exit(1)

    if Point2(IMG_IN.size) != Point2(IMG_MASK.size):
        error(
            "Input mask and image must have the same pixel"
            " size! image: %dx%d  mask: %dx%d" %
            (IMG_IN.size.y, IMG_IN.size.x, IMG_MASK.size.y, IMG_MASK.size.x)
        )
        sys.exit(1)

    # creation parameters
    PARAM = {
        'path':   OUTPUT,
        'nrow':   IMG_IN.size.y,
        'ncol':   IMG_IN.size.x,
        'nband':  IMG_IN.size.z,
        'dtype':  IMG_IN.dtype,
        'options' : FOPTS.options,
        'nodata': NODATA,
    }
    PARAM.update(IMG_IN.geocoding) # add geo-coding

    # open output image
    IMG_OUT = create_geotiff(**PARAM)

    # block size
    TILE_SIZE = (int(FOPTS["BLOCKXSIZE"]), int(FOPTS["BLOCKYSIZE"]))

    print "Clipping image by a mask ..."
    execute(
        IMG_OUT.tiles(TILE_SIZE), process, (
            IMG_IN, IMG_MASK, IMG_OUT, NODATA, MASKBG,
        ),
        progress=Progress(sys.stdout, IMG_OUT.tile_count(TILE_SIZE)),
    )
