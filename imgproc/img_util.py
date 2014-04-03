#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
#  Common utilities.
#
# Project: Image Processing Tools
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
import math as m 

#-------------------------------------------------------------------------------


PROGRES2STR = [ '0','.','.','.','10','.','.','.','20',
    '.','.','.','30','.','.','.','40','.','.','.','50','.','.','.','60',
    '.','.','.','70','.','.','.','80','.','.','.','90','.','.','.','100' ] 

class Progress:
    """ simple progress printer """

    def __init__( self, final = 100 ) :
        """ initialize progres printer """

        self.__pos     =  0 
        self.__current =  0.0
        self.__final   =  float( final ) 

    def __iadd__( self , increment ) : 
        """ initialize progres printer """

        self.__current += float(increment)

        if self.__current > self.__final : 
            self.__current = self.__final

        return self 

    def __str__( self ) : 

        l = [] 
        while self.__pos <= int(40.0*self.__current/self.__final) : 
            l.append( PROGRES2STR[ self.__pos ] ) 
            self.__pos += 1 

        return "".join(l) 

    def istr( self , inc ):
        self += inc 
        return str( self ) 


