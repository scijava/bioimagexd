# -*- coding: iso-8859-1 -*-
"""
 Unit: FileListDataSource
 Project: BioImageXD
 Created: 29.03.2006, KP
 Description: A datasource for a list of given files as a time series, dependent on the given number of slices in a stack

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
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import ConfigParser
import struct
import re
import Image
import messenger

import codecs
        

import os.path
from DataSource import *
import DataUnit
import Dialogs
import glob

def getExtensions(): return []
def getFileType(): return "filelist"
def getClass(): return FileListDataSource    
    

class FileListDataSource(DataSource):
    """
    Created: 12.04.2005, KP
    Description: File list datasource for reading a dataset from a given set of files
    """
    def __init__(self, filenames=[], pattern="", callback = None):
        """
        Created: 12.04.2005, KP
        Description: Constructor
        """    
        DataSource.__init__(self)
        self.name= "Import"
        self.extMapping = {"tif":"TIFF","tiff":"TIFF","png":"PNG","jpg":"JPEG","jpeg":"JPEG","pnm":"PNM","vti":"XMLImageData","vtk":"DataSet","bmp":"BMP"}
        self.dimMapping={"bmp":2,"tif":2,"tiff":2,"png":2,"jpg":2,"jpeg":2,"pnm":2,"vti":3,"vtk":3}
        
        self.callback = callback
        self.dimensions = None
        self.voxelsize = (1,1,1)
        self.spacing = (1,1,1)
        self.pattern = ""
        self.color = None
        self.shift = None
        self.tps=-1
        if filenames:
            self.numberOfImages = len(filenames)
            self.getDataSetCount()
        
        self.imageDims={}
        
        self.numberOfImages = 0
        self.readers = []
        self.slicesPerTimepoint = 1
        self.is3D = 0
        
    def setColorTransferFunction(self, ctf):
        """
        Created: 04.06.2007, KP
        Description: Set the color transfer function
        """
        self.ctf = ctf
        
    def is3DImage(self):
        """
        Created: 08.05.2007, KP
        Description: Return a flag indicating whether the images are 2D or 3D images
        """
        return self.is3D
        
        
    def setPattern(self, pattern):
        """
        Created: 07.05.2007, KP
        Description: Set a pattern describing which files to use
        """
        self.pattern = pattern
        
    def setFilenames(self, filenames, pattern=-1):
        """
        Created: 07.05.2007, KP
        Description: set the filenames that will be read
        """
        if pattern != -1:
            self.pattern = pattern
        if not self.dimensions:
            self.retrieveImageInfo(filenames[0])
        self.filenames = filenames
        self.numberOfImages = len(filenames)
        if not self.checkImageDimensions(filenames):
            raise Logging.GUIError("Image dimensions do not match","Some of the selected files have differing dimensions, and cannot be imported into the same dataset.")        
        self.getReadersFromFilenames()
                
        
        
    def checkImageDimensions(self, filenames):
        """
        Created: 16.05.2007, KP
        Description: check that each image in the list has the same dimensions
        """
        s = None
        for file in filenames:
            i = Image.open(file)
            self.imageDims[file] = i.size
            if s and i.size != s:
                x0,y0 = s
                x1,y1 = i.size
                return 0
            s = i.size        
            fn = file        
        return 1
        
    def getReaderByExtension(self, ext, isRGB = 0):
        """
        Created: 08.05.2007, KP
        Description: return a VTK image reader based on file extension
        """
        assert ext in self.extMapping,"Extension not recognized: %s"%ext
        mpr = self.extMapping[ext]
        # If it's a tiff file, we use our own, extended TIFF reader
        if self.extMapping[ext]=="TIFF":
            mpr="ExtTIFF"
            
        self.rdrstr = "vtk.vtk%sReader()"%mpr
        rdr = eval(self.rdrstr)
        if ext =="bmp":
            rdr.Allow8BitBMPOn()                
        if mpr=="ExtTIFF" and not isRGB:
            rdr.RawModeOn()
        
        return rdr

    def getReadersFromFilenames(self):
        """
        Created: 07.05.2007, KP
        Description: create the reader list from a given set of file names and parameters
        """        
        self.z=int(self.slicesPerTimepoint)

        assert self.z>0,"Number of slices per timepoint is greater than 0"
        assert self.z <= len(self.filenames),"Number of timepoints cannot exceed number of files given"

        for i in self.readers:
            del i
        self.readers = []
        

        if not self.filenames:
            raise Logging.GUIError("No files could be found","For some reason, no files were listed to be imported.")        
                    
        files = self.filenames
        print "Determining readers from ",self.filenames
        
        isRGB = 1
        ext = files[0].split(".")[-1].lower()
        
        if ext in ["tif","tiff"]:
            tiffimg = Image.open(files[0])
            if tiffimg.palette:
                print "HAS PALETTE, THEREFORE NOT RGB"
                isRGB = 0
            else:
                print "NO PALETTE, IS AN RGB IMAGE"
        rdr = self.getReaderByExtension(ext, isRGB)
                
        dirn=os.path.dirname(files[0])
        print "THERE ARE ",self.z,"SLICES PER TIMEPOINT"
        ext=files[0].split(".")[-1].lower()

        dim = self.dimMapping[ext]
        self.is3D = (dim==3)
        self.readers=[]
        
        if dim==3:
            totalFiles = len(files)
            for i,file in enumerate(files):                       
                # This is not required for VTK dataset readers, so 
                # we ignore any errors 0
                Logging.info("Reading ",file,kw="io")
                rdr.SetFileName(file)
                if mpr=="ExtTIFF" and not isRGB:
                    rdr.RawModeOn()
                self.readers.append(rdr)
               
                #self.callback(i,"Reading dataset %d / %d"%(i+1,totalFiles))
#                self.writeData(outname,data,i,len(files))
        else:
            totalFiles = len(files) / self.z

            pattern = self.pattern
            n=pattern.count("%")
            
            Logging.info("Number of %s=",n,kw="io")
            imgAmnt=len(files)
            # If there's only one timepoint
            if len(files)==self.z:
                arr = vtk.vtkStringArray()
                for i in files:
                    arr.InsertNextValue(os.path.join(dirn,i))
                rdr.SetFileNames(arr)
                self.readers.append(rdr)
            elif n==0 and imgAmnt>1:
                # If the pattern doesn't have %, then we just use
                # the given filenames and allocate them to timepoints
                # using  slicesPerTimepoint slices per timepoint
                ntps = len(files) / self.slicesPerTimepoint
                filelst = files[:]
                dirn 
                for tp in range(0, ntps):
                    rdr = self.getReaderByExtension(ext, isRGB)
                    arr = vtk.vtkStringArray()
                    for i in range(0, self.slicesPerTimepoint):                                        
                        arr.InsertNextValue(filelst[0])
                        filelst = filelst[1:]
                    
                    rdr.SetFileNames(arr)
                    rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                    rdr.SetDataSpacing(self.spacing)
                    rdr.SetDataOrigin(0,0,0)
                
                    self.readers.append(rdr)
            
                #print "FOO"
                #Dialogs.showerror(self,"You are trying to import multiple files but have not defined a proper pattern for the files to be imported","Bad pattern")
                return
            elif n==0:
                # If no pattern % and only one file
                rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                rdr.SetDataSpacing(self.spacing)
                rdr.SetDataOrigin(0,0,0)
                
                rdr.SetFileName(files[0])
                #rdr.Update()

                Logging.info("Reader = ",rdr,kw="io")
                self.readers.append(rdr)
                
            elif n==1:
                # If there is a % in the pattern
                j=0
                Logging.info("self.z=%d",self.z,kw="io")
                start=0
                for i in range(0,imgAmnt):                    
                    file=dirn+os.path.sep+pattern%i
                    if os.path.exists(file):
                        start=i
                        break
                    
                for i in range(start,imgAmnt+start,self.z):
                    rdr = self.getReaderByExtension(ext, isRGB)
                    rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                    rdr.SetDataSpacing(self.spacing)
                    rdr.SetDataOrigin(0,0,0)
                    
                    if i:
                        Logging.info("Setting slice offset to ",i,kw="io")
                        rdr.SetFileNameSliceOffset(i)
                    rdr.SetFilePrefix(dirn+os.path.sep)
                    rdr.SetFilePattern("%s"+pattern)
                   
                    self.callback(j,"Reading dataset %d / %d"%(j+1,totalFiles))
                    self.readers.append(rdr)
                    j=j+1
            elif n==2:
                tps = imgAmnt / self.z
                for i in range(tps):
                    rdr = self.getReaderByExtension(ext, isRGB)
                    rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                    rdr.SetDataSpacing(self.spacing)
                    rdr.SetDataOrigin(0,0,0)
                    
                    pos=pattern.rfind("%")
                    begin=pattern[:pos-1]
                    end=pattern[pos-1:]
                    currpat=begin%i+end
                    Logging.info("Pattern for timepoint %d is "%i,currpat,kw="io")
                                     
                    rdr.SetFilePrefix(dirn+os.path.sep)
                    rdr.SetFilePattern("%s"+currpat)
                    Logging.info("Reader = ",rdr,kw="io")
                    # rdr.Update()
                    self.readers.append(rdr)
                    self.callback(i,"Reading dataset %d / %d"%(i+1,totalFiles))
                
    def setSlicesPerTimepoint(self, n):
        """
        Created: 07.05.2007, KP
        Description: Set the number of slices that belong to a given timepoint
        """
        assert n>0,"Slices per timepoint needs to be greater than 0"
        print "Setting slices per timepoint to ",n
        self.slicesPerTimepoint = n
        self.z = n
        self.readers = []
        
    def getDataSetCount(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        """
        return int(self.numberOfImages / self.slicesPerTimepoint)
        
        
    def getFileName(self):
        """
        Created: 21.07.2005
        Description: Return the file name
        """    
        return self.filename
        
    def getDataSet(self, i,raw=0):
        """
        Created: 12.04.2005, KP
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        """
        data=self.getTimepoint(i)
        data=self.getResampledData(data,i)
        if not self.shift:
            self.shift=vtk.vtkImageShiftScale()
            self.shift.SetOutputScalarTypeToUnsignedChar()
        self.shift.SetInput(data)
            
        x0,x1=data.GetScalarRange()
        print "Scalar range=",x0,x1
        if not x1:
            x1=1
        scale=255.0/x1
        
        if scale:
            self.shift.SetScale(scale)
        self.shift.Update()
        data=self.shift.GetOutput()
        data.ReleaseDataFlagOff()
        return data
        
    def retrieveImageInfo(self,filename):
        """
        Created: 21.04.2005, KP
        Description: A method that reads information from an image
        """        
        assert filename,"Filename must be defined"
        assert os.path.exists(filename),"File that we're retrieving information from (%s) needs to exist, but doesn't."%filename
        ext  = filename.split(".")[-1].lower()
        rdr = self.getReaderByExtension(ext)
        
        if ext =="bmp":
            rdr.Allow8BitBMPOn()
        
        rdr.SetFileName(filename)
        rdr.Update()
        data=rdr.GetOutput()
        self.x,self.y, z=data.GetDimensions()
        self.dimensions = (self.x, self.y, self.slicesPerTimepoint)
        if z>1:
            self.slicesPerTimepoint = z
            self.z = z
            self.dimensions= (self.x, self.y, self.z)
                
    def getTimepoint(self,n,onlyDims=0):
        """
        Created: 16.02.2006, KP
        Description: Return the nth timepoint
        """        
        if not self.readers:
            self.getReadersFromFilenames()
            
        if n>= len(self.readers):
            raise Logging.GUIError("Attempt to read bad timepoint","Timepoint %d is not defined by the given filenames"%n)
            #print "TRYING TO GET TIMEPOINT",n,"THERE ARE ",len(self.readers),"readers"
            n=0
            
        self.reader = self.readers[n]
        
    
        data=self.reader.GetOutput()
        
        if not self.voxelsize:
            size=data.GetSpacing()
            x,y,z=[size.GetElement(x) for x in range(0,3)]
            self.voxelsize=(x,y,z)
            print "Read voxel size",self.voxelsize

        if onlyDims:
            return 
        return data        
    def getDimensions(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if self.resampleDims:
            return self.resampleDims
        if not self.dimensions:            
            self.getVoxelSize()
            #print "Got dimensions=",self.dimensions                
        return self.dimensions

        
    def getSpacing(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the spacing of the datasets this 
                     dataunit contains
        """
        if not self.spacing:
            a,b,c = self.getVoxelSize()
            self.spacing=[1,b/a,c/a]
        return self.spacing
        
    def getVoxelSize(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the voxel size of the datasets this 
                     dataunit contains
        """
        return self.voxelsize
  
    def setVoxelSize(self, vxs):
        """
        Created: 08.05.2007, KP
        Description: set the voxel sizes of the images that are read
        """
        self.voxelsize = vxs
        a,b,c = vxs
        self.spacing=[1,b/a,c/a]        
            
            
    def loadFromFile(self, filename):
        """
        Created: 12.04.2005, KP
        Description: Loads the specified .oif-file and imports data from it.
        """
        return []
        

    def getName(self):
        """
        Created: 18.11.2005, KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        return self.name

        
    def getColorTransferFunction(self):
        """
        Created: 26.04.2005, KP
        Description: Returns the ctf of the dataset series which this datasource
                     operates on
        """
        return self.ctf