#!/usr/bin/env python 
#
#  JP2k reader + GMLJ2k dump
#
#  The CLI tool dumps all nested association boxes stored in the jp2 file.
#  In most cases there will be only the embedded GMLJP2000.
#
# Author: Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

import struct
import sys
import os.path

FT = ("FALSE", "TRUE ")

class JP2000Stop(Exception):
    pass

class JP2000Abort(Exception):
    pass

class JP2000Error(Exception):
    pass

class JP2000ParsingError(JP2000Error):
    pass

#------------------------------------------------------------------------------
# jpeg 2000 boxes

class Box(object):
    """ base box class """
    subboxes = property(lambda s: s.__subboxes)
    btype = property(lambda s: s.__btype)
    offset = property(lambda s: s.__offset)
    length = property(lambda s: s.__length)
    is_super = property(lambda s: s.__is_super)

    def __init__(self, btype, offset, length, is_super=False):
        self.__btype = btype    # box type (ID string)
        self.__offset = offset   # offset to payload
        self.__length = length   # length of the payload
        self.__is_super = is_super # indicates whether box has subboxes
        self.__is_loaded = False  # indicates whether box has subboxes
        self.__subboxes = []

    def parse(self, fid):
        # omit payload parsing for non-super or already parsed payload
        if (not self.__is_super) or self.__is_loaded:
            return
        self.__subboxes = parse_boxes(fid, self.offset, self.length)

    def sprint_sub(self, indent=''):
        i2 = "  %s"%indent
        o = []
        for i in self.subboxes:
            o.append(i.sprint(i2))
        return "\n".join(o)

    def sprint(self, indent=''):
        o = []
        o.append("%s Box[%s] %d %d" % (indent, repr(self.btype), self.offset, self.length))
        if len(self.subboxes) > 0:
            o.append(self.sprint_sub(indent))
        return "\n".join(o)

    def __str__(self):
        return self.sprint('')

#------------------------------------------------------------------------------

class BoxSuper(Box):
    """ JP2000 Header  box parser """

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, True)
        self.parse(fid)

#------------------------------------------------------------------------------
# auxiliary block hadler

class BoxDump(Box):
    """ Auxiliary box loading and dumping its payload. """

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, False)
        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)
        self.data = fid.read(length)

    def sprint(self, indent=''):
        o = []
        o.append("%s Box[%s] %d %d" % (indent, repr(self.btype), self.offset, self.length))
        o.append("Payload:")
        o.append(repr(self.data))
        return "\n".join(o)

#------------------------------------------------------------------------------
# load data payload

class BoxBuffer(Box): # NOTE: must follow signature
    """ Auxiliary box loading its payload. """
    data = property(lambda s: s.__data)

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, False)
        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)
        self.__data = fid.read(length)

    def sprint(self, indent=''):
        o = []
        o.append("%s BoxBuffer[%s] %d %d" % (indent, repr(self.btype), self.offset, self.length))
        o.append("Payload:")
        o.append(repr(self.data))
        return "\n".join(o)

#------------------------------------------------------------------------------
# association text handler

class BoxAssocText(BoxBuffer):
    """ Association Base Text Box """
    text = property(lambda s: s.__text)

    def __init__(self, fid, btype, offset, length):
        BoxBuffer.__init__(self, fid, btype, offset, length)
        tmp = self.data if (self.data[-1] != '\x00') else self.data[:-1]
        self.__text = unicode(tmp)

    def sprint(self, indent=''):
        o = []
        o.append("%s BoxAssocText %d %d" % (indent, self.offset, self.length))
        o.append("%s   text:\n%s" % (indent, self.text))
        return "\n".join(o)


class BoxAssocLabel(BoxAssocText):
    """ Association Label Box """

    def sprint(self, indent=''):
        o = []
        o.append("%s BoxAssocLabel %d %d" % (indent, self.offset, self.length))
        o.append("%s   label: %s " % (indent, self.text))
        return "\n".join(o)


class BoxAssocXML(BoxAssocText):
    """ Association Label Box """

    def sprint(self, indent=''):
        o = []
        o.append("%s BoxAsocXML %d %d" % (indent, self.offset, self.length))
        o.append("%s   XML:\n%s" % (indent, self.text))
        return "\n".join(o)

#------------------------------------------------------------------------------
# defining specific boxes

class BoxSignature(Box):
    """ JP2000 File Singnature box parser """

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, False)
        # check the signature
        if (self.btype != btype) or (self.offset != 8) or (self.length != 4):
            raise JP2000ParsingError("Invalid file signature!")
        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)
        data = fid.read(4)
        # check payload
        if data != '\r\n\x87\n':
            raise JP2000ParsingError("Invalid file signature!")

    def sprint(self, indent=''):
        return "%s FileSignature %d %d" % (indent, self.offset, self.length)

#------------------------------------------------------------------------------

class BoxFileType(Box): # NOTE: must follow signature (fixed offset!)
    """ JP2000 File Type box parser """
    brand = property(lambda s: s.__brand)
    minver = property(lambda s: s.__minvr)
    cmpl = property(lambda s: s.__cmpl)

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, False)
        # check the signature
        if (self.btype != btype) or (self.offset != 20) \
                or ((self.length % 4) != 0) or (self.length < 12):
            raise JP2000ParsingError("Invalid FileType!")
        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)
        self.__brand = fid.read(4)
        self.__minvr = struct.unpack(">L", fid.read(4))[0]

        # compatibility list
        tmp = []
        for _ in xrange(length/4 - 2):
            tmp.append(fid.read(4))
        self.__cmpl = tmp

        # check payload
        if self.__brand != "jp2 ":
            raise JP2000ParsingError("Invalid file-type brand!")

        if "jp2 " not in self.__cmpl:
            raise JP2000ParsingError("Compatibility with baseline JP2000 not"
                " indicated!")


    def sprint(self, indent=''):
        o = []
        o.append("%s FileType %d %d" % (indent, self.offset, self.length))
        o.append("%s   brand:   %s" % (indent, repr(self.brand)))
        o.append("%s   version: %s" % (indent, self.minver))
        o.append("%s   compatibility: %s " % (indent,
                    ",".join([repr(s) for s in self.cmpl])))
        return "\n".join(o)

#------------------------------------------------------------------------------

class BoxJP2Header(Box): # NOTE: must be only once before codestream
    """ JP2000 Header  box parser """

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, True)
        self.parse(fid)

    def sprint(self, indent=''):
        o = []
        o.append("%s JP2 Header %d %d" % (indent, self.offset, self.length))
        if len(self.subboxes) > 0:
            o.append(self.sprint_sub(indent))
        return "\n".join(o)

#------------------------------------------------------------------------------

class BoxAssociation(Box):
    """ JP2000 association box """

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, True)
        self.parse(fid)

    def sprint(self, indent=''):
        o = []
        o.append("%s AssociationBox %d %d" % (indent, self.offset, self.length))
        if len(self.subboxes) > 0:
            o.append(self.sprint_sub(indent))
        return "\n".join(o)

#------------------------------------------------------------------------------

class BoxImageHeader(Box):
    """ Image Header box parser """
    height = property(lambda s: s.__height)
    width = property(lambda s: s.__width)
    ncomp = property(lambda s: s.__ncomp)
    unkc = property(lambda s: s.__unkc)
    iprbox = property(lambda s: s.__iprbox)
    signed = property(lambda s: s.__signed)
    bpcvar = property(lambda s: s.__bpcvar)
    bitpc = property(lambda s: s.__bitpc)
    compr = property(lambda s: s.__compr)

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, False)

        # check the signature
        if (self.btype != btype) or (length != 14):
            raise JP2000ParsingError("Invalid Image Header!")

        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)

        h, w, nc, bpc, c, unkc, ipr = self.__minvr = \
                            struct.unpack(">LLHBBBB", fid.read(14))

        if unkc not in (0, 1):
            raise JP2000ParsingError("Invalid Image Header! "
                                            "[ColorspaceUnknownn=%d]"%unkc)

        if ipr not in (0, 1):
            raise JP2000ParsingError("Invalid Image Header! [IPR=%d]"%ipr)

        bpcvar = (bpc == 0xFF)
        signed = (not bpcvar) and bool(bpc&0x80)
        bpc = 0 if bpcvar else ((bpc & 0x7F) + 1)

        if bpc > 38:
            raise JP2000ParsingError("Invalid Image Header! [BPC=%d]"%bpc)

        self.__height = h   # image height (number of rows)
        self.__width = w   # image width (numer of columns)
        self.__ncomp = nc  # number of components (bands)
        self.__bitpc = bpc # bist per component (band)
        self.__signed = signed # signed pixel value
        self.__bpcvar = bpcvar # variable bitdepth
        self.__compr = c   # compression type
        self.__unkc = bool(unkc) # colorspace unknown (boolean flag)
        self.__iprbox = bool(ipr)  # IPR box present (boolean flag)


    def sprint(self, indent=''):

        if self.bpcvar:
            tmp = "VARIABLE"
        elif self.signed:
            tmp = "%d (signed int)" % self.bitpc
        else:
            tmp = "%d (unsigned int)" % self.bitpc

        o = []
        o.append("%s ImageHeader %d %d" % (indent, self.offset, self.length))
        o.append("%s   height: %d" % (indent, self.height))
        o.append("%s   width:  %d" % (indent, self.width))
        o.append("%s   ncomp:  %d" % (indent, self.ncomp))
        o.append("%s   bitsPerComp: %s" % (indent, tmp))
        o.append("%s   compression: %d" % (indent, self.compr))
        o.append("%s   unknownColSpace: %s" % (indent, FT[self.unkc]))
        o.append("%s   hasIPRBox:   %s" % (indent, FT[self.iprbox]))

        return "\n".join(o)

#------------------------------------------------------------------------------

CS_METHOD = {1: "Enumerated Colourspace", 2: "Restricted ICC Profile"}
CS_CSENUM = {16: "sRGB", 17: "Grayscale", 18: "sYCC"}

class BoxColorSpec(Box):
    """ Color Specification box """
    method = property(lambda s: s.__meth)
    preced = property(lambda s: s.__prec)
    approx = property(lambda s: s.__appr)
    icc = property(lambda s: s.__icc)
    cspace = property(lambda s: s.__ecsp)

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, False)

        # check the signature
        if self.btype != btype:
            raise JP2000ParsingError("Invalid Colour Specification!")

        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)

        meth, prec, appr = struct.unpack(">BBB", fid.read(3))

        self.__meth = meth # method - enumerated (1) or ICC profile (2)
        self.__prec = prec # precedence (ignored, typicallt 0)
        self.__appr = appr # approximation (ignored, typically 0)
        self.__icc = None # ICC profile
        self.__ecsp = None # enumerated colorspace

        if meth == 1: # enumerated colorspace
            self.__ecsp = struct.unpack(">L", fid.read(4))[0]
        elif meth == 2: # ICC profile
            # load ICC profile and keep it as binary blob
            self.__icc = fid.read(self.length - 3)
        else:
            raise JP2000ParsingError("Invalid Colour Specification! "
                                            "[method=%d]"%meth)

    def sprint(self, indent=''):
        o = []
        o.append("%s ColourSpec %d %d" % (indent, self.offset, self.length))
        o.append("%s   method:    %d [%s]" % (indent, self.method, CS_METHOD[self.method]))
        o.append("%s   preced.:   %d" % (indent, self.preced))
        o.append("%s   approx.:   %d" % (indent, self.approx))
        if self.method == 1:
            tmp = ""
            if self.cspace in CS_CSENUM:
                tmp = "[%s]"%CS_CSENUM[self.cspace]
            o.append("%s   col.space: %d %s" % (indent, self.cspace, tmp))
        return "\n".join(o)

#------------------------------------------------------------------------------

class BoxChannelDef(Box):
    """ Channel Definition box """

    cdef = property(lambda s: s.__cdef)

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, False)

        # check the signature
        if (self.btype != btype) \
          or (self.length < 2):
            raise JP2000ParsingError("Invalid Channel Definition!")

        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)

        count = struct.unpack(">H", fid.read(2))[0]

        if self.length != (count * 6 + 2):
            raise JP2000ParsingError("Invalid Channel Definition!")

        tmp = []
        for _ in xrange(count):
            tmp.append(tuple(struct.unpack(">HHH", fid.read(6))))

        self.__cdef = tmp

    def sprint(self, indent=''):
        o = []
        o.append("%s ChannelDef %d %d" % (indent, self.offset, self.length))
        o.append("%s   count:  %d" % (indent, len(self.cdef)))
        for cdef in self.cdef:
            o.append("%s      %d,%d,%d" % (indent, cdef[0], cdef[1], cdef[2]))
        return "\n".join(o)

#------------------------------------------------------------------------------

class BoxJP2CodeStream(Box): # NOTE: must be only once before codestream
    """ JP2000 Code Stream box parser """

    def __init__(self, fid, btype, offset, length):
        Box.__init__(self, btype, offset, length, True)

        # load payload
        if fid.tell() != offset:
            fid.seek(offset, 0)

        # not implemented 
#------------------------------------------------------------------------------
# box parser

BOX_REG = {
    "jP  ": BoxSignature,
    "ftyp": BoxFileType,
    "jp2h": BoxJP2Header,
    "ihdr": BoxImageHeader,
    "asoc": BoxAssociation,
    "lbl ": BoxAssocLabel,
    "xml ": BoxAssocXML,
    "colr": BoxColorSpec,
    "cdef": BoxChannelDef,
    "uuid": BoxDump,
    "jp2c": BoxJP2CodeStream,
}
    #"jp2c": BoxSuper,

def parse_boxes(fid, offset=0, length=-1):
    # by default parse from the offset to the end of the file
    if length < 0:
        fid.seek(0, 2)
        length = fid.tell() - offset

        if length < 0:
            raise ValueError("Invalid box payload offset!")

    # parse boxes
    box_list = []

    if fid.tell() != offset:
        fid.seek(offset, 0)

    while length > 0:
        box_off = fid.tell() # get box offset (including header)

        # read block length
        box_len = struct.unpack(">L", fid.read(4))[0]
        box_type = fid.read(4)

        # header size in bytes
        hsize = 8

        if box_len == 0: # box size from here to end of the block
            box_len = length
        elif box_len == 1:
            # long box
            box_len = struct.unpack(">Q", fid.read(8))[0]
            hsize = 16

        if box_len < hsize:
            raise ValueError, "Ivalid block length!"

        bclass = BOX_REG.get(box_type, None)

        if bclass:
            box_list.append(bclass(fid, box_type, box_off+hsize, box_len-hsize))
        else:
            # create box
            box_list.append(Box(box_type, box_off+hsize, box_len-hsize))
            fid.seek(box_len - hsize, 1)

        # jump to the next block
        length -= box_len

    return box_list

#==============================================================================



if __name__ == "__main__" : 

    EXENAME = os.path.basename(sys.argv[0])
    try: 
        FNAME = sys.argv[1]  
    except IndexError: 
        print >>sys.stderr, "ERROR: Not enough input arguments!"
        print >>sys.stderr, "USAGE: %s <jp2-file>"%EXENAME
        sys.exit(1) 

    with open( FNAME ) as fid : 
        blist = parse_boxes(fid) 

    # filter out association boxes 
    blist = [b for b in blist if b.btype == 'asoc']

    # print the assoctiatio boxes
    for b in blist : 
        print repr(b), b.btype 
        print b
