#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasTimepointSelection
 Project: BioImageXD
 Created: 12.03.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This is a timeline based GUI for controlling the rendering of datasets. The GUI allows users
 to specify a path for the camera to follow (using Heikki Uuksulainen's MayaVi animator code)
 and also allows them to produce videos of the rendering using ffmpeg.
 
 This is the wxPanel based class implementing a timepoint selection.
 
 Modified: 12.03.2005 KP - Created the module
 
 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import wx.wizard
import TimepointSelection

class UrmasTimepointSelection(wx.wizard.PyWizardPage):
    """
    Class: UrmasTimepointSelection
    Created: 12.03.2005, KP
    Description: Implements selection of timepoints for Urmas
    """     
    def __init__(self,parent):
        wx.wizard.PyWizardPage.__init__(self,parent)
        self.timepointSelection=TimepointSelection.TimepointSelectionPanel(self)
        
    def GetNext(self):
        """
        Method: GetNext()
        Created: 14.03.2005, KP
        Description: Returns the page that comes after this one
        """          
        return self.next
        
    def GetPrev(self):
        """
        Method: GetPrev()
        Created: 14.03.2005, KP
        Description: Returns the page that comes before this one
        """              
        return self.prev
        
    def setDataUnit(self,du):
        """
        Method: setDataUnit
        Created: 12.03.2005, KP
        Description: Sets the dataunit
        """          
        self.timepointSelection.setDataUnit(du)
