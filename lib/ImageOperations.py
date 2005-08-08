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
import math
import struct
import Logging
#from enthought.tvtk import messenger
import messenger

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


def scaleImage(data,factor,z=-1,interpolation=1):
    """
    Method: scaleImage(data,factor)
    Created: 01.08.2005, KP
    Description: Scale an image with cubic interpolation
    """    
    if z!=-1:
        data=getSlice(data,z)
    data.SetSpacing(1,1,1)
    x,y,z=data.GetDimensions()
    data.SetOrigin(x/2.0,y/2.0,0)
    transform=vtk.vtkTransform()
    x0,x1,y0,y1,z0,z1=data.GetExtent()
    transform.Scale(1/factor,1/factor,1)
    #transform.Translate((x1*factor)/2.0,(y1*factor)/2.0,0)
    reslice=vtk.vtkImageReslice()
#    reslice.SetOutputSpacing(1,1,1)
    reslice.SetOutputOrigin(0,0,0)
    reslice.SetInput(data)
    reslice.SetOutputExtent(x0*factor,x1*factor,y0*factor,y1*factor,z0,z1)
    #reslice.SetOutputDimensions(x*factor,y*factor,z)
    reslice.SetResliceTransform(transform)
    if interpolation==1:
        #reslice.SetInterpolationModeToNearestNeighbor()
        reslice.SetInterpolationModeToLinear()
    else:
        reslice.SetInterpolationModeToCubic()
    reslice.Update() 
    return reslice.GetOutput()
    
def loadNIHLut(data):
    """
    Method: loadNIHLut(data)
    Created: 17.04.2005, KP
    Description: Load an NIH Image LUT and return it as CTF
    """    
    if not len(data):
        raise "loadNIHLut got no data"
    n=256
    d=len(data)-32
    
    s="4s2s2s2s2s8s8si%ds"%d
    Logging.info("Unpacking ",s,"d=",d,"len(data)=",len(data))#,kw="imageop")
    header,version,ncolors,start,end,fill1,fill2,filler,lut = struct.unpack(s,data)
    if header!="ICOL":
        raise "Did not get NIH header!"
    ncolors=ord(ncolors[0])*(2**8)+ord(ncolors[1])
    start=ord(start[0])*(2**8)+ord(start[1])
    end=ord(end[0])*(2**8)+ord(end[1])
    
    reds=lut[:ncolors]
    greens=lut[ncolors:(2*ncolors)]
    blues=lut[(2*ncolors):(3*ncolors)]
    return reds,greens,blues

    
def loadLUT(filename,ctf=None,ctfrange=(0,256)):
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
    f=open(filename,"rb")
    lut=f.read()
    f.close()
    loadLUTFromString(lut,ctf,ctfrange)
    return ctf
    
def loadLUTFromString(lut,ctf,ctfrange=(0,256)):
    """
    Method: loadLUTFromString(binarystring,ctf,range)
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
    
    step=int(math.ceil(ctfrange[1]/256.0))
    j=0
    Logging.info("Ctf range = ",ctfrange[0]," - ",ctfrange[1],"step=",step)
    for i in range(int(ctfrange[0]),int(ctfrange[1]),int(step)):
        r=ord(reds[j])
        g=ord(greens[j])
        b=ord(blues[j])
        r/=255.0
        g/=255.0
        b/=255.0
        ctf.AddRGBPoint(i,r,g,b)
        j+=1
    
    
def saveLUT(ctf,filename):
    """
    Method: saveLUT(ctf,filename)
    Created: 17.04.2005, KP
    Description: Save a CTF as ImageJ binary LUT
    """    
    f=open(filename,"wb")
    s=lutToString(ctf)
    f.write(s)
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
            if r<0:r=0
            if b<0:b=0
            if g<0:g=0
            if r>=255:r=255
            if g>=255:g=255
            if b>=255:b=255
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
        #Logging.info("Getting slice %d"%slice,kw="imageop")
        data=getSlice(data,slice,startpos,endpos)
        
    exporter=vtk.vtkImageExport()
    print "data.GetWholeExtent()=",data.GetWholeExtent()
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
def vtkImageDataToPngString(data,slice=-1,startpos=None,endpos=None):
    """
    Method: vtkImageDataToPngString()
    Created: 26.07.2005, KP
    Description: A function that returns a vtkImageData object as png
                 data in a string
    """    
    if slice>=0:
        #Logging.info("Getting slice %d"%slice,kw="imageop")
        data=getSlice(data,slice,startpos,endpos)
        
    pngwriter=vtk.vtkPNGWriter()
    pngwriter.WriteToMemoryOn()
    pngwriter.SetInput(data)
    #pngwriter.Update()
    pngwriter.Write()
    result=pngwriter.GetResult()
    data=""
    for i in range(result.GetNumberOfTuples()):
        data+=chr(result.GetValue(i))
    return data
    
    

    
def vtkImageDataToPreviewBitmap(imageData,color,width=0,height=0,bgcolor=(0,0,0),getpng=0):
    """
    Method: vtkImageDataToPreviewBitmap
    Created: KP
    Description: A function that will take a volume and do a simple
                 maximum intensity projection that will be converted to a
                 wxBitmap
    """   
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
    Logging.info("Got MIP",kw="imageop")
    mip.Update()
    
    if output.GetNumberOfScalarComponents()==1:
        Logging.info("Mapping MIP through ctf",kw="imageop")
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(output)
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        imagedata=maptocolor.GetOutput()
    else:
        imagedata=output
    if getpng:
        Logging.info("Getting PNG string",kw="imageop")
        pngstr=vtkImageDataToPngString(imagedata)
    image = vtkImageDataToWxImage(imagedata)

    if not width and height:
        aspect=float(x)/y
        width=aspect*height
    if not height and width:
        aspect=float(y)/x
        height=aspect*width
    if not width and not height:
        width=height=64
    Logging.info("Scaling to %dx%d"%(width,height),kw="imageop")
    image.Rescale(width,height)
    bitmap=image.ConvertToBitmap()
    if getpng:
        return bitmap,pngstr
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

def fire(x0,x1):
    reds=[0,0,1,25,49,73,98,122,146,162,173,184,195,207,217,229,240,252,255,255,255,255,255,255,255,255,255,255,255,255,255,255]
    greens=[0,0,0,0,0,0,0,0,0,0,0,0,0,14,35,57,79,101,117,133,147,161,175,190,205,219,234,248,255,255,255,255]
    blues=[31,61,96,130,165,192,220,227,210,181,151,122,93,64,35,5,0,0,0,0,0,0,0,0,0,0,0,35,98,160,223,255]
    n=min(len(reds),len(greens),len(blues))
    div=x1/n
    
    ctf=vtk.vtkColorTransferFunction()
    ctf.AddRGBPoint(0,0,0,0)
    for i in range(0,n):
        r=reds[i]/255.0
        g=greens[i]/255.0
        b=blues[i]/255.0
        ctf.AddRGBPoint(i*div,r,g,b)
    return ctf

def getOverlay(width,height,color,alpha):
    """
    Method: getOverlay(width,height,color,alpha=
    Created: 11.07.2005, KP
    Description: Create an overlay
    """       
    siz=width*height*3
    fs="%ds"%siz    
    r,g,b=color
    s=chr(r)+chr(g)+chr(b)
    s=(width*height)*s
    ss=struct.pack(fs,s)
    img=wx.EmptyImage(width,height)
    img.SetData(ss)
    siz=width*height
    s=chr(alpha)
    fs="%ds"%siz    
    s=siz*s
    ss=struct.pack(fs,s)
    img.SetAlphaData(ss)
    return img
    
    
def histogram(imagedata,ctf=None,bg=(200,200,200),logarithmic=1,ignore_border=0,lower=0,upper=0,percent_only=0):
    """
    Method: histogram(imagedata)
    Created: 11.07.2005, KP
    Description: Draw a histogram of a volume
    """       
    accu=vtk.vtkImageAccumulate()
    accu.SetInput(imagedata)
    accu.Update()

    data=accu.GetOutput()
    values=[]
    sum=0
    sumth=0
    percent=0
    Logging.info("lower=",lower,"upper=",upper,kw="imageop")
    for i in range(0,256):
        c=data.GetScalarComponentAsDouble(i,0,0,0)
        values.append(c)
        sum+=c
        if (lower or upper):
            if i>=lower and i<=upper:
                sumth+=c
    retvals=values[:]
    if sumth:
        percent=(float(sumth)/sum)
        #Logging.info("percent=",percent,kw="imageop")
    if ignore_border:
        ma=max(values[5:])
        mi=min(values[0:250])
        for i in range(0,5):
            values[i]=ma
        for i in range(250,255):
            values[i]=mi
            
    for i,value in enumerate(values):
        if value==0:values[i]=1
    if logarithmic:
        values=map(math.log,values)
    m=max(values)
    scale=150.0/m
    values=[x*scale for x in values]
    w=256
    x1=max(values)
    diff=0
    if ctf:
        diff=40
    if percent:
        diff+=30
    Logging.info("Creating a %dx%d bitmap for histogram"%(int(w),int(x1)+diff),kw="imageop")
        
    bmp=wx.EmptyBitmap(int(w),int(x1)+diff)
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    dc.BeginDrawing()
    
    blackpen=wx.Pen((0,0,0),1)
    graypen=wx.Pen((100,100,100),1)
    whitepen=wx.Pen((255,255,255),1)
    
    dc.SetBackground(wx.Brush(bg))

    dc.Clear()
    dc.SetBrush(wx.Brush(wx.Colour(200,200,200)))
    dc.DrawRectangle(0,0,256,150)
    xoffset=7
    for i in range(0,255):
        c=values[i]
        c2=values[i+1]
        dc.SetPen(graypen)
        dc.DrawLine(xoffset+i,x1,xoffset+i,x1-c)
        dc.SetPen(blackpen)
        dc.DrawLine(xoffset+i,x1-c,xoffset+i+1,x1-c2)
    
    if not logarithmic:
        points=range(1,150,150/8)
    else:
        #         
        points=[4,8,16,28,44,64,88,116,148]
        points=[p+2 for p in points]
        points.reverse()
        
    for i in points:
        y=i
        dc.SetPen(blackpen)
        dc.DrawLine(0,y,5,y)
        dc.SetPen(whitepen)
        dc.DrawLine(0,y-1,5,y-1)
            
    if ctf:
        Logging.info("Painting ctf",kw="imageop")
        for i in range(0,256):
            val=[0,0,0]
            ctf.GetColor(i,val)
            r,g,b = val
            r=int(r*255)
            b=int(b*255)
            g=int(g*255)
            dc.SetPen(wx.Pen(wx.Colour(r,g,b),1))
            dc.DrawLine(xoffset+i,x1+8,xoffset+i,x1+30)
        dc.SetPen(whitepen)
        dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        dc.DrawText("255",230,x1+10)
    else:
        Logging.info("Got no ctf for histogram",kw="imageop")
    
    dc.EndDrawing()
    dc.SelectObject(wx.NullBitmap)
    dc = None    
    return bmp,percent,retvals


def scatterPlot(imagedata1,imagedata2,z,countVoxels, wholeVolume,logarithmic=1):
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
#    Logging.info("Scatterplot has dimensions:",data.GetDimensions(),kw="imageop")
    if logarithmic:
        Logging.info("Scaling scatterplot logarithmically",kw="imageop")
        logscale=vtk.vtkImageLogarithmicScale()
        logscale.SetInput(data)
        logscale.Update()
        data=logscale.GetOutput()
#    Logging.info("Logarithmic has dimensions:",data.GetDimensions(),kw="imageop")        
    x0,x1=data.GetScalarRange()
    #print "max=",x1
    scale=255.0/x1
    #print "scale=",scale
    shiftscale=vtk.vtkImageShiftScale()
    shiftscale.SetOutputScalarTypeToUnsignedShort()
    shiftscale.SetScale(scale)
    shiftscale.SetInput(data)
    shiftscale.Update()
    data=shiftscale.GetOutput()
#    Logging.info("Shift scale has dimensions:",data.GetDimensions(),kw="imageop")            
    
    if countVoxels:
        x0,x1=data.GetScalarRange()
        Logging.info("Scalar range of scatterplot=",x0,x1,kw="imageop")
        ctf=fire(x0,x1)
        n = scatter.GetNumberOfPairs()
        Logging.info("Number of pairs=%d"%n,kw="imageop")
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(data)
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        data=maptocolor.GetOutput()
    Logging.info("Scatterplot has dimensions:",data.GetDimensions(),data.GetExtent(),kw="imageop")                        
    data.SetWholeExtent(data.GetExtent())
    print "data.GetWHoleExtent()=",data.GetWholeExtent()
    image=vtkImageDataToWxImage(data)
    print "Image dims=",image.GetWidth(),image.GetHeight()
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
    if not filename:return
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
    
def imageDataTo3Component(image,ctf):
    """
    Method: imageDataTo3Component
    Created: 22.07.2005, KP
    Description: Processes image data to get it to proper 3 component RGB data
    """         
    ncomps = image.GetNumberOfScalarComponents()
        
    if ncomps==1:
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(image)
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        imagedata=maptocolor.GetOutput()
    elif ncomps>3:
        Logging.info("Data has %d components, extracting"%ncomps,kw="imageop")
        extract=vtk.vtkImageExtractComponents()
        extract.SetComponents(0,1,2)
        extract.SetInput(image)
        extract.Update()
        imagedata=extract.GetOutput()

    else:
        imagedata=image
    return imagedata
