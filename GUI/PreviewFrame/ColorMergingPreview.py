# -*- coding: iso-8859-1 -*-

"""
 Unit: ColorMergingPreviewFrame.py
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
 JH - Juha Hyyti�inen, juhyytia@st.jyu.fi
 JM - Jaakko M�ntymaa, jahemant@cc.jyu.fi
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


class ColorMergingPreview(PreviewFrame):
    """
    Class: ColorCombinationPreview
    Created: 10.11.2004, JV
    Description: A widget inherited from PreviewFrame that displays a preview of
                 color combination. Made after ColocalizationPreview.
    """
    def __init__(self,master,parentwin=None,**kws):
        PreviewFrame.__init__(self,master,parentwin,**kws)
        self.mapper=vtk.vtkImageMapper()
        self.mapper.SetZSlice(self.z)
        self.mapper.SetColorWindow(255.0);
        self.mapper.SetColorLevel(127.5);

        self.actor=vtk.vtkActor2D()
        self.actor.SetMapper(self.mapper)
        self.renderer.AddActor(self.actor)
        self.mapToColors=vtk.vtkImageMapToColors()
        self.mapToColors.SetLookupTable(self.getColorTransferFunction())
        self.mapToColors.SetOutputFormatToRGB()

        self.running=0
        self.rgbMode=1

    def getColorTransferFunction(self):
    	ct=vtk.vtkColorTransferFunction()
    	br,bg,bb=self.bgColor
        r2,g2,b2=self.rgb
        r2/=255.0
        g2/=255.0
        b2/=255.0

        ct.AddRGBPoint(0,0,0,0)
        r,g,b=255,0,0
        r/=255.0
        g/=255.0
        b/=255.0
        ct.AddRGBPoint(255,r,g,b)
        self.currentCt=ct
        return ct


    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.11.2004, KP
        Description: Update the preview
        Parameters:
        renew    Whether the method should recalculate the images
        """

        if not self.running:
            renew=1
            self.running=1
        try:
            preview=self.dataUnit.doPreview(self.z,renew,self.timePoint)
        except GUIError, ex:
            ex.show()
            return
        if self.renderingPreviewEnabled()==True:
            return self.previewInMayavi(preview,None,renew)

    	self.mapper.SetZSlice(self.z)
    	if not preview:
    	    raise "Did not get a preview"
    	# Update the lookup table if colors have changed
#    	self.mapToColors.SetInput(preview)
#    	self.mapToColors.Update()
#    	self.currentImage=self.mapToColors.GetOutput()
        self.currentImage=preview
        self.mapper.SetInput(self.currentImage)
        self.renwin.Render()
