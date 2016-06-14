#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Processing subroutines.
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

from numpy import ones, empty, log10
from .points import Point2, Point3
from .block import Block
from .extent import Extent

def clone(b_data):
    """ Clone the data block by making and identical copy."""
    b_new = Block(b_data.dtype, b_data.size, b_data.offset)
    b_new.data[...] = b_data.data[...]
    return b_new


def threshold_values(tile, threshold, low_value, high_value, dtype='uint8'):
    """ Threshold the provided values using the given threshold value.
    The output value is set either to the low_value or the high value
        (high_value if value > threshold else low_value)
    """
    output = Block(dtype, tile.size, tile.offset)
    output.data[:, :, :] = low_value
    output.data[tile.data > threshold] = high_value
    return output


def normalize_values(tile, min_value, max_value, dtype='float32'):
    """ Normalize pixel values between the given minimum and maximum. """
    output = Block(dtype, tile.size, tile.offset)
    scale = 1.0 / (max_value - min_value)
    output.data[:, :, :] = (tile.data - min_value) * scale
    return output


def replace_bool(b_mask, false=0x00, true=0xFF, dtype='uint8'):
    """ Replace boolean mask values by the given constants. """
    b_out = Block(dtype, b_mask)
    b_out.fill(false)
    b_out.data[b_mask.data] = true
    return b_out


def extract_mask(b_data, nodata, all_valid=False):
    """ Extract valid data mask.  Two modes supported:
      ANY mode: any band contains valid data
      ALL mode: all bands contain valid data
    """
    b_mask = Block('bool', Point2(b_data.size), Point2(b_data.offset))
    _get_data_mask(b_mask.data[:, :, 0], b_data.data, nodata, all_valid)
    return b_mask


def extract_mask_multi(b_data, nodata, all_valid=False):
    #pylint: disable=too-many-arguments
    """ Extract valid data mask.  Two modes supported:
      ANY mode: any band contains valid data
      ALL mode: all bands contain valid data
    Multi-value variant.
    """
    b_mask = Block('bool', Point2(b_data.size), Point2(b_data.offset))
    _get_data_mask_multi_nd(b_mask.data[:, :, 0], b_data.data, nodata, all_valid)
    return b_mask


def clip_to_mask(b_data, b_mask, nodata, clipped_mask_value=0):
    """ Clip image data to the map.
    The function re-writes the original block.
    """
    if b_data.shape[:-1] != b_mask.shape[:-1]:
        raise ValueError("Equal blocks' sizes required!")
    if b_mask.shape[-1] < 1:
        raise ValueError("The mask has to have at least one band.")
    b_new = clone(b_data) # clone the input data
    mask = (b_mask.data[..., 0] == clipped_mask_value)
    for idx in xrange(b_data.shape[-1]):
        b_new.data[..., idx][mask] = nodata[idx]
    return b_new


def count_mask_pixels(b_mask, value, equal=True, bitwise_and=False):
    """ Count all mask pixels satisfying the match criteria:

        equal   bitwise_and   expression
        ------------------------------------------------
        False   False         mask[...] != 0
        True    False         mask[...] == value         [DEFAULT]
        False   True          mask[...] & value != 0
        True    True          mask[...] & value == value
    """
    if b_mask.shape[-1] < 1:
        raise ValueError("The mask has to have at least one band.")
    mask = b_mask.data[..., 0]
    if bitwise_and:
        mask &= value
    return ((mask == value) if equal else (mask != 0)).sum()


def extract_bit_mask(b_flags, value, equal=True):
    """ Extract bit mask from pixel values satisfying the match criteria:

        equal   expression
        ----------------------------------
        False   mask[...] & value != 0
        True    mask[...] & value == value  [DEFAULT]
    """
    #pylint: disable=too-many-arguments
    if b_flags.shape[-1] < 1:
        raise ValueError("The flag-mask has to have at least one band.")
    b_mask = Block('bool', Point2(b_flags.size), Point2(b_flags.offset))
    mask = b_flags.data[..., 0] & value
    b_mask.data[..., 0] = (mask == value) if equal else (mask != 0)
    return b_mask


def set_bit_mask(b_flags, b_mask, bmask_value):
    """ Set bit mask. """
    assert b_flags.size.z == 1 and b_mask.size.z == 1
    b_out = Block(b_flags.dtype, b_flags)
    b_out.data[...] = b_flags.data & ~bmask_value
    b_out.data[...] |= b_mask.data * bmask_value
    return b_out


def get_data_extent(b_mask, nodata):
    """ Extract extent envelope of the data. """
    if b_mask.shape[-1] < 1:
        raise ValueError("The mask has to have at least one band.")
    data = b_mask.data[..., 0]

    ymin, ymax = data.shape[0], data.shape[0]
    for idx in xrange(data.shape[0]):
        if (data[idx, :] != nodata).any():
            ymin = idx
            break
    for idx in xrange(data.shape[0] - 1, ymin, -1):
        if (data[idx, :] != nodata).any():
            ymax = idx + 1
            break

    if ymin >= ymax: # no data found
        return Extent((0, 0, b_mask.size.z), b_mask.offset)

    xmin, xmax = data.shape[1], data.shape[1]
    for idx in xrange(data.shape[1]):
        if (data[ymin:ymax, idx] != nodata).any():
            xmin = idx
            break
    for idx in xrange(data.shape[1] - 1, xmin, -1):
        if (data[ymin:ymax, idx] != nodata).any():
            xmax = idx + 1
            break

    return Extent(
        (xmax - xmin, ymax - ymin, b_mask.size.z),
        b_mask.offset + Point3(xmin, ymin, 0)
    )


def range_stretch_uint8(b_in, b_mask, vmin, vmax, scale_type="linear",
                        add_alpha=False):
    # pylint: disable=too-many-arguments
    """ Stretch multi-band data input to UInt8. """
    assert b_mask.dtype == 'bool' and b_mask.size.z == 1

    # expand the scalar vmin and vmax
    if not hasattr(vmin, "__len__"):
        vmin = b_in.size.z * [vmin]
    if not hasattr(vmax, "__len__"):
        vmax = b_in.size.z * [vmax]

    # prepare output block
    b_out = Block(
        'uint8', (b_in.size.x, b_in.size.y, b_in.size.z + add_alpha),
        Point2(b_in.offset)
    )
    b_out.fill(0)

    # scale data and update data mask
    scaled_data, mask = _SCALE[scale_type](
        empty(b_in.data.shape, 'float32'), b_in.data, b_mask.data[..., 0],
        vmin, vmax, 253.0, 2.0
    )

    for idx in xrange(b_in.shape[-1]):
        tmp = scaled_data[..., idx][mask]
        tmp[tmp < 1.0] = 1.0
        tmp[tmp > 255.0] = 255.0
        b_out.data[..., idx][mask] = tmp
    if add_alpha:
        b_out.data[..., -1][mask] = 255
    return b_out


def scale_values(b_in, b_mask_in, scale_type="linear", vmin=0.0, vmax=1.0,
                 scale=1.0, offset=0.0, dtype='float32'):
    # pylint: disable=too-many-arguments
    """ Scale values. """
    assert b_mask_in.dtype == 'bool' and b_mask_in.size.z == 1

    # expand the scalar vmin and vmax
    if not hasattr(vmin, "__len__"):
        vmin = b_in.size.z * [vmin]
    if not hasattr(vmax, "__len__"):
        vmax = b_in.size.z * [vmax]

    # copy the mask
    b_mask_out = Block(b_mask_in.dtype, b_mask_in)
    b_mask_out.data[...] = b_mask_in.data

    # allocate output array
    b_out = Block(dtype, b_in)
    # scale
    _SCALE[scale_type](
        b_out.data, b_in.data, b_mask_out.data[:, :, 0],
        vmin, vmax, scale, offset
    )
    return b_out, b_mask_out


# ------------------------------------------------------------------------------
# low level subroutines

def _scale_identity(out, data, mask, vmins, vmaxs, scale=1.0, offset=0.0):
    # pylint: disable=unused-argument, too-many-arguments
    """ A scale which passes unmodified input data. """
    out[...] = data
    return out, mask


def _scale_linear(out, data, mask, vmins, vmaxs, scale=1.0, offset=0.0):
    # pylint: disable=too-many-arguments
    """ Linear data scaling. The mask is not updated."""
    _scales = [scale / float(vmax - vmin) for vmin, vmax in zip(vmins, vmaxs)]
    _offsets = [offset - _scale * vmin for vmin, _scale in zip(vmins, _scales)]
    for idx in xrange(data.shape[-1]):
        out[:, :, idx] = _scales[idx] * data[:, :, idx] + _offsets[idx]
    return out, mask


def _scale_log10(out, data, mask, vmins, vmaxs, scale=1.0, offset=0.0):
    # pylint: disable=too-many-arguments
    """ logarithmic data scaling. """
    _scales = [scale / float(vmax - vmin) for vmin, vmax in zip(vmins, vmaxs)]
    _offsets = [offset - _scale * vmin for vmin, _scale in zip(vmins, _scales)]
    for idx in xrange(data.shape[-1]):
        mask &= (data[:, :, idx] > 0.0)
        out[:, :, idx][mask] = (
            _scales[idx] * log10(data[:, :, idx][mask]) + _offsets[idx]
        )
    return out, mask


def _scale_db(out, data, mask, vmins, vmaxs, scale=1.0, offset=0.0):
    # pylint: disable=too-many-arguments
    """ decibel data scaling. """
    vmins = [0.1*v for v in vmins]
    vmaxs = [0.1*v for v in vmaxs]
    return _scale_log10(out, data, mask, vmins, vmaxs, scale, offset)


_SCALE = {
    "decibel": _scale_db,
    "logarithmic": _scale_log10,
    "identity": _scale_identity,
    "linear": _scale_linear,
}


def _get_data_mask(mask, data, nodata, all_valid=False):
    """ Extract valid data mask.  Two modes supported:
      ANY mode: any band contains valid data
      ALL mode: all bands contain valid data
    """
    if all_valid:
        return _get_data_mask_if_all_valid(mask, data, nodata)
    else:
        return _get_data_mask_if_any_valid(mask, data, nodata)


def _get_data_mask_multi_nd(mask, data, nodata, all_valid=False):
    if all_valid:
        return _get_data_mask_if_all_valid_multi_nd(mask, data, nodata)
    else:
        return _get_data_mask_if_any_valid_multi_nd(mask, data, nodata)


def _get_data_mask_if_any_valid(mask, data, nodata):
    """ Extract data mask if any band contains valid data."""
    if nodata:
        mask[...] = False
        for idx in xrange(data.shape[-1]):
            mask |= (data[..., idx] != nodata[idx])
    else:
        mask[...] = True
    return mask

def _get_data_mask_if_any_valid_multi_nd(mask, data, nodata):
    #pylint: disable=invalid-name
    """ Extract data mask if any band contains valid data."""
    if nodata:
        mask[...] = False
        for idx in xrange(data.shape[-1]):
            tmp = ones(mask.shape, 'bool')
            for value in nodata[idx]:
                tmp &= (data[..., idx] != value)
            mask |= tmp
    else:
        mask[...] = True
    return mask

def _get_data_mask_if_all_valid(mask, data, nodata):
    """ Extract data mask if all bands contain valid data."""
    if data.shape[-1] > 0:
        mask[...] = True
        if nodata:
            for idx in xrange(data.shape[-1]):
                mask &= (data[..., idx] != nodata[idx])
    else:
        mask[...] = False
    return mask


def _get_data_mask_if_all_valid_multi_nd(mask, data, nodata):
    #pylint: disable=invalid-name
    """ Extract data mask if all bands contain valid data."""
    if data.shape[-1] > 0:
        mask[...] = True
        if nodata:
            for idx in xrange(data.shape[-1]):
                for value in nodata[idx]:
                    mask &= (data[..., idx] != value)
    else:
        mask[...] = False
    return mask
