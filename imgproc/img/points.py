#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Point primitives
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

from collections import namedtuple
from math import sqrt

_BasePoint2 = namedtuple("_BasePoint2", ['x', 'y'])
_BasePoint3 = namedtuple("_BasePoint3", ['x', 'y', 'z'])


class Point2(_BasePoint2):
    """ 2D point class. """
    __slots__ = ()

    def __new__(cls, x, y=None):
        if isinstance(x, (_BasePoint2, _BasePoint3)):
            x, y = x.x, x.y
        elif isinstance(x, (tuple, list)):
            x, y = x
        return super(Point2, cls).__new__(cls, x, y)

    def __str__(self):
        return str(tuple(self))

    def __lt__(self, other):
        x, y = _parse2(other)
        return self.__class__(self.x < x, self.y < y)

    def __le__(self, other):
        x, y = _parse2(other)
        return self.__class__(self.x <= x, self.y <= y)

    def __gt__(self, other):
        x, y = _parse2(other)
        return self.__class__(self.x > x, self.y > y)

    def __ge__(self, other):
        x, y = _parse2(other)
        return self.__class__(self.x >= x, self.y >= y)

    def __neg__(self):
        return self.__class__(-self.x, -self.y)

    def __add__(self, other):
        x, y = _parse2(other)
        return self.__class__(self.x + x, self.y + y)

    def __sub__(self, other):
        x, y = _parse2(other)
        return self.__class__(self.x - x, self.y - y)

    def __floordiv__(self, other):
        x, y = _parse2(other)
        return self.__class__(self.x // x, self.y // y)

    def min(self, other):
        """ Get minimum of this and the other value. """
        x, y = _parse2(other)
        return self.__class__(min(self.x, x), min(self.y, y))

    def max(self, other):
        """ Get maximum of this and the other value. """
        x, y = _parse2(other)
        return self.__class__(max(self.x, x), max(self.y, y))

    def prod(self):
        """ Get product of the values. """
        return self.x * self.y

    def dot(self, other):
        """ Calculate dot product. """
        return (self.x * other.x) + (self.y * other.y)

    def dot_self(self, other):
        """ Calculate dot product with itself. """
        return self.dot(self)

    def length(self):
        """ Get the vector length. """
        return sqrt(self.dot(self))


class Point3(_BasePoint3):
    """ 3D point class. """
    __slots__ = ()

    def __new__(cls, x, y=None, z=None):
        if isinstance(x, _BasePoint3):
            x, y, z = x.x, x.y, x.z
        elif isinstance(x, (tuple, list)):
            x, y, z = x
        return super(Point3, cls).__new__(cls, x, y, z)

    def __lt__(self, other):
        x, y, z = _parse3(other)
        return self.__class__(self.x < x, self.y < y, self.z < z)

    def __le__(self, other):
        x, y, z = _parse3(other)
        return self.__class__(self.x <= x, self.y <= y, self.z <= z)

    def __gt__(self, other):
        x, y, z = _parse3(other)
        return self.__class__(self.x > x, self.y > y, self.z > z)

    def __ge__(self, other):
        x, y, z = _parse3(other)
        return self.__class__(self.x >= x, self.y >= y, self.z >= z)

    def __str__(self):
        return str(tuple(self))

    def __neg__(self):
        return self.__class__(-self.x, -self.y, -self.z)

    def __add__(self, other):
        x, y, z = _parse3(other)
        return self.__class__(self.x + x, self.y + y, self.z + z)

    def __sub__(self, other):
        x, y, z = _parse3(other)
        return self.__class__(self.x - x, self.y - y, self.z - z)

    def __floordiv__(self, other):
        x, y, z = _parse3(other)
        return self.__class__(self.x // x, self.y // y, self.z // z)

    def min(self, other):
        """ Get minimum of this and the other value. """
        x, y, z = _parse3(other)
        return self.__class__(min(self.x, x), min(self.y, y), min(self.z, z))

    def max(self, other):
        """ Get maximum of this and the other value. """
        x, y, z = _parse3(other)
        return self.__class__(max(self.x, x), max(self.y, y), max(self.z, z))

    def prod(self):
        """ Get product of the values. """
        return self.x * self.y * self.z

    def dot(self, other):
        """ Calculate dot product. """
        return (self.x * other.x) + (self.y * other.y) + (self.z * other.z)

    def dot_self(self, other):
        """ Calculate dot product with itself. """
        return self.dot(self)

    def length(self):
        """ Get the vector length. """
        return sqrt(self.dot(self))


def _parse2(value):
    """ Parse any input. """
    if isinstance(value, (_BasePoint2, _BasePoint3)):
        return value.x, value.y
    else:
        return value, value


def _parse3(value):
    """ Parse any input. """
    if isinstance(value, _BasePoint3):
        return value.x, value.y, value.z
    else:
        return value, value, value
