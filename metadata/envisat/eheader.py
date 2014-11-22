#
# $Id$
#
# Project: Envisat Product Utilities
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

try:
    from  cStringIO import StringIO
except ImportError:
    from  StringIO import StringIO

import ehtypes as eht

#------------------------------------------------------------------------------
# header sections offsets and sizes

MPH_SIZE = 1247 # main product header size - constant

#------------------------------------------------------------------------------

class Record(object):
    """ class holding single header record """

    @property
    def value(self):
        "record's value object"
        return self.__v

    @property
    def key(self):
        "record's key"
        return self.__k

    @property
    def dtype(self):
        "value's type"
        return self.__v.__class__.__name__.upper()

    def __str__(self):
        if self.key is None:
            rv = str(self.value)
        else:
            rv = "%s=%s" % (self.key, self.value)

        if len(rv) != self.length:
            raise RuntimeError("Record length overflow! RECORD='%s'" % rv)

        return rv

    def __init__(self, data):
        try: # split the key and value
            self.__k, tmp = data.split('=')
        except ValueError: # separator
            self.__k, self.__v = None, eht.Spare(data)
        else: # parse key/value pair
            self.__v = eht.parse_header_value(tmp)

    @property
    def length(self):
        """ return length of the record """

        if self.key is None:
            return self.value.length
        else:
            return self.value.length + len(self.__k) + 1

#------------------------------------------------------------------------------

class HeaderSection(object):
    """ class holding header section of an ENVISAT format file """

    def __init__(self, data):
        """ parse from string block """
        #TODO: change to ordered dict
        #lreci - list of records (preserves order and spares)
        #irec - dictionary of the key vlaue pairs
        lrec, irec = [], {}

        # parse records
        for srec in data.split('\n')[:-1]:
            tmp = Record(srec)
            lrec.append(tmp)
            irec[tmp.key] = tmp.value

        # store the parsed records
        self.__lrec, self.__irec = lrec, irec

    def __getitem__(self, key):
        """ get record value """
        return  self.__irec[key].get()

    def __setitem__(self, key, value):
        """ set record value """
        self.__irec[key].set(value)

    @property
    def length(self):
        """ return length of the header """
        raise RuntimeError

    def __str__(self):
        """ dump header to a file """
        tmp = [str(r) for r in self.__lrec]
        tmp.append("")
        return "\n".join(tmp)

#------------------------------------------------------------------------------

class ProductHeader(object):
    """
        Envisat product class

        The class constructor reads and parses product header from the provided
        file. Any field can be read or modified. The [modified] header can be
        dupmed as a string by the __str__() method.

    """

    @property
    def mph(self):
        "product's MPH"
        return self.__mph

    @property
    def sph(self):
        "product's SPH"
        return self.__sph

    @property
    def dsd(self):
        "product's DSDs"
        return self.__idsd

    @property
    def dsds(self):
        "list product's DSDs"
        return self.__ldsd

    @property
    def dsds_all(self):
        "list of product's DSDs including the spares"
        return self.__ldsd_all

    @property
    def length(self):
        """ return length of the  """
        return self.__len


    def __init__(self, fid, fname=None):
        """ parse product headers """
        # MPH - Main Product Header
        self.__mph = HeaderSection(fid.read(MPH_SIZE))

        # read the important sizes
        dsd_size = self.mph['DSD_SIZE']
        dsd_cnt = self.mph['NUM_DSD'] - 1
        sph_size = self.mph['SPH_SIZE'] - dsd_size * self.mph['NUM_DSD']

        self.__len = MPH_SIZE + self.mph['SPH_SIZE']

        # SPH - Specific Product Header
        self.__sph = HeaderSection(fid.read(sph_size))

        # DSDs - Data Set Descriptors
        #ldsd - list of DSDs (preserves order)
        #idsd - dictionary of the key/DSD pairs
        ldsd_all, ldsd, idsd = [], [], {}

        for _ in xrange(dsd_cnt):
            dsd = HeaderSection(fid.read(dsd_size))
            ldsd_all.append(dsd)
            try:
                idsd[dsd["DS_NAME"].strip()] = dsd
                ldsd.append(dsd)
            except KeyError:
                pass # spare (see, e.g., MER_FR__2P)

        # load the terminating spare
        ldsd_all.append(HeaderSection(fid.read(dsd_size)))

        self.__ldsd_all, self.__ldsd, self.__idsd = ldsd_all, ldsd, idsd


    def __str__(self):
        rv = []
        rv.append(str(self.mph))
        rv.append(str(self.sph))
        for dsd in self.__ldsd_all:
            rv.append(str(dsd))
        rv = "".join(rv)
        if len(rv) != self.length:
            raise RuntimeError("Header size mismatch!")
        return rv


    def copy(self):
        """ make identical independent copy of this product header """
        return self.__class__(StringIO(str(self)))


# quick test
#if __name__ == "__main__":
#    import sys
#    with file(sys.argv[1]) as fid0:
#        h = ProductHeader(fid0)
#        h.mph["LEAP_ERR"] = 1
#        sys.stdout.write(str(h))
