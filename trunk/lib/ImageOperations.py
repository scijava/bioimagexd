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
import random
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

def paintLogarithmicScale(ctfbmp, ctf, vertical=1):
    """
    Created: 04.08.2006
    Description: Paint a logarithmic scale on a bitmap that represents the given ctf
    """
    minval,maxval=ctf.GetRange()
    width, height = ctfbmp.GetWidth(),ctfbmp.GetHeight()
    
    bmp = wx.EmptyBitmap(width+10,height)
    
    
    
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    dc.BeginDrawing()
    colour=wx.Colour(255,255,255)
    dc.SetBackground(wx.Brush(colour))
    dc.SetPen(wx.Pen(colour,0))
    dc.SetBrush(wx.Brush(colour))
    dc.DrawRectangle(0,0,width+16,height)
   
    dc.SetPen(wx.Pen(wx.Colour(0,0,0),1))
    dc.DrawBitmap(ctfbmp,5,0)
    
    size=max(width,height)
    maxval = max(ctf.originalRange)
    l=math.log(maxval)
    scale = size/float(maxval)
    for i in range(3*int(l)+1,1,-1):
        i/=3.0  
        x1 = int(math.exp(i)*scale)
#        print "\n\n*** PAINTING AT ",i,"=",x1
        if not vertical:
            dc.DrawLine(x1,0,x1,8)
            
        else:
            dc.DrawLine(0,x1,4,x1)
            dc.DrawLine(width+6,x1,width+10,x1)
#    dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
#    dc.DrawText("%d"%mmin,2,height-10)
#    dc.DrawText("%d"%mmax,2,10)

        
    dc.EndDrawing()
    dc.SelectObject(wx.NullBitmap)
    dc = None    
    return bmp    
    
    
    
def paintCTFValues(ctf,width=256,height=32, paintScale = 0, paintScalars = 0):
    """
    Created: 18.04.2005, KP
    Description: Paint a bar representing a ctf
    """    
    vertical=0
    if height>width:
        vertical=1
    bmp = wx.EmptyBitmap(width,height,-1)
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    dc.BeginDrawing()
        
        
    size = width
    if vertical:size=height
    
    minval,maxval=ctf.GetRange()
    d = float(maxval)/size
    for x1 in range(0,size):
        val=[0,0,0]
        ctf.GetColor(x1*d,val)
        r,g,b = val
        r*=255
        g*=255
        b*=255
        r=int(r)
        g=int(g)
        b=int(b)
        
        dc.SetPen(wx.Pen((r,g,b)))
        if not vertical:
            dc.DrawLine(x1,0,x1,height)
        else:
            dc.DrawLine(0,height-x1,width,height-x1)
            
    if paintScalars:
        mmin, mmax  = ctf.GetRange()
        #dc.SetBrush(wx.Brush((255,255,255)))
        dc.SetTextForeground(wx.Colour(255,255,255))
        dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.NORMAL))
        if vertical:
                        
            dc.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.NORMAL))
            dc.DrawText("%d"%mmin,8,height-20)
            dc.SetFont(wx.Font(6,wx.SWISS,wx.NORMAL,wx.NORMAL))
            dc.SetTextForeground(wx.Colour(0,0,0))
            dc.DrawText("%d"%mmax,1,10)
        else:
            dc.DrawText("%d"%mmin,5,6)
            dc.SetTextForeground(wx.Colour(0,0,0))
            dc.DrawText("%d"%mmax,width-35,6)
                    
    dc.EndDrawing()
    dc.SelectObject(wx.NullBitmap)
    dc = None    
    if paintScale:
        bmp = paintLogarithmicScale(bmp, ctf)
    return bmp


def scaleImage(data,factor=1.0,z=-1,interpolation=1,xfactor=0.0,yfactor=0.0):
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
    if not (xfactor or yfactor):
        transform.Scale(1/factor,1/factor,1)
    else:
        transform.Scale(1/xfactor,1/yfactor,1)
    
    #transform.Translate((x1*factor)/2.0,(y1*factor)/2.0,0)
    reslice=vtk.vtkImageReslice()
#    reslice.SetOutputSpacing(1,1,1)
    reslice.SetOutputOrigin(0,0,0)
    reslice.SetInput(data)
    if not (xfactor or yfactor):
        reslice.SetOutputExtent(int(x0*factor),int(x1*factor),int(y0*factor),int(y1*factor),z0,z1)
    else:
        reslice.SetOutputExtent(int(x0*xfactor),int(x1*xfactor),int(y0*yfactor),int(y1*yfactor),z0,z1)  
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
    Created: 17.04.2005, KP
    Description: Load an NIH Image LUT and return it as CTF
    """    
    if not len(data):
        raise "loadNIHLut got no data"
    #n=256
    d=len(data)-32
    n=d
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
    Created: 18.04.2005, KP
    Description: Load an ImageJ binary LUT from string
    Parameters:
        lut      A binary string representing the lookup table
        ctf      The CTF to modify
        ctfrange The range to which construct the CTF
    """        
    print "\n\nlen(lut)=",len(lut)
    failed=1
    if len(lut)!=768:
        try:
            reds,greens,blues=loadNIHLut(lut)
            failed=0
        except:
            failed=1
    
    if failed:
        n = len(lut)
        k = n/3
        reds=lut[0:k-1]        
        greens=lut[k-1:2*(k-1)]
        blues=lut[2*(k-1):3*(k-1)]
    n=len(reds)    
    #print k,ctfrange
    step=int(math.ceil(ctfrange[1]/k))
    if step==0:
        return vtk.vtkColorTransferFunction()
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
    Created: 18.04.2005, KP
    Description: Write a lut to a string
    """    
    s=""
    minval,maxval=ctf.GetRange()
    d=maxval/255.0
    for col in range(0,3):
        for i in range(0,maxval+1,d):
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
    lst=[   iTF.GetBrightness(),
            iTF.GetContrast(),
            iTF.GetGamma(),
            iTF.GetMinimumThreshold(),
            iTF.GetMinimumValue(),
            iTF.GetMaximumThreshold(),
            iTF.GetMaximumValue(),
            iTF.GetProcessingThreshold(),
            iTF.GetRangeMax()]
    return lst
    
def setFromParameterList(iTF,list):
    br,cr,g,mt,mv,mat,mav,mpt,rangemax=list
    iTF.SetRangeMax(rangemax)
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
    Logging.info("Setting update extent to ",data.GetWholeExtent(),kw="imageop")
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

    
def getMIP(imageData,color):
    """
    Created: 1.9.2005, KP
    Description: A function that will take a volume and do a simple
                 maximum intensity projection that will be converted to a
                 wxBitmap
    """   

    #print "imageData=",imageData
    mip=vtk.vtkImageSimpleMIP()
    #imageData.SetUpdateExtent(imageData.GetWholeExtent())
    #print "imageData.GetUpdateExtent()=",imageData.GetUpdateExtent()
    mip.SetInput(imageData)
    #mip.DebugOn()
    mip.Update()
    
    imageData.SetUpdateExtent(imageData.GetWholeExtent())        
    x,y,z=imageData.GetDimensions()
    
    output=mip.GetOutput()
    #Logging.info("Got MIP",kw="imageop")
    if output.GetNumberOfScalarComponents()==1:
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
    
#        Logging.info("Mapping MIP through ctf",kw="imageop")
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(output)
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        imagedata=maptocolor.GetOutput()
    else:
        imagedata=output
    return imagedata
    
def vtkImageDataToPreviewBitmap(dataunit,timepoint,color,width=0,height=0,bgcolor=(0,0,0),getpng=0):
    """
    Created: KP
    Description: A function that will take a volume and do a simple
                 maximum intensity projection that will be converted to a
                 wxBitmap
    """   
    imagedata=dataunit.getMIP(timepoint,color,small=1)

    #imagedata=getMIP(imageData,color)
    if getpng:
        Logging.info("Getting PNG string",kw="imageop")
        pngstr=vtkImageDataToPngString(imagedata)
    image = vtkImageDataToWxImage(imagedata)
    x,y=image.GetWidth(),image.GetHeight()
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
    Created: 06.06.2005, KP
    Description: Get a plane from given the volume
    """   
    X,Y,Z=0,1,2
    permute=vtk.vtkImagePermute()
    dx,dy,dz=data.GetDimensions()
    voi=vtk.vtkExtractVOI()
    #voi.SetInput(permute.GetOutput())
    voi.SetInput(data)
    permute.SetInput(voi.GetOutput())
    if plane=="zy":
        data.SetUpdateExtent(x,x,0,dy-1,0,dz-1)
        voi.SetVOI(x,x,0,dy-1,0,dz-1)
        permute.SetFilteredAxes(Z,Y,X)
        
    elif plane=="xz":
        data.SetUpdateExtent(0,dx-1,y,y,0,dz-1)
        #voi.SetVOI(0,dx-1,0,dz-1,y,y)
        voi.SetVOI(0,dx-1,y,y,0,dz-1)
        permute.SetFilteredAxes(X,Z,Y)
    #permute.SetInput(data)
    #return voi.GetOutput()    
    permute.Update()
    return permute.GetOutput()

def watershedPalette(x0,x1):    
    ctf = vtk.vtkColorTransferFunction()
#    ctf.AddRGBPoint(0,1,1,1)
#    ctf.AddRGBPoint(1,0,0,0)
    ctf.AddRGBPoint(0,0,0,0)
    ctf.AddRGBPoint(1,0,0,0)
    if x0<=1:x0=2
    for i in range(int(x0),int(x1)):        
        r = random.random()
        g = random.random()
        b = random.random()
        ctf.AddRGBPoint(float(i), float(r),float(g),float(b))
        
    return ctf
        

def fire(x0,x1):
    reds=[0,0,1,25,49,73,98,122,146,162,173,184,195,207,217,229,240,252,255,255,255,255,255,255,255,255,255,255,255,255,255,255]
    greens=[0,0,0,0,0,0,0,0,0,0,0,0,0,14,35,57,79,101,117,133,147,161,175,190,205,219,234,248,255,255,255,255]
    blues=[31,61,96,130,165,192,220,227,210,181,151,122,93,64,35,5,0,0,0,0,0,0,0,0,0,0,0,35,98,160,223,255]
    n=min(len(reds),len(greens),len(blues))
    div=x1/float(n)
    
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
    Method: getOverlay(width,height,color,alpha)
    Created: 11.07.2005, KP
    Description: Create an overlay of given color with given alpha
    """       
    #print "\n\nGetting overlay",width,height
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
    
def getOverlayBorders(width,height,color,alpha):
    """
    Method: getOverlayBorders(width,height,color,alpha)
    Created: 12.04.2005, KP
    Description: Create borders for an overlay that are only very little transparent
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
    s=chr(0)
    fs="%ds"%siz    
    s=siz*s
    ss=struct.pack(fs,s)
    ss=chr(alpha)*(2*width)+ss[2*width:]
    x=len(ss)
    ss=ss[:x-(2*width)]+chr(alpha)*2*width
    twochar=chr(alpha)+chr(alpha)
    for i in range(0,width*height,width):
        if i:
            ss=ss[:i-2]+2*twochar+ss[i+2:]
        else:
            ss=ss[:i]+twochar+ss[i+2:]
    img.SetAlphaData(ss)
        
    return img    
    
    
def get_histogram(image):
    """
    Created: 06.08.2006, KP
    Description: Return the histogrm of the image as a list of floats
    """
    accu = vtk.vtkImageAccumulate()
    accu.SetInput(image)
    x0,x1 = image.GetScalarRange()
    accu.SetComponentExtent(0,x1,0,0,0,0)
    accu.Update() 
    data = accu.GetOutput()
    
    
    values=[]
    x0,x1,y0,y1,z0,z1 = data.GetWholeExtent()

    for i in range(0,int(x1)+1):
        c=data.GetScalarComponentAsDouble(i,0,0,0)
        values.append(c)
    return values

    
def histogram(imagedata,ctf=None,bg=(200,200,200),logarithmic=1,ignore_border=0,lower=0,upper=0,percent_only=0,maxval=255):
    """
    Created: 11.07.2005, KP
    Description: Draw a histogram of a volume
    """       
    values = get_histogram(imagedata)
    sum=0
    xoffset=10
    sumth=0
    percent=0
    Logging.info("lower=",lower,"upper=",upper,kw="imageop")
    for i,c in enumerate(values):
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
        mi=min(values[:-5])
        n = len(values)
        for i in range(0,5):
            values[i]=ma
        for i in range(n-5,n):
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
    w+=xoffset+5
    
    
    diff=0
    if ctf:
        diff=40
    if percent:
        diff+=30
    Logging.info("Creating a %dx%d bitmap for histogram"%(int(w),int(x1)+diff),kw="imageop")
        
    # Add an offset of 15 for the percentage text
    bmp=wx.EmptyBitmap(int(w),int(x1)+diff+15)
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    dc.BeginDrawing()
    
    blackpen=wx.Pen((0,0,0),1)
    graypen=wx.Pen((100,100,100),1)
    whitepen=wx.Pen((255,255,255),1)
    
    dc.SetBackground(wx.Brush(bg))

    dc.Clear()
    dc.SetBrush(wx.Brush(wx.Colour(200,200,200)))
    dc.DrawRectangle(0,0,w,150)
    
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
    
    
    d=(len(values)-1)/255.0
    for i in range(0,255):
        c=values[int(i*d)]
        #print "i=",i,"d=",d,"i*d=",i*d,"i*d+d=",int((i*d)+d)
        c2=values[int((i*d)+d)]
        dc.SetPen(graypen)
        dc.DrawLine(xoffset+i,x1,xoffset+i,x1-c)
        dc.SetPen(blackpen)
        
        dc.DrawLine(xoffset+i,x1-c,xoffset+i+1,x1-c2)
    
            
    if ctf:
        Logging.info("Painting ctf",kw="imageop")
        for i in range(0,256):
            val=[0,0,0]
            ctf.GetColor(i*d,val)
            r,g,b = val
            r=int(r*255)
            b=int(b*255)
            g=int(g*255)
            dc.SetPen(wx.Pen(wx.Colour(r,g,b),1))
            dc.DrawLine(xoffset+i,x1+8,xoffset+i,x1+30)
        dc.SetPen(whitepen)
        dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        dc.DrawText(str(int(maxval)),230,x1+10)
    else:
        Logging.info("Got no ctf for histogram",kw="imageop")
    
    dc.EndDrawing()
    dc.SelectObject(wx.NullBitmap)
    dc = None    
    return bmp,percent,retvals,xoffset

def getMaskFromROIs(rois, mx, my, mz):
    """
    Created: 06.08.2006, KP
    Description: Create a mask that contains all given Regions of Interest
    """
    insideMap={}
    for shape in rois:
        insideMap.update(shape.getCoveredPoints())
    insMap={}
    for x,y in insideMap.keys():
        insMap[(x,y)]=1    
    return getMaskFromPoints(insMap,mx,my,mz)
    
def getMaskFromPoints(points,mx,my,mz):
    """
    Created: KP
    Description: Create a mask where all given points are set to 255
    """
    siz = mx*my
    fs="%dB"%siz    
    #data=[255*((i % mx,i / my) in points) for i in range(0,mx*my)]
    #data = [255*((x,y) in points) for x in range(0,mx) for y in range(0,my)]
    data=[]
    for y in range(0,my):
        for x in range(0,mx):
            data.append(255*points.get((x,y),0))
    ss = struct.pack(fs,*data)
    
    importer=vtk.vtkImageImport()
    importer.CopyImportVoidPointer(ss,mx*my)
    importer.SetDataScalarTypeToUnsignedChar()
    importer.SetNumberOfScalarComponents(1)
    importer.SetDataExtent(0,mx-1,0,my-1,0,0)
    importer.SetWholeExtent(0,mx-1,0,my-1,0,0)

    importer.Update()
    image = importer.GetOutput()
    #writer = vtk.vtkPNGWriter()
    #writer.SetFileName("foo.png")
    #writer.SetInput(image)
    #writer.Write()
    
    append = vtk.vtkImageAppend()
    append.SetAppendAxis(2)
    for z in range(0,mz):
        append.SetInput(z,image)
    append.Update()
    image2 = append.GetOutput()
    #print "Image2=",image2
    return image2
    

    
def equalize(imagedata, ctf):
    histogram = get_histogram(imagedata)
    maxval = len(histogram)
    
    def weightedValue(x):
        if x<2:return x
        return math.sqrt(x)
    
    intsum = weightedValue(histogram[0])
    for i in range(1,maxval):
        intsum+=2*weightedValue(histogram[i])
    intsum+=weightedValue(histogram[-1])
    
    scale = maxval / float(intsum)
    lut=[0]*(maxval+1)
    intsum = weightedValue(histogram[0])
    for i in range(1,maxval):
        delta = weightedValue(histogram[i])
        intsum += delta
        c = math.ceil(intsum*scale)
        f = math.floor(intsum*scale)
        a=f
        if abs(c-intsum*scale)<abs(f-intsum*scale):
            a=c
        lut[i] = a
        intsum += delta
        
    lut[-1]=maxval
    
    ctf2 = vtk.vtkColorTransferFunction()
    for i,value in enumerate(lut):
        val=[0,0,0]
        ctf.GetColor(value, val)
        ctf2.AddRGBPoint(i, *val)
        
    return ctf2
        
    
def scatterPlot(imagedata1,imagedata2,z,countVoxels, wholeVolume=1,logarithmic=1):
    """
    Created: 25.03.2005, KP
    Description: Create scatterplot
    """       
    imagedata1.SetUpdateExtent(imagedata1.GetWholeExtent())
    imagedata2.SetUpdateExtent(imagedata1.GetWholeExtent())
    
    x0,x1 = imagedata1.GetScalarRange()
    d = 255.0/ x1
    shiftscale=vtk.vtkImageShiftScale()
    shiftscale.SetOutputScalarTypeToUnsignedChar()
    shiftscale.SetScale(d)
    shiftscale.SetInput(imagedata1)
    imagedata1 = shiftscale.GetOutput()

    x0,x1 = imagedata2.GetScalarRange()
    d = 255.0/ x1
    shiftscale=vtk.vtkImageShiftScale()
    shiftscale.SetOutputScalarTypeToUnsignedChar()
    shiftscale.SetScale(d)
    shiftscale.SetInput(imagedata2)
    imagedata2 = shiftscale.GetOutput()
    
    app=vtk.vtkImageAppendComponents()
    app.AddInput(imagedata1)
    app.AddInput(imagedata2)
    #app.Update()
    acc=vtk.vtkImageAccumulate()
    
    #n = max(imagedata1.GetScalarRange())
    #n2 = max(max(imagedata2.GetScalarRange()),n)
    #print "n=",n
    n=255
    acc.SetComponentExtent(0,n,0,n,0,0)
    acc.SetInput(app.GetOutput())
    acc.Update()
    data=acc.GetOutput()
    
    originalRange = data.GetScalarRange()
    
    
    if logarithmic:
        Logging.info("Scaling scatterplot logarithmically",kw="imageop")
        logscale=vtk.vtkImageLogarithmicScale()
        logscale.SetInput(data)
        logscale.Update()
        data=logscale.GetOutput()
        
    x0,x1=data.GetScalarRange()
    print "Scalar range of logarithmic scatterplot=",x0,x1
    
    if countVoxels:
        x0,x1=data.GetScalarRange()
        Logging.info("Scalar range of scatterplot=",x0,x1,kw="imageop")
        ctf=fire(x0,x1)
        ctf = equalize(data, ctf)
        #n = scatter.GetNumberOfPairs()
        #Logging.info("Number of pairs=%d"%n,kw="imageop")
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(data)
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        data=maptocolor.GetOutput()
        ctf.originalRange = originalRange
    Logging.info("Scatterplot has dimensions:",data.GetDimensions(),data.GetExtent(),kw="imageop")                        
    data.SetWholeExtent(data.GetExtent())
    #print "data.GetWholeExtent()=",data.GetWholeExtent()
    img = vtkImageDataToWxImage(data)
    #if img.GetWidth()>255:
    #    
    #    img.Rescale(255,255)
    return img,ctf
    
def getZoomFactor(x1,y1,x2,y2):
    """
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
    Created: KP
    Description: Scale an image to a given size
    """           
    return image.Scale(x,y)
    
def zoomImageByFactor(image,f):
    """
    Created: KP
    Description: Scale an image by a given factor
    """       
    x,y=image.GetWidth(),image.GetHeight()
    x,y=int(f*x),int(f*y)
    return zoomImageToSize(image,x,y)

def getSlice(volume,zslice,startpos=None,endpos=None):
    """
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
