#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Safe file metadata extraction
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

import re
from functools import wraps
from util.zipfile import ZipFile
from .exceptions import FileNotFound
from .xpath import extract_xpath

# register of the extractors
EXTRACTORS = {
    "XPATH": extract_xpath,
}


def zip_file(func):
    """ Decorator turning the first argument into a ZipFile. """
    @wraps(func)
    def __wrapper__(fobj, *args, **kwargs):
        with ZipFile(fobj, "r") as fzip:
            return func(fzip, *args, **kwargs)
    return __wrapper__


@zip_file
def extract_metadata(fobj, schema, name=None, size=None):
    """ Extract metadata from safe object. """
    # group the fields by file the regular expressions
    files = {}
    for field_def in schema['fields']:
        re_file = field_def.get('file', None) or None
        file_fields = files.get(re_file, None)
        if file_fields is None:
            files[re_file] = file_fields = []
        file_fields.append(field_def)

    # locate the files
    for re_file, fields in files.items():
        if re_file:
            regex = re.compile(re_file)
            for name in fobj.namelist():
                if regex.match(name):
                    break
            else:
                raise FileNotFound(re_file)
        else:
            name = None
        files[re_file] = (name, fields)

    # group the fields by the file extractors
    extractors = {}
    for file_name, fields in files.values():
        for field_def in fields:
            item = extractors.get((file_name, field_def['extractor']), None)
            if item is None:
                extractors[(file_name, field_def['extractor'])] = item = []
            item.append(field_def)

    # extract the actual metadata
    results = {}
    for (file_name, extractor), fields in extractors.items():
        if extractor == 'NONE': # no-op place holder
            continue
        if extractor == 'SAFE_NAME': # the actual SAFE file-name
            results[field_def['name']] = field_def.get('format', "%s") % name
        if extractor == 'SAFE_SIZE': # the actual SAFE file-size
            results[field_def['name']] = field_def.get('format', "%s") % size
        if extractor == 'FILENAME': # fill fields from filenames
            for field_def in fields:
                match = re.match(field_def['file'], file_name)
                tmp = match.groups()[0] if match.groups() else file_name
                results[field_def['name']] = field_def.get('format', "%s") % tmp
        elif file_name is None and extractor == 'CONSTANT':
            for field_def in fields:
                results[field_def['name']] = field_def['value']
        else:
            with fobj.open(file_name) as ftmp:
                results.update(EXTRACTORS[extractor](ftmp, file_name, fields))


    return results

