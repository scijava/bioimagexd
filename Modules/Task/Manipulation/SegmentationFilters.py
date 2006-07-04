#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: SegmentationFilters
 Project: BioImageXD
 Created: 07.06.2006, KP
 Description:

 A module containing the segmentation filters for the processing task.
                            
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
import ManipulationFilters
import ImageOperations
import wx
try:
    import itk
except:
    pass
import vtk
import types

import GUI.GUIBuilder as GUIBuilder
import messenger

SEGMENTATION="Segmentation"
ITK="ITK"

MEASUREMENT="Measurements"


class WatershedObjectList(wx.ListCtrl):
    def __init__(self, parent, log):
        wx.ListCtrl.__init__(
            self, parent, -1, 
            size = (350,250),
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES,
            
            )

#        self.il = wx.ImageList(16, 16)
#        self.idx1 = self.il.Add(images.getSmilesBitmap())
#        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)



        self.InsertColumn(0, "Object #")
        self.InsertColumn(1, u"Volume (\u03BCm)")
        self.InsertColumn(2, u"Volume (px)")
        self.InsertColumn(3,"Centroid")
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
        self.volumeList = []
        self.centroidList = []
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    
    def setCentroids(self, centroidList):
        self.centroidList = centroidList

    def setVolumes(self,volumeList):
#        print "Set volumes",volumeList
        self.volumeList = volumeList
        self.SetItemCount(len(volumeList))
        self.Refresh()
        
    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        #print ('OnItemSelected: "%s", "%s", "%s", "%s"\n' %
        #                   (self.currentItem,
        #                    self.GetItemText(self.currentItem),
        #                    self.getColumnText(self.currentItem, 1),
        #                    self.getColumnText(self.currentItem, 2)))

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        print "item=",self.currentItem,"number of centroids=",len(self.centroidList)
        if len(self.centroidList)>=self.currentItem:            
            centroid = self.centroidList[self.currentItem]
            x,y,z = centroid
            print "Sending zslice change to ",z
            
            messenger.send(None,"zslice_changed",z)
            print "Sending show centroid",centroid
            messenger.send(None,"show_centroid",self.currentItem,centroid)
        
        print ("OnItemActivated: %s\nTopItem: %s\n" %
                           (self.GetItemText(self.currentItem), self.GetTopItem()))

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnItemDeselected(self, evt):
        print ("OnItemDeselected: %s" % evt.m_itemIndex)

    def OnGetItemText(self, item, col):
        
        if item>=len(self.volumeList):
            return "No item %d at col %d"%(item,col)
        if col==0:
            return "#%d"%item
        elif col==1:
            return u"%.3f \u03BCm"%self.volumeList[item][1]
        elif col==2:
            return "%d px"%self.volumeList[item][0]
        else:
            return "(%d, %d, %d)"%self.centroidList[item]

    def OnGetItemImage(self, item):
#        if item % 3 == 0:
#            return self.idx1
#        else:
         return -1

    def OnGetItemAttr(self, item):
        if item % 2 == 1:
            return self.attr1
        elif item % 2 == 0:
            return self.attr2
        else:
            return None


class ThresholdFilter(ManipulationFilters.ManipulationFilter):
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
        ManipulationFilters.ManipulationFilter.__init__(self,(1,1))
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
            return GUIBuilder.THRESHOLD
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
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
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
            self.origCtf = origCtf
            ctf = vtk.vtkColorTransferFunction()
            ctf.AddRGBPoint(0,0,0,0.0)
            if lower>0:
                ctf.AddRGBPoint(lower,0, 0, 1.0)
                ctf.AddRGBPoint(lower+1, 0, 0, 0)
            
            
            val=[0,0,0]
            origCtf.GetColor(255,val)
            r,g,b=val
            ctf.AddRGBPoint(upper, r, g, b)
            if upper<255:
                ctf.AddRGBPoint(upper+1,0,0,0)
                ctf.AddRGBPoint(255, 1.0, 0, 0)
            self.dataUnit.getSettings().set("ColorTransferFunction",ctf)
            if self.gui:
                print "Replacing CTF"
                self.gui.histograms[0].setReplacementCTF(ctf)
                self.gui.histograms[0].updatePreview(renew=1)
                self.gui.histograms[0].Refresh()
            
            return image
class MaskFilter(ManipulationFilters.ManipulationFilter):
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
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
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
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
        self.vtkfilter.SetInput1(self.getInput(1))
        
        self.vtkfilter.SetInput2(self.getInput(2))
        self.vtkfilter.SetMaskedOutputValue(self.parameters["OutputValue"])
        
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()   

class ITKWatershedSegmentationFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: ITKAnisotropicDiffusionFilterFilter
    Created: 13.04.2006, KP
    Description: A class for doing anisotropic diffusion on ITK
    """     
    name = "Watershed Segmentation"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"Threshold":"Segmentation Threshold","Level":"Segmentation Level"}
        self.itkFlag = 1

        #scripting.loadITK(filters=1)
        f3 = itk.Image.F3
        self.itkfilter = itk.WatershedImageFilter[f3].New()
            
        
            
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
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image,cast=types.FloatType)
        print "Feeding to watershed",image
        print "parameters=",self.parameters["Threshold"],self.parameters["Level"]
        self.itkfilter.SetInput(image)
        self.itkfilter.SetThreshold(self.parameters["Threshold"])
        self.itkfilter.SetLevel(self.parameters["Level"])
                
        self.setImageType("UL3")
        if update:
            self.itkfilter.Update()
            print "Updating..." 
        data=self.itkfilter.GetOutput()            
        print "Returning ",data
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UL3")
        return data
        
        
class ITKRelabelImageFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: ITKRelabelImageFilter
    Created: 13.04.2006, KP
    Description: Re-label an image produced by watershed segmentation
    """     
    name = "Re-Label Image"
    category = ITK
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"Threshold":"Remove objects with less voxels than:"}
        self.itkFlag = 1

        #scripting.loadITK(filters=1)
        f3 = itk.Image.UL3
        self.itkfilter = itk.RelabelComponentImageFilter[itk.Image.UL3,itk.Image.UL3].New()

            
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
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        self.itkfilter.SetInput(image)
        
        self.setImageType("UL3")

        data=self.itkfilter.GetOutput()            
                   
        
        if update:
            self.itkfilter.Update()
        
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UL3")
        return data



class MeasureVolumeFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: MeasureVolumeFilter
    Created: 15.05.2006, KP
    Description: 
    """     
    name = "Measure Segmented Volumes"
    category = MEASUREMENT
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
        self.itkFlag = 1
        self.descs = {}      
        self.values = None
        self.centroids = None
        self.reportGUI = None
        self.itkfilter = None
        import labelShape
        self.labelShape = labelShape

    def getGUI(self,parent,taskPanel):
        """
        Method: getGUI
        Created: 13.04.2006, KP
        Description: Return the GUI for this filter
        """              
        gui = ManipulationFilters.ManipulationFilter.getGUI(self,parent,taskPanel)
        if not self.reportGUI:
            self.reportGUI = WatershedObjectList(self.gui,-1)
            if self.values:
                self.reportGUI.setVolumes(self.values)
                self.reportGUI.setCentroids(self.centroids)
            gui.sizer.Add(self.reportGUI,(1,0),flag=wx.EXPAND|wx.ALL)
        return gui

            
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
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image)
        
        
        if not self.itkfilter:
            
            #ul3 = itk.Image.UL3
            self.itkfilter = self.labelShape.LabelShapeImageFilter[image].New()

        self.itkfilter.SetInput(image)
        
        self.setImageType("UL3")

        data=self.itkfilter.GetOutput()            
                   
            
        x,y,z = self.dataUnit.getVoxelSize()
        x*=1000000
        y*=1000000
        z*=1000000
        vol = x*y*z
        
    
        self.itkfilter.Update()
        n = self.itkfilter.GetNumberOfLabels()
        values = []
        centroids = []
        for i in range(0,n):
            volume = self.itkfilter.GetVolume(i)
            centroid = self.itkfilter.GetCenterOfGravity(i)
            c = []
            for i in range(0,3):
                c.append(centroid.GetElement(i))
            centroids.append(tuple(c))
            values.append((volume,volume*vol))
        print "volumes=",values
        print "centroids=",centroids
        
            
        #if self.prevFilter and self.prevFilter.getITK():
        #    image = self.convertITKtoVTK(image,imagetype=self.prevFilter.getImageType(),force=1)
        #    image.Update()
            

        #x0,x1=image.GetScalarRange()
        #print "Scalar range of measured image=",x0,x1
        ctf = ImageOperations.watershedPalette(0, n)
        self.dataUnit.getSettings().set("ColorTransferFunction",ctf)        
        
        #print image.GetScalarTypeAsString()
        #accu = vtk.vtkImageAccumulate()
        #accu.SetInput(image)
        #accu.SetComponentExtent(0,x1,0,0,0,0)
        #accu.Update() 
        #data = accu.GetOutput()
        
        
#        values=[]
#        x0,x1,y0,y1,z0,z1 = data.GetWholeExtent()
#        print x0,x1,y0,y1,z0,z1
        
#        for i in range(0,int(x1)):
#            c=data.GetScalarComponentAsDouble(i,0,0,0)
#            values.append(c)
        
        self.values = values
        self.centroids = centroids
        if self.reportGUI:
            self.reportGUI.setVolumes(values)
            self.reportGUI.setCentroids(centroids)
        return image

class FilterObjectsFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: FilterObjects
    Created: 16.05.2006, KP
    Description: 
    """     
    name = "Filter Objects"
    category = MEASUREMENT
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
        
        self.descs = {"Threshold":"Filter objects with fewer voxels than:"}        

            
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
        return [["Filtering threshold",("Threshold",)]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        
        
        if self.prevFilter and self.prevFilter.getITK():
            image = self.convertITKtoVTK(image,imagetype="UL3",force=1)
            image.Update()

        x0,x1=image.GetScalarRange()
        print "Input to filter has scalar range",x0,x1
        print image.GetScalarTypeAsString()
        accu = vtk.vtkImageAccumulate()
        accu.SetInput(image)
        accu.SetComponentExtent(0,x1,0,0,0,0)
        accu.Update() 
        data = accu.GetOutput()
        
        x0,x1,y0,y1,z0,z1 = data.GetWholeExtent()
        
        th = self.parameters["Threshold"]
        filterval=0
        print "th=",th
        for i in range(0,int(x1)):
            c=data.GetScalarComponentAsDouble(i,0,0,0)
            if th and c<th and i>0:
                filterval=i
                break

        print image.GetScalarRange(),image.GetScalarTypeAsString()

        print "Filtering from",filterval
        self.threshold = vtk.vtkImageThreshold()
        
        self.threshold.ThresholdByLower(filterval)
        
        self.threshold.SetOutValue(0)
        self.threshold.ReplaceOutOn()
        self.threshold.SetInput(image)
        self.threshold.SetOutputScalarTypeToUnsignedLong ()
        self.threshold.Update()
        data=self.threshold.GetOutput()
        print data.GetScalarRange(),data.GetScalarTypeAsString()
        return data
        
class ITKConfidenceConnectedFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: ITKConfidenceConnectedThresholdFilter
    Created: 29.05.2006, KP
    Description: A class for doing confidence connected segmentation
    """     
    name = "Confidence Connected"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 26.05.2006, KP
        Description: Initialization
        """
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"Seed":"Seed voxel","Neighborhood":"Initial Neighborhood Size",
            "Multiplier":"Range relaxation","Iterations":"Iterations"}
        self.itkFlag = 1
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.ConfidenceConnectedImageFilter[uc3,uc3].New()

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 26.05.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "Seed":
            return []
        elif parameter=="Multiplier":
            return 2.5
        elif parameter == "Iterations":
            return 5
        elif parameter == "Neighborhood":
            return 2
            
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 26.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter == "Seed":
            return GUIBuilder.PIXELS
        elif parameter == "Multiplier":
            return types.FloatType
        elif parameter == "Iterations":
            return types.IntType
        elif parameter=="Neighborhood":
            return types.IntType
            
            
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Seed",(("Seed",),)],
        ["Segmentation",("Neighborhood","Multiplier","Iterations")]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
#        print "Using as input",image
        image = self.convertVTKtoITK(image)
        self.itkfilter.SetInput(image)
        
        pixelidx = itk.Index[3]()
        for (x,y,z) in self.parameters["Seed"]:
            pixelidx.SetElement(0,x)
            pixelidx.SetElement(1,y)
            pixelidx.SetElement(2,z)
            print "Using as seed",x,y,z,pixelidx
            self.itkfilter.AddSeed(pixelidx)    
            
        iters = self.parameters["Iterations"]
        self.itkfilter.SetNumberOfIterations(iters)
        
        mult = self.parameters["Multiplier"]
        print "mult=",mult
        self.itkfilter.SetMultiplier(mult)
        rad = self.parameters["Neighborhood"]
        self.itkfilter.SetInitialNeighborhoodRadius(rad)
        
        self.itkfilter.SetReplaceValue(255)
        if update:
            self.itkfilter.Update()
            
        data = self.itkfilter.GetOutput()
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UC3")
            
        return data            

class ITKConnectedThresholdFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: ITKConnectedThresholdFilter
    Created: 26.05.2006, KP
    Description: A class for doing confidence connected segmentation
    """     
    name = "Connected Threshold"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 26.05.2006, KP
        Description: Initialization
        """        
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)        
        
        self.descs = {"Seed":"Seed voxel","Upper":"Upper threshold","Lower":"Lower threshold"}
        self.itkFlag = 1
        self.setImageType("UC3")
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.ConnectedThresholdImageFilter[uc3,uc3].New()

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 26.05.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "Seed":
            return []
        elif parameter == "Upper":
            return 255
        elif parameter == "Lower":
            return 128
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 26.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Lower","Upper"]:
            return GUIBuilder.THRESHOLD
        return GUIBuilder.PIXELS
                
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Seed",(("Seed",),)],
        ["Threshold",(("Lower","Upper"),)]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
#        print "Using as input",image
        image = self.convertVTKtoITK(image)
        self.itkfilter.SetInput(image)
        self.itkfilter.SetLower(self.parameters["Lower"])
        self.itkfilter.SetUpper(self.parameters["Upper"])
        
        pixelidx = itk.Index[3]()
        for (x,y,z) in self.parameters["Seed"]:
            pixelidx.SetElement(0,x)
            pixelidx.SetElement(1,y)
            pixelidx.SetElement(2,z)
            print "Using as seed",x,y,z,pixelidx
            self.itkfilter.AddSeed(pixelidx)    
        print "Threshold=",self.parameters["Lower"],self.parameters["Upper"]
        
        
        self.itkfilter.SetReplaceValue(255)
        if update:
            self.itkfilter.Update()
            
        data = self.itkfilter.GetOutput()
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UC3")
            
        return data      
        
class ITKNeighborhoodConnectedThresholdFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: ITKNeighborhoodConnectedThresholdFilter
    Created: 29.05.2006, KP
    Description: A class for doing connected threshold segmentation 
    """     
    name = "Neighborhood Connected Threshold"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 29.05.2006, KP
        Description: Initialization
        """        
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
        self.setImageType("UC3")
        
        self.descs = {"Seed":"Seed voxel","Upper":"Upper threshold","Lower":"Lower threshold",
            "RadiusX":"X Neighborhood Size",
            "RadiusY":"Y Neighborhood Size",
            "RadiusZ":"Z Neighborhood Size"}
        self.itkFlag = 1
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.NeighborhoodConnectedImageFilter[uc3,uc3].New()

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 29.05.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "Seed":
            return []
        elif parameter == "Upper":
            return 255
        elif parameter == "Lower":
            return 128
        elif parameter in ["RadiusX","RadiusY"]:
            return 2
        return 1
            
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 29.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Lower","Upper"]:
            return GUIBuilder.THRESHOLD
        elif "Radius" in parameter:
            return types.IntType
        return GUIBuilder.PIXELS
                
    def getParameters(self):
        """
        Method: getParameters
        Created: 29.05.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Seed",(("Seed",),)],
        ["Threshold",(("Lower","Upper"),)],
        ["Neighborhood",("RadiusX","RadiusY","RadiusZ")]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 29.05.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
#        print "Using as input",image
        image = self.convertVTKtoITK(image)
        self.itkfilter.SetInput(image)
        self.itkfilter.SetLower(self.parameters["Lower"])
        self.itkfilter.SetUpper(self.parameters["Upper"])
        
        pixelidx = itk.Index[3]()
        for (x,y,z) in self.parameters["Seed"]:
            pixelidx.SetElement(0,x)
            pixelidx.SetElement(1,y)
            pixelidx.SetElement(2,z)
            print "Using as seed",x,y,z,pixelidx
            self.itkfilter.AddSeed(pixelidx)    
        print "Threshold=",self.parameters["Lower"],self.parameters["Upper"]
        
        rx,ry,rz = self.parameters["RadiusX"],self.parameters["RadiusY"],self.parameters["RadiusZ"]
        
        size = itk.Size[3]()
        size.SetElement(0,rx)
        size.SetElement(0,ry)
        size.SetElement(0,rz)
        print "size=",size
        self.itkfilter.SetRadius(size)
        print "Using a radius of ",rx,ry
        self.itkfilter.SetReplaceValue(255)
        if update:
            self.itkfilter.Update()
            
        data = self.itkfilter.GetOutput()
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UC3")
            
        return data            

class ITKOtsuThresholdFilter(ManipulationFilters.ManipulationFilter):
    """
    Class: ITKOtsuThresholdFilter
    Created: 26.05.2006, KP
    Description: A class for thresholding the image using the otsu thresholding
    """     
    name = "Otsu Threshold"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Method: __init__()
        Created: 26.05.2006, KP
        Description: Initialization
        """        
        ManipulationFilters.ManipulationFilter.__init__(self,inputs)
        
        
        self.descs = {"Upper":"Upper threshold","Lower":"Lower threshold"}
        self.itkFlag = 1
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.OtsuThresholdImageFilter[uc3,uc3].New()

            
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 26.05.2006, KP
        Description: Return the default value of a parameter
        """    
        return 0
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 26.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Lower","Upper"]:
            return GUIBuilder.THRESHOLD
                
    def getParameters(self):
        """
        Method: getParameters
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Threshold",(("Lower","Upper"),)]]


    def execute(self,inputs,update=0,last=0):
        """
        Method: execute
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ManipulationFilters.ManipulationFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
#        print "Using as input",image
        image = self.convertVTKtoITK(image)
        self.itkfilter.SetInput(image)
        
        self.itkfilter.SetInsideValue(0)
        self.itkfilter.SetOutsideValue(255)
        self.itkfilter.SetNumberOfHistogramBins(255)
        if update:
            self.itkfilter.Update()
        
        print "OTSU THRESHOLD=",self.itkfilter.GetThreshold()
            
        data = self.itkfilter.GetOutput()
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UC3")
            
        return data            
        
