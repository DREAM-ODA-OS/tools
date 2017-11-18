#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Extract pixel count.
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
from img import ImageFileReader, Progress, Block, aggregate, Point2
from img.algs import count_mask_pixels
from img.cli import error

def usage():
    """Print a short command usage help."""
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <input image> <data-value> [EQUAL] [AND] [ALL]" % exename
    )


def process(tile, img_mask, value, equal, bitwise_and):
    """ Process one tile. """
    tile = tile & img_mask # clip tile to the image extent
    b_mask = img_mask.read(Block(img_mask.dtype, tile))
    return count_mask_pixels(b_mask, value, equal, bitwise_and)


if __name__ == "__main__":
    ALLOWED_OPTIONS = set(("EQUAL", "AND", "ALL"))
    OPTIONS = set()
    VALUE = None
    DEBUG = False
    try:
        INPUT = sys.argv[1]
        for arg in sys.argv[2:]:
            if arg in ALLOWED_OPTIONS:
                OPTIONS.add(arg)
            elif arg == "DEBUG":
                DEBUG = True
            elif VALUE is None:
                VALUE = int(arg)
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    if "ALL" in OPTIONS:
        OPTIONS = set(("ALL",))
        VALUE = None

    if DEBUG:
        print >>sys.stderr, "INPUT:   %s" % INPUT
        print >>sys.stderr, "OPTIONS: %s" % " ".join(OPTIONS)
        print >>sys.stderr, "VALUE:   %s" % VALUE

    # open the mask image
    IMG_MASK = ImageFileReader(INPUT)

    # check mask properties
    if IMG_MASK.size.z > 1:
        error("Multi-band masks are not supported!")
        sys.exit(1)

    if IMG_MASK.dtype != 'uint8':
        error("Unsupported mask data type '%s'!" % IMG_MASK.dtype)
        sys.exit(1)

    print >>sys.stderr, "Counting pixels ..."

    if "ALL" in OPTIONS:
        print Point2(IMG_MASK.size).prod()
    else:
        TILE_SIZE = (256, 256)
        print aggregate(
            IMG_MASK.tiles(TILE_SIZE), process,
            lambda value, memo: memo + value, 0,
            (IMG_MASK, VALUE, "EQUAL" in OPTIONS, "AND" in OPTIONS),
            progress=Progress(sys.stderr, IMG_MASK.tile_count(TILE_SIZE)),
        )
