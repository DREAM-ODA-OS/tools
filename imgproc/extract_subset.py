#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   This tool extracts subset of an image specified by the row/column
#   offset of the upper-left corner and row/column size of extracted
#   block. The tool takes care of preserving the geocoding.
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
    FormatOptions, create_geotiff, DEF_GEOTIFF_FOPT,
    Extent, Block, ImageFileReader, Progress, execute,
    pixel_offset
)
from img.cli import error

def usage():
    """Print a short command usage help."""
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <input image> <output TIF> "
        "<offset-x>,<offset-y>,<sizex>,<sizey>" % exename
    )
    print >>sys.stderr, (
        "EXAMPLE: %s input.tif subset.tif 10,20,200,200" % exename
    )


def parse_subset(subset_str):
    """ Parse subset string. """
    try:
        offx, offy, sizex, sizey = (int(v) for v in subset_str.split(","))
        return Extent((max(0, sizex), max(0, sizey)), (offx, offy))
    except ValueError:
        raise ValueError("Invalid subset specification! %r" % subset_str)


def process(tile, img_in, img_out, subset):
    """ Process one tile. """
    tile = tile & img_out # clip tile to the image extent
    b_in = img_in.read(Block(img_in.dtype, tile + subset.offset))
    b_in -= subset.offset
    img_out.write(b_in)


if __name__ == "__main__":
    FOPTS = FormatOptions(DEF_GEOTIFF_FOPT) # default format options
    try:
        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        SUBSET = parse_subset(sys.argv[3])
        #anything else treated as a format option
        FOPTS.set_options(sys.argv[5:])
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)
    except ValueError as exc:
        error(exc)
        sys.exit(1)

    # open input image
    IMG_IN = ImageFileReader(INPUT)

    # trim the subset by the input image extent
    SUBSET = (SUBSET & IMG_IN).set_z(IMG_IN)

    # creation parameters
    PARAM = {
        'path':   OUTPUT,
        'nrow':   SUBSET.size.y,
        'ncol':   SUBSET.size.x,
        'nband':  IMG_IN.size.z,
        'dtype':  IMG_IN.dtype,
        'nodata': IMG_IN.nodata,
        'options' : FOPTS.options,
    }
    # add translated geo-coding
    PARAM.update(
        pixel_offset(IMG_IN.geocoding, (SUBSET.offset.x, SUBSET.offset.y))
    )

    # open output image
    IMG_OUT = create_geotiff(**PARAM)

    # block size
    TILE_SIZE = (int(FOPTS["BLOCKXSIZE"]), int(FOPTS["BLOCKYSIZE"]))

    print "Extracting image subset..."
    execute(
        IMG_OUT.tiles(TILE_SIZE), process, (IMG_IN, IMG_OUT, SUBSET),
        progress=Progress(sys.stdout, IMG_OUT.tile_count(TILE_SIZE)),
    )
