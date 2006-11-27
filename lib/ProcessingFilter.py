#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ProcessingFilter
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module that contains the base class for various data processing filters used in the Process
 task and other task modules.
                            
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import types
import vtk
import Command
try:
    import itk
except:
    pass
import messenger
import scripting as bxd

import GUI.GUIBuilder as GUIBuilder
import ImageOperations

from GUI.GUIBuilder import FILTER_EXPERIENCED, FILTER_BEGINNER, FILTER_INTERMEDIATE



class ProcessingFilter(GUIBuilder.GUIBuilderBase):
    """
    Created: 13.04.2006, KP
    Description: A base class for manipulation filters
    """ 
    category = "No category"
    name = "Generic Filter"
    level = FILTER_EXPERIENCED
    def __init__(self,numberOfInputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """
        self.taskPanel = None                
        self.dataUnit = None
        GUIBuilder.GUIBuilderBase.__init__(self, changeCallback = self.notifyTaskPanel)

        self.numberOfInputs = numberOfInputs
        self.noop = 0
        self.parameters = {}
        self.gui = None
        
        self.sourceUnits = []
        self.inputs =[]
        self.nextFilter = None
        self.prevFilter = None
        self.itkToVtk = None
        self.enabled = 1
        self.itkFlag = 0
        self.inputIndex=0
        self.imageType = "UC3"
        self.inputMapping = {}
        for item in self.getPlainParameters():
            self.setParameter(item,self.getDefaultValue(item))
        
        self.vtkToItk = None
        self.itkToVtk = None
        self.G = "UC3"

    def set(self, parameter, value):
        """
        Created: 21.07.2006, KP
        Description: Set the given parameter to given value
        """   
        GUIBuilder.GUIBuilder.setParameter(self, parameter, value)
        # Send a message that will update the GUI
        messenger.send(self,"set_%s"%parameter,value)

        
    def setParameter(self,parameter,value):
        """
        Created: 13.04.2006, KP
        Description: Set a value for the parameter
        """ 
        
        if self.taskPanel:                
            lst = self.taskPanel.getFilters(self.name)
            i = lst.index(self)
            if len(lst)==1:
                func="getFilter('%s')"%self.name
            else:
                func="getFilter('%s', %d)"%(self.name,i)        
            oldval = self.parameters[parameter]
            if self.getType(parameter)==GUIBuilder.ROISELECTION:
                i,roi = value
                setval="bxd.visualizer.getRegionsOfInterest()[%d]"%i
                rois = bxd.visualizer.getRegionsOfInterest()
                if oldval in rois:
                    n = rois.index(oldval)
                    setoldval="bxd.visualizer.getRegionsOfInterest()[%d]"%n
                else:
                    setoldval=""
                # First record the proper value
                value = roi
            else:
                if type(value) in [types.StringType,types.UnicodeType]:
                    
                    setval="'%s'"%value
                    setoldval="'%s'"%oldval
                else:
                    #print "Not string"
                    setval=str(value)
                    setoldval=str(oldval)
            
            #print "setval=",setval,"oldval=",oldval
            n = bxd.mainWindow.currentTaskWindowName
            do_cmd="bxd.mainWindow.tasks['%s'].%s.set('%s',%s)"%(n,func,parameter,setval)
            if setoldval:
                undo_cmd="bxd.mainWindow.tasks['%s'].%s.set('%s',%s)"%(n,func,parameter,setoldval)
            else:
                undo_cmd=""
            cmd=Command.Command(Command.PARAM_CMD,None,None,do_cmd,undo_cmd,desc="Change parameter '%s' of filter '%s'"%(parameter,self.name))
            cmd.run(recordOnly = 1)          
            
        #print "\n\nSetting ",parameter,"to",value
        GUIBuilder.GUIBuilderBase.setParameter(self, parameter, value)
        
    def writeOutput(self, dataUnit, timePoint):
        """
        Created: 09.07.2006, KP
        Description: Optionally write the output of this module during the processing
        """   
        pass
        
        
    def notifyTaskPanel(self, module):
        """
        Created: 31.05.2006, KP
        Description: Notify the task panel that filter has changed
        """                     
        if self.taskPanel:
            self.taskPanel.filterModified(self)

        
    def setImageType(self,it):
        """
        Created: 15.05.2006, KP
        Description: Set the image type of the ITK image
        """             
        self.imageType = it
        
    def getImageType(self):
        """
        Created: 15.05.2006, KP
        Description: Get the image type of the ITK image
        """                 
        return self.imageType
        
    def setTaskPanel(self,p):
        """
        Created: 14.05.2006, KP
        Description: Set the task panel that controsl this filter
        """
        self.taskPanel = p
        
    def convertVTKtoITK(self,image,cast=None):
        """
        Created: 18.04.2006, KP
        Description: Convert the image data to ITK image
        """         
        if "itkImage" in str(image.__class__):
            return image
        if not self.itkFlag:
            messenger.send(None,"show_error","Non-ITK filter tries to convert to ITK","A non-ITK filter %s tried to convert data to ITK image data"%self.name)
            return image

        #if not self.vtkToItk:            
        ImageType = itk.VTKImageToImageFilter.IUC3
            
        if cast==types.FloatType:
            ImageType = itk.VTKImageToImageFilter.IF3
        
            
        scalarType = image.GetScalarTypeAsString()
        
        if scalarType=="unsigned char":
            ImageType = itk.VTKImageToImageFilter.IUC3
        elif scalarType == "unsigned int":
            conv = vtk.vtkImageCast()
            conv.SetInput(image)        
            ImageType = itk.VTKImageToImageFilter.IUL3
            conv.SetOutputScalarTypeToUnsignedLong ()
            image = conv.GetOutput()
        
        self.vtkToItk = ImageType.New()
        
        #if self.prevFilter and self.prevFilter.getITK():
        #    return image
        if cast:            
            icast = vtk.vtkImageCast()
            if cast==types.FloatType:
                icast.SetOutputScalarTypeToFloat()
            icast.SetInput(image)
            image = icast.GetOutput()
        self.vtkToItk.SetInput(image)
        self.vtkToItk.Update()
        return self.vtkToItk.GetOutput()
            
            
    def convertITKtoVTK(self,image,cast=None,imagetype = "UC3",force=0):
        """
        Created: 18.04.2006, KP
        Description: Convert the image data to ITK image
        """  
        # For non-ITK images, do nothing
        if image.__class__ == vtk.vtkImageData:
#        if not force and self.prevFilter and not self.prevFilter.getITK() and not self.getITK():
            return image
        
        #if not self.itkToVtk:            
        #    c=eval("itk.Image.%s"%imagetype)
        #    self.itkToVtk = itk.ImageToVTKImageFilter[c].New()
        del self.itkToVtk
        self.itkToVtk = itk.ImageToVTKImageFilter[image].New()
        # If the next filter is also an ITK filter, then won't
        # convert
        if not force and self.nextFilter and self.nextFilter.getITK():
            print "NEXT FILTER IS ITK"
            return image
        self.itkToVtk.SetInput(image)
        self.itkToVtk.Update()
        return self.itkToVtk.GetOutput()        
        
    def setNextFilter(self,nfilter):
        """
        Created: 18.04.2006, KP
        Description: Set the next filter in the chain
        """        
        self.nextFilter = nfilter        
    
    def setPrevFilter(self,pfilter):
        """
        Created: 18.04.2006, KP
        Description: Set the previous filter in the chain
        """        
        self.prevFilter = pfilter
        
    def getITK(self):
        """
        Created: 18.04.2006, KP
        Description: Return whether this filter is working on ITK side of the pipeline
        """
        return self.itkFlag
        
    def getInput(self,n):
        """
        Created: 17.04.2006, KP
        Description: Return the input imagedata #n
        """             
        print "input mapping=",self.inputMapping
        print "n=",n
        if n not in self.inputMapping:
            self.inputMapping[n]=n-1
        if self.inputMapping[n]==0:        
            print "Using input%d from stack as input %d"%(n-1,n)
            image = self.inputs[self.inputIndex]
            self.inputIndex+=1
        else:
            print "Using input from channel %d as input %d"%(self.inputMapping[n]-1,n)
            image = self.getInputFromChannel(self.inputMapping[n]-1)
        return image
        
    def getInputFromChannel(self,n, timepoint=-1):
        """
        Created: 17.04.2006, KP
        Description: Return an imagedata object that is the current timepoint for channel #n
        """             
        if not self.sourceUnits:
            self.sourceUnits = self.dataUnit.getSourceDataUnits()
        tp=bxd.visualizer.getTimepoint()
        if bxd.processingTimepoint != -1:
            tp = bxd.processingTimepoint
        if timepoint!=-1:
            tp=timepoint
        print "RETURNING TIMEPOINT %d AS SOURCE"%tp
        return self.sourceUnits[n].getTimePoint(tp)
        
    def getNumberOfInputs(self):
        """
        Created: 17.04.2006, KP
        Description: Return the number of inputs required for this filter
        """             
        return self.numberOfInputs
        
    def setInputChannel(self,inputNum,chl):
        """
        Created: 17.04.2006, KP
        Description: Set the input channel for input #inputNum
        """            
        self.inputMapping[inputNum] = chl
        
    def getInputName(self,n):
        """
        Created: 17.04.2006, KP
        Description: Return the name of the input #n
        """          
        return "Source dataset %d"%n
        
    def getEnabled(self):
        """
        Created: 13.04.2006, KP
        Description: Return whether this filter is enabled or not
        """                   
        return self.enabled
        
    def setDataUnit(self,du):
        """
        Created: 15.04.2006, KP
        Description: Set the dataunit that is the input of this filter
        """                   
        self.dataUnit = du
        
    def getDataUnit(self):
        """
        Created: 15.04.2006, KP
        Description: return the dataunit
        """                           
        return self.dataUnit

    def setEnabled(self,flag):
        """
        Created: 13.04.2006, KP
        Description: Set whether this filter is enabled or not
        """                   
        print "Setting ",self,"to enabled=",flag
        self.enabled = flag     
    
        
    def getGUI(self,parent,taskPanel):
        """
        Created: 13.04.2006, KP
        Description: Return the GUI for this filter
        """              
        self.taskPanel = taskPanel
        if not self.gui:
            self.gui = GUIBuilder.GUIBuilder(parent,self)
        return self.gui
            
    @classmethod            
    def getName(s):
        """
        Created: 13.04.2006, KP
        Description: Return the name of the filter
        """        
        return s.name
        
    @classmethod
    def getCategory(s):
        """
        Created: 13.04.2006, KP
        Description: Return the category this filter should be classified to 
        """                
        return s.category
        

    def execute(self,inputs):
        """
        Created: 13.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """          
        self.inputIndex = 0
        n=len(inputs)
        self.inputs = inputs
        return 1
        if n< self.numberOfInputs[0] or (self.numberOfInputs[1]!=-1 and n>self.numberOfInputs[1]):
            messenger.send(None,"show_error","Bad number of inputs to filter","Filter %s was given a wrong number of inputs"%self.name)
            return 0
        return 1
