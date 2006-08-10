#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationFilters
 Project: BioImageXD
 Created: 13.04.2006, KP
 Description:

 A module containing classes representing the filters available in ManipulationPanelC
                            
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

class IntensityMeasurementList(wx.ListCtrl):
    def __init__(self, parent, log):
        wx.ListCtrl.__init__(
            self, parent, -1, 
            size = (350,250),
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES,
            
            )

        self.measurements =[]
        self.InsertColumn(0, "ROI")
        self.InsertColumn(1, "# of voxels")
        self.InsertColumn(2, "Tot. int.")
        self.InsertColumn(3,"Avg. int.")
        #self.InsertColumn(2, "")
        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 100)
        self.SetColumnWidth(3, 100)

        self.SetItemCount(1000)

        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour("white")

        self.attr2 = wx.ListItemAttr()
        self.attr2.SetBackgroundColour("light blue")
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
#        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        #self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def setMeasurements(self, measurements):
        self.measurements = measurements
        
    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex

        
    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnGetItemText(self, item, col):
        
        
        if item>=len(self.measurements):
            return ""
        m = self.measurements[item]
        
        if col==0:
            return "%s"%m[0]
        elif col==3:
            return "%.2f"%m[3]
        return "%d"%m[col]

    def OnGetItemImage(self, item):
         return -1

    def OnGetItemAttr(self, item):
        if item % 2 == 1:
            return self.attr1
        elif item % 2 == 0:
            return self.attr2
        else:
            return None


def getFilterList():
    return [ErodeFilter,DilateFilter,RangeFilter,SobelFilter,
            MedianFilter,AnisotropicDiffusionFilter,SolitaryFilter,
            ShiftScaleFilter,AddFilter,SubtractFilter,MultiplyFilter,
            DivideFilter,SinFilter,CosFilter,LogFilter,ExpFilter,SQRTFilter,
            GradientFilter,GradientMagnitudeFilter,
            AndFilter,OrFilter,XorFilter,NotFilter,NandFilter,NorFilter,
            ThresholdFilter,VarianceFilter,HybridMedianFilter,
            ITKAnisotropicDiffusionFilter,ITKGradientMagnitudeFilter,
            ITKWatershedSegmentationFilter, MorphologicalWatershedSegmentationFilter,MeasureVolumeFilter,
            ITKRelabelImageFilter,FilterObjectsFilter,ITKConnectedThresholdFilter,ITKNeighborhoodConnectedThresholdFilter,
            ITKLocalMaximumFilter,ITKOtsuThresholdFilter,ITKConfidenceConnectedFilter,
            MaskFilter,ITKSigmoidFilter, ITKInvertIntensityFilter, ConnectedComponentFilter,
            MaximumObjectsFilter,TimepointCorrelationFilter,
            ROIIntensityFilter]
            
MATH="Math"
SEGMENTATION="Segmentation"
FILTERING="Filtering"
ITK="ITK"
MEASUREMENT="Measurements"
REGION_GROWING="Region Growing"
   
class ManipulationFilter(GUIBuilder.GUIBuilderBase):
    """
    Class: ManipulationFilter
    Created: 13.04.2006, KP
    Description: A base class for manipulation filters
    """ 
    category = "No category"
    name = "Generic Filter"
    def __init__(self,numberOfInputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """
        self.taskPanel = None                
        GUIBuilder.GUIBuilderBase.__init__(self, changeCallback = self.notifyTaskPanel)

        self.numberOfInputs = numberOfInputs
        
        self.parameters = {}
        self.gui = None
        self.dataUnit = None
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
                setval=str(value)
                setoldval=str(oldval)
            do_cmd="bxd.mainWindow.tasks['Process'].%s.set('%s',%s)"%(func,parameter,setval)
            if setoldval:
                undo_cmd="bxd.mainWindow.tasks['Process'].%s.set('%s',%s)"%(func,parameter,setoldval)
            else:
                undo_cmd=""
            cmd=Command.Command(Command.PARAM_CMD,None,None,do_cmd,undo_cmd,desc="Change parameter '%s' of filter '%s'"%(parameter,self.name))
            cmd.run(recordOnly = 1)          
            
        print "\n\nSetting ",parameter,"to",value
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
        
        if self.prevFilter and self.prevFilter.getITK():
            return image
        if cast:            
            icast = vtk.vtkImageCast()
            if cast==types.FloatType:
                icast.SetOutputScalarTypeToFloat()
            icast.SetInput(image)
            image = icast.GetOutput()
        self.vtkToItk.SetInput(image)
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
        self.itkToVtk = itk.ImageToVTKImageFilter[image].New()
        # If the next filter is also an ITK filter, then won't
        # convert
        if not force and self.nextFilter and self.nextFilter.getITK():
            print "NEXT FILTER IS ITK"
            return image
        self.itkToVtk.SetInput(image)
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
        if n not in self.inputMapping:
            self.inputMapping[n]=0
        if self.inputMapping[n]==0:        
            print "Using input%d from stack as input %d"%(n-1,n)
            image = self.inputs[self.inputIndex]
            self.inputIndex+=1
        else:
            print "Using input from channel %d as input %d"%(self.inputMapping[n]-1,n)
            image = self.getInputFromChannel(self.inputMapping[n]-1)
        return image
        
    def getInputFromChannel(self,n):
        """
        Created: 17.04.2006, KP
        Description: Return an imagedata object that is the current timepoint for channel #n
        """             
        if not self.sourceUnits:
            self.sourceUnits = self.dataUnit.getSourceDataUnits()
        return self.sourceUnits[n].getTimePoint(self.taskPanel.timePoint)
        
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

        

class AnisotropicDiffusionFilter(ManipulationFilter):
    """
    Class: Anisotropic diffusion
    Created: 13.04.2006, KP
    Description: An edge preserving smoothing filter
    """     
    name = "Anisotropic Diffusion 3D"
    category = FILTERING
    
    def __init__(self):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageAnisotropicDiffusion3D()
        self.descs={"Faces":"Faces","Corners":"Corners","Edges":"Edges",
            "CentralDiff":"Central Difference","Gradient":"Gradient to Neighbor",
                "DiffThreshold":"Diffusion Threshold:","DiffFactor":"Diffusion Factor:"}
    
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [ 
        "Neighborhood:",["",( ("Faces","Corners","Edges"), )],
        "Threshold:",["Gradient measure",( ("CentralDiff","Gradient"),("cols",2)) ],
        ["",("DiffThreshold","DiffFactor")]
        ]
        
    def getDesc(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return a long description of the parameter
        """     
        if parameter == "Faces":
            return "Toggle whether the 6 voxels adjoined by faces are included in the neighborhood."
        elif parameter == "Corners":
            return "Toggle whether the 8 corner connected voxels are included in the neighborhood."
        elif parameter == "Edges":
            return "Toggle whether the 12 edge connected voxels are included in the neighborhood."
        return ""
        
    def getType(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Faces","Edges","Corners"]:
            return types.BooleanType
        elif parameter in ["CentralDiff","Gradient"]:
            return GUIBuilder.RADIO_CHOICE
        return types.FloatType
        
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter in ["Faces","Edges","Corners"]:
            return 1
        elif parameter == "DiffThreshold":
            return 5.0
        elif parameter == "DiffFactor":
            return 1.0
        return 2
        

    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        image = self.getInput(1)
        self.vtkfilter.SetInput(image)
        
        self.vtkfilter.SetDiffusionThreshold(self.parameters["DiffThreshold"])
        self.vtkfilter.SetDiffusionFactor(self.parameters["DiffFactor"])
        self.vtkfilter.SetFaces(self.parameters["Faces"])
        self.vtkfilter.SetEdges(self.parameters["Edges"])
        self.vtkfilter.SetCorners(self.parameters["Corners"])
        self.vtkfilter.SetGradientMagnitudeThreshold(self.parameters["CentralDiff"])
        
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()      

class SolitaryFilter(ManipulationFilter):
    """
    Created: 13.04.2006, KP
    Description: A filter for removing solitary noise pixels
    """     
    name = "Solitary filter"
    category = FILTERING
    
    def __init__(self):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageSolitaryFilter()
        self.descs={"HorizontalThreshold":"X:","VerticalThreshold":"Y:","ProcessingThreshold":"Processing threshold:"}
    
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [ "Thresholds:",["",("HorizontalThreshold","VerticalThreshold","ProcessingThreshold")]]
        
    def getDesc(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return a long description of the parameter
        """ 
        Xhelp="Threshold that a pixel's horizontal neighbor needs to be over so that the pixel is not removed."
        Yhelp="Threshold that a pixel's vertical neighbor needs to be over so that the pixel is not removed."
        Thresholdhelp="Threshold that a pixel needs to be over to get processed by solitary filter."
        
        if parameter == "HorizontalThreshold":
            return Xhelp
        elif parameter == "VerticalThreshold":
            return Yhelp
        elif parameter == "ProcessingThreshold":
            return Thresholdhelp
        return ""
        
        
    def getType(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["HorizontalThreshold","VerticalThreshold","ProcessingThreshold"]:
            return types.IntType
        
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """     
        return 0
        

    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        image = self.getInput(1)
        self.vtkfilter.SetInput(image)
        
        self.vtkfilter.SetFilteringThreshold(self.parameters["ProcessingThreshold"])
        self.vtkfilter.SetHorizontalThreshold(self.parameters["HorizontalThreshold"])
        self.vtkfilter.SetVerticalThreshold(self.parameters["VerticalThreshold"])
        
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()      

class ShiftScaleFilter(ManipulationFilter):
    """
    Class: SolitaryFilter
    Created: 13.04.2006, KP
    Description: A filter for shifting the values of dataset by constant and scaling by a constant
    """     
    name = "Shift and Scale"
    category = MATH
    
    def __init__(self):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageShiftScale()
        self.descs={"Shift":"Shift:","Scale":"Scale:","AutoScale":"Scale to range 0-255"}
    
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Shift","Scale","AutoScale")]]
        
    def getDesc(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return a long description of the parameter
        """ 
        return ""
        
        
    def getType(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Shift","Scale"]:
            return types.FloatType
        elif parameter == "AutoScale":
            return types.BooleanType
        
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter in ["Shift","Scale"]:
            return 0
        return 1
        

    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        image = self.getInput(1)
        #print "Using ",image
        self.vtkfilter.SetInput(image)
        if self.parameters["AutoScale"]:
            x,y=image.GetScalarRange()
            print "image type=",image.GetScalarTypeAsString()
            print "Range of data=",x,y
            self.vtkfilter.SetOutputScalarTypeToUnsignedChar()
            if not y:
                messenger.send(None,"show_error","Bad scalar range","Data has scalar range of %d -%d"%(x,y))
                return vtk.vtkImageData()
            scale = 255.0 / y
            print "Scale=",scale
            self.vtkfilter.SetShift(0)
            self.vtkfilter.SetScale(scale)
        else:
            self.vtkfilter.SetShift(self.parameters["Shift"])
            self.vtkfilter.SetScale(self.parameters["Scale"])
        
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()    
        
        
        

class TimepointCorrelationFilter(ManipulationFilter):
    """
    Created: 31.07.2006, KP
    Description: A filter for calculating the correlation between two timepoints
    """     
    name = "Timepoint Correlation"
    category = MEASUREMENT
    
    def __init__(self):
        """
        Created: 31.07.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageAutoThresholdColocalization()
        self.box=None
        self.descs={"Timepoint1":"First timepoint:","Timepoint2":"Second timepoint:"}
    
    def getParameters(self):
        """
        Created: 31.07.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Timepoint1","Timepoint2")]]
        
    def getGUI(self,parent,taskPanel):
        """
        Created: 31.07.2006, KP
        Description: Return the GUI for this filter
        """              
        gui = ManipulationFilters.ManipulationFilter.getGUI(self,parent,taskPanel)
        if not self.box:
            
            self.corrLbl=wx.StaticText(gui,-1,"Correlation:")
            self.corrLbl2 = wx.StaticText(gui,-1,"0.0")
            box=wx.BoxSizer(wx.HORIZONTAL)
            box.Add(self.corrLbl)
            box.Add(self.corrLbl2)
            self.box=box
            gui.sizer.Add(box,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        return gui
        
        
    def getType(self,parameter):
        """
        Created: 31.07.2006, KP
        Description: Return the type of the parameter
        """    
        return GUIBuilder.SLICE
        
    def getDefaultValue(self,parameter):
        """
        Created: 31.07.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter=="Timepoint1":
            return 0
        return 1
        
        
    def getRange(self, parameter):
        """
        Created: 31.07.2006, KP
        Description: Return the range for the parameter
        """             
        return (0,self.dataUnit.getLength())

    def execute(self,inputs,update=0,last=0):
        """
        Created: 31.07.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        tp1=self.parameters["Timepoint1"]
        tp2=self.parameters["Timepoint2"]
        units=self.dataUnit.getSourceDataUnits()
        data1=units[0].getTimePoint(tp1)
        # We need to prepare a copy of the data since
        # when we get the next timepoint, the data we got earlier will reference the
        # new data
        tp = vtk.vtkImageData()
        tp.DeepCopy(data1)
        data2=units[0].getTimePoint(tp2)
        data1=tp
        
        self.vtkfilter.AddInput(data1)
        self.vtkfilter.AddInput(data2)
        # Set the thresholds so they won't be calculated
        self.vtkfilter.SetLowerThresholdCh1(0)
        self.vtkfilter.SetLowerThresholdCh2(0)
        self.vtkfilter.SetUpperThresholdCh1(255)
        self.vtkfilter.SetUpperThresholdCh2(255)
       
        #print "Using ",image
        
        
        self.vtkfilter.Update()
        self.corrLbl2.SetLabel("%.5f"%self.vtkfilter.GetPearsonWholeImage())
        return self.getInput(1)
        
        
class ROIIntensityFilter(ManipulationFilter):
    """
    Created: 04.08.2006, KP
    Description: A filter for calculating the volume, total and average intensity of a ROI
    """     
    name = "ROI Measurements"
    category = MEASUREMENT
    
    def __init__(self):
        """
        Created: 31.07.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageAutoThresholdColocalization()
        self.reportGUI=None
        self.measurements =[]
        self.descs={"ROI":"Region of Interest","AllROIs":"Measure all ROIs"}
    
    def getParameters(self):
        """
        Created: 31.07.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("ROI","AllROIs")]]
        
        
    def getGUI(self,parent,taskPanel):
        """
        Created: 31.07.2006, KP
        Description: Return the GUI for this filter
        """              
        gui = ManipulationFilters.ManipulationFilter.getGUI(self,parent,taskPanel)
        if not self.reportGUI:
            self.reportGUI = IntensityMeasurementList(self.gui,-1)
            if self.measurements:
                self.reportGUI.setMeasurements(self.measurements)
                
            gui.sizer.Add(self.reportGUI,(1,0),flag=wx.EXPAND|wx.ALL)
            
        return gui
        
        
    def getType(self,parameter):
        """
        Created: 31.07.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter=="ROI":
            return GUIBuilder.ROISELECTION
        return types.BooleanType
        
    def getDefaultValue(self,parameter):
        """
        Created: 31.07.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter=="ROI":
            n=bxd.visualizer.getRegionsOfInterest()
            if n:return n[0]
            return 0
        return 0
        
    def execute(self,inputs,update=0,last=0):
        """
        Created: 31.07.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        
        if not self.parameters["AllROIs"]:
            rois = [self.parameters["ROI"]]
        else:
            rois=bxd.visualizer.getRegionsOfInterest()
            print rois
        imagedata =  self.getInput(1)

        
        mx, my, mz = self.dataUnit.getDimensions()
        values = []
        for mask in rois:
            if not mask:
                print "No mask"
                return imagedata
            print "Processing mask=",mask
            maskImage = ImageOperations.getMaskFromROIs([mask],mx,my,mz)
            maskhistogram = ImageOperations.get_histogram(maskImage)
            n = sum(maskhistogram[1:])
            maskFilter = vtk.vtkImageMask()
            maskFilter.SetMaskedOutputValue(0)
            maskFilter.SetMaskInput(maskImage)
            maskFilter.SetImageInput(imagedata)
            maskFilter.Update()
            data = maskFilter.GetOutput()
            #mip=vtk.vtkImageSimpleMIP()
            #mip.SetInput(data)
            #w=vtk.vtkPNGWriter()
            #w.SetFileName("%s.png"%mask.getName())
            #w.SetInput(mip.GetOutput())
            #w.Write()
            histogram = ImageOperations.get_histogram(data)
            #n = sum(histogram)
            totint=0
            for i,x in enumerate(histogram):
                totint+=i*x
            
            avgint = totint/float(n)
            values.append((mask.getName(),n,totint,avgint))
        if self.reportGUI:
            self.reportGUI.setMeasurements(values)
            self.reportGUI.Refresh()
        self.measurements = values
        return imagedata
        
class GradientFilter(ManipulationFilter):
    """
    Created: 13.04.2006, KP
    Description: A class for calculating the gradient of the image
    """     
    name = "Gradient"
    category = MATH
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageGradient()
        self.vtkfilter.SetDimensionality(3)
    
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return []

    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        self.vtkfilter.SetInput(self.getInput(1))
            
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()            

class GradientMagnitudeFilter(ManipulationFilter):
    """
    Created: 13.04.2006, KP
    Description: A class for calculating the gradient magnitude of the image
    """     
    name = "Gradient Magnitude"
    category = MATH
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageGradientMagnitude()
        self.vtkfilter.SetDimensionality(3)
    
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return []

    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        self.vtkfilter.SetInput(self.getInput(1))
            
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()            


        
class ITKAnisotropicDiffusionFilter(ManipulationFilter):
    """
    Class: ITKAnisotropicDiffusionFilterFilter
    Created: 13.04.2006, KP
    Description: A class for doing anisotropic diffusion on ITK
    """     
    name = "Gradient Anisotropic Diffusion"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """

        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"TimeStep":"Time step for iterations","Conductance":"Conductance parameter",
            "Iterations":"Number of iterations"}
        self.itkFlag = 1
        self.itkfilter = None

            
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "TimeStep":
            return 0.0630
        if parameter == "Conductance":
            return 9.0
        if parameter == "Iterations":
            return 5
        return 0
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["TimeStep","Conductance"]:
            return types.FloatType
        return types.IntType
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("TimeStep","Conductance","Iterations")]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image,cast=types.FloatType)
        
        self.itkfilter = itk.GradientAnisotropicDiffusionImageFilter[f3,f3].New()

        self.itkfilter.SetInput(image)
        self.itkfilter.SetTimeStep(self.parameters["TimeStep"])
        self.itkfilter.SetConductanceParameter(self.parameters["Conductance"])
        self.itkfilter.SetNumberOfIterations(self.parameters["Iterations"])
        
        if update:
            self.itkfilter.Update()
        return self.itkfilter.GetOutput()            

class ITKGradientMagnitudeFilter(ManipulationFilter):
    """
    Class: ITKGradientMagnitudeFilter
    Created: 13.04.2006, KP
    Description: A class for calculating gradient magnitude on ITK
    """     
    name = "ITK Gradient Magnitude"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.itkFlag = 1
        self.itkfilter = None
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return []        

    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image)
        if not self.itkfilter:
            self.itkfilter = itk.GradientMagnitudeImageFilter[image, image].New()

        self.itkfilter.SetInput(image)
        
        #self.setImageType("F3")
        
        if update:
            self.itkfilter.Update()
        data = self.itkfilter.GetOutput()
        #if last or self.nextFilter and not self.nextFilter.getITK():            
        #    print "Converting to VTK"
        #    data=self.convertITKtoVTK(data,imagetype="F3")
        #    print "data=",data
        return data            

class ITKSigmoidFilter(ManipulationFilter):
    """
    Class: ITKSigmoidFilter
    Created: 29.05.2006, KP
    Description: A class for mapping an image data thru sigmoid image filter
    """     
    name = "ITK Sigmoid Filter"
    category = FILTERING
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.itkFlag = 1
        self.descs = {"Minimum":"Minimum output value","Maximum":"Maximum Output Value","Alpha":"Alpha","Beta":"Beta"}
        f3=itk.Image.F3
        self.itkfilter = itk.SigmoidImageFilter[f3,f3].New()
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Data range",("Minimum","Maximum")],
        ]        
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "Minimum":
            return 0.0
        if parameter == "Maximum":
            return 1.0
        if parameter== "Alpha":
            return 
        return 0
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.FloatType


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image,cast=types.FloatType)
        self.itkfilter.SetInput(image)
        
        self.setImageType("F3")
        
        if update:
            self.itkfilter.Update()
        data = self.itkfilter.GetOutput()
        #if last or self.nextFilter and not self.nextFilter.getITK():            
        #    print "Converting to VTK"
        #    data=self.convertITKtoVTK(data,imagetype="F3")
        #    print "data=",data
        return data            




class ITKLocalMaximumFilter(ManipulationFilter):
    """
    Class: ITKLocalMaximumFilter
    Created: 29.05.2006, KP
    Description: A class for finding the local maxima in an image
    """     
    name = "Find Local Maxima"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 26.05.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"Connectivity":"Use 8 neighbors for connectivity"}
        self.itkFlag = 1
        

            
    def getDefaultValue(self,parameter):
        """
        Created: 26.05.2006, KP
        Description: Return the default value of a parameter
        """   
        if parameter == "Connectivity":
            return 1
        return 0
    def getType(self,parameter):
        """
        Created: 26.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Connectivity"]:
            return types.BooleanType
                
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Connectivity",)]]

    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
#        print "Using as input",image
        image = self.convertVTKtoITK(image)
        
        
        uc3 = itk.Image.UC3
        shift = itk.ShiftScaleImageFilter[uc3,uc3].New()
        recons = itk.ReconstructionByDilationImageFilter[uc3,uc3].New()
        subst = itk.SubtractImageFilter[uc3,uc3,uc3].New()
        shift.SetInput(image)
        shift.SetShift(-1)
        recons.SetMaskImage(image)
        recons.SetMarkerImage(shift.GetOutput())
        recons.SetFullyConnected(self.parameters["Connectivity"])
        
        subst.SetInput1(image)
        subst.SetInput2(recons.GetOutput())
        
        if update:
            subst.Update()
            
        data = subst.GetOutput()
#        if last:
#            return self.convertITKtoVTK(data,imagetype="UC3")
            
        return data            

from MathFilters import *
from SegmentationFilters import *
from MorphologicalFilters import *
