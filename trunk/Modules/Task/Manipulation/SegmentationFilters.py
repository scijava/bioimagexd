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
#import ManipulationFilters
from lib import ProcessingFilter
import ImageOperations
import wx
import time
import scripting as bxd
import csv
import codecs
import os.path
try:
    import itk
except:
    pass
import vtk
import types

import Logging
import MathFilters
import GUI.GUIBuilder as GUIBuilder
import messenger


import  wx.lib.mixins.listctrl  as  listmix
SEGMENTATION="Segmentation"
#ITK="ITK"

MEASUREMENT="Measurements"
WATERSHED="Watershed segmentation"
REGIONGROWING="Region growing"

class WatershedTotalsList(wx.ListCtrl):
    def __init__(self, parent, log):
        wx.ListCtrl.__init__(
            self, parent, -1, 
            size = (350,60),
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES,
            
            )

        self.InsertColumn(0, "# of objects")
        self.InsertColumn(1, u"Avg. Volume (px)")
        self.InsertColumn(2, u"Avg. Volume (\u03BCm)")
        self.InsertColumn(3,"Avg. intensity")
        #self.InsertColumn(2, "")
        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 70)
        self.SetColumnWidth(2, 105)
        self.SetColumnWidth(3, 105)
        self.stats= []
    

        self.SetItemCount(1)

        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour("white")

        self.attr2 = wx.ListItemAttr()
        self.attr2.SetBackgroundColour("light blue")

    def setStats(self,stats):
        self.stats = stats
        
    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnGetItemText(self, item, col):
        if not self.stats:
            return ""
        if col>len(self.stats):
            return ""
        if col==0:
            return "%d"%self.stats[0]
        elif col==2:
            return u"%.3f \u03BCm"%self.stats[1]
        elif col==1:
            return "%d px"%self.stats[2]
        elif col==3:
            return "%.3f"%self.stats[3]
 
    def OnGetItemImage(self, item):
        return -1

    def OnGetItemAttr(self, item):
        if item % 2 == 1:
            return self.attr1
        elif item % 2 == 0:
            return self.attr2
        else:
            return None


class WatershedObjectList(wx.ListCtrl, listmix.ListCtrlSelectionManagerMix):
    """
    Created: KP
    Description: A list control object that is used to display a list of the results of
                 a watershed segmentation or a connected components analysis
    """
    def __init__(self, parent, wid, gsize=(350,250)):
        wx.ListCtrl.__init__(
            self, parent, wid, 
            size = gsize,
            style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES,
            )
        listmix.ListCtrlSelectionManagerMix.__init__(self)
        self.InsertColumn(0, "Object #")
        self.InsertColumn(1, u"Volume (px)")
        self.InsertColumn(2, u"Volume (\u03BCm)")
        
        self.InsertColumn(3,"Center Of Mass")
        self.InsertColumn(4,"Avg. intensity")
        #self.InsertColumn(2, "")
        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 70)
        self.SetColumnWidth(2, 70)
        self.SetColumnWidth(3, 70)
        self.SetColumnWidth(4, 70)

        self.highlightSelected = 1
        #self.SetItemCount(1000)

        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour("white")
        
        self.counter = 0
        self.attr2 = wx.ListItemAttr()
        self.attr2.SetBackgroundColour("light blue")
        self.volumeList = []
        self.centersOfMassList = []
        self.avgIntList=[]
        
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.OnItemFocused)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def setSelectionHighlighting(self, flag):
        """
        Created: 26.11.2006, KP
        Description: Set the flag indicating whether the selection of the objects will be highlighted
        """
        self.highlightSelected = flag
    def setCentersOfMass(self, centersofmassList):
        self.centersOfMassList = centersofmassList
        self.Freeze()
        for i,cog in enumerate(centersofmassList):
            if self.GetItemCount()<i:
                self.InsertStringItem(i,"")        
            self.SetStringItem(i, 3,"(%d,%d,%d)"%(cog))
        self.Thaw()
        self.Refresh()
    def setVolumes(self,volumeList):
        self.volumeList = volumeList
#        self.SetItemCount(len(volumeList))
        self.Freeze()
        for i,(vol,volum) in enumerate(volumeList):
            #print "vol=",vol,"volum=",volum
            if self.GetItemCount()<=i:
                self.InsertStringItem(i,"")
            self.SetStringItem(i,0,"#%d"%i)
            self.SetStringItem(i, 1,"%d px"%(vol))   
            self.SetStringItem(i, 2,u"%.3f \u03BCm"%(volum))   
        self.Thaw()
        self.Refresh()
        
    def setAverageIntensities(self, avgIntList):
        self.avgIntList= avgIntList
        for i,avgint in enumerate(avgIntList):
            if self.GetItemCount()<i:
                self.InsertStringItem(i,"")        
            self.SetStringItem(i, 4,"%.3f"%(avgint))
        self.Refresh()
        
    def OnItemFocused(self, event):
        event.Skip()
        
    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        item=-1
        #print "Selected=",event.GetText()
        
        if self.highlightSelected:
            self.counter+=1
            
            wx.FutureCall(200,self.sendHighlight)
        event.Skip()
    def sendHighlight(self):
        """
        Created: 26.11.2006, KP
        Description: Send an event that will highlight the selected objects
        """
        
        self.counter-=1
        if self.counter<=0:
            messenger.send(None,"selected_objects",self.getSelection())
            self.counter=0
    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        
        if len(self.centersOfMassList)>=self.currentItem:            
            centerofmass = self.centersOfMassList[self.currentItem]
            x,y,z = centerofmass
            
            messenger.send(None,"show_centerofmass",self.currentItem,centerofmass)
            messenger.send(None,"zslice_changed",int(z))
            messenger.send(None,"update_helpers",1)
        

    def OnItemDeselected(self, evt):
        print ("OnItemDeselected: %s" % evt.m_itemIndex)

    
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


class ThresholdFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 15.04.2006, KP
    Description: A thresholding filter
    """     
    name = "Threshold"
    category = SEGMENTATION
    level = bxd.COLOR_BEGINNER
    
    def __init__(self):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,(1,1))
        self.vtkfilter = vtk.vtkImageThreshold()
        self.origCtf = None
        
        self.ignoreObjects = 1
        self.descs={"ReplaceInValue":"Value for voxels inside thresholds",
            "ReplaceOutValue":"Value for voxels outside thresholds",
            "ReplaceIn":"Inside thresholds","ReplaceOut":"Outside thresholds",
            "LowerThreshold":"Lower Threshold","UpperThreshold":"Upper threshold",
            "Demonstrate":"Use lookup table to demonstrate effect"}
    
    def getParameterLevel(self, parameter):
        """
        Created: 9.11.2006, KP
        Description: Return the level of the given parameter
        """
        if parameter in ["ReplaceInValue","ReplaceOutValue"]:
            return bxd.COLOR_INTERMEDIATE
        
        
        return bxd.COLOR_BEGINNER                
    
    def setParameter(self,parameter,value):
        """
        Created: 18.01.2007, KP
        Description: Set a value for the parameter
        """    
        
        oldval = self.parameters.get(parameter,"ThisIsABadValueThatNoOneWillEverUse")
        ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
        if self.initDone and value != oldval:
            messenger.send(None,"data_changed",0)
        
    def getParameters(self):
        """
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
        if parameter in ["LowerThreshold","UpperThreshold"]:
            return GUIBuilder.THRESHOLD
        elif parameter in ["ReplaceIn","ReplaceOut","Demonstrate"]:
            return types.BooleanType
        return types.IntType
        
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """     
        if parameter == "LowerThreshold":
            return 128
        if parameter == "UpperThreshold":
            return 255
        if parameter == "ReplaceInValue":
            return 255
        if parameter == "ReplaceOutValue":
            return 0
        if parameter == "Demonstrate":
            return 0
        if parameter in ["ReplaceIn","ReplaceOut"]:
            return 1

    def onRemove(self):
        """
        Created: 26.1.2006, KP
        Description: Restore palette upon filter removal
        """        
        if self.origCtf:            
            self.dataUnit.getSettings().set("ColorTransferFunction",self.origCtf)            
            
    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """            
        
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
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
            
class MaskFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 13.04.2006, KP
    Description: A base class for image mathematics filters
    """     
    name = "Mask"
    category = SEGMENTATION
    level = bxd.COLOR_BEGINNER
    def __init__(self,inputs=(2,2)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        self.vtkfilter = vtk.vtkImageMask()
        
        self.descs = {"OutputValue":"Masked output value"}
            
    def getDesc(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
            
    def getInputName(self,n):
        """
        Created: 17.04.2006, KP
        Description: Return the name of the input #n
        """          
        if n==1:
            return "Source dataset %d"%n    
        return "Mask dataset"
        
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        return 0
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("OutputValue",)]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
        self.vtkfilter.SetInput1(self.getInput(1))
        
        self.vtkfilter.SetInput2(self.getInput(2))
        self.vtkfilter.SetMaskedOutputValue(self.parameters["OutputValue"])
        
        if update:
            self.vtkfilter.Update()
        return self.vtkfilter.GetOutput()   

class ITKWatershedSegmentationFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 13.04.2006, KP
    Description: A filter for doing watershed segmentation
    """     
    name = "Watershed segmentation (old)"
    category = WATERSHED
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        
        
        self.descs = {"Threshold":"Segmentation Threshold","Level":"Segmentation Level"}
        self.itkFlag = 1

        #scripting.loadITK(filters=1)
        f3 = itk.Image.F3
        self.itkfilter = itk.WatershedImageFilter[f3].New()

    def getParameterLevel(self, parameter):
        """
        Created: 9.11.2006, KP
        Description: Return the level of the given parameter
        """
        return bxd.COLOR_INTERMEDIATE
        
            
    def getDefaultValue(self,parameter):
        """
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
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.FloatType
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Threshold","Level")]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
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

class MorphologicalWatershedSegmentationFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 05.07.2006, KP
    Description: A filter for doing morphological watershed segmentation
    """     
    name = "Morphological watershed segmentation"
    category = WATERSHED
    level = bxd.COLOR_BEGINNER
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        
        
        self.descs = {"Level":"Segmentation Level","MarkWatershedLine":"Mark the watershed line",
        "Threshold":"Remove objects with less voxels than:"}
        self.itkFlag = 1
        self.origCtf = None
        self.n=0
        self.ignoreObjects = 2
        self.relabelFilter  = None
        self.itkfilter = None
        #scripting.loadITK(filters=1)            

    def getParameterLevel(self, parameter):
        """
        Created: 9.11.2006, KP
        Description: Return the level of the given parameter
        """
        if parameter in ["Leve","Threshold","Level"]:
            return bxd.COLOR_INTERMEDIATE
        
        
        return bxd.COLOR_BEGINNER                    
            
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "Level":
            return 5
        
        return 0
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter == "MarkWatershedLine":
            return types.BooleanType
        return types.IntType
             
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("Level","MarkWatershedLine")],["Minimum object size (in pixels)",("Threshold",)]]

    def onRemove(self):
        """
        Created: 26.1.2006, KP
        Description: Restore palette upon filter removal
        """        
        if self.origCtf:            
            self.dataUnit.getSettings().set("ColorTransferFunction",self.origCtf)            
            
    
    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image)
        if not self.itkfilter:
            try:
                ul3 = itk.Image.UL3
                self.itkfilter = itk.MorphologicalWatershedImageFilter[image, ul3].New()
            except:
                import watershed
                self.itkfilter = watershed.MorphologicalWatershedImageFilter[image, ul3].New()
        
        markWatershedLine = self.parameters["MarkWatershedLine"]
        self.itkfilter.SetMarkWatershedLine(markWatershedLine)

        t =time.time()
        #print "Feeding to watershed",image
        #print "Level=",self.parameters["Level"]
        self.itkfilter.SetInput(image)
        self.itkfilter.SetLevel(self.parameters["Level"])
                
        self.setImageType("UL3")
        self.itkfilter.Update()
        print "Morphological watershed took",time.time()-t,"seconds"
        data=self.itkfilter.GetOutput()            
        if not self.relabelFilter:
            
            self.relabelFilter = itk.RelabelComponentImageFilter[data,data].New()
        self.relabelFilter.SetInput(data)
        th = self.parameters["Threshold"]
        if th:
            self.relabelFilter.SetMinimumObjectSize(th)
                
            #self.setImageType("UL3")
    
        data=self.relabelFilter.GetOutput()            
                
        self.relabelFilter.Update()
        n = self.relabelFilter.GetNumberOfObjects()
        
        settings = self.dataUnit.getSettings()
        ncolors = settings.get("PaletteColors")
        if not ncolors or ncolors < n:
            if not ncolors:ncolors=0
            print "Creating new palette, old had ",ncolors,"colors, new will have",n
            ctf = ImageOperations.watershedPalette(0, n)
            
            if markWatershedLine:
                ctf.AddRGBPoint(0,1.0,1.0,1.0)
            if not self.origCtf:
                self.origCtf = self.dataUnit.getColorTransferFunction()
            self.dataUnit.getSettings().set("ColorTransferFunction",ctf)    
            val=[0,0,0]
            ctf.GetColor(1,val)
            print "ctf value at 1=",val
            settings.set("PaletteColors",n)
        #print "Returning ",data
        return data

class ConnectedComponentFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 12.07.2006, KP
    Description: A filter for labeling all separate objects in an image
    """     
    name = "Connected component labeling"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        self.ignoreObjects = 1
        
        self.descs = {"Threshold":"Remove objects with less voxels than:"}        
        self.itkFlag = 1
        self.origCtf = None
        self.relabelFilter = None
        self.itkfilter = None
        #scripting.loadITK(filters=1)            
        
    def getParameterLevel(self, parameter):
        """
        Created: 9.11.2006, KP
        Description: Return the level of the given parameter
        """
        return bxd.COLOR_INTERMEDIATE
            
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        return 0
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        #return [["",("Level",)]]
        return [["Minimum object size (in pixels)",("Threshold",)]]

    def onRemove(self):
        """
        Created: 26.1.2006, KP
        Description: Restore palette upon filter removal
        """        
        if self.origCtf:            
            self.dataUnit.getSettings().set("ColorTransferFunction",self.origCtf)            
            
    
    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            print "\n\nFailed to execute"
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image)
        if not self.itkfilter:            
            self.itkfilter = itk.ConnectedComponentImageFilter[image, itk.Image.UL3].New()

        self.itkfilter.SetInput(image)
        #self.itkfilter.SetLevel(self.parameters["Level"])
                
        self.setImageType("UL3")
        self.itkfilter.Update()
        #print "Morphological watershed took",time.time()-t,"seconds"
        data=self.itkfilter.GetOutput()        
    
        if not self.relabelFilter:
            
            self.relabelFilter = itk.RelabelComponentImageFilter[data,data].New()
        self.relabelFilter.SetInput(data)
        th = self.parameters["Threshold"]
        if th:
            self.relabelFilter.SetMinimumObjectSize(th)
                
            #self.setImageType("UL3")
    
        data=self.relabelFilter.GetOutput()            
            
        self.relabelFilter.Update()
        n = self.relabelFilter.GetNumberOfObjects()
    
        settings = self.dataUnit.getSettings()
        ncolors = settings.get("PaletteColors")
        print "NColors=",ncolors,"n=",n
        if not ncolors or ncolors < n:
            ctf = ImageOperations.watershedPalette(0, n)
            if not self.origCtf:
                self.origCtf = self.dataUnit.getColorTransferFunction()
            self.dataUnit.getSettings().set("ColorTransferFunction",ctf)    
            settings.set("PaletteColors",n)
        return data

class MaximumObjectsFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 12.07.2006, KP
    Description: A filter for labeling all separate objects in an image
    """     
    name = "Threshold for maximum object number"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        
        
        self.descs = {"MinSize":"Minimum object size in pixels"}
        self.itkFlag = 1
        
        self.itkfilter = None
        #scripting.loadITK(filters=1)            

    def getParameterLevel(self, parameter):
        """
        Created: 9.11.2006, KP
        Description: Return the level of the given parameter
        """
        return bxd.COLOR_INTERMEDIATE
            
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "MinSize":
            return 15
        return 0
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("MinSize",)]]
        


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image)
        if not self.itkfilter:            
            self.itkfilter = itk.ThresholdMaximumConnectedComponentsImageFilter[image].New()

        self.itkfilter.SetOutsideValue(0)
        self.itkfilter.SetInsideValue(255)
        self.itkfilter.SetInput(image)
        self.itkfilter.SetMinimumObjectSizeInPixels(self.parameters["MinSize"])
                
        self.setImageType("UL3")
        self.itkfilter.Update()
        #print "Morphological watershed took",time.time()-t,"seconds"
        data=self.itkfilter.GetOutput()            
        #print "Returning ",data
        return data

        
class ITKRelabelImageFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 13.04.2006, KP
    Description: Re-label an image produced by watershed segmentation
    """     
    name = "Re-label image"
    category = WATERSHED
    level = bxd.COLOR_BEGINNER
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        
        
        self.descs = {"Threshold":"Remove objects with less voxels than:"}
        self.itkFlag = 1

        #scripting.loadITK(filters=1)
        #f3 = itk.Image.UL3
        self.itkfilter = None
        
    def getParameterLevel(self, parameter):
        """
        Created: 9.11.2006, KP
        Description: Return the level of the given parameter
        """
        return bxd.COLOR_INTERMEDIATE

            
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        return 0
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Minimum object size (in pixels)",("Threshold",)]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image)
        if not self.itkfilter:
            print "Image=",image
            self.itkfilter = itk.RelabelComponentImageFilter[image,image].New()
        self.itkfilter.SetInput(image)
        th = self.parameters["Threshold"]
        self.itkfilter.SetMinimumObjectSize(th)

        
        #self.setImageType("UL3")

        data=self.itkfilter.GetOutput()            
                
        self.itkfilter.Update()
        
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UL3")
        return data

class ITKInvertIntensityFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 05.07.2006, KP
    Description: Invert the intensity of the image
    """     
    name = "Invert intensity"
    category = WATERSHED
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
                
        self.descs = {}
        self.itkFlag = 1
        self.itkfilter = None
            
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    

        return 0
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
        
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
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
            
        image = self.getInput(1)
        image = self.convertVTKtoITK(image)

        if not self.itkfilter:
            self.itkfilter = itk.InvertIntensityImageFilter[image, image].New()
            
        self.itkfilter.SetInput(image)
        
        #self.setImageType("UL3")

        data=self.itkfilter.GetOutput()            
        
        
        self.itkfilter.Update()
        
        return data

class MeasureVolumeFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 15.05.2006, KP
    Description: 
    """     
    name = "Calculate object statistics"
    category = MEASUREMENT
    level = bxd.COLOR_BEGINNER
    def __init__(self,inputs=(2,2)):
        """
        Created: 13.04.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        self.itkFlag = 1
        self.descs = {}      
        self.values = None
        self.centersofmass = None
        self.avgintCalc = None
        self.umcentersofmass = None
        self.avgIntList = None
        self.descs = {"StatisticsFile":"Results file:"}
        self.reportGUI = None
        self.itkfilter = None
        self.labelShape = None
        
    def setDataUnit(self, dataUnit):
        """
        Created: 04.04.2007, KP
        Description: a method to set the dataunit used by this filter
        """
        ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
        self.parameters["StatisticsFile"] = self.getDefaultValue("StatisticsFile")
            
    def getDefaultValue(self,parameter):
        """
        Created: 15.04.2006, KP
        Description: Return the default value of a parameter
        """    
        if not self.dataUnit:
            return "statistics.csv"
        else:
            return self.dataUnit.getName()+".csv"
        
    def getType(self,parameter):
        """
        Created: 13.04.2006, KP
        Description: Return the type of the parameter
        """    
        return GUIBuilder.FILENAME
        
        
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Measurement results",
        (("StatisticsFile","Select the file to which the statistics will be writen","*.csv"),)]]
        
    def writeOutput(self, dataUnit, timepoint):
        """
        Created: 09.07.2006, KP
        Description: Optionally write the output of this module during the processing
        """   
        fileroot=self.parameters["StatisticsFile"].split(".")
        fileroot=".".join(fileroot[:-1])
        dircomp = os.path.dirname(fileroot)
        if not dircomp:
            bxddir = dataUnit.getOutputDirectory()
            fileroot = os.path.join(bxddir,fileroot)
        #filename = "%s_%d.csv"%(fileroot,timepoint)
        filename="%s.csv"%fileroot
        f=codecs.open(filename,"awb","latin1")
        
        w=csv.writer(f,dialect="excel",delimiter=";")
        
        settings = dataUnit.getSettings()
        settings.register("StatisticsFile")
        settings.set("StatisticsFile",filename)
        w.writerow(["Timepoint %d"%timepoint])
        w.writerow(["Object #","Volume (micrometers)","Volume (pixels)","Center of Mass","Center of Mass (micrometers)","Avg. Intensity"])
        for i,(volume,volumeum) in enumerate(self.values):
            cog = self.centersofmass[i]
            umcog = self.umcentersofmass[i]
            avgint = self.avgIntList[i]
            w.writerow([str(i),str(volumeum),str(volume),str(cog),str(umcog),str(avgint)])
        f.close()

    def getGUI(self,parent,taskPanel):
        """
        Created: 13.04.2006, KP
        Description: Return the GUI for this filter
        """              
        gui = ProcessingFilter.ProcessingFilter.getGUI(self,parent,taskPanel)
        
        if not self.reportGUI:
            self.reportGUI = WatershedObjectList(self.gui,-1)
            
            self.totalGUI = WatershedTotalsList(self.gui,-1)
            if self.values:
                def avg(lst):
                    return sum(lst)/float(len(lst))
                n = len(self.values)
                avgints = avg(self.avgIntList)
                ums = [x[1] for x in self.values]
                
                # Remove the objects 0 and 1 because hey will distort the values
                #ums.pop(0)
                #ums.pop(0)
                avgums = avg(ums)
                pxs = [x[0] for x in self.values]
                
                #pxs.pop(0)
                #pxs.pop(0)
                avgpxs = avg(pxs)
                
                self.totalGUI.setStats([n,avgums,avgpxs,avgints])
                self.reportGUI.setVolumes(self.values)
                self.reportGUI.setCentersOfMass(self.centersofmass)
                self.reportGUI.setAverageIntensities(self.avgIntList)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.reportGUI,1)
            sizer.Add(self.totalGUI)
            gui.sizer.Add(sizer,(1,0),flag=wx.EXPAND|wx.ALL)
        return gui


   
    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
        image = self.getInput(1)
        #print "INPUT IMAGE FOR MEASUREMENT=",image
        #print "converting to ITK, image=",image
        image = self.convertVTKtoITK(image)
        #print "image now=",image
        
        
        if not self.labelShape:
            import labelShape
            self.labelShape = labelShape

            #ul3 = itk.Image.UL3
        print "Setting as input to labelshape",image
        self.itkfilter = self.labelShape.LabelShapeImageFilter[image].New()
        self.itkfilter.SetInput(image)
        self.itkfilter.Update()
        print "done"
        #self.setImageType("UL3")
        data=self.itkfilter.GetOutput()            
                   
            
        x,y,z = self.dataUnit.getVoxelSize()
        x*=1000000
        y*=1000000
        z*=1000000
        vol = x*y*z
        
        voxelSizes=[x,y,z]
        n = self.itkfilter.GetNumberOfLabels()
        values = []
        centersofmass = []
        umcentersofmass = []
        avgints=[]
        
        vtkimage = self.convertITKtoVTK(image)                
        origInput = self.getInput(2)
        origInput.Update()
        
        if self.avgintCalc:
            del self.avgintCalc
        print "Doing label average"
        self.avgintCalc = avgintCalc = vtk.vtkImageLabelAverage()
        #avgintCalc.DebugOn()

        # We require unsigned long input data
        if vtkimage.GetScalarType() != 9:
            dt = vtkimage.GetScalarTypeAsString()
            Logging.error("Wrong input type for Object Statistics",
            "The calculate object statistics requires an input dataset of type unsigned long.\nA dataset of type %s was provided.\nTypically, you will use Calculate Object Statistics Filter after a Watershed filter, or Connected Component Labeling filter.\nThis error may be caused by not having either of those filters in the procedure list."%(dt))
            return vtkimage
        
        #print "Using as input",origInput
        #print "And",vtkimage
        avgintCalc.AddInput(origInput)
        avgintCalc.AddInput(vtkimage)
        
        avgintCalc.Update()
                    
        #print "done"
        if self.prevFilter:        
            startIntensity = self.prevFilter.ignoreObjects
        else:
            startIntensity=0
        for i in range(startIntensity,n):
            volume = self.itkfilter.GetVolume(i)
            centerOfMass = self.itkfilter.GetCenterOfGravity(i)
            avgInt = avgintCalc.GetAverage(i)
            if not self.itkfilter.HasLabel(i):
                centersofmass.append((0,0,0))
                values.append((0,0))
                avgints.append(0.0)
                umcentersofmass.append((0,0,0))
            else:
                c = []
                c2 = []
                for i in range(0,3):
                    v = centerOfMass.GetElement(i)
                    c.append(v)
                    c2.append(v*voxelSizes[i])
                centersofmass.append(tuple(c))
                umcentersofmass.append(tuple(c2))
                values.append((volume,volume*vol))                
                avgints.append(avgInt)
#        print "volumes=",values
#        print "centers of mass=",centersofmass
        #print "avg. ints=",avgints
            

        self.values = values
        self.centersofmass = centersofmass
        self.umcentersofmass = umcentersofmass
        self.avgIntList = avgints
        if self.reportGUI:
            self.reportGUI.setVolumes(values)
            self.reportGUI.setCentersOfMass(centersofmass)
            self.reportGUI.setAverageIntensities(self.avgIntList)
            def avg(lst):
                return sum(lst)/len(lst)
            n = len(self.values)
            avgints = avg(self.avgIntList)
            ums = [x[0] for x in values]
            avgums = avg(ums)
            pxs = [x[1] for x in values]
            avgpxs = avg(pxs)
            
            self.totalGUI.setStats([n,avgums,avgpxs,avgints])
            
        return self.itkfilter.GetOutput()
        
class ITKConfidenceConnectedFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 29.05.2006, KP
    Description: A class for doing confidence connected segmentation
    """     
    name = "Confidence connected threshold"
    category = REGIONGROWING
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 26.05.2006, KP
        Description: Initialization
        """
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        
        
        self.descs = {"Seed":"Seed voxel","Neighborhood":"Initial neighborhood size",
            "Multiplier":"Range relaxation","Iterations":"Iterations"}
        self.itkFlag = 1
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.ConfidenceConnectedImageFilter[uc3,uc3].New()

    def getParameterLevel(self, parameter):
        """
        Created: 9.11.2006, KP
        Description: Return the level of the given parameter
        """
        if parameter in ["Multiplier","Iterations"]:
            return bxd.COLOR_EXPERIENCED
        if parameter == "Neighborhood":
            return bxd.COLOR_INTERMEDIATE
        
        
        return bxd.COLOR_BEGINNER            
            
    def getDefaultValue(self,parameter):
        """
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
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Seed",(("Seed",),)],
        ["Segmentation",("Neighborhood","Multiplier","Iterations")]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
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

class ITKConnectedThresholdFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 26.05.2006, KP
    Description: A class for doing confidence connected segmentation
    """     
    name = "Connected threshold"
    category = REGIONGROWING
    level = bxd.COLOR_BEGINNER
    def __init__(self,inputs=(1,1)):
        """
        Created: 26.05.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)        
        
        self.descs = {"Seed":"Seed voxel","Upper":"Upper threshold","Lower":"Lower threshold"}
        self.itkFlag = 1
        self.setImageType("UC3")
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.ConnectedThresholdImageFilter[uc3,uc3].New()

            
    def getDefaultValue(self,parameter):
        """
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
        Created: 26.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Lower","Upper"]:
            return GUIBuilder.THRESHOLD
        return GUIBuilder.PIXELS
                
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Seed",(("Seed",),)],
        ["Threshold",(("Lower","Upper"),)]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
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
        
class ITKNeighborhoodConnectedThresholdFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 29.05.2006, KP
    Description: A class for doing connected threshold segmentation 
    """     
    name = "Neighborhood connected threshold"
    category = REGIONGROWING
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 29.05.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        self.setImageType("UC3")
        
        self.descs = {"Seed":"Seed voxel","Upper":"Upper threshold","Lower":"Lower threshold",
            "RadiusX":"X neighborhood size",
            "RadiusY":"Y neighborhood size",
            "RadiusZ":"Z neighborhood size"}
        self.itkFlag = 1
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.NeighborhoodConnectedImageFilter[uc3,uc3].New()

    def getParameterLevel(self, parameter):
        """
        Created: 1.11.2006, KP
        Description: Return the level of the given parameter
        """
        if parameter in ["RadiusX","RadiusY","RadiusZ"]:
            return bxd.COLOR_INTERMEDIATE
        
        
        return bxd.COLOR_BEGINNER                        
        
    def getDefaultValue(self,parameter):
        """
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
        Created: 29.05.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Seed",(("Seed",),)],
        ["Threshold",(("Lower","Upper"),)],
        ["Neighborhood",("RadiusX","RadiusY","RadiusZ")]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 29.05.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
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

class ITKOtsuThresholdFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 26.05.2006, KP
    Description: A class for thresholding the image using the otsu thresholding
    """     
    name = "Otsu threshold"
    category = SEGMENTATION
    
    def __init__(self,inputs=(1,1)):
        """
        Created: 26.05.2006, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        
        
        self.descs = {"Upper":"Upper threshold","Lower":"Lower threshold"}
        self.itkFlag = 1
        
        uc3 = itk.Image.UC3
        self.itkfilter = itk.OtsuThresholdImageFilter[uc3,uc3].New()

            
    def getDefaultValue(self,parameter):
        """
        Created: 26.05.2006, KP
        Description: Return the default value of a parameter
        """    
        return 0
        
    def getType(self,parameter):
        """
        Created: 26.05.2006, KP
        Description: Return the type of the parameter
        """    
        if parameter in ["Lower","Upper"]:
            return GUIBuilder.THRESHOLD
                
    def getParameters(self):
        """
        Created: 15.04.2006, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["Threshold",(("Lower","Upper"),)]]


    def execute(self,inputs,update=0,last=0):
        """
        Created: 15.04.2006, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
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
        
        #print "OTSU THRESHOLD=",self.itkfilter.GetThreshold()
            
        data = self.itkfilter.GetOutput()
        #if last:
        #    return self.convertITKtoVTK(data,imagetype="UC3")
            
        return data            
        
