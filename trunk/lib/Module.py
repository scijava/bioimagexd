# -*- coding: iso-8859-1 -*-
"""
 Unit: Module.py
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 A Base Class for all data processing modules.
                           
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
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.19 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import ImageOperations
import Logging
#from enthought.tvtk import messenger
import messenger
import scripting

class Module:
    """
    Created: 03.11.2004, KP
    Description: A Base class for all data processing modules
    """
    def __init__(self,**kws):
        """
        Created: 03.11.2004, KP
        Description: Initialization
        """
        self.images=[]
        self.dataunits=[]
        self.doRGB=0
        self.x,self.y,self.z=0,0,0
        self.extent=None
        self.zoomFactor=1
        self.settings=None
        self.timepoint=-1
        self.limit = scripting.get_memory_limit()
        # Gracefully handle lack of vtkParallel kit
        try:
            self.streamer = vtk.vtkMemoryLimitImageDataStreamer()
            if self.limit:
                self.streamer.SetMemoryLimit(1024*self.limit)
        except:
            self.streamer = None
        self.eventDesc="Processing data"
        self.controlUnit = None
     
    def setControlDataUnit(self, dataunit):
        """
        Created: 10.07.2006, KP
        Description: Set the dataunit that is controlling the execution of this module
        """
        self.controlUnit = dataunit
        
    def getControlDataUnit(self):
        """
        Created: 10.07.2006, KP
        Description: Set the dataunit that is controlling the execution of this module
        """
        return self.controlUnit
    
 

    def updateProgress(self,obj,evt):
        """
        Created: 13.07.2004, KP
        Description: Sends progress update event
        """        
        progress=obj.GetProgress()
        progress=self.shift+progress*self.scale
        txt=obj.GetProgressText()
        if not txt:txt=self.eventDesc
        messenger.send(None,"update_progress",progress,txt,0)        
        
    def setTimepoint(self,tp):
        """
        Created: 21.06.2005, KP
        Description: Sets the timepoint this module is processing
        """
        self.timepoint=tp
        
    def setSettings(self,settings):
        """
        Created: 27.03.2005, KP
        Description: Sets the settings object of this module
        """
        self.settings=settings
        
    def setZoomFactor(self,factor):
        """
        Created: 23.02.2005, KP
        Description: Sets the zoom factor for the produced dataset.
                     This means that the preview dataset will be zoomed with
                     the specified zoom factor
        """
        self.zoomFactor=factor
            
    def zoomDataset(self,dataset):
        """
        Created: 23.02.2004, KP
        Description: Returns the dataset zoomed with the zoom factor
        """
        if self.zoomFactor != 1:
            return ImageOperations.vtkZoomImage(dataset,self.zoomFactor)
        return dataset
            
    def getZoomFactor(self,factor):
        """
        Created: 23.02.2004, KP
        Description: Returns the zoom factor
        """
        return self.zoomFactor

    def reset(self):
        """
        Created: 04.11.2004, KP
        Description: Resets the module to initial state
        """
        self.images=[]
        for i in self.images:
         del i
        self.extent=None
        self.x,self.y,self.z=0,0,0
        self.shift=0
        self.scale=1

    def addInput(self,dataunit,imageData):
        """
         Created: 03.11.2004, KP
         Description: Adds an input vtkImageData dataset for the module.
        """
        #imageData.SetScalarTypeToUnsignedChar()
        x,y,z=imageData.GetDimensions()
        if self.x and self.y and self.z:
            if x!=self.x or y!=self.y or z!=self.z:
                raise ("ERROR: Dimensions do not match: currently (%d,%d,%d), "
                "new dimensions (%d,%d,%d)"%(self.x,self.y,self.z,x,y,z))
        else:            
            self.x,self.y,self.z=imageData.GetDimensions()
            #Logging.info("Dataset dimensions =(%d,%d,%d)"%(x,y,z),kw="dataunit")
        extent=imageData.GetExtent()
        if self.extent:
            if self.extent!=extent:
                raise "ERROR: Extents do not match"
        else:
            self.extent=extent
        self.images.append(imageData)
        self.dataunits.append(dataunit)

    def getPreview(self,z):
        """
        Created: 03.11.2004, KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        raise "Abstract method getPreview() called"

    def processData(self,z,newData,toZ=None):
        """
        Created: 03.11.2004, KP
        Description: Processes the input data
        Parameters: z        The z coordinate of the plane to be processed
                    newData  The output vtkImageData object
                    toZ      Optional parameter defining the z coordinate
                             where the colocalization data is written
        """
        raise "Abstract method processData(z,data)"

    def doOperation(self):
        """
        Created: 01.12.2004, KP
        Description: Does the operation for the specified datasets.
        """
        raise "Abstract method doOperation() called"

    def getLimitedOutput(self,filter):
        """
        Created: 27.04.2006, KP
        Description: Return the results of the pipeline possibly executed in chunks
        """
        if self.limit and self.streamer:
            self.streamer.SetInput(filter.GetOutput())
            self.streamer.Update()
            print "Executing through streamer"
            return self.streamer.GetOutput()
        else:
            filter.Update()
            return filter.GetOutput()
