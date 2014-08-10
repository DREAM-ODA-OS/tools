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
#==============================================================================

import datetime

# mapping between month names and month number
IDX2MON = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN",
           7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC"}

MON2IDX = dict([(j, i) for i, j in IDX2MON.items()])

#-------------------------------------------------------------------------------
# UTC timezone

try:
    from pytz import UTC

except ImportError:
    # UTC time-zone info class
    class ClassUTC(datetime.tzinfo):
        def utcoffset(self, dt):
            return ClassUTC._timedelta_zerro_

        def dst(self, dt):
            return ClassUTC._timedelta_zerro_

        def tzname(self, dt):
            return 'UTC'

    # zerro timedelta
    ClassUTC._timedelta_zerro_ = datetime.timedelta()

    # making the tzinfo instance
    UTC = ClassUTC()

#-------------------------------------------------------------------------------
# MJD 2000 - Modified Julian Date

DT_REF = datetime.datetime(2000, 1, 1, tzinfo=UTC)

def mjd2dt(mjd):
    """ convert MJD2000 to Python UTC datetime """
    delta = datetime.timedelta(days=mjd[0], seconds=mjd[1], microseconds=mjd[2])
    return DT_REF + delta


def dt2mjd(dt):
    """ convert Python datetime to MJD2000 (assumed UTC for naive DT)"""
    if not isinstance(dt, datetime.datetime):
        raise ValueError("Invalid datetime value!")
    if dt.tzinfo is None: # naive time -> assumed to be in UTC
        dt = dt.replace(tzinfo=UTC)
    else: # convert to UTC
        dt = dt.astimezone(UTC)
    delta = dt - DT_REF
    return (delta.days, delta.seconds, delta.microseconds)
