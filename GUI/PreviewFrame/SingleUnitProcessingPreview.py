# -*- coding: iso-8859-1 -*-

"""
 Unit: PreviewFrame.py
 Project: Selli
 Created: 03.11.2004
 Creator: KP
 Description:

 A widget that can be used to Preview any operations done by a subclass of Module

 Modified 03.11.2004 KP - Methods for colocalization window to pass on the file 
                          names to be processed
          04.11.2004 KP - Inherited specialized preview classes from the 
                          PreviewFrame
          08.11.2004 KP - Preview now uses the dataunit's doPreview() method to do 
                      the preview. No more nosing around with dataunits internal
                      structure
          08.11.2004 KP - Preview now uses the color of the dataunits
          08.11.2004 KP - The preview is now generated in a single image at the
                          specified depth, and the previewed depth is controlled
                          with vtkImageMapper's SetZSlice()-method
          09.11.2004 KP - Added the ability to display a pixels value
          10.11.2004 JV - Added class ColorCombinationPreview (made after 
                          ColocalizationPreview)
          11.11.2004 JV - Changed updateDepth so that it works with color merging
                          preview
          16.11.2004 KP - Refactoring code from ColocalizationPreview back to the 
                          base class PreviewFrame
          13.12.2004 KP - Added code for previewing in MayaVi

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 ""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.63 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"
"""
import os.path
import RenderingInterface

from PreviewFrame import *
import wx

from Logging import *
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
import vtk
import wx.lib.scrolledpanel as scrolled

class SingleUnitProcessingPreview(PreviewFrame):
    """
    Class: SingleUnitProcessingPreview
    Created: 03.11.2004
    Creator: KP
    Description: A widget inherited from PreviewFrame that displays a preview of
                 a single processed dataunit.
    """
    def __init__(self,master,parentwin=None,**kws):
        PreviewFrame.__init__(self,master,parentwin,**kws)
        self.running=0
        self.mapToColors=vtk.vtkImageMapToColors()
        self.mapToColors.SetLookupTable(self.currentCt)
        self.mapToColors.SetOutputFormatToRGB()
        
        
    def updateColor(self):
        """
        Method: updateColor()
        Created: 20.11.2004, KP
        Description: Update the preview to use the selected color transfer 
                     function
        Parameters:
        """
        if self.dataUnit:
            self.rgb = self.settings.get("Color")
            print "Got color ",self.rgb            
        self.currentCt=ImageOperations.getColorTransferFunction(self.rgb)
        self.mapToColors.SetLookupTable(self.currentCt)
        self.mapToColors.SetOutputFormatToRGB()

    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.11.2004, KP
        Description: Update the preview
        Parameters:
        renew    Whether the method should recalculate the images
        """
        if not self.dataUnit:
            return
        self.updateColor()
        if not self.running:
            renew=1
            self.running=1
        try:
            preview=self.dataUnit.doPreview(self.z,renew,self.timePoint)
        except GUIError, ex:
            ex.show()
            return
        if not preview:
            raise "Did not get a preview"
        self.currentImage=preview
        if self.renderingPreviewEnabled()==True:
            self.updateColor()
            return self.previewInMayavi(preview,self.currentCt,
            renew)
        

        self.mapToColors.RemoveAllInputs()
        self.mapToColors.SetInput(preview)
        colorImage=self.mapToColors.GetOutput()
        
        colorImage.SetUpdateExtent(preview.GetExtent())
        
        x,y,z=preview.GetDimensions()
    
        if x!=self.oldx or y!=self.oldy:
            self.renderpanel.resetScroll()
            self.renderpanel.setScrollbars(x,y)
            self.oldx=x
            self.oldy=y
            
        self.mapToColors.Update()

        self.renderpanel.setZSlice(self.z)
        self.renderpanel.setImage(colorImage)
        self.renderpanel.updatePreview()
    
        self.finalImage=colorImage
