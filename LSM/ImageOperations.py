# -*- coding: iso-8859-1 -*-

"""
 Unit: ImageOperations
 Project: Selli 2
 Created: 10.02.2005
 Creator: KP
 Description:

 This is a module with functions for various kind of image operations, for example
 conversion from VTK image data to wxPython bitmap
 
 Modified: 10.02.2005 KP - Created the class

 Selli 2 includes the following persons:
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2005 Selli 2 Project.
"""

__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import wx
import struct

def getAsParameterList(iTF):
    lst=[]
    lst.append(iTF.GetBrightness())
    lst.append(iTF.GetContrast())
    lst.append(iTF.GetGamma())
    lst.append(iTF.GetMinimumThreshold())
    lst.append(iTF.GetMinimumValue())
    lst.append(iTF.GetMaximumThreshold())
    lst.append(iTF.GetMaximumValue())
    lst.append(iTF.GetProcessingThreshold())
    return lst
    
def setFromParameterList(iTF,list):
    iTF.SetContrast(float(cr))
    iTF.SetGamma(float(g))
    iTF.SetMinimumThreshold(int(mt))
    iTF.SetMinimumValue(int(mv))
    iTF.SetMaximumThreshold(int(mat))
    iTF.SetMaximumValue(int(mav))
    iTF.SetProcessingThreshold(int(mpt))
    
    iTF.SetBrightness(int(br))

def vtkImageDataToBitmap(imageData,slice,color,width=0,height=0):
    extract=vtk.vtkExtractVOI()
    extract.SetInput(imageData)
    x,y,z=imageData.GetDimensions()
    z=slice
    
    ctf=vtk.vtkColorTransferFunction()
    ctf.AddRGBPoint(0.0,0,0,0)
    r,g,b=color
    r/=255
    g/=255
    b/=255
    ctf.AddRGBPoint(255.0,r,g,b)
    
    extract.SetVOI(0,x,0,y,z,z)
    maptocolor=vtk.vtkImageMapToColors()
    maptocolor.SetInput(extract.GetOutput())
    maptocolor.SetLookupTable(ctf)
    maptocolor.SetOutputFormatToRGB()
    maptocolor.Update()
    exporter=vtk.vtkImageExport()
    exporter.SetInput(maptocolor.GetOutput())
    siz=exporter.GetDataMemorySize()
    fs="%ds"%siz
    ss=struct.pack(fs,"")
    exporter.SetExportVoidPointer(ss)
    exporter.Export()

    print "Original image size=(%d,%d)"%(x,y)
    image=wx.EmptyImage(x,y)
    image.SetData(ss)
    if not width and height:
        aspect=float(x)/y
        width=aspect*height
    if not height and width:
        aspect=float(y)/x
        height=aspect*width
    if not width and not height:
        width=height=64
    print "Scaling to %d,%d"%(width,height)
    image.Rescale(width,height)
    bitmap=image.ConvertToBitmap()
    return bitmap
