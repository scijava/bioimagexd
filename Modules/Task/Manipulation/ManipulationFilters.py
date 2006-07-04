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
try:
    import itk
except:
    pass
import messenger
import scripting

import GUI.GUIBuilder as GUIBuilder
import ImageOperations


def getFilterList():
    return [ErodeFilter,DilateFilter,RangeFilter,SobelFilter,
            MedianFilter,AnisotropicDiffusionFilter,SolitaryFilter,
            ShiftScaleFilter,AddFilter,SubtractFilter,MultiplyFilter,
            DivideFilter,SinFilter,CosFilter,LogFilter,ExpFilter,SQRTFilter,
            GradientFilter,GradientMagnitudeFilter,
            AndFilter,OrFilter,XorFilter,NotFilter,NandFilter,NorFilter,
            ThresholdFilter,VarianceFilter,HybridMedianFilter,
            ITKAnisotropicDiffusionFilter,ITKGradientMagnitudeFilter,
            ITKWatershedSegmentationFilter,MeasureVolumeFilter,
            ITKRelabelImageFilter,FilterObjectsFilter,ITKConnectedThresholdFilter,ITKNeighborhoodConnectedThresholdFilter,
            ITKLocalMaximumFilter,ITKOtsuThresholdFilter,ITKConfidenceConnectedFilter,
            MaskFilter,ITKSigmoidFilter]
            
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
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """
        self.taskPanel = None
        print self
        
        
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
        
    def notifyTaskPanel(self, module):
        """
        Method: notifyTaskPanel
        Created: 31.05.2006, KP
        Description: Notify the task panel that filter has changed
        """                     
        if self.taskPanel:
            self.taskPanel.filterModified(self)

        
    def setImageType(self,it):
        """
        Method: setImageType
        Created: 15.05.2006, KP
        Description: Set the image type of the ITK image
        """             
        self.imageType = it
        
    def getImageType(self):
        """
        Method: getImageType
        Created: 15.05.2006, KP
        Description: Get the image type of the ITK image
        """                 
        return self.imageType
        
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
        if not self.vtkToItk:            
            ImageType = itk.VTKImageToImageFilter.IUC3
            if cast==types.FloatType:
                ImageType = itk.VTKImageToImageFilter.IF3

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
        Method: convertITKtoVTK
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
            self.gui = GUIBuilder.GUIBuilder(parent,self)
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
            return GUIBuilder.RADIO_CHOICE
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

class GradientMagnitudeFilter(ManipulationFilter):
    """
    Class: GradientMagnitudeFilter
    Created: 13.04.2006, KP
    Description: A class for calculating the gradient magnitude of the image
    """     
    name = "Gradient Magnitude"
    category = MATH
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageGradientMagnitude()
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
        
        f3 = itk.Image.F3
        self.itkfilter = itk.GradientAnisotropicDiffusionImageFilter[f3,f3].New()

            
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
    name = "ITK Gradient Magnitude"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        self.itkFlag = 1
        
        f3=itk.Image.F3
        self.itkfilter = itk.GradientMagnitudeImageFilter[f3,f3].New()
        
        
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
        
        self.setImageType("F3")
        
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
        Method: __init__()
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
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Data range",("Minimum","Maximum")],
        ]        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
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
        Method: getType
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.FloatType


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
        Method: __init__()
        Created: 26.05.2006, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"Connectivity":"Use 8 neighbors for connectivity"}
        self.itkFlag = 1
        

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 26.05.2006, KP
        Description: Return the default value of a parameter
        """   
        if parameter == "Connectivity":
            return 1
        return 0
    def getType(self,parameter):
        """
        Method: getType
        Created: 26.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Connectivity"]:
            return types.BooleanType
                
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Connectivity",)]]

    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
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
