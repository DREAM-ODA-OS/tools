#!/usr/bin/env python 
#------------------------------------------------------------------------------
# 
#   rasterize geometry
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

import sys 
import os.path 
import img_block as ib 
import img_geom as ig 
import numpy as np 
#import math as m 
from osgeo import ogr ; ogr.UseExceptions() 
from osgeo import osr ; ogr.UseExceptions() 
from osgeo import gdal ; gdal.UseExceptions() 

#------------------------------------------------------------------------------

if __name__ == "__main__" : 

    # TODO: to improve CLI 

    EXENAME = os.path.basename( sys.argv[0] ) 

    DEBUG=False 

    try: 

        INPUT = sys.argv[1]
        OUTPUT = sys.argv[2]
        VALUE = tuple(map(float,sys.argv[3].split(",")))
        NP = 3 
        if len(sys.argv) > NP : 
            for arg in sys.argv[NP:] : 
                if ( arg == "DEBUG" ) : DEBUG = True # dump debuging output

    except IndexError : 
        
        sys.stderr.write("ERROR: Not enough input arguments!\n") 
        sys.stderr.write("\nRasterize gemetry to an existing image.\n\n") 
        sys.stderr.write("USAGE: %s <geometry> <image> <pixel-value> [DEBUG]\n"%EXENAME) 
        sys.exit(1) 

    #--------------------------------------------------------------------------
    # import geometry 

    # open input geometry file 
    fin = sys.stdin if INPUT == "-" else open(INPUT) 

    # read the data 
    try: 
        geom = ig.parseGeom( fin.read() , DEBUG ) 
    except Exception as e : 
        if DEBUG : traceback.print_exc( file=sys.stderr ) 
        print >>sys.stderr, "ERROR: %s: %s"%(EXENAME,e)
        sys.exit(1)

    #--------------------------------------------------------------------------

    # open input image 
    imo = ib.ImgFileOut( OUTPUT ) 

    # convert the pixel value to a proper data type 
    VALUE = tuple( map( np.dtype(imo.dtype).type, VALUE ) )

    # check number of pixel values 
    if len(VALUE) != imo.sz :
        print >>sys.stderr, "ERROR: %s: The number of pixel values does not" \
                            " match the actual nuber of bands!"%(EXENAME)

    #get the raster spatial reference 
    if imo.ds.GetProjection() : 
        sr = osr.SpatialReference( imo.ds.GetProjection() ) 
    else : 
        sr = None 

    # check the spatial refereces 
    if ( sr is None ) != ( geom.GetSpatialReference() is None ) : 
        print >>sys.stderr, "ERROR: %s: Missing spatial reference!"%(EXENAME)
        sys.exit(1) 

    if ( sr is not None ) and ( geom.GetSpatialReference() is not None ) : 
        if not sr.IsSame( geom.GetSpatialReference() ) : 
            print >>sys.stderr, "ERROR: %s: Mixed non-equal spatial references!"%(EXENAME)
            sys.exit(1) 

    #--------------------------------------------------------------------------
    # rasterization 

    # crete in-memory layer 
    # create virtual in-memory OGR datasource 
    vds = ogr.GetDriverByName('Memory').CreateDataSource('out')

    # create layer 
    ly = vds.CreateLayer('geom',sr,geom.GetGeometryType())

    # feature 
    ft = ogr.Feature(ly.GetLayerDefn())
    ft.SetGeometry(geom)
    ly.CreateFeature(ft)
    ft.Destroy()

    bands = tuple( i for i in xrange(1,1+imo.sz) ) 

    gdal.RasterizeLayer( imo.ds, bands, ly, burn_values=VALUE )  
