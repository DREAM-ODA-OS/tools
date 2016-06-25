#-------------------------------------------------------------------------------
#
#  SWIFT object file-like interface.
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

from sys import stderr
import re
from swiftclient.exceptions import ClientException
from .chunk_reader import ChunkReader

class SWIFTChunkReader(ChunkReader):
    """ Test file-based chunk-reader object. """
    RE_CONTENT_RANGE = re.compile(r"^bytes ([0-9]+)-([0-9]+)/([0-9]+)$")

    def __init__(self, swift_conn, container_name, object_name, chunk_size=None):
        self._conn = swift_conn
        self._container_name = container_name
        self._object_name = object_name
        resp_headers = self._conn.head_object(
            self._container_name, self._object_name
        )
        size = int(resp_headers['content-length'])
        if resp_headers['accept-ranges'] != "bytes":
            raise ClientException("Server does not accept byte ranges!")
        super(SWIFTChunkReader, self).__init__(size, chunk_size)
        self.headers = resp_headers

    def refresh(self):
        """ Refresh the object size. """
        resp_headers = self._conn.head_object(
            self._container_name, self._object_name
        )
        self._size = int(resp_headers['content-length'])

    def get_chunk(self, offset, size):
        """ Get chunk. """
        resp_headers, data = self._conn.get_object(
            self._container_name,
            self._object_name,
            headers={'range': 'bytes=%d-%d' % (offset, offset + size -1)}
        )
        #print >>stderr, 'content-length: ', resp_headers['content-length']
        #print >>stderr, 'content-range: ', resp_headers['content-range']

        # check the response
        size_mismatch = (
            size != len(data) or
            size != int(resp_headers['content-length'])
        )
        match = self.RE_CONTENT_RANGE.match(resp_headers['content-range'])
        if match and not size_mismatch:
            start, stop, size = (int(v) for v in match.groups())
            size_mismatch = size_mismatch or (
                start != offset or stop != (offset + size -1)
            )
            self._size = size
        else:
            size_mismatch = True

        return data

    def close(self):
        """ close file reader """
        super(SWIFTChunkReader, self).close()
