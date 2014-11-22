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

import re
import datetime
import etime as et

#------------------------------------------------------------------------------
# regular expression for record parsing

# simple flag
re_flag = r'(?P<flag>[A-Z0-9])'

# string
re_str = r'(?P<string>[^"]*)'

# datetime
re_d_day = r'(?P<day>0[1-9]|[12][0-9]|3[01])'
re_d_mon = r'(?P<month>JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)'
re_d_year = r'(?P<year>[0-9]{4,4})'
re_t_hour = r'(?P<hour>[01][0-9]|2[0-3])'
re_t_min = r'(?P<min>[0-5][0-9])'
re_t_sec = r'(?P<sec>[0-5][0-9]|60)' # be preapred for leap second
re_t_usec = r'(?P<usec>[0-9]{6,6})'

re_time = r'%s:%s:%s.%s'%(re_t_hour, re_t_min, re_t_sec, re_t_usec)
re_date = r'%s-%s-%s'%(re_d_day, re_d_mon, re_d_year)
re_dtime = r'(?P<datetime>%s %s)'%(re_date, re_time)

# numbers
re_n_int = r'(?P<int>[+-][0-9]*)' # integer part
re_n_frac = r'\.(?P<frac>[0-9]+)' # fraction part
re_n_exp = r'E(?P<exp>[+-][0-9]+)' # exponent part
re_n_unit = r'<(?P<unit>.+)>' # unit

re_number = r'(?P<number>%s(?:%s)?(?:%s)?)'%(re_n_int, re_n_frac, re_n_exp)
re_numwu = r'(?P<numwu>%s(?:%s)?)'%(re_number, re_n_unit)


# final regular expression
re_final = r'^(?:%s|%s|"(?:%s|%s)")$'%(re_flag, re_numwu, re_dtime, re_str)

regex_parser = re.compile(re_final)

# parsing of the floating point numbers
re_efloat = r'^%s(?:%s)?(?:%s)?$'%(re_n_int, re_n_frac, re_n_exp)
regex_efloat = re.compile(re_efloat)

re_efloat_simple = r'(?P<mnt>[+-][0-9](?:\.[0-9]+))E(?P<exp>[+-][0-9]+)'
regex_efloat_simple = re.compile(re_efloat_simple)

# removing leading zerro
regex_lzerro = p = re.compile(r"([+-])0\.")


# non-capturing number
re_num_nc = r'(?:[+-][0-9]*)(?:\.(?:[0-9]+))?(?:E(?:[+-][0-9]+))?'

# number array
re_numarr = r'^(?P<numarr>(?:%s){2,})(?:%s)?$'%(re_num_nc, re_n_unit)

regex_number = re.compile("^%s$"%re_number)
regex_numarr = re.compile(re_numarr)
regex_numarr_split = re.compile(re_num_nc)

#------------------------------------------------------------------------------

def parse_header_array(s):
    """
        match the number arrays
    """
    # match the string using the precompiled regular expression parser
    m = regex_numarr.match(s)
    if not m or not m.group('numarr'): # no match
        raise ValueError("The passed value is not a proper header value!"\
                         " VALUE=%s" % repr(s))

    # parse indvidual record
    def _parse(s):
        "parse single value"
        m = regex_number.match(s) # number split to parts
        if m.group('frac') or m.group('exp'): # floating point value
            type_class = Float
        else: # integer
            type_class = Integer
        return type_class(**m.groupdict())

    # create array
    arr = [_parse(s) for s in regex_numarr_split.findall(m.group('numarr'))]

    return NumberArray(array=arr, unit=m.group('unit'))


def parse_header_value(s):
    """
    this is the record value parser returning proper instances of proper
    type classess
    """
    # match the string using the precompiled regular expression parser
    m = regex_parser.match(s)
    if not m: # no match
        # try to match array
        return parse_header_array(s)

    if m.group('flag'): # single character flag
        type_class = Flag

    elif m.group('numwu'): # number with (or without) unit
        if m.group('frac') or m.group('exp'): # floating point value
            type_class = Float

        else: # integer
            type_class = Integer

    elif m.group('datetime'): # day-time string
        type_class = DateTime

    elif m.group('string'): # string
        type_class = String

    else:
        # anything else is invalid
        raise ValueError("The passed value is not a proper header value!"\
                         " VALUE=%s" % repr(s))
    # instantiate type
    return type_class(**m.groupdict())

#------------------------------------------------------------------------------
# header separator

class Spare(object):
    """class holdning the header separator (spare)"""

    def __init__(self, spare):
        self.__s = str(spare)

    def __str__(self):
        return self.__s

    @property
    def length(self):
        return len(self.__s)

#------------------------------------------------------------------------------
# record type classes

class Type(object):
    "abstract base record holding the type base"

    def __str__(self):
        "convert back to string presentation"
        raise NotImplementedError

    def get(self):
        "value getter"
        raise NotImplementedError

    def set(self, v):
        "value setter"
        raise NotImplementedError

    # bind property to setter/getter functions
###    value = property(get, set) ;

    @property
    def length(self):
        "total length of the value string presentation"
        raise NotImplementedError

    @property
    def unit(self):
        return None

#------------------------------------------------------------------------------

class Flag(Type):
    "single alpha-numeric ASCII character flag"

    def __init__(self, flag, **kw):
        self.__v = None
        self.set(flag)

    def __str__(self):
        return self.__v

    def set(self, v):
        self.__v = str(v)[0]

    def get(self):
        return self.__v

    # bind property to setter/getter functions
###    value = property(get, set) ;

    @property
    def length(self):
        return 1

#------------------------------------------------------------------------------

class String(Type):
    "ASCII string"

    def __init__(self, string, **kw):
        self.__v = None
        self.__len = len(string) # length of the stored string
        self.__frm = ""
        self.set(string)

    def __str__(self):
        return "\"%s\""%self.__v

    def set(self, v):
        self.__v = str(v)[:self.__len].ljust(self.__len)

    def get(self):
        return self.__v

    # bind property to setter/getter functions
###    value = property(get, set) ;

    @property
    def length(self):
        return self.__len + 2

#------------------------------------------------------------------------------

class DateTime(Type):
    "date/time type"

    def __init__(self, dtime=None, **kw):

        self.__v = None
        #tzinfo = None

        #try: # by default parse input date
        if True:
            self.set(
                datetime.datetime(
                    year=int(kw['year']),
                    month=et.MON2IDX[kw['month']],
                    day=int(kw['day']),
                    hour=int(kw['hour']),
                    minute=int(kw['min']),
                    second=int(kw['sec']),
                    microsecond=int(kw['usec']),
                    tzinfo=et.UTC,
                )
            )
        #except:
        else:
            self.set(dtime)


    def __str__(self):
        dt = self.__v
        return "\"%2.2d-%3.3s-%4.4d %2.2d:%2.2d:%2.2d.%6.6d\"" % (
            dt.day, et.IDX2MON[dt.month], dt.year, dt.hour, dt.minute,
            dt.second, dt.microsecond)

    def set(self, v):
        """ set value - expecting date time """
        if not isinstance(v, datetime.datetime):
            raise ValueError("Invalid datetime value!")

        if v.tzinfo is None: # naive time -> assumed to be in UTC
            self.__v = v.replace(tzinfo=et.UTC)

        else: # convert to UTC
            self.__v = v.astimezone(et.UTC)

    def get(self):
        return self.__v

    # bind property to setter/getter functions
###    value = property(get, set) ;

    @property
    def length(self):
        return 29

#------------------------------------------------------------------------------

class Number(Type):
    "abstract number base type"

    def __init__(self, unit=None, **kw):
        self.__unit = unit

    def __str__(self):
        return "<%s>"%self.__unit if self.__unit else ""

    @property
    def unit(self):
        return self.__unit

    @property
    def _unit_length(self):
        "total length of the unit"
        return (len(self.__unit)+2) if self.__unit else 0

#------------------------------------------------------------------------------

class NumberArray(Number):

    def __init__(self, array, **kw):
        Number.__init__(self, **kw)

        self.__arr = array

    def __str__(self):

        s = [str(s) for s in self.__arr]
        s.append(Number.__str__(self))

        return "".join(s)

    def get(self):
        return self

    def __len__(self):
        return len(self.__arr)

    def __getitem__(self, idx):
        return self.__arr[idx].get()

    def __setitem__(self, idx, val):
        return self.__arr[idx].set(val)

    @property
    def length(self):
        return self._unit_length+reduce(lambda r, v: r+v.length, self.__arr, 0)

#------------------------------------------------------------------------------

class Integer(Number):

    def __init__(self, number, **kw):
        Number.__init__(self, **kw)

        self.__len = len(number)-1 # number of digits excluding the sign
        self.__frm = "%%+%d.%dd%%s"%(self.__len, self.__len) # format character

        self.__v = int(number)

    def __str__(self):
        return self.__frm % (self.__v, Number.__str__(self))

    def set(self, v):
        self.__v = int(v)
        # validate the format
        if len(str(self)) != self.length:
            raise ValueError("Integer value is too large to fit!")

    def get(self):
        return self.__v

    # bind property to setter/getter functions
###    value = property(get, set) ;

    @property
    def length(self):
        return self._unit_length + self.__len + 1


#------------------------------------------------------------------------------

class Float(Number):

    def __init__(self, number, **kw):
        Number.__init__(self, **kw)
        self.__v = None

        if kw.get('int') and (kw.get('frac') or kw.get('exp')):
            # parts are already parsed
            part = kw

        else:
            # parts need to be parsed
            try:
                part = regex_efloat.match(number).groupdict()
            except:
                raise ValueError("Invalid input!")

            if not (part.get('int')and(part.get('frac') or part.get('exp'))):
                raise ValueError("Invalid input!")

        # store the lengths
        self.__lint = len(part['int']) - 1
        self.__lfrc = len(part['frac']) if part.get('frac') else 0
        self.__lexp = len(part['exp']) - 1 if part.get('exp') else 0

        # prepare format string

        if self.__lexp > 0: # floating point mantisa/exponent notation
            #make sure the integer part has one digit only and a sign
            if 1 != self.__lint:
                raise ValueError("Invalid input!")
            self.__frm0 = "%%+%d.%dE"%(5+self.__lfrc+self.__lexp, self.__lfrc)
            self.__frm1 = "%%+%d.%dd"%(self.__lexp, self.__lexp)
            self.__frm2 = "%sE%s%s"

        else: # fixed point notation
            self.__frm = "%%0+%d.%df%%s"%(2+self.__lint+self.__lfrc, self.__lfrc)

        # check that the integer part of the sci. notation has one digit only
        if part.get('exp') and (2 != len(part['int'])):
            raise ValueError("Invalid input!")

        self.set(number)

    def __str__(self):
        if self.__lexp > 0: # floating point mantisa/exponent notation
            # extract  manitisa and exponent
            tmp = regex_efloat_simple.match(self.__frm0 % self.__v)
            mnt, exp = tmp.group('mnt'), tmp.group('exp')
            # fix padding of the exponent
            exp = self.__frm1 % int(exp)
            # form the final result
            return self.__frm2 % (mnt, exp, Number.__str__(self))

        else: # fixed point notation
            tmp = self.__frm % (self.__v, Number.__str__(self))
            if 0 == self.__lint: # remove the leading zerro
                tmp = regex_lzerro.sub(r"\1.", tmp)
            return tmp

    def set(self, v):
        self.__v = float(v)
        # validate the format
        if len(str(self)) != self.length:
            raise ValueError("Floating point value is too large to fit!")

    def get(self):
        return self.__v

    # bind property to setter/getter functions
###    value = property(get, set) ;

    @property
    def length(self):
        if self.__lexp > 0: # floating point mantisa/exponent notation
            return 5 + self.__lfrc + self.__lexp + self._unit_length
        else: # fixed point notation
            return 2 + self.__lint + self.__lfrc + self._unit_length

#------------------------------------------------------------------------------
