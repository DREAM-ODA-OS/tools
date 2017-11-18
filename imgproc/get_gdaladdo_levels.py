#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Calculate possible >gdaladdo< overview levels
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
from img import ImageFileReader, Point2
from img.cli import error

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, (
        "USAGE: %s <input image> <stop_size_max> <stop_size_min>" % exename
    )
    print >>sys.stderr, "EXAMPLE: %s input.tif 256 16" % exename


def get_overlay_levels(size, stop_min, stop_max):
    """ Calculate overlay levels. """
    size = Point2(size)
    level = 1
    levels = []
    while (
            (size.x >= stop_min and size.y >= stop_min) and
            (size.x > stop_max and size.y > stop_max)
        ):
        level *= 2
        levels.append(level)
        size = (size + 1) // 2
    return levels


if __name__ == "__main__":
    try:
        INPUT = sys.argv[1]
        STOP_MAX = int(sys.argv[2])
        STOP_MIN = int(sys.argv[3])
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    print " ".join(
        str(level) for level
        in get_overlay_levels(ImageFileReader(INPUT).size, STOP_MIN, STOP_MAX)
    )
