# -*- coding: iso-8859-1 -*-

"""
 Unit: ImageOperations
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 This is a module with functions for various kind of image operations, for example
 conversion from VTK image data to wxPython bitmap

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

__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import wx
import struct
import Logging

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
        val=[0,0,0]
        ctf.GetColor(x1,val)
        r,g,b = val
        r*=255
        g*=255
        b*=255
        r=int(r)
        g=int(g)
        b=int(b)
        
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
            val=[0,0,0]
            ctf.GetColor(i,val)
            r,g,b = val
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
    br,cr,g,mt,mv,mat,mav,mpt=list
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
        Logging.info("Getting slice %d"%slice,kw="imageop")
        data=getSlice(data,slice,startpos,endpos)
        
    exporter=vtk.vtkImageExport()
    data.SetUpdateExtent(data.GetWholeExtent())
    data.Update()
    
    exporter.SetInput(data)

    siz=exporter.GetDataMemorySize()
    
    fs="%ds"%siz
    
    ss=struct.pack(fs,"")
    
    exporter.SetExportVoidPointer(ss)
    
    exporter.Export()
    

    x,y,z=data.GetDimensions()
    image=wx.EmptyImage(x,y)
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
    output=mip.GetOutput()
    mip.Update()
    if output.GetNumberOfScalarComponents()==1: 
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(mip.GetOutput())
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()

        imagedata=maptocolor.GetOutput()
    else:
        imagedata=mip.GetOutput()
    image = vtkImageDataToWxImage(imagedata)

    if not width and height:
        aspect=float(x)/y
        width=aspect*height
    if not height and width:
        aspect=float(y)/x
        height=aspect*width
    if not width and not height:
        width=height=64
    
    image.Rescale(width,height)
    bitmap=image.ConvertToBitmap()
    return bitmap

def getPlane(data,plane,x,y,z):
    """
    Method: getPlane(data,plane,coord)
    Created: 06.06.2005, KP
    Description: Get a plane from given the volume
    """   
    permute=vtk.vtkImagePermute()
    dx,dy,dz=data.GetDimensions()
    voi=vtk.vtkExtractVOI()
    voi.SetInput(permute.GetOutput())
    if plane=="zy":
        data.SetUpdateExtent(x,x,0,dy-1,0,dz-1)
        voi.SetVOI(0,dz-1,0,dy-1,x,x)
        permute.SetFilteredAxes(2,1,0)
        
    elif plane=="xz":
        data.SetUpdateExtent(0,dx-1,y,y,0,dz-1)
        voi.SetVOI(0,dx-1,0,dz-1,y,y)
        permute.SetFilteredAxes(1,2,0)
    permute.SetInput(data)
    voi.Update()
    return voi.GetOutput()


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
        
        ctf=vtk.vtkColorTransferFunction()
        n = scatter.GetNumberOfPairs()
        Logging.info("Number of pairs=%d"%n,kw="colocalization")
        p=0.75/n
        ctf.AddHSVPoint(0,0,0.0,0.0)
        for i in xrange(1,n,255):
            
            ctf.AddHSVPoint(i, 0.75*(i/float(p)), 1.0, 1.0)

        ctf.SetColorSpaceToHSV()
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
    """
    Method: getZoomFactor(x1,y1,x2,y2)
    Created: KP
    Description: Calculate a zoom factor so that the image
                 will be zoomed to be as large as possible
                 while fitting to x2,y2
    """       
    
    xf=float(x2)/x1
    yf=float(y2)/y1
    return min(xf,yf)
    
def vtkZoomImage(image,f):
    """
    Method: vtkZoomImage()
    Created: KP
    Description: Zoom a volume
    """       
    
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
    """
    Method: zoomImagetoSize()
    Created: KP
    Description: Scale an image to a given size
    """       
    
    return image.Scale(x,y)
    
def zoomImageByFactor(image,f):
    """
    Method: zoomImageByFactor()
    Created: KP
    Description: Scale an image by a given factor
    """       
    x,y=image.GetWidth(),image.GetHeight()
    x,y=int(f*x),int(f*y)
    return zoomImageToSize(image,x,y)

def getSlice(volume,zslice,startpos=None,endpos=None):
    """
    Method: getSlice
    Created: KP
    Description: Extract a given slice from a volume
    """           
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
    """
    Method: saveImageAs
    Created: KP
    Description: Save a given slice of a volume
    """       
    
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
    """
    Method: getColorTransferFunction
    Created: KP
    Description: Return a color transfer function based on a color
    """       
    
    ct=vtk.vtkColorTransferFunction()
    ct.AddRGBPoint(0,0,0,0)
    r,g,b=fg
    r/=255.0
    g/=255.0
    b/=255.0
    ct.AddRGBPoint(255,r,g,b)
    return ct    
    
def drawScaleBar(widthPx=0,widthMicro=0,voxelSize=(1,1,1),bgColor=(127,127,127),scaleFactor=1.0,vertical=0,round=1):
    """
    Method: drawScaleBar
    Created: 05.06.2005, KP
    Description: Draw a scalar bar of given size. Size is defined either
                 in pixels or in micrometers
    Parameters:
        widthPx       Scalar bar's width in pixels
        widthMicro    Scalar bar's width in micrometers
    """         
    bg=bgColor
    vx = voxelSize[0]
    vx*=1000000
    snapToMicro=[0.5,1,2,5,10]
    for i in range(10,5000,5):
        snapToMicro.append(i)
    Logging.info("voxel x=%d, scale=%f"%(vx,scaleFactor),kw="scale")
    vx/=float(scaleFactor)
    Logging.info("scaled voxel size=%f"%vx,kw="scale")
    if widthPx:
        widthMicro=widthPx*vx
        if int(widthMicro)!=widthMicro:
            Logging.info("Pixel width %.4f equals %.4f um. Snapping..."%(widthPx,widthMicro),kw="scale")
            for i,micro in enumerate(snapToMicro[:-1]):
                if micro<=widthMicro and snapToMicro[i+1]>widthMicro:
                    widthMicro=micro
                    Logging.info("Snapped to %.4fum"%widthMicro,kw="scale")
            widthPx=0
            
    if widthMicro and not widthPx:
        # x*vx = 10
        widthPx=widthMicro/vx
        Logging.info("%f micrometers is %f pixels"%(widthMicro,widthPx),kw="scale")
        widthPx=int(widthPx)
        
    if not vertical:
        heightPx=32
        
    else:
        heightPx=widthPx
        widthPx=32
        
    bmp = wx.EmptyBitmap(widthPx,heightPx)
    
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    dc.BeginDrawing()
    dc.SetBackground(wx.Brush(bg))
    dc.SetBrush(wx.Brush(bg))
    dc.SetPen(wx.Pen(bg,1))
    dc.DrawRectangle(0,0,widthPx,heightPx)
    
    dc.SetPen(wx.Pen((255,255,255),2))
    if not vertical:
        dc.DrawLine(0,6,widthPx,6)
        dc.DrawLine(1,3,1,9)
        dc.DrawLine(widthPx-1,3,widthPx-1,9)
    else:
        dc.DrawLine(6,0,6,heightPx)
        dc.DrawLine(3,1,9,1)
        dc.DrawLine(3,heightPx-1,9,heightPx-1)
        
    dc.SetTextForeground((255,255,255))
    if not vertical:
        dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
    else:
        dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.NORMAL))
    if int(widthMicro)==widthMicro:
        text=u"%d\u03bcm"%widthMicro
    else:
        text=u"%.2f\u03bcm"%widthMicro
    w,h=dc.GetTextExtent(text)
    if not vertical:
        x=widthPx/2
        x-=(w/2)
        
        dc.DrawText(text,x,12)
    else:
        y=heightPx/2
        y-=(h/2)
        dc.DrawRotatedText(text,12,y,90)
    
    dc.EndDrawing()
    dc.SelectObject(wx.NullBitmap)
    dc = None 
    return bmp
    
