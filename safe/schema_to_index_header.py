#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Extract index file header from the SAFE header.
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

import sys
from sys import stderr, stdout
import json
from os.path import basename

def error(message, *arg):
    """ Print error message. """
    print >>stderr, "ERROR: %s" % (message % arg)

def usage():
    """ Print short command usage. """
    exename = basename(sys.argv[0])
    print >>stderr, "USAGE: %s <md-schema>" % exename
    print >>stderr, ""
    print >>stderr, "Dump the index file header from the meta-data schema."


def print_header(schema):
    """ Metadata output. """
    # pylint: disable=redefined-outer-name
    delimiter = schema.get('index', {}).get('delimiter', '\t')
    line_end = schema.get('index', {}).get('eol', '\n')
    stdout.write(delimiter.join(
        field_def['name'] for field_def in schema['fields']
    ))
    stdout.write(line_end)


if __name__ == "__main__":
    # pylint: disable=invalid-name
    try:
        schema = sys.argv[1]
    except IndexError:
        error("Not enough input arguments.")
        usage()
        sys.exit(1)

    # load JSON schema
    with open(schema) as fobj:
        print_header(json.load(fobj))

