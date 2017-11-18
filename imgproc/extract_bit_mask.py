#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool extracts a single bit-mask plane (as a 'byte' mask) from
#   a bit-flag image.
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
from img import (
    FormatOptions, ImageFileReader, create_geotiff, DEF_GEOTIFF_FOPT,
    Progress, Block, execute,
)
from img.algs import extract_bit_mask
from img.cli import error

MASKBG = 0x00
MASKFG = 0xFF

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <input image> <output mask/TIF> <bitwise-and-mask> "
        " [EQUAL]" % exename
    )
    print >>sys.stderr, "EXAMPLE: %s input.tif mask.tif 128" % exename
    print >>sys.stderr, "EXAMPLE: %s input.tif mask.tif 12 EQUAL" % exename


def process(tile, img_in, img_out, value, equal):
    """ Process one tile. """
    tile = tile & img_out # clip tile to the image extent
    b_in = img_in.read(Block(img_in.dtype, tile))
    b_mask = extract_bit_mask(b_in, value, equal)
    b_out = replace_bool(b_mask, MASKBG, MASKFG, 'uint8')
    img_out.write(b_out)


if __name__ == "__main__":
    ALLOWED_DTYPES = ('uint8', 'uint16', 'uint32', 'int8', 'int16', 'int32')
    FOPTS = FormatOptions(DEF_GEOTIFF_FOPT) # default format options
    EQUAL = False
    MASKBG = 0x00
    MASKFG = 0xFF
    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        VALUE = int(sys.argv[3])
        for opt in sys.argv[4:]:
            if opt.upper() == "EQUAL":
                EQUAL = True
            else:
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
        error("Multi-band bit-masks are not supported!")
        sys.exit(1)

    if IMG_IN.dtype not in ALLOWED_DTYPES:
        error("Unsupported bit-mask data type '%s'!" % IMG_IN.dtype)
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
    TILE_SIZE = (int(FOPTS["BLOCKXSIZE"]), int(FOPTS["BLOCKYSIZE"]))

    print "Extracting bit-flags as a mask ..."
    execute(
        IMG_OUT.tiles(TILE_SIZE), process, (IMG_IN, IMG_OUT, VALUE, EQUAL),
        progress=Progress(sys.stdout, IMG_OUT.tile_count(TILE_SIZE)),
    )
