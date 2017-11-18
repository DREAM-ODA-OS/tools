#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Shared utilities
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

class Progress(object):
    """ Simple CLI progress indicator. """
    # pylint: disable=too-few-public-methods

    PROGRES_STRING = [
        '0', '.', '.', '.', '10', '.', '.', '.', '20', '.', '.', '.',
        '30', '.', '.', '.', '40', '.', '.', '.', '50', '.', '.', '.',
        '60', '.', '.', '.', '70', '.', '.', '.', '80', '.', '.', '.',
        '90', '.', '.', '.', '100\n'
    ]

    def __init__(self, fout, final=100):
        self._fout = fout # output file-stream
        self._final = final # final progress limit
        self._scale = (len(self.PROGRES_STRING) - 1) / float(final)
        self._current = 0 # current progress
        self._strpos = 0 # position in the progress string

    def update(self, increment=1):
        """ Update the progress output. """
        self._current = min(self._final, self._current + increment)
        new_strpos = 1 + int(round(self._current * self._scale))
        self._fout.write("".join(self.PROGRES_STRING[self._strpos:new_strpos]))
        self._fout.flush()
        self._strpos = new_strpos


class FormatOptions(dict):
    """ Helper class holding GDAL format options. """
    def __init__(self, options=None):
        dict.__init__(self, options)

    def set_option(self, option):
        """ Parse and set one option. """
        key, val = option.split("=")
        self[key.strip()] = val.strip()

    def set_options(self, options):
        """ Parse and set multiple options. """
        for option in options:
            self.set_option(option)

    @property
    def options(self):
        """ Parse and set multiple options. """
        return ["%s=%s" % (key, val) for key, val in self.iteritems()]
