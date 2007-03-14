#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: RegistrationFilters
 Project: BioImageXD
 Created: 14.03.2007, KP
 Description:

 A module containing the registration filters for the processing task.
                            
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
import csv
import codecs
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

from lib.ProcessingFilter import FILTER_BEGINNER, FILTER_EXPERIENCED
import  wx.lib.mixins.listctrl  as  listmix
SEGMENTATION="Segmentation"
#ITK="ITK"

MEASUREMENT="Measurements"
WATERSHED="Watershed segmentation"
REGIONGROWING="Region growing"
REGISTRATION="Registration"


class RegistrationFilter(ProcessingFilter.ProcessingFilter):
    """
    Created: 14.03.2007, KP
    Description: A filter for doing registration
    """     
    name = "Morphological watershed segmentation"
    category = SEGMENTATION
    level = FILTER_EXPERIENCED
    def __init__(self,inputs=(1,1)):
        """
        Created: 14.03.2007, KP
        Description: Initialization
        """        
        ProcessingFilter.ProcessingFilter.__init__(self,inputs)
        
        self.descs = {"FixedTimepoint":"Timepoint for fixed image"}
        self.itkFlag = 1
        
    def getParameterLevel(self, parameter):
        """
        Created: 14.03.2007, KP
        Description: Return the level of the given parameter
        """
        if parameter in ["FixedTimepoint"]:
            return GUIBuilder.FILTER_INTERMEDIATE
        
        
        return GUIBuilder.FILTER_BEGINNER                    
            
    def getDefaultValue(self,parameter):
        """
        Created: 14.03.2007, KP
        Description: Return the default value of a parameter
        """    
        if parameter == "FixedTimepoint":
            return 0
        
        return 0
        
    def getRange(self, parameter):
        """
        Created: 14.03.2007, KP
        Description: return the range for a given parameter
        """
        if parameter == "FixedTimepoint":
            return (0,self.dataUnit.getLength())
    def getType(self,parameter):
        """
        Created: 14.03.2007, KP
        Description: Return the type of the parameter
        """    
        if parameter == "FixedTimepoint":
            return GUIBuilder.SLICE
        return types.IntType
             
        
    def getParameters(self):
        """
        Created: 14.03.2007, KP
        Description: Return the list of parameters needed for configuring this GUI
        """            
        return [["",("FixedTimepoint",)]]

    def onRemove(self):
        """
        Created: 14.03.2007, KP
        Description: Restore palette upon filter removal
        """        
        if self.origCtf:            
            self.dataUnit.getSettings().set("ColorTransferFunction",self.origCtf)            
            
    
    def execute(self,inputs,update=0,last=0):
        """
        Created: 14.03.2007, KP
        Description: Execute the filter with given inputs and return the output
        """                    
        if not ProcessingFilter.ProcessingFilter.execute(self,inputs):
            return None
            
        units=self.dataUnit.getSourceDataUnits()
        tp1 = self.parameters["FixedTimepoint"]
        tp2 = self.getCurrentTimePoint()
        if tp2 >=units[0].getLength():
            tp2 = units[0].getLength()-1
        data1=units[0].getTimePoint(tp1)
        # We need to prepare a copy of the data since
        # when we get the next timepoint, the data we got earlier will reference the
        # new data
        tp = vtk.vtkImageData()
        tp.DeepCopy(data1)
        data2=units[0].getTimePoint(tp2)
        data1=tp
        data1.Update()
        data2.Update()
        fixed = self.convertVTKtoITK(data1,cast=types.FloatType)
        moving = self.convertVTKtoITK(data2,cast=types.FloatType)
        
        
        self.transform = itk.VersorRigid3DTransform.D.New()
        self.optimizer = itk.VersorRigid3DTransformOptimizer.New()
        self.metric = itk.MeanSquaresImageToImageMetric.IF3IF3.New()
        self.interpolator = itk.LinearInterpolateImageFunction.IF3D.New()
        self.registrationMethod = itk.ImageRegistrationMethod.IF3IF3.New()
        
        self.registrationMethod.SetMetric( self.metric )
        self.registrationMethod.SetOptimizer( self.optimizer )
        self.registrationMethod.SetInterpolator( self.interpolator )
        self.registrationMethod.SetTransform (self.transform )
        
        
        self.registrationMethod.SetFixedImage(fixed)
        self.registrationMethod.SetMovingImage(moving)
        
        self.registrationMethod.SetFixedImageRegion(fixed.GetBufferedRegion())
        
        initializer = itk.CenteredTransformInitializer[self.transform, fixed, moving].New()
        initializer.SetTransform( transform )
        initializer.SetFixedImage( fixed )
        initializer.SetMovingImage( moving )
        initializer.MomentsOn()
        initializer.InitializeTransform()
        
        self.transform.VersorR
        t =time.time()
        print "Registration took",time.time()-t,"seconds"
        return data

        
