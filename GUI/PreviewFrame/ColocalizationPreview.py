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
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.63 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path
import RenderingInterface
from PreviewFrame import *
import wx

from Logging import *
#from vtk import *
import vtk
import wx.lib.scrolledpanel as scrolled

class ColocalizationPreview(PreviewFrame):
    """
    Class: ColocalizationPreview
    Created: 03.11.2004, KP
    Description: A widget inherited from PreviewFrame that displays a preview of
                 colocalization.
    """
    def __init__(self,master,parentwin=None,**kws):
        PreviewFrame.__init__(self,master,parentwin,**kws)

        self.mapToColors=vtk.vtkImageMapToColors()
        self.mapToColors.SetOutputFormatToRGB()

        self.running=0

        self.colocpercentLbl=wx.StaticText(self,-1,"0 of 0 (0%) possible voxels colocalizing")
        self.sizer.Add(self.colocpercentLbl,(4,0))
        self.Layout()

    def updateColor(self):
        """
        Method: updateColor()
        Created: 20.11.2004, KP
        Description: Update the preview to use the selected color transfer
                     function
        Parameters:
        """
        self.rgb=self.dataUnit.getColor()
        self.currentCt=ImageOperations.getColorTransferFunction(self.rgb)
        self.mapToColors.SetLookupTable(self.currentCt)

    def updatePreview(self,renew=1):
        """
        Method: updatePreview(renew=1)
        Created: 03.11.2004, KP
        Description: Update the preview
        Parameters:
                renew    Whether the method should recalculate the images
        """
        self.updateColor()
        if not self.running:
            renew=1
            self.running=1
        try:
        	preview=self.dataUnit.doPreview(self.z,renew,self.timePoint)
        except GUIError, ex:
            ex.show()
            return
        if self.renderingPreviewEnabled()==True:
            return self.previewInMayavi(preview,self.getColorTransferFunction(),
            renew)

    	if not preview:
    	    raise "Did not get a preview"
    	# Update the lookup table if colors have changed

        self.mapToColors.SetInput(preview)
        colorImage=self.mapToColors.GetOutput()        
        colorImage.SetUpdateExtent(preview.GetExtent())        
        self.mapToColors.Update()
        
        self.currentImage=self.mapToColors.GetOutput()
        x,y,z=preview.GetDimensions()
        if x!=self.oldx or y!=self.oldy:
            self.renderpanel.resetScroll()
            self.renderpanel.setScrollbars(x,y)
            self.oldx=x
            self.oldy=y
        
        self.renderpanel.setZSlice(self.z)
        
        self.finalImage=self.currentImage
        self.renderpanel.setImage(self.currentImage)
        self.renderpanel.updatePreview()        
        
        coloc,least=self.dataUnit.getColocalizationInfo()
        percent=float(coloc)/least

        self.colocpercentLbl.SetLabel("%d of %d (%.2f%%) possible voxels colocalizing"%\
        (coloc,least,100*percent))
