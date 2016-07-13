#!/usr/bin/env python
#------------------------------------------------------------------------------
#
#   Covert histogram to a value ranges given by the user define percentiles.
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
from img.histogram import parse_histogram
from img.cli import error

def usage():
    """ Print simple usage help. """
    exename = basename(sys.argv[0])
    print >>sys.stderr, "USAGE: %s <histogram> <min.pct> <max.pct>" % exename
    print >>sys.stderr, "EXAMPLE: %s test.hist 5 95" % exename

if __name__ == "__main__":
    try:
        INPUT = sys.argv[1]
        MINPCT = max(0.0, min(100.0, float(sys.argv[2])))
        MAXPCT = max(0.0, min(100.0, float(sys.argv[3])))
    except IndexError:
        error("Not enough input arguments!")
        usage()
        sys.exit(1)

    with sys.stdin if INPUT == "-" else open(INPUT) as fobj:
        HISTOGRAM, METADATA = parse_histogram(fobj)

    if MINPCT >= MAXPCT:
        error("The lower percentile is not lower than the upper one!")

    print " ".join(
        ",".join("%g" % value for value in values) for values
        in zip(*HISTOGRAM.get_range(0.01*MINPCT, 0.01*MAXPCT))
    )
