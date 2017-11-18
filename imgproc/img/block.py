#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Block data class
#
# Author: Martin Paces <martin.paces@eox.at>
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

from numpy import empty
from .extent import Extent, Size
from .histogram import Histogram

class BaseBlock(Extent):
    """ Base multi-band image block class.

        Do not use this class directly unless you know what you are doing!
    """
    def __init__(self, data, size, offset=None):
        super(BaseBlock, self).__init__(size, offset)
        self._data = data

    data = property(lambda s: s._data, doc="data array(RO)")
    dtype = property(lambda s: s._data.dtype, doc="data type(RO)")
    shape = property(lambda s: s._data.shape, doc="array shape(RO)")

    def __str__(self):
        return "%s(size=%s, offset=%s, dtype=%s)" % (
            self.__class__.__name__, self.size, self.offset, self.dtype
        )

    def fill(self, value=0):
        """ Fill by a constant value. """
        self._data[...] = value
        return self

    def histogram(self, min_value, max_value, nbins, mask=None):
        """ Calculate histogram of the tile data. """
        histogram = Histogram(self.size.z, min_value, max_value, nbins)
        histogram.update(self._data if mask is None else self._data[mask])
        return histogram


class Block(BaseBlock):
    """ Multi-band image block class. """

    def __init__(self, dtype, size, offset=None):
        _size = size.size if isinstance(size, Extent) else Size(size)
        data = empty((_size.y, _size.x, _size.z), dtype)
        super(Block, self).__init__(data, size, offset)
