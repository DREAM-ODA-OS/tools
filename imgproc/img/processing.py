#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Tile-based batch processing.
#
# Project: Image Processing Tools
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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

def execute(tileset, process, args=None, kwargs=None, progress=None):
    """ Apply process sequentially to the tile-set. """
    for tile in tileset:
        process(tile, *(args or ()), **(kwargs or {}))
        if progress:
            progress.update()


def aggregate(tileset, process, aggregator, initial_value,
              args=None, kwargs=None, progress=None):
    #pylint: disable=too-many-arguments
    """ Apply process sequentially to the tile-set aggregating the results. """
    aggregated_value = initial_value
    for tile in tileset:
        result = process(tile, *(args or ()), **(kwargs or {}))
        aggregated_value = aggregator(result, aggregated_value)
        if progress:
            progress.update()
    return aggregated_value
