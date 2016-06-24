#-------------------------------------------------------------------------------
#
#  Simple file-like reader interface wrapping arbitrary range reading protocol
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

class ChunkReader(object):
    """ Base chunk reader class. """
    DEFAULT_CHUNK_SIZE = 1048576 # 1MB default chunk size

    def __init__(self, size, chunk_size=None):
        self.closed = False
        self._position = 0
        self._size = size
        self._chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self._chunks = {}

    def get_chunk(self, offset, size):
        """ Get chunk. """
        raise NotImplementedError

    def load_chunks(self, chunk_list):
        """ Multi-chunk loader. """
        #print "load_chunks(%s)" % (chunk_list)

        def _group_to_ranges_(chunk_list):
            """ Group sorted list of chunks to ranges. """
            it_chunk_list = iter(chunk_list)
            last = it_chunk_list.next()
            group = [last]
            for chunk_id in it_chunk_list:
                if last + 1 == chunk_id:
                    group.append(chunk_id)
                else:
                    yield (group[0], 1 + group[-1] - group[0])
                    group = [chunk_id]
                last = chunk_id
            yield (group[0], 1 + group[-1] - group[0])

        for start, count in _group_to_ranges_(chunk_list):
            byte_offset = start * self._chunk_size
            byte_size = max(0, min(
                self._size, (start + count) * self._chunk_size
            ) - byte_offset)
            print "get_chunk(%s, %s)" % (byte_offset, byte_size)
            if byte_size > 0:
                data = self.get_chunk(byte_offset, byte_size)
            else:
                data = ""
            for idx, chunk_id in enumerate(xrange(start, start + count)):
                offset = idx * self._chunk_size
                self._chunks[chunk_id] = data[offset:offset+self._chunk_size]

    def merge_chunks(self, start, stop):
        """ Merge range of chunks to a single block. """
        #print "merge_chunks(%s, %s)" % (start, stop)
        chunk_range = range(start, stop)
        missing_chunks = set(chunk_range) - set(self._chunks)
        if missing_chunks:
            self.load_chunks(missing_chunks)
        return "".join(self._chunks[id_] for id_ in chunk_range)

    def read(self, size=None):
        """ Read at most size bytes. """
        #print "read(%s)" % size
        #print "start position: %s" % self._position
        #print "file size:      %s" % self._size
        start = max(0, self._position)
        stop = self._size if size is None else min(self._size, start + size)
        size = stop - start
        #print "_read(%s, %s)" % (start, size)
        if size > 0:
            offset = start % self._chunk_size
            #print "chunk local offset:", offset
            data = self.merge_chunks(
                start // self._chunk_size, 1 + (stop - 1) // self._chunk_size
            )
            #print "chunk aligned data size", len(data)
            data = data[offset:offset+size]
        else:
            data = ""
        self._position += len(data)
        #print "end position: %s (%+d)" % (self._position, len(data))
        return data

    def seek(self, offset, whence=None):
        """ Seek the file position. """
        #print "seek(%s, %s)" % (offset, whence)
        if whence is None or whence == 0:
            self._position = offset
        elif whence == 1:
            self._position += offset
        elif whence == 2:
            self._position = offset + self._size
        else:
            raise ValueError("Invalid whence value! whence=%r" % whence)

    def tell(self):
        """ Tell the current file position. """
        return self._position

    def close(self):
        """ Close the file. """
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
