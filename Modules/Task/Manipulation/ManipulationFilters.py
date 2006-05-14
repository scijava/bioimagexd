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
import messenger
import scripting

import ManipulationGUI
import ImageOperations

def getFilterList():
    return [ErodeFilter,DilateFilter,RangeFilter,SobelFilter,
            MedianFilter,AnisotropicDiffusionFilter,SolitaryFilter,
            ShiftScaleFilter,AddFilter,SubtractFilter,MultiplyFilter,
            DivideFilter,SinFilter,CosFilter,LogFilter,ExpFilter,SQRTFilter,
            GradientFilter,
            AndFilter,OrFilter,XorFilter,NotFilter,NandFilter,NorFilter,
            ThresholdFilter,VarianceFilter,HybridMedianFilter,MaskFilter,
            ITKAnisotropicDiffusionFilter,ITKGradientMagnitudeFilter,
            ITKWatershedSegmentationFilter,MapToRGBFilter]
            
MORPHOLOGICAL="Morphological"
MATH="Math"
SEGMENTATION="Segmentation"
FILTERING="Filtering"
LOGIC="Logic"
ITK="ITK"

   
class ManipulationFilter:
    """
    Class: ManipulationFilter
    Created: 13.04.2006, KP
    Description: A base class for manipulation filters
    """ 
    category = "No category"
    name = "Generic Filter"
    def __init__(self,numberOfInputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """
        self.numberOfInputs = numberOfInputs
        self.taskPanel = None
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
        self.inputMapping = {}
        for item in self.getPlainParameters():
            self.setParameter(item,self.getDefaultValue(item))
        
        self.vtkToItk = None
        self.itkToVtk = None
        
    def setTaskPanel(self,p):
        """
        Method: setTaskPanel
        Created: 14.05.2006, KP
        Description: Set the task panel that controsl this filter
        """
        self.taskPanel = p
        
    def convertVTKtoITK(self,image,cast=None):
        """
        Method: convertVTKtoITK
        Created: 18.04.2006, KP
        Description: Convert the image data to ITK image
        """         
        if not self.itkFlag:
            messenger.send(None,"show_error","Non-ITK filter tries to convert to ITK","A non-ITK filter %s tried to convert data to ITK image data"%self.name)
            return image
        if not self.itkToVtk:
            if not scripting.ItkVtkGlue:
                scripting.loadITK()
        if not self.vtkToItk:            
            ImageType = scripting.ItkVtkGlue.ImageToVTKImageFilter.IUC3
            if cast==types.FloatType:
                ImageType = scripting.ItkVtkGlue.VTKImageToImageFilter.IF3
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
            
            
    def convertITKtoVTK(self,image,cast=None,imagetype = "UC3"):
        """
        Method: convertITKtoVTK
        Created: 18.04.2006, KP
        Description: Convert the image data to ITK image
        """  
        # For non-ITK images, do nothing
        if not self.prevFilter.getITK():
            return image
        if not self.itkToVtk:
            if not scripting.ItkVtkGlue:
                scripting.loadITK()            
        
        if not self.itkToVtk:            
            #ImageType = scripting.ITKCommonA.Image[PixelType, dim]
            
            c=eval("scripting.ITKCommonA.Image.%s"%imagetype)
            #self.itkToVtk = scripting.ItkVtkGlue.ImageToVTKImageFilter[scripting.ITKCommonA.Image.UC3].New()
            self.itkToVtk = scripting.ItkVtkGlue.ImageToVTKImageFilter[c].New()
        # If the next filter is also an ITK filter, then won't
        # convert
        if self.nextFilter and self.nextFilter.getITK():
            return image
        self.itkToVtk.SetInput(image)
        return self.itkToVtk.GetOutput()
        
        
        
        
    def setNextFilter(self,nfilter):
        """
        Method: setNextFilter
        Created: 18.04.2006, KP
        Description: Set the next filter in the chain
        """        
        self.nextFilter = nfilter        
    
    def setPrevFilter(self,pfilter):
        """
        Method: setNextFilter
        Created: 18.04.2006, KP
        Description: Set the previous filter in the chain
        """        
        self.prevFilter = pfilter
        
    def getITK(self):
        """
        Method: isInITK
        Created: 18.04.2006, KP
        Description: Return whether this filter is working on ITK side of the pipeline
        """
        return self.itkFlag
        
    def getPlainParameters(self):
        """
        Method: getPlainParameters
        Created: 15.04.2006, KP
        Description: Return whether this filter is enabled or not
        """
        ret=[]
        for item in self.getParameters():
            # If it's a label
            if type(item)==types.StringType:
                continue
            elif type(item)==types.ListType:
                title,items=item
                if type(items[0]) == types.TupleType:
                    items=items[0]
                ret.extend(items)
        return ret
        
    def getInput(self,n):
        """
        Method: getInput
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
        Method: getInputFromChannel
        Created: 17.04.2006, KP
        Description: Return an imagedata object that is the current timepoint for channel #n
        """             
        if not self.sourceUnits:
            self.sourceUnits = self.dataUnit.getSourceDataUnits()
        return self.sourceUnits[n].getTimePoint(self.taskPanel.timePoint)
        
    def getNumberOfInputs(self):
        """
        Method: getNumberOfInputs
        Created: 17.04.2006, KP
        Description: Return the number of inputs required for this filter
        """             
        return self.numberOfInputs
        
    def setInputChannel(self,inputNum,chl):
        """
        Method: setInputChannel
        Created: 17.04.2006, KP
        Description: Set the input channel for input #inputNum
        """            
        self.inputMapping[inputNum] = chl
        
    def getInputName(self,n):
        """
        Method: getInputName
        Created: 17.04.2006, KP
        Description: Return the name of the input #n
        """          
        return "Source dataset %d"%n
        
    def getEnabled(self):
        """
        Method: getEnabled
        Created: 13.04.2006, KP
        Description: Return whether this filter is enabled or not
        """                   
        return self.enabled
        
    def setDataUnit(self,du):
        """
        Method: setDataUnit
        Created: 15.04.2006, KP
        Description: Set the dataunit that is the input of this filter
        """                   
        self.dataUnit = du
        
    def getDataUnit(self):
        """
        Method: getDataUnit
        Created: 15.04.2006, KP
        Description: return the dataunit
        """                           
        return self.dataUnit

    def setEnabled(self,flag):
        """
        Method: setEnabled
        Created: 13.04.2006, KP
        Description: Set whether this filter is enabled or not
        """                   
        print "Setting ",self,"to enabled=",flag
        self.enabled = flag     
    
        
    def getGUI(self,parent,taskPanel):
        """
        Method: getGUI
        Created: 13.04.2006, KP
        Description: Return the GUI for this filter
        """              
        self.taskPanel = taskPanel
        if not self.gui:
            self.gui = ManipulationGUI.GUIBuilder(parent,self)
        return self.gui
            
    @classmethod            
    def getName(s):
        """
        Method: getName
        Created: 13.04.2006, KP
        Description: Return the name of the filter
        """        
        return s.name
        
    @classmethod
    def getCategory(s):
        """
        Method: getCategory
        Created: 13.04.2006, KP
        Description: Return the category this filter should be classified to 
        """                
        return s.category
        
    def setParameter(self,parameter,value):
        """
        Method: setParameter
        Created: 13.04.2006, KP
        Description: Set a value for the parameter
        """    
        self.parameters[parameter]=value
        if self.taskPanel:
            self.taskPanel.filterModified(self)
        
    def execute(self,inputs):
        """
        Method: execute
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
        
    def getDesc(self,parameter):
        """
        Method: getDesc
        Created: 13.04.2006, KP
        Description: Return the description of the parameter
        """    
        try:
            return self.descs[parameter]
        except:            
            return ""
        
    def getLongDesc(self,parameter):
        """
        Method: getLongDesc
        Created: 13.04.2006, KP
        Description: Return the long description of the parameter
        """    
        return ""
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 13.04.2006, KP
        Description: Return the default value of a parameter
        """           
        return 0
        
        
class MorphologicalFilter(ManipulationFilter):
    """
    Class: ManipulationFilter
    Created: 13.04.2006, KP
    Description: A base class for manipulation filters
    """     
    name = "Morphological filter"
    category = MORPHOLOGICAL
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
    
        self.descs={"KernelX":"X","KernelY":"Y","KernelZ":"Z"}
    
    def getParameters(self):
        """
        Method: getParameters
        Created: 13.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [ ["Convolution kernel",("KernelX","KernelY","KernelZ")] ]
        
    def getDesc(self,parameter):
        """
        Method: getDesc
        Created: 13.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 13.04.2006, KP
        Description: Return the default value of a parameter
        """           
        return 2
        

    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 13.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        x,y,z=self.parameters["KernelX"],self.parameters["KernelY"],self.parameters["KernelZ"]
        self.vtkfilter.SetKernelSize(x,y,z)
        
        image = self.getInput(1)
          
        print "Setting input=",image  
        self.vtkfilter.SetInput(image)
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()                
        
class ErodeFilter(MorphologicalFilter):
    """
    Class: ErodeFilter
    Created: 13.04.2006, KP
    Description: An erosion filter
    """     
    name = "Erode 3D"
    category = MORPHOLOGICAL
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageContinuousErode3D()
        
class VarianceFilter(MorphologicalFilter):
    """
    Class: VarianceFilter
    Created: 13.04.2006, KP
    Description: An erosion filter
    """     
    name = "Variance 3D"
    category = MORPHOLOGICAL
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageVariance3D()        
        
class DilateFilter(MorphologicalFilter):
    """
    Class: DilateFilter
    Created: 13.04.2006, KP
    Description: A dilation filter
    """      
    name = "Dilate 3D"
    category = MORPHOLOGICAL
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageContinuousDilate3D()  
  
class RangeFilter(MorphologicalFilter):
    """
    Class: RangeFilter
    Created: 13.04.2006, KP
    Description: A filter that sets the value of the neighborhood to be the max-min of that nbh
    """     
    name = "Range 3D"
    category = MORPHOLOGICAL
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageRange3D()     
        
class SobelFilter(MorphologicalFilter):
    """
    Class: MedianFilter
    Created: 13.04.2006, KP
    Description: A median filter
    """     
    name = "Sobel 3D"
    category = MORPHOLOGICAL
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageSobel3D()          
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 13.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """  
        return []
        
    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 13.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None        
        image = self.getInput(1)
        self.vtkfilter.SetInput(image)
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()         
        
class HybridMedianFilter(MorphologicalFilter):
    """
    Class: HybridMedianFilter
    Created: 13.04.2006, KP
    Description: A 2D median filter that preserves edges and corners
    """     
    name = "Hybrid Median 2D"
    category = FILTERING
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageHybridMedian2D()        
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 13.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """  
        return []
        
    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 13.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None        
        image = self.getInput(1)
        self.vtkfilter.SetInput(image)
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()         
        
        
class MedianFilter(MorphologicalFilter):
    """
    Class: MedianFilter
    Created: 13.04.2006, KP
    Description: A median filter
    """     
    name = "Median 3D"
    category = FILTERING
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageMedian3D()        

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
        Method: __init__()
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
        Method: getParameters
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
        Method: getDesc
        Created: 15.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Method: getLongDesc
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
        Method: getType
        Created: 15.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Faces","Edges","Corners"]:
            return types.BooleanType
        elif parameter in ["CentralDiff","Gradient"]:
            return ManipulationGUI.RADIO_CHOICE
        return types.FloatType
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
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
        Method: execute
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
    Class: SolitaryFilter
    Created: 13.04.2006, KP
    Description: A filter for removing solitary noise pixels
    """     
    name = "Solitary filter"
    category = FILTERING
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageSolitaryFilter()
        self.descs={"HorizontalThreshold":"X:","VerticalThreshold":"Y:","ProcessingThreshold":"Processing threshold:"}
    
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [ "Thresholds:",["",("HorizontalThreshold","VerticalThreshold","ProcessingThreshold")]]
        
    def getDesc(self,parameter):
        """
        Method: getDesc
        Created: 15.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Method: getLongDesc
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
        Method: getType
        Created: 15.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["HorizontalThreshold","VerticalThreshold","ProcessingThreshold"]:
            return types.IntType
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """     
        return 0
        

    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
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
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageShiftScale()
        self.descs={"Shift":"Shift:","Scale":"Scale:","AutoScale":"Scale to range 0-255"}
    
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Shift","Scale","AutoScale")]]
        
    def getDesc(self,parameter):
        """
        Method: getDesc
        Created: 15.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Method: getLongDesc
        Created: 15.04.2006, KP
        Description: Return a long description of the parameter
        """ 
        return ""
        
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 15.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Shift","Scale"]:
            return types.FloatType
        elif parameter == "AutoScale":
            return types.BooleanType
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter in ["Shift","Scale"]:
            return 0
        return 1
        

    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        image = self.getInput(1)
        self.vtkfilter.SetInput(image)
        if self.parameters["AutoScale"]:
            x,y=image.GetScalarRange()
            self.vtkfilter.SetOutputScalarTypeToUnsignedChar()
            if not y:
                messenger.send(None,"show_error","Bad scalar range","Data has scalar range of %d -%d"%(x,y))
                return vtk.vtkImageData()
            scale = 255.0 / y
            self.vtkfilter.SetShift(0)
            self.vtkfilter.SetScale(scale)
        else:
            self.vtkfilter.SetShift(self.parameters["Shift"])
            self.vtkfilter.SetScale(self.parameters["Scale"])
        
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()    
        
class ThresholdFilter(ManipulationFilter):
    """
    Class: ThresholdFilter
    Created: 15.04.2006, KP
    Description: A thresholding filter
    """     
    name = "Threshold"
    category = SEGMENTATION
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageThreshold()
        self.origCtf = None
        self.descs={"ReplaceInValue":"Value for voxels inside thresholds",
            "ReplaceOutValue":"Value for voxels outside thresholds",
            "ReplaceIn":"Inside Thresholds","ReplaceOut":"Outside Thresholds",
            "LowerThreshold":"Lower Threshold","UpperThreshold":"Upper Threshold",
            "Demonstrate":"Use lookup table to demonstrate effect"}
    
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Threshold",(("LowerThreshold","UpperThreshold"),)],
                ["Replace voxels",(("ReplaceIn","ReplaceOut"),)],
                ["",("ReplaceInValue",)],
                ["",("ReplaceOutValue",)],
                ["",("Demonstrate",)]
                ]
        
    def getDesc(self,parameter):
        """
        Method: getDesc
        Created: 15.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getLongDesc(self,parameter):
        """
        Method: getLongDesc
        Created: 15.04.2006, KP
        Description: Return a long description of the parameter
        """ 
        return ""
        
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 15.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["LowerThreshold","UpperThreshold"]:
            return ManipulationGUI.THRESHOLD
        elif parameter in ["ReplaceIn","ReplaceOut","Demonstrate"]:
            return types.BooleanType
        return types.IntType
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter == "LowerThreshold":
            return 0
        if parameter == "UpperThreshold":
            return 128
        if parameter == "ReplaceInValue":
            return 255
        if parameter == "ReplaceOutValue":
            return 0
        if parameter == "Demonstrate":
            return 0
        if parameter in ["ReplaceIn","ReplaceOut"]:
            return 1

    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        image = self.getInput(1)
        if not self.parameters["Demonstrate"]:
            if self.origCtf:
                self.dataUnit.getSettings().set("ColorTransferFunction",self.origCtf)
                if self.gui:
                    self.gui.histograms[0].setReplacementCTF(None)                
                    self.gui.histograms[0].updatePreview(renew=1)
            self.vtkfilter.SetInput(image)
            
            self.vtkfilter.ThresholdByLower(self.parameters["UpperThreshold"])
            self.vtkfilter.ThresholdByUpper(self.parameters["LowerThreshold"])
        
        
            self.vtkfilter.SetReplaceIn(self.parameters["ReplaceIn"])
            if self.parameters["ReplaceIn"]:
                self.vtkfilter.SetInValue(self.parameters["ReplaceInValue"])
            
            self.vtkfilter.SetReplaceOut(self.parameters["ReplaceOut"])
            if self.parameters["ReplaceOut"]:
                self.vtkfilter.SetOutValue(self.parameters["ReplaceOutValue"])
            
            if update:
                self.vtkfilter.Update()
            return self.vtkfilter.GetOutput()
        else:
            lower = self.parameters["LowerThreshold"]
            upper = self.parameters["UpperThreshold"]
            origCtf = self.dataUnit.getSourceDataUnits()[0].getColorTransferFunction()
            self.origCtf = self.dataUnit.getColorTransferFunction()
            ctf = vtk.vtkColorTransferFunction()
            ctf.AddRGBPoint(0,0,0,0.0)
            ctf.AddRGBPoint(lower,0, 0, 1.0)
            ctf.AddRGBPoint(lower+1, 0, 0, 0)
            val=[0,0,0]
            origCtf.GetColor(255,val)
            r,g,b=val
            ctf.AddRGBPoint(upper, r, g, b)
            ctf.AddRGBPoint(upper+1,0, 0, 0)
            ctf.AddRGBPoint(255, 1.0, 0, 0)
            self.dataUnit.getSettings().set("ColorTransferFunction",ctf)
            if self.gui:
                print "Replacing CTF"
                self.gui.histograms[0].setReplacementCTF(ctf)
                self.gui.histograms[0].updatePreview(renew=1)
                self.gui.histograms[0].Refresh()
            self.dataUnit
            return image
        
        
class MathFilter(ManipulationFilter):
    """
    Class: MathFilter
    Created: 13.04.2006, KP
    Description: A base class for image mathematics filters
    """     
    name = "Math filter"
    category = MATH
    
    def __init__(self,inputs=(2,2)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageMathematics()
    
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return []

    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            
            return None
        
        image = self.getInput(1)
       
        if self.numberOfInputs[0]>1:
            self.vtkfilter.SetInput1(image)
            self.vtkfilter.SetInput2(self.getInput(2))
        else:
            self.vtkfilter.SetInput1(image)
            self.vtkfilter.SetInput2(image)
            self.vtkfilter.SetInput(image)    
        f="self.vtkfilter.SetOperationTo%s()"%self.operation
        eval(f)
        
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput() 
        
class LogicFilter(MathFilter):
    """
    Class: MathFilter
    Created: 13.04.2006, KP
    Description: A base class for image mathematics filters
    """     
    name = "Logic filter"
    category = LOGIC
    
    def __init__(self,inputs=(2,2)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageLogic()
        self.vtkfilter.SetOutputTrueValue(255)
    
        
class AndFilter(LogicFilter):
    """
    Class: AndFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating logical and
    """     
    name = "And"
   
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        LogicFilter.__init__(self)
        self.operation = "And"    
        
class OrFilter(LogicFilter):
    """
    Class: OrFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating logical or
    """     
    name = "Or"
   
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        LogicFilter.__init__(self)
        self.operation = "Or"    
class XorFilter(LogicFilter):
    """
    Class: XorFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating logical xor
    """     
    name = "Xor"
   
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        LogicFilter.__init__(self)
        self.operation = "Xor"   
       
class NotFilter(LogicFilter):
    """
    Class: XorFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating logical not
    """     
    name = "Not"
                
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        LogicFilter.__init__(self,inputs=(1,1))
        self.operation = "Not"       
        
class NorFilter(LogicFilter):
    """
    Class: NorFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating logical nor
    """     
    name = "Nor"
   
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        LogicFilter.__init__(self)
        self.operation = "Nor"    
        
class NandFilter(LogicFilter):
    """
    Class: NandFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating logical nand
    """     
    name = "Nand"
   
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        LogicFilter.__init__(self)
        self.operation = "Nand"          
        
class SubtractFilter(MathFilter):
    """
    Class: SubtractFilter
    Created: 15.04.2006, KP
    Description: A filter for subtracting two channels
    """     
    name = "Subtract"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self)
        self.operation = "Subtract"

class AddFilter(MathFilter):
    """
    Class: AddFilter
    Created: 15.04.2006, KP
    Description: A filter for adding two channels
    """     
    name = "Add"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 15.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self)
        self.operation = "Add"
        
class DivideFilter(MathFilter):
    """
    Class: DivideFilter
    Created: 15.04.2006, KP
    Description: A filter for dividing two channels
    """     
    name = "Divide"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self)
        self.operation = "Divide"
        
class MultiplyFilter(MathFilter):
    """
    Class: MultiplyFilter
    Created: 15.04.2006, KP
    Description: A filter for multiplying two channels
    """     
    name = "Multiply"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self)
        self.operation = "Multiply"     
     
class SinFilter(MathFilter):
    """
    Class: SinFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating sine of input
    """     
    name = "Sin"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self,(1,1))
        self.operation = "Sin"        
     
class CosFilter(MathFilter):
    """
    Class: CosFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating cosine of input
    """     
    name = "Cos"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self,(1,1))
        self.operation = "Cos"   

class ExpFilter(MathFilter):
    """
    Class: ExpFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating exp of input
    """     
    name = "Exp"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self,(1,1))
        self.operation = "Exp" 
        
class LogFilter(MathFilter):
    """
    Class: LogFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating logarithm of input
    """     
    name = "Log"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self,(1,1))
        self.operation = "Log"    
   
class SQRTFilter(MathFilter):
    """
    Class: SQRTFilter
    Created: 15.04.2006, KP
    Description: A filter for calculating square root of input
    """     
    name = "Sqrt"
    category = MATH
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        MathFilter.__init__(self,(1,1))
        self.operation = "SquareRoot"   
            
        
        
class GradientFilter(ManipulationFilter):
    """
    Class: GradientFilter
    Created: 13.04.2006, KP
    Description: A class for calculating the gradient of the image
    """     
    name = "Gradient"
    category = MATH
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageGradient()
        self.vtkfilter.SetDimensionality(3)
    
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return []

    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,inputs):
            return None
        
        self.vtkfilter.SetInput(self.getInput(1))
            
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()            
        

class MaskFilter(ManipulationFilter):
    """
    Class: MaskFilter
    Created: 13.04.2006, KP
    Description: A base class for image mathematics filters
    """     
    name = "Mask"
    category = SEGMENTATION
    
    def __init__(self,inputs=(2,2)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageMask()
        
        self.descs = {"OutputValue":"Masked output value"}
            
    def getDesc(self,parameter):
        """
        Method: getDesc
        Created: 13.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
            
    def getInputName(self,n):
        """
        Method: getInputName
        Created: 17.04.2006, KP
        Description: Return the name of the input #n
        """          
        if n==1:
            return "Source dataset %d"%n    
        return "Mask dataset"
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        return 0
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("OutputValue",)]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
        self.vtkfilter.SetInput1(self.getInput(1))
        
        self.vtkfilter.SetInput2(self.getInput(2))
        self.vtkfilter.SetMaskedOutputValue(self.parameters["OutputValue"])
        
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
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"TimeStep":"Time step for iterations","Conductance":"Conductance parameter",
            "Iterations":"Number of iterations"}
        self.itkFlag = 1
        scripting.loadITK(filters=1)
        f3 = scripting.ITKCommonA.Image.F3
        self.itkfilter = scripting.ITKBasicFiltersA.GradientAnisotropicDiffusionImageFilter[f3,f3].New()

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
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
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["TimeStep","Conductance"]:
            return types.FloatType
        return types.IntType
        
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("TimeStep","Conductance","Iterations")]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image,cast=types.FloatType)
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
    name = "Gradient Magnitude"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.itkFlag = 1
        scripting.loadITK(filters=1)
        f3=scripting.ITKCommonA.Image.F3
        self.itkfilter = scripting.ITKBasicFiltersA.GradientMagnitudeImageFilter[f3,f3].New()
        
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return []


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image,cast=types.FloatType)
        self.itkfilter.SetInput(image)
        
        if update:
            self.itkfilter.Update()
        return self.itkfilter.GetOutput()            


class ITKWatershedSegmentationFilter(ManipulationFilter):
    """
    Class: ITKAnisotropicDiffusionFilterFilter
    Created: 13.04.2006, KP
    Description: A class for doing anisotropic diffusion on ITK
    """     
    name = "Watershed Segmentation"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"Threshold":"Segmentation Threshold","Level":"Segmentation level"}
        self.itkFlag = 1

        scripting.loadITK(filters=1)
        f3 = scripting.ITKCommonA.Image.F3
        self.itkfilter = scripting.ITKAlgorithms.WatershedImageFilter[f3].New()

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "Threshold":
            return 0.01
        if parameter == "Level":
            return 0.2
        return 0
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.FloatType
        
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Threshold","Level")]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image,cast=types.FloatType)
        self.itkfilter.SetInput(image)
        self.itkfilter.SetThreshold(self.parameters["Threshold"])
        self.itkfilter.SetLevel(self.parameters["Level"])

        

        if update:
            self.itkfilter.Update()
        data=self.itkfilter.GetOutput()            
        if last:
            return self.convertITKtoVTK(data)
        return data
        
class MapToRGBFilter(ManipulationFilter):
    """
    Class: MapToRGBFilter
    Created: 13.05.2006, KP
    Description: 
    """     
    name = "Map To RGB"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {}
        self.itkFlag = 1

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        return 0
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
        
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return []


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        import itk
        
        image = self.convertITKtoVTK(image,imagetype="UL3")
        image.Update()
        
        
        x0,x1 = image.GetScalarRange()
        print "Generating palette from ",x0,"to",x1
        #ctf = ImageOperations.watershedPalette(x0,x1)
        ctf = ImageOperations.fire(x0,x1)
    
        self.mapper = vtk.vtkImageMapToColors()
        self.mapper.SetOutputFormatToRGB()
        self.mapper.SetLookupTable(ctf)
        self.mapper.AddInput(image)
        
        if update:
            self.mapper.Update()
        data=self.mapper.GetOutput()            
            
        return data
