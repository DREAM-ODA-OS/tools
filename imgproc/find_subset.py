#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  This tool takes a mask and searches the minimum subset of the image
#  containing all the valid pixel. The extent of this subset is then returned
#  as pixel offset and size.
#
#  As output the command writes 4 comma separated integers values:
#
#   <col. offset>, <row offset>, <number of cols.>, <number of rows>
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
from img import ImageFileReader, Block
from img.algs import get_data_extent
from img.cli import error

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, "USAGE: %s <input image mask> <no data value>" % exename
    print >>sys.stderr, "EXAMPLE: %s mask.tif 0" % exename


def format_subset(subset):
    """ Format the subset extent. """
    return  "%d,%d,%d,%d" % (
        subset.offset.x, subset.offset.y, subset.size.x, subset.size.y,
    )


def process(tile, img_in, nodata_value):
    """ Single tile process. """
    tile = tile & img_in # clip tile to the image extent
    return get_data_extent(img_in.read(Block(img_in.dtype, tile)), nodata_value)


if __name__ == "__main__":
    ALLOWED_DTYPES = ('uint8', 'uint16', 'uint32', 'int8', 'int16', 'int32')
    try:
        INPUT = sys.argv[1]
        NODATA = sys.argv[2]
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

    if IMG_IN.dtype not in ALLOWED_DTYPES:
        error("Unsupported mask data type '%s'!" % IMG_IN.dtype)
        sys.exit(1)

    # convert no-data values to the image's data type
    NODATA = dtype(IMG_IN.dtype).type(NODATA)

    # extract and print the subset
    print format_subset(process(IMG_IN, IMG_IN, NODATA))
