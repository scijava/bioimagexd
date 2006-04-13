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
def getFilterList():
    return [ErodeFilter,DilateFilter,MedianFilter]
    
   
MORPHOLOGICAL="Morphological"
MATH="Math"
SEGMENTATION="Segmentation"
FILTERING="Filtering"
   
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
        Created: 13.04.2007, KP
        Description: Initialization
        """
        self.numberOfInputs = numberOfInputs
        self.parameters = {}
        self.erode = None
        self.gui = None
        self.enabled = 1
        for i in self.getParameters():
            title,items = i
            for item in items:
                self.setParameter(item,self.getDefaultValue(item))
        
    def getEnabled(self):
        """
        Method: getEnabled
        Created: 13.04.2007, KP
        Description: Return whether this filter is enabled or not
        """                   
        return self.enabled
        
    def setEnabled(self,flag):
        """
        Method: setEnabled
        Created: 13.04.2007, KP
        Description: Set whether this filter is enabled or not
        """                   
        print "Setting ",self,"to enabled=",flag
        self.enabled = flag     
    
        
    def getGUI(self,parent):
        """
        Method: getGUI
        Created: 13.04.2007, KP
        Description: Return the GUI for this filter
        """              
        if not self.gui:
            self.gui = GUIBuilder(parent,self)
        return self.gui
            
    @classmethod            
    def getName(s):
        """
        Method: getName
        Created: 13.04.2007, KP
        Description: Return the name of the filter
        """        
        return s.name
        
    @classmethod
    def getCategory(s):
        """
        Method: getCategory
        Created: 13.04.2007, KP
        Description: Return the category this filter should be classified to 
        """                
        return s.category
        
    def setParameter(self,parameter,value):
        """
        Method: setParameter
        Created: 13.04.2007, KP
        Description: Set a value for the parameter
        """    
        self.parameters[parameter]=value
        print "Setting parameter ",parameter,"to",value
        
    def execute(self,*inputs):
        """
        Method: execute
        Created: 13.04.2007, KP
        Description: Execute the filter with given inputs and return the output
        """            
        n=len(inputs)
        if n< self.numberOfInputs[0] or (self.numberOfInputs[1]!=-1 and n>self.numberOfInputs[1]):
            messenger.send(None,"show_error","Bad number of inputs to filter","Filter %s was given a wrong number of inputs"%self.name)
            return 0
        return 1
        
        
class GUIBuilder(wx.Panel):
    """
    Class: GUIBuilder
    Created: 13.04.2006, KP
    Description: A GUI builder for the manipulation filters
    """      
    def __init__(self,parent,myfilter):
        """
        Method: __init__()
        Created: 13.04.2007, KP
        Description: Initialization
        """ 
        wx.Panel.__init__(self,parent,-1)
        self.filter = myfilter
        self.sizer = wx.GridBagSizer()
        
        
        self.buildGUI(myfilter)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        
    def buildGUI(self,currfilter):
        """
        Method: buildGUI
        Created: 13.04.2007, KP
        Description: Build the GUI for a given filter
        """         
        parameters = currfilter.getParameters()
        gy=0
        sbox=wx.StaticBox(self,-1,currfilter.getName())
        sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.sizer.Add(sboxsizer,(0,0))
        sizer=wx.GridBagSizer()
        sboxsizer.Add(sizer)
        for param in parameters:
            if type(param)==types.ListType:
                sboxname,items = param
                sbox = wx.StaticBox(self,-1,sboxname)
                sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)
                
                sizer.Add(sboxsizer,(gy,0),flag=wx.EXPAND)
                itemsizer = wx.GridBagSizer()
                sboxsizer.Add(itemsizer)
                y=0                
                for item in items:
                    desc = currfilter.getDesc(item)
                    lbl = wx.StaticText(self,-1,desc)
                    ftype = currfilter.getType(item)
                    defval = currfilter.getDefaultValue(item)
                    
                    
                    if ftype == types.IntType:
                        input = wx.TextCtrl(self,-1,str(defval))
                        valid=lambda evt,f=filter,p=item,t=ftype,i=input:self.validateAndPassOn(evt,i,p,ftype,f)
                        input.Bind(wx.EVT_TEXT,valid)
                    
                    itemsizer.Add(lbl,(y,0))
                    itemsizer.Add(input,(y,1))
                    y+=1
            gy+=1
        
                        
                    
                
    def validateAndPassOn(self,event,input,parameter,ftype,currfilter):
        """
        Method: buildGUI
        Created: 13.04.2007, KP
        Description: Build the GUI for a given filter
        """
        if ftype==types.IntType:
            try:
                value=int(input.GetValue())
            except:
                return
        currfilter.setParameter(parameter,value)
                
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
        Created: 13.04.2007, KP
        Description: Initialization
        """        
        ManipulationFilter.__init__(self,(1,1))
    
        self.descs={"KernelX":"X","KernelY":"Y","KernelZ":"Z"}
    
    def getParameters(self):
        """
        Method: getParameters
        Created: 13.04.2007, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [ ["Convolution kernel",("KernelX","KernelY","KernelZ")] ]
        
    def getDesc(self,parameter):
        """
        Method: getDesc
        Created: 13.04.2007, KP
        Description: Return the description of the parameter
        """    
        return self.descs[parameter]
        
    def getType(self,parameter):
        """
        Method: getType
        Created: 13.04.2007, KP
        Description: Return the type of the parameter
        """    
        return types.IntType
        
    def getDefaultValue(self,parameter):
        """
        Method: getDefaultValue
        Created: 13.04.2007, KP
        Description: Return the default value of a parameter
        """           
        return 2
        

    def execute(self,inputs,update=0):
        """
        Method: execute
        Created: 13.04.2007, KP
        Description: Execute the filter with given inputs and return the output
        """            
        if not ManipulationFilter.execute(self,*inputs):
            return None
        
        x,y,z=self.parameters["KernelX"],self.parameters["KernelY"],self.parameters["KernelZ"]
        self.vtkfilter.SetKernelSize(x,y,z)
        
        image = inputs[0]
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
        Created: 13.04.2007, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageContinuousErode3D()
        
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
        Created: 13.04.2007, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageContinuousDilate3D()        
        
class MedianFilter(MorphologicalFilter):
    """
    Class: MedianFilter
    Created: 13.04.2006, KP
    Description: A median filter
    """     
    name = "Median 3D"
    category = MORPHOLOGICAL
    
    def __init__(self):
        """
        Method: __init__()
        Created: 13.04.2007, KP
        Description: Initialization
        """        
        MorphologicalFilter.__init__(self)
        self.vtkfilter = vtk.vtkImageMedian3D()        
