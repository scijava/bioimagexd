# -*- coding: iso-8859-1 -*-

"""
 Unit: ImageOperations
 Project: BioImageXD
 Created: 10.02.2005
 Creator: KP
 Description:

 This is a module with functions for various kind of image operations, for example
 conversion from VTK image data to wxPython bitmap
 
 Modified: 10.02.2005 KP - Created the class

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project
"""

__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import wx
import struct

def gcd2(a, b):
    """Greatest common divisor using Euclid's algorithm."""
    while a:
        a, b = b%a, a
    return b
    
def lcm2(a,b):
    return float(a*b)/gcd2(a,b)
    
def gcd(numbers):
    return reduce(gcd2,numbers)
    
def lcm(numbers):
    return reduce(lcm2,numbers)  


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

def vtkImageDataToWxImage(data,slice=-1,startpos=None,endpos=None):
    if slice>=0:
        data=getSlice(data,slice,startpos,endpos)
    exporter=vtk.vtkImageExport()
    exporter.SetInput(data)

    siz=exporter.GetDataMemorySize()
    fs="%ds"%siz
    ss=struct.pack(fs,"")
    exporter.SetExportVoidPointer(ss)
    exporter.Export()

    x,y,z=data.GetDimensions()
    #print "Original image size=(%d,%d)"%(x,y)
    image=wx.EmptyImage(x,y)
    #image.SetData(exporter.GetPointerToData())
    image.SetData(ss)
    return image

    
def vtkImageDataToPreviewBitmap(imageData,color,width=0,height=0):
    x,y,z=imageData.GetDimensions()
    
    ctf=vtk.vtkColorTransferFunction()
    ctf.AddRGBPoint(0.0,0,0,0)
    r,g,b=color
    r/=255
    g/=255
    b/=255
    ctf.AddRGBPoint(255.0,r,g,b)
    
    # We do a simple mip that sets each pixel (x,y) of the image to have the
    # value of the brightest voxel (x,y,0) - (x,y,z)
    mip=vtk.vtkImageSimpleMIP()
    mip.SetInput(imageData)
#    mip.Update()
#    output=mip.GetOutput()
    maptocolor=vtk.vtkImageMapToColors()
    maptocolor.SetInput(mip.GetOutput())
    maptocolor.SetLookupTable(ctf)
    maptocolor.SetOutputFormatToRGB()
    maptocolor.Update()

    image = vtkImageDataToWxImage(maptocolor.GetOutput())

    if not width and height:
        aspect=float(x)/y
        width=aspect*height
    if not height and width:
        aspect=float(y)/x
        height=aspect*width
    if not width and not height:
        width=height=64
    #print "Scaling to %d,%d"%(width,height)
    image.Rescale(width,height)
    bitmap=image.ConvertToBitmap()
    return bitmap

def scatterPlot(imagedata1,imagedata2,z):
    scatter=vtk.vtkImageScatterPlot()
    scatter.SetZSlice(z)
    scatter.AddInput(imagedata1)
    scatter.AddInput(imagedata2)
    scatter.Update()
    image=vtkImageDataToWxImage(scatter.GetOutput())
    return image
    
def getZoomFactor(x1,y1,x2,y2):
    xf=float(x2)/x1
    yf=float(y2)/y1
    return min(xf,yf)
    
def vtkZoomImage(image,f):
    f=1.0/f
    reslice=vtk.vtkImageReslice()
    reslice.SetInput(image)
    
    spacing=image.GetSpacing()
    extent=image.GetExtent()
    origin=image.GetOrigin()
    extent=(extent[0],extent[1]/f,extent[2],extent[3]/f,extent[4],extent[5])
    
    spacing=(spacing[0]*f,spacing[1]*f,spacing[2])
    reslice.SetOutputSpacing(spacing)
    reslice.SetOutputExtent(extent)
    reslice.SetOutputOrigin(origin)

    # These interpolation settings were found to have the
    # best effect:
    # If we zoom out, no interpolation
    if f>1:
        reslice.InterpolateOff()
    else:
    # If we zoom in, use cubic interpolation
        reslice.SetInterpolationModeToCubic()
        reslice.InterpolateOn()
    reslice.Update()
    return reslice.GetOutput()
    
def zoomImageToSize(image,x,y):
    return image.Scale(x,y)
    
def zoomImageByFactor(image,f):
    x,y=image.GetWidth(),image.GetHeight()
    x,y=int(f*x),int(f*y)
    return zoomImageToSize(image,x,y)

def getSlice(volume,zslice,startpos=None,endpos=None):
    voi=vtk.vtkExtractVOI()
    voi.SetInput(volume)
    x,y,z=volume.GetDimensions()
    x0,y0=0,0
    if startpos:
        x0,y0=startpos
        x,y=endpos
    voi.SetVOI(x0,x-1,y0,y-1,zslice,zslice)
    voi.Update()
    return voi.GetOutput()
    
def saveImageAs(imagedata,zslice,filename):
    ext=filename.split(".")[-1]        
    extMap={"tiff":"TIFF","tif":"TIFF","jpg":"JPEG","jpeg":"JPEG","png":"PNG"}
    if not extMap.has_key(ext):
        Dialogs.showerror(None,"Extension not recognized: %s"%ext,"Extension not recognized")
        return
    vtkclass="vtk.vtk%sWriter()"%extMap[ext]
    writer=eval(vtkclass)
    img=getSlice(imagedata,zslice)
    writer.SetInput(img)
    writer.SetFileName(filename)
    writer.Write()
    
def getColorTransferFunction(fg):
    ct=vtk.vtkColorTransferFunction()

    ct.AddRGBPoint(0,0,0,0)
    r,g,b=fg
    r/=255.0
    g/=255.0
    b/=255.0
    ct.AddRGBPoint(255,r,g,b)
    return ct    

