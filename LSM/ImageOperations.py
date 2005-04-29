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

 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

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
    
    
def paintCTFValues(ctf,height=32):
    """
    Method: paintCTFValues(ctf)
    Created: 18.04.2005, KP
    Description: Paint a bar representing a ctf
    """    
    bmp = wx.EmptyBitmap(256,height,-1)
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    dc.BeginDrawing()
        
    for x1 in range(0,256):
        r,g,b = ctf.GetColor(x1)      
        r*=255
        g*=255
        b*=255
        r=int(r)
        g=int(g)
        b=int(b)
        #print x1,"=",(r,g,b)
        dc.SetPen(wx.Pen((r,g,b)))
        dc.DrawLine(x1,0,x1,height)
                    
    dc.EndDrawing()
    dc.SelectObject(wx.NullBitmap)
    dc = None    
    return bmp
    
    
def loadNIHLut(data):
    """
    Method: loadNIHLut(data)
    Created: 17.04.2005, KP
    Description: Load an NIH Image LUT and return it as CTF
    """    
    n=256
    d=len(data)-32
    header,version,ncolors,start,end,fill1,fill2,filler,lut = struct.unpack("4s2s2s2s2s8s8si%ds"%d,data)
    if header!="ICOL":
        raise "Did not get NIH header!"
    ncolors=ord(ncolors[0])*(2**8)+ord(ncolors[1])
    start=ord(start[0])*(2**8)+ord(start[1])
    end=ord(end[0])*(2**8)+ord(end[1])
    #print "start=",start,"end=",end,"ncolors=",ncolors
    #print "ranges=[",0,":",ncolors,"],[",ncolors,":",(2*ncolors),"],[",(2*ncolors),":",(3*ncolors),"]"
    
    reds=lut[:ncolors]
    greens=lut[ncolors:(2*ncolors)]
    blues=lut[(2*ncolors):(3*ncolors)]
    return reds,greens,blues

    
def loadLUT(filename,ctf=None):
    """
    Method: loadLUT(filename)
    Created: 17.04.2005, KP
    Description: Load an ImageJ binary LUT and return it as CTF. If a ctf
                 is passed as parameter, it is modified in place
    """    
    if ctf:
        ctf.RemoveAllPoints()
    else:
        ctf=vtk.vtkColorTransferFunction()    
    f=open(filename)
    lut=f.read()
    f.close()
    loadLUTFromString(lut,ctf)
    return ctf
    
def loadLUTFromString(lut,ctf):
    """
    Method: loadLUTFromString(string)
    Created: 18.04.2005, KP
    Description: Load an ImageJ binary LUT from string
    """        
    if len(lut)!=768:
        reds,greens,blues=loadNIHLut(lut)
    else:
        reds=lut[0:256]
        greens=lut[256:512]
        blues=lut[512:768]
    n=len(reds)
    #print "n=",n
    for i in range(0,n):
        r=ord(reds[i])
        g=ord(greens[i])
        b=ord(blues[i])
        r/=255.0
        g/=255.0
        b/=255.0
        ctf.AddRGBPoint(i,r,g,b)
    
    
def saveLUT(ctf,filename):
    """
    Method: saveLUT(ctf,filename)
    Created: 17.04.2005, KP
    Description: Save a CTF as ImageJ binary LUT
    """    
    f=open(filename,"wb")
    f.write(lutToString(ctf))
    f.close()
    
def lutToString(ctf):
    """
    Method: lutToString()
    Created: 18.04.2005, KP
    Description: Write a lut to a string
    """    
    s=""
    for col in range(0,3):
        for i in range(0,256):
            r,g,b = ctf.GetColor(i)      
            r*=255
            g*=255
            b*=255
            r=int(r)
            g=int(g)
            b=int(b)
            color=[r,g,b]
            s+=chr(color[col])
    return s
        
                    
    
    

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
        #print "Getting slice=",slice
        data=getSlice(data,slice,startpos,endpos)
    exporter=vtk.vtkImageExport()
    data.SetUpdateExtent(data.GetWholeExtent())
    data.Update()
    
    exporter.SetInput(data)

    siz=exporter.GetDataMemorySize()
    #print "siz=",siz
    fs="%ds"%siz
    #print "size=",siz
    ss=struct.pack(fs,"")
    #print "len(ss)=",len(ss)
    exporter.SetExportVoidPointer(ss)
    #print "Exporting..."
    exporter.Export()
    

    x,y,z=data.GetDimensions()
    #print "Dimensions=",x,y,z
    #print "Original image size=(%d,%d)"%(x,y)
    image=wx.EmptyImage(x,y)
    #image.SetData(exporter.GetPointerToData())
    image.SetData(ss)
    return image

    
def vtkImageDataToPreviewBitmap(imageData,color,width=0,height=0,bgcolor=(0,0,0)):
    mip=vtk.vtkImageSimpleMIP()
    mip.SetInput(imageData)
    x,y,z=imageData.GetDimensions()
    
    if type(color)==type( (0,0,0)) :
        ctf=vtk.vtkColorTransferFunction()
        r,g,b=(0,0,0)
        ctf.AddRGBPoint(0.0,r,g,b)
        
        r,g,b=color
        r/=255
        g/=255
        b/=255
        ctf.AddRGBPoint(255.0,r,g,b)
    else:
        ctf=color
    
    # We do a simple mip that sets each pixel (x,y) of the image to have the
    # value of the brightest voxel (x,y,0) - (x,y,z)
    #imageData.SetUpdateExtent(imageData.GetWholeExtent())
    #print "doing mip of ",imageData
    #mip.Update()
#    output=mip.GetOutput()
    maptocolor=vtk.vtkImageMapToColors()
    maptocolor.SetInput(mip.GetOutput())
    maptocolor.SetLookupTable(ctf)
    maptocolor.SetOutputFormatToRGB()
    maptocolor.Update()

    imagedata=maptocolor.GetOutput()
    image = vtkImageDataToWxImage(imagedata)

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

def scatterPlot(imagedata1,imagedata2,z,countVoxels, wholeVolume):
    """
    Method: scatterPlot(imageData,imageData2,z,countVoxels,wholeVolume)
    Created: 25.03.2005, KP
    Description: Create scatterplot
    """       
    scatter=vtk.vtkImageScatterPlot()
    if not wholeVolume:
        scatter.SetZSlice(z)
    if countVoxels:
        scatter.CountVoxelsOn()
    scatter.AddInput(imagedata1)
    scatter.AddInput(imagedata2)
    scatter.Update()
    data=scatter.GetOutput()
    if countVoxels:
        #print "Got data=",data
        ctf=vtk.vtkColorTransferFunction()
        n = scatter.GetNumberOfPairs()
        print "Number of pairs=",n
        p=0.75/n
        ctf.AddHSVPoint(0,0,0.0,0.0)
        for i in xrange(1,n,255):
            #print "AddHSVPoint(%d,%f,%f,%f)"%(i,i*p,1.0,1.0)
            ctf.AddHSVPoint(i, 0.75*(i/float(p)), 1.0, 1.0)

        ctf.SetColorSpaceToHSV()
        print "Using ctf=",ctf
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(data)
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        data=maptocolor.GetOutput()
        #print "data=",data
        
    image=vtkImageDataToWxImage(data)
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

