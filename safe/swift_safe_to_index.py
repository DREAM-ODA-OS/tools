#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Safe file metadata extraction from SWIFT object
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
from contextlib import closing
import requests
from swiftclient.client import Connection
from swiftclient.exceptions import ClientException
from util.swift_chunk_reader import SWIFTChunkReader
from safe import extract_metadata
from safe.index import write_metadata
from util.cli import error

# Disables SSL warnings
requests.packages.urllib3.disable_warnings()

def usage():
    """ Print short command usage. """
    exename = basename(sys.argv[0])
    print >>stderr, (
        "USAGE: %s <md-schema> <auth-conf> <auth-url> <container> <object>"
        "" % exename
    )
    print >>stderr, ""
    print >>stderr, (
        "This command reads a SAFE file from the SWIFT object storage, "
        "extracts the metadata defined by the schema and "
        "writes them to the standard output as one index file line.\n"
    )


if __name__ == "__main__":
    # pylint: disable=invalid-name
    try:
        schema = sys.argv[1]
        auth_conf = sys.argv[2]
        auth_url = sys.argv[3]
        container = sys.argv[4]
        object_name = sys.argv[5]
    except IndexError:
        error("Not enough input arguments.")
        usage()
        sys.exit(1)

    # load JSON schema
    with open(schema) as fobj:
        schema = json.load(fobj)

    # load authorisation configuration
    with open(auth_conf) as fobj:
        auth_conf = json.load(fobj)

    # open SWIFT connection
    with closing(Connection(**auth_conf[auth_url])) as conn:
        # check the object
        try:
            fobj = SWIFTChunkReader(conn, container, object_name, 256*1024)
        except ClientException as exc:
            if exc.http_status == 404:
                error("Object not found! %r", object_name)
            else:
                error("%s", exc)
            sys.exit(1)

        # make sure that the object has the required attributes
        if fobj.headers["content-type"] != "application/zip":
            error("Unexpected content type! %r", fobj.headers["content-type"])

        # extract and print meta-data
        write_metadata(extract_metadata(fobj, schema), schema)
