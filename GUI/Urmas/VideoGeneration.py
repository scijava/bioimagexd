#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: VideoGeneration
 Project: BioImageXD
 Created: 10.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This module contains a panel that can be used to control the creation of a movie
 out of a set of rendered images.
 
 Modified: 10.02.2005 KP - Created the module
 
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

class VideoGeneration(wx.wizard.PyWizardPage):
    """
    Class: VideoGeneration
    Created: 23.02.2005, KP
    Description: A panel for controlling the movie generation.        
    """
    def __init__(self,parent):
        wx.wizard.PyWizardPage.__init__(self,parent)
        self.mainsizer=wx.GridBagSizer()

        
        self.SetSizer(self.mainsizer)
        self.SetAutoLayout(True)
        self.mainsizer.Fit(self)
        
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
