#-------------------------------------------------------------------------------
#
# File based chunk reader
#  - it's purpose is to test the base ChunkReader class.
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

from .chunk_reader import ChunkReader

class FileChunkReader(ChunkReader):
    """ Test file-based chunk-reader object. """

    def __init__(self, path, chunk_size=None):
        self.fobj = open(path, "rb")
        self.fobj.seek(0, 2)
        size = self.fobj.tell()
        super(ChunkReaderFile, self).__init__(size, chunk_size)

    def get_chunk(self, offset, size):
        """ Get chunk. """
        self.fobj.seek(offset)
        return self.fobj.read(size)

    def close(self):
        """ close file reader """
        super(ChunkReaderFile, self).close()
        self.fobj.close()

