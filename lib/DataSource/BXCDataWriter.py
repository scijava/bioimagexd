
# -*- coding: iso-8859-1 -*-
"""
 Unit: BXCDataWriter
 Project: BioImageXD
 Created: 22.02.2005, KP
 Description:

 A writer of BioImageXD .bxc channel files
 
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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"


from ConfigParser import *
from DataSource import *
import vtk
import os.path

import Logging
import DataUnit

class MyConfigParser(RawConfigParser):
    def optionxform(self, optionstr):
        return optionstr
        
class BXCDataWriter(DataWriter):
    """
    Created: 26.03.2005, KP
    Description: A writer of BioImageXD dataset channel (.bxc) files
    """

    def __init__(self,filename):
        """
        Created: 26.03.2005,KP
        Description: Constructor
        """
        DataWriter.__init__(self)
        # list of references to individual datasets (= timepoints) stored in 
        # vti-files
        self.dataSets = []
        # filename of the .bxc-file
        
        self.filename = filename
        # path to the .bxc-file and .vti-file(s)
        self.path=""
        # List of images and their paths
        self.imagesToWrite=[]
        
        # Number of datasets added to this datasource
        self.counter=0

        self.dataUnitSettings={}
        self.parser = None
        
    def getFilename(self):
        """
        Created: 08.02.2007, KP
        Description: return the filename
        """
        return self.filename
        
        
    def getParser(self):
        """
        Created: 27.03.2005, KP
        Description: Returns the parser that is used to read the .du file
        """
        if not self.parser:
            self.parser = MyConfigParser()
        return self.parser
        

    def sync(self,n=-1):
        """
        Created: 26.03.2005, KP
        Description: Writes all datasets pending a write to disk
        """
        ret=0
        toremove=[]
        for item in self.imagesToWrite:
            imagedata,path=item
            if n==0:break
            self.writeImageData(imagedata,path)
            toremove.append(item)
            n=n-1
            ret+=1
        for item in toremove:
            self.imagesToWrite.remove(item)
        return ret
        
    def write(self):
        """
        Created: 26.03.2005, KP
        Description: Writes the given datasets and their information to a du file
        """
        # Create a parser to write settings to disk:
        parser=self.getParser()
        if not parser.has_section("ImageData"):
            parser.add_section("ImageData")
        n=len(self.dataSets)
        parser.set("ImageData","numberOfFiles","%d"%n)
        for i in range(n):
            parser.set("ImageData","file_%d"%i,self.dataSets[i])
                    
        try:
            print "Trying to open",self.filename,repr(self.filename)
            fp=open(self.filename,"w")
        except IOError,ex:
            Logging.error("Failed to write settings",
            "BXDDataSource Failed to open .bxd file %s for writing settings (%s)"%(self.filename,str(ex)))
            return
        parser.write(fp)
        fp.close()
        self.sync()

    def addImageData(self,imageData):
        """
        Created: 1.12.2004,KP
        Description: Add a vtkImageData object to be written to the disk.
        """
        # We find out the path to the directory where the image data is written
        if not self.path:
            # This is determined from self.filename which is the name of the 
            # .du file this datasource has been loaded from
            self.path=os.path.dirname(self.filename)

        print "filename=",self.filename,repr(self.filename)
        print "Self.path=",self.path,repr(self.path)
        # Next we determine the name for the .vti file we are writing
        # We take the name of the .du file this datasource is associated with
        duFileName=os.path.basename(self.filename)
        print "dufilename=",duFileName,repr(duFileName)
        # and strip the .du from the end
        i=duFileName.rfind(".")
        imageDataName=duFileName[:i]
        fileName="%s_%d.vti"%(imageDataName,self.counter)
        print "adding with filename",fileName
        fileName=fileName.encode("ascii")
        self.counter+=1
        # Add the file name to our internal list of datasets
        self.dataSets.append(fileName)
        filepath=os.path.join(self.path,fileName)
        # Add data to waiting queue
        self.imagesToWrite.append((imageData,filepath))


    def addImageDataObjects(self,imageDataList):
        """
        Created: 10.11.2004, KP
        Description: Adds a list of vtkImageData objects to be written to the
                      disk. Uses addVtiObject to do all the dirty work
        """
        for i in range(0,len(imageDataList)):
            self.addImageData(imageDataList[i])


    def writeImageData(self,imageData,filename):
        """
        Created: 09.11.2004, JM
        Description: Writes the given vtkImageData-instance to disk
                     as .vti-file with the given filename
        Parameters:   imageData  vtkImageData-instance to be written
                      filename  filename to be used
        """
        #print "Writing image data to %s"%filename
        writer=vtk.vtkXMLImageDataWriter()
        writer.SetFileName(filename)
        #print "Writing ",imageData
        #imageData.Update()
        imageData.UpdateInformation()
        x,y,z = imageData.GetDimensions()
        pieces = (x*y*z)/(1024*1024)
        if pieces<4:pieces = 4
        print "Using ",pieces,"pieces"
        writer.SetNumberOfPieces(pieces)
        writer.SetInput(imageData)
        def f(obj, evt):
            if obj:
                print "Progress=",obj.GetProgress()
        writer.AddObserver("ProgressEvent",f)
        try:
            ret=writer.Write()
            if ret==0:
                Logging.error("Failed to write image data",
                "Failed to write vtkImageData object to file %s"%self.filename)
                return
        except Exception, ex:
            Logging.error("Failed to write image data",
            "Failed to write vtkImageData object to file %s"%self.filename,ex)
            return
        print "done"

