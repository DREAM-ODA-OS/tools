#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool writes a single bit-mask plane (from a 'byte' mask) to a bit-flag
#   image.
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
    ImageFileReader, ImageFileWriter, Progress, Block, execute, Point2
)
from img.algs import set_bit_mask
from img.cli import error

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <bit-flag-image> <mask> <bit-mask-value>" % exename
    )
    print >>sys.stderr, "EXAMPLE: %s flags.tif mask.tif 128" % exename
    print >>sys.stderr, "DESCRIPTION:"
    print >>sys.stderr, "  Burn binary mask to an existing bit flag image"
    print >>sys.stderr, "  as a new bit layer."


def process(tile, img_mask, img_flags, bmask_value, negate):
    """ Process one tile. """
    tile = tile & img_flags # clip tile to the image extent
    b_mask = Block('bool', tile)
    b_mask.data[...] = img_mask.read(Block(img_mask.dtype, tile)).data != 0
    if negate:
        b_mask.data[...] = ~b_mask.data
    b_flags = img_flags.read(Block(img_flags.dtype, tile))
    b_out = set_bit_mask(b_flags, b_mask, bmask_value)
    img_flags.write(b_out)


if __name__ == "__main__":
    ALLOWED_TYPES = ('uint8', 'uint16', 'uint32', 'int8', 'int16', 'int32')
    NEGATE = False
    try:
        OUTPUT = sys.argv[1]
        INPUT = sys.argv[2]
        BMASK = int(sys.argv[3])
        for opt in sys.argv[4:]:
            if opt.upper() in ("NEGATE", "NOT"):
                NEGATE = True
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    # open input image
    IMG_IN = ImageFileReader(INPUT)

    # open output image
    IMG_OUT = ImageFileWriter(OUTPUT)

    if IMG_IN.size.z > 1 or IMG_OUT.size.z > 1:
        error("Multi-band images are not supported!")
        sys.exit(1)

    if Point2(IMG_IN.size) != Point2(IMG_OUT.size):
        error("The image sizes must be equal")
        sys.exit(1)

    if IMG_IN.dtype not in ALLOWED_TYPES:
        error("Unsupported image mask's data type '%s'!" % IMG_IN.dtype)
        sys.exit(1)

    if IMG_OUT.dtype not in ALLOWED_TYPES:
        error(
            "Unsupported image bit-flag-image's data type '%s'!" % IMG_OUT.dtype
        )
        sys.exit(1)

    # convert bit mask values to the image's data type
    BMASK = dtype(IMG_OUT.dtype).type(BMASK)

    # block size
    #TILE_SIZE = (256, 256)
    TILE_SIZE = IMG_OUT[0].GetBlockSize()
    print "TILE_SIZE:", TILE_SIZE

    print "Adding bit flag ..."
    execute(
        IMG_OUT.tiles(TILE_SIZE), process, (IMG_IN, IMG_OUT, BMASK, NEGATE),
        progress=Progress(sys.stdout, IMG_OUT.tile_count(TILE_SIZE)),
    )
