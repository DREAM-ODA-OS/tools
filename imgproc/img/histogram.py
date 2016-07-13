#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Image histogram.
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

from numpy import zeros, histogram, linspace

class Histogram(object):
    """ Multi-band image histogram. """
    def __init__(self, nband, vmin, vmax, nbin):
        self.vmin = float(vmin)
        self.vmax = float(vmax)
        self.nbin = max(1, int(nbin))
        self.step = (self.vmax - self.vmin) / self.nbin
        # histogram arrays
        self.accum = zeros((nband, nbin + 2), 'uint64')
        self.count = zeros(nband, 'uint64')

    @property
    def density(self):
        """ Return probability density function (normalised histogram). """
        data = self.accum.astype('float')
        for idx in xrange(self.accum.shape[0]):
            if self.count[idx] > 0:
                data[idx, :] *= 1.0 / self.count[idx]
        return data

    @property
    def cumulative_density(self):
        """ Return cumulative density function (normalised histogram). """
        return self.density.cumsum(1)

    @property
    def centres(self):
        """ Return array of the bin centres. """
        return linspace(
            self.vmin - 0.5*self.step, self.vmax + 0.5*self.step, self.nbin + 2
        )

    def get_range(self, lower_pct, upper_pct):
        """ Get ranges for the given lower and upper percentiles. """
        assert lower_pct < 1.0
        assert upper_pct > 0.0

        ycdf = self.cumulative_density
        xcnt = self.centres
        ranges = []
        for band in xrange(ycdf.shape[0]):
            if lower_pct > 0:
                idx = (ycdf[band, :] < lower_pct).nonzero()[0].max()
                xmin = xcnt[idx] + (
                    self.step * (lower_pct - ycdf[band, idx]) /
                    (ycdf[band, idx+1] - ycdf[band, idx])
                )
            else:
                xmin = xcnt[0]
            if upper_pct < 1:
                idx = (ycdf[band, :] > upper_pct).nonzero()[0].min()
                xmax = xcnt[idx + 1] + (
                    self.step * (ycdf[band, idx] - upper_pct) /
                    (ycdf[band, idx] - ycdf[band, idx - 1])
                )
            else:
                xmax = xcnt[-1]
            ranges.append((xmin, xmax))
        return ranges

    def __add__(self, other):
        """ Join two histograms. """
        if other is None:
            return self
        new = Histogram(self.count.size, self.vmin, self.vmax, self.nbin)
        new.accum = self.accum + other.accum
        new.count = self.count + other.count
        return new

    def update(self, data):
        """ Add data to histogram. """
        vrange = (self.vmin - self.step, self.vmax + self.step)
        # clip the outliers
        data[data < self.vmin] = self.vmin - 0.5*self.step
        data[data > self.vmax] = self.vmax + 0.5*self.step
        # calculate the histograms
        for idx in xrange(self.accum.shape[0]):
            band_hist, _ = histogram(data[..., idx], self.nbin + 2, vrange)
            self.accum[idx, :] += band_hist
            self.count[idx] += band_hist.sum()

    def write(self, fobj, metadata=None):
        """ Write histogram to a file. """
        metadata_items = (metadata or {}).items() + [
            ("nband", self.count.size),
            ("vmin", self.vmin),
            ("vmax", self.vmax),
            ("nbin", self.nbin),
        ]
        # print header
        print >>fobj, "# HISTOGRAM"
        for item in metadata_items:
            print >>fobj, "#   %s: %s" % item
        print >>fobj, "# COUNT: %s" % " ".join("%d" % v for v in self.count)

        # print values
        for idx in xrange(self.nbin + 2):
            x_bin = (idx - 0.5) * self.step + self.vmin
            print >>fobj, "%g\t%s" % (
                x_bin, "\t".join("%d" % v for v in self.accum[:, idx])
            )


def parse_histogram(fobj):
    """ Parse histogram file. """
    # check signature
    try:
        if fobj.next().strip() != "# HISTOGRAM":
            raise ValueError
    except (StopIteration, ValueError):
        raise ValueError("Wrong histogram file signature!")

    # parse header
    line = None
    header = {}
    for line in fobj:
        if line[0] == "#":
            line = line[1:].strip()
            key, sep, val = line.partition(":")
            if sep == ":":
                header[key.strip()] = val.strip()
        else:
            break
    else:
        raise ValueError("No data line!")

    try:
        vmin = float(header['vmin'])
        vmax = float(header['vmax'])
        nbin = int(header['nbin'])
        nband = int(header['nband'])
        nband = int(header['nband'])
    except KeyError as exc:
        raise ValueError("Corrupted histogram header: missing key %s!" % exc)
    except ValueError as exc:
        raise ValueError("Corrupted histogram header: %s!" % exc)

    del header['vmin']
    del header['vmax']
    del header['nbin']
    del header['nband']
    if 'COUNT' in header:
        del header['COUNT']

    # create new histogram
    hist = Histogram(nband, vmin, vmax, nbin)

    # parse histogram values
    hist.accum[:, 0] = [int(v) for v in line.strip().split()[1:]]
    for idx in xrange(1, nbin + 2):
        line = fobj.next()
        hist.accum[:, idx] = [int(v) for v in line.strip().split()[1:]]

    # update counts
    hist.count[:] = hist.accum.sum(1)

    return hist, header
