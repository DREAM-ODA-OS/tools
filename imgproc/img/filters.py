#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Image filters.
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

from math import sqrt, erf
from numpy import linspace, empty, zeros, vectorize
from .block import BaseBlock
from .points import Point3

def coeff1d_gauss(whs):
    """ Evaluate Gauss Blur 1D convolution filter coefficients
    for the given window half size.
    """
    # pylint: disable=invalid-name
    c0 = 3.0 / sqrt(2.0)
    f0 = 0.5 / erf(c0)
    tmp = f0 * vectorize(erf)(c0 * linspace(-1.0, 1.0, 2*whs + 2))
    return tmp[1:] - tmp[:-1]


def coeff1d_boxcar(whs):
    """ Evaluate Box-Car 1D convolution filter coefficients
    for the given window half size.
    """
    coeff = empty(2*whs + 1)
    coeff = 1.0 / len(coeff)
    return coeff


def coeff1d_identity(whs):
    """ Evaluate Box-Car 1D convolution filter coefficients
    for the given window half size.
    """
    coeff = zeros(2*whs + 1)
    coeff[whs] = 1.0
    return coeff


def filter_conv_separable(tile, row_kernel, col_kernel, dtype='float32'):
    """ Apply separable convolution filter to the image.
    The tile is expected to enlarged by the half of the kernel size
    on each side.
    """
    n_row, n_col = len(row_kernel), len(col_kernel)
    assert (n_row % 2 == 1) and (n_col % 2 == 1)

    output_size = tile.size - Point3(n_col - 1, n_row - 1, 0)
    output_offset = tile.offset + Point3(n_col // 2, n_row // 2, 0)

    # PASS 1 - convolute by rows
    src = tile.data
    dst = zeros((output_size.y, tile.size.x, tile.size.z), dtype)
    size = dst.shape[0]
    for i in xrange(n_row):
        dst += row_kernel[i] * src[i:(i + size), :, :]

    # PASS 2 - convolute by columns
    src = dst
    dst = zeros((output_size.y, output_size.x, tile.size.z), dtype)
    size = dst.shape[1]
    for i in xrange(n_col):
        dst += col_kernel[i] * src[:, i:(i + size), :]

    return BaseBlock(dst, output_size, output_offset)


def filter_boxcar(tile, row_whs, col_whs, dtype='float32'):
    """ Apply separable convolution filter to the image.
    The tile is expected to enlarged by the half of the kernel size
    on each side.
    """
    n_row, n_col = 2*row_whs + 1, 2*col_whs + 1
    output_size = tile.size - Point3(n_col - 1, n_row - 1, 0)
    output_offset = tile.offset + Point3(n_col // 2, n_row // 2, 0)

    # PASS 1 - convolute by rows
    src = tile.data
    dst = zeros((output_size.y, tile.size.x, tile.size.z), dtype)
    size = dst.shape[0]
    for i in xrange(n_row):
        dst += src[i:(i + size), :, :]

    # PASS 2 - convolute by columns
    src = dst
    dst = zeros((output_size.y, output_size.x, tile.size.z), dtype)
    size = dst.shape[1]
    for i in xrange(n_col):
        dst += src[:, i:(i + size), :]

    dst *= 1.0 / (n_row * n_col)

    return BaseBlock(dst, output_size, output_offset)


def mirror_borders(tile, image):
    """ Mirror the border values for the tiles extending the image borders. """
    # lower X-edge
    diff = max(0, image.offset.x - tile.offset.x)
    tile.data[:, :diff, :] = tile.data[:, (2*diff - 1):(diff - 1):-1, :]

    # upper X-edge
    size = tile.size.x
    diff = max(0, (tile.offset.x + size) - (image.offset.x + image.size.x))
    tile.data[:, (size - 1):(size - diff - 1):-1, :] = (
        tile.data[:, (size - 2*diff):(size - diff), :]
    )

    # lower Y-edge
    diff = max(0, image.offset.y - tile.offset.y)
    tile.data[:diff, :, :] = tile.data[(2*diff - 1):(diff - 1):-1, :, :]

    # upper Y-edge
    size = tile.size.y
    diff = max(0, (tile.offset.y + size) - (image.offset.y + image.size.y))
    tile.data[(size - 1):(size - diff - 1):-1, :, :] = (
        tile.data[(size - 2*diff):(size - diff), :, :]
    )
    return tile
