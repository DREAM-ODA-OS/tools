#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Extent class
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

from .points import Point2, Point3

class Offset(Point3):
    """ 3D offset class. """
    def __new__(cls, x, y=None, z=0):
        if hasattr(x, '__len__') and len(x) == 2:
            x, y = x
        return super(Offset, cls).__new__(cls, x, y, z)


class Size(Point3):
    """ 3D size class. """
    def __new__(cls, x, y=None, z=1):
        if hasattr(x, '__len__') and len(x) == 2:
            x, y = x
        return super(Size, cls).__new__(cls, x, y, z)


class Extent(object):
    """ Multi-band image extent object

        &   - area intersection (maximum common area)
        |   - area expansion (minimum area containing both boxes)
        +   - offset translation (adding vector to current value)
        -   - offset translation (subtracting vector from current value)
        +=  - in-place offset translation (adding vector to current value)
        -=  - in-place offset translation (subtracting vector from current value)
    """

    def __init__(self, size, offset=None):
        if isinstance(size, Extent):
            self.size, self.offset = size.size, size.offset
        else:
            self.size, self.offset = Size(size), Offset(offset or (0, 0, 0))

    def __str__(self):
        return "%s(size=%s, offset=%s)" % (
            self.__class__.__name__, self.size, self.offset
        )

    def __repr__(self):
        return self.__str__()

    @property
    def extent(self):
        """ Extent of the extent. """
        return self.size.max(0).prod()

    def set_z(self, size_z, offset_z=0):
        """ Change Z component of the size and offset. """
        if isinstance(size_z, Extent):
            size_z, offset_z = size_z.size.z, size_z.offset.z
        else:
            if isinstance(size_z, Point3):
                size_z = size_z.z
            if isinstance(offset_z, Point3):
                offset_z = offset_z.z # pylint: disable=no-member
        return Extent(
            (self.size.x, self.size.y, size_z),
            (self.offset.x, self.offset.y, offset_z),
        )

    def extend(self, extra_size):
        """ Extend the extend by the given size in the x and y directions. """
        extra = Point2(extra_size)
        return Extent(
            (self.size.x + 2*extra.x, self.size.y + 2*extra.y, self.size.z),
            (self.offset.x - extra.x, self.offset.y - extra.y, self.offset.z),
        )

    # area operators
    def __and__(self, other):
        """ operator - intersection """
        offset = self.offset.max(other.offset)
        size = (self.offset + self.size).min(other.offset + other.size) - offset
        return Extent(size, offset)

    def __or__(self, other):
        """ operator - expansion """
        offset = self.offset.min(other.offset)
        size = (self.offset + self.size).max(other.offset + other.size) - offset
        return Extent(size, offset)

    # offset translations
    def __add__(self, offset):
        """ operator - offset translation """
        return Extent(self.size, self.offset + Offset(offset))

    def __sub__(self, offset):
        """ operator - offset translation """
        return Extent(self.size, self.offset - Offset(offset))

    def __iadd__(self, offset):
        """ operator - offset translation """
        self.offset = self.offset + Offset(offset)
        return self

    def __isub__(self, offset):
        """ operator - offset translation """
        self.offset = self.offset - Offset(offset)
        return self

    def _tile_ranges(self, tsz):
        """ Get tile ranges. """
        low = self.offset
        upr = self.offset + self.size
        return (
            (low.x//tsz.x, 1 + (upr.x - 1)//tsz.x),
            (low.y//tsz.y, 1 + (upr.y - 1)//tsz.y),
        )

    def tiles(self, tile_size):
        """ Generate extent tiles. """
        tile_size = Point2(tile_size)
        (tx0, tx1), (ty0, ty1) = self._tile_ranges(tile_size)
        tile_extent = Extent((tile_size.x, tile_size.y, self.size.z))
        for tidx_y in xrange(ty0, ty1):
            for tidx_x in xrange(tx0, tx1):
                extent = tile_extent + (tidx_x*tile_size.x, tidx_y*tile_size.y)
                yield extent

    def tile_count(self, tile_size):
        """ Count extent tiles. """
        (tx0, tx1), (ty0, ty1) = self._tile_ranges(Point2(tile_size))
        return (max(tx0, tx1) - tx0) * (max(ty0, ty1) - ty0)
