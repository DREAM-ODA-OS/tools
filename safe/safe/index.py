#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Index file output
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

from sys import stdout

def write_metadata(fields, schema, fout=stdout):
    """ Write meta-data as one index file line. """
    # pylint: disable=redefined-outer-name
    delimiter = schema.get('index', {}).get('delimiter', '\t')
    line_end = schema.get('index', {}).get('eol', '\n')
    fout.write(delimiter.join(
        fields.get(field) or '' for field in (
            field_def['name'] for field_def in schema['fields']
        )
    ))
    fout.write(line_end)


def write_header(schema, fout=stdout):
    """ Write an index file header. """
    # pylint: disable=redefined-outer-name
    delimiter = schema.get('index', {}).get('delimiter', '\t')
    line_end = schema.get('index', {}).get('eol', '\n')
    fout.write(delimiter.join(
        field_def['name'] for field_def in schema['fields']
    ))
    fout.write(line_end)
