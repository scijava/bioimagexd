# -*- coding: iso-8859-1 -*-

"""
 Unit: RenderingManager
 Project: BioImageXD
 Created: 10.11.2004, KP
 Description:

 The window that is used for selecting the timepoints that are sent to MayaVi
 to be rendered.

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

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import os.path

from PreviewFrame import *
import sys
import RenderingInterface
import Logging
import Dialogs
import vtk
from TimepointSelection import *

    
    
import wx.lib.scrolledpanel as scrolled

class RenderingManager(TimepointSelection):
    """
    Class: RenderingManager
    Created: 10.11.2004
    Creator: KP
    Description: The window that is used to select the timepoints that are sent
                 to MayaVi to be rendered.
    """

    def __init__(self,parent):
        """
        Method: __init__
        Created: 10.11.2004
        Creator: KP
        Description: Initialization
        """
        TimepointSelection.__init__(self,parent)
        self.parent=parent
        self.rendering=0
        self.SetTitle("Rendering Manager")
        self.createConfigFrame()

        self.setLabel("Select Time Points to be Rendered")
        self.renderint=RenderingInterface.getRenderingInterface()

        #self.panel.mainsizer.Layout()
        
        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.mainsizer.SetSizeHints(self)

        self.mainsizer.Fit(self)
        
    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 31.1.2005
        Creator: KP
        Description: Creates the standard control buttons
        """
        TimepointSelection.createButtonBox(self)

        self.createSettingsBtn=wx.Button(self,-1,"Create MayaVi settings")
        self.createSettingsBtn.Bind(EVT_BUTTON,self.createVisualization)
        self.buttonsSizer1.Add(self.createSettingsBtn,flag=wx.ALIGN_LEFT)
        self.actionBtn.SetLabel("Render")
        self.actionBtn.Bind(EVT_BUTTON,self.doRendering)
        

    def createConfigFrame(self):
        """
        Method: createConfigFrame(self)
        Created: 17.11.2004
        Creator: KP
        Description: A callback that is used to close this window
        """             
        self.configSizer=wx.GridBagSizer()
        self.rendir=wx.TextCtrl(self,size=(350,-1))
        self.rendirLbl=wx.StaticText(self,
        -1,"Directory for rendered frames:")
        
        self.dirBtn=wx.Button(self,-1,"...")
        self.dirBtn.Bind(EVT_BUTTON,self.selectDirectory)

        self.configSizer.Add(self.rendirLbl,(1,0))
        self.configSizer.Add(self.rendir,(2,0))
        self.configSizer.Add(self.dirBtn,(2,1))
        
        self.mvfile=wx.TextCtrl(self,size=(350,-1))
        self.mvfileLbl=wx.StaticText(self,-1,"MayaVi Settings file:")
        self.mvfileBtn=wx.Button(self,-1,"...")
        self.mvfileBtn.Bind(EVT_BUTTON,self.loadVisualization)
        
        self.configSizer.Add(self.mvfileLbl,(3,0))
        self.configSizer.Add(self.mvfile,(4,0))
        self.configSizer.Add(self.mvfileBtn,(4,1))
        
        self.mainsizer.Add(self.configSizer,(1,0),flag=wx.EXPAND|wx.ALL)
        print "Added some stuff"
        

    def selectDirectory(self,event=None):
        """
        Method: selectDirectory()
        Created: 10.11.2004
        Creator: KP
        Description: A callback that is used to select the directory where
                     the rendered frames are stored
        """
        dirname=Dialogs.askDirectory(self,"Directory for rendered frames",".")
        self.rendir.SetValue(dirname)

    def createVisualization(self,event=None):
        """
        Method: createVisualization()
        Created: 30.11.2004
        Creator: KP
        Description: A callback that is used to create a .mv file for use in the
                     rendering. This is done by opening MayaVi and letting user
                     define the camera, module etc. settings
        """
        self.renderint.setDataUnit(self.dataUnit)
        self.renderint.setTimePoints([0])
        self.renderint.setOutputPath(self.rendir.GetValue())
        
        initFile="settings.mv"
        wc="Mayavi Settings File (*.mv)|*.mv"
        filename=""
        dlg=wx.FileDialog(self,"Create Mayavi Settings file",defaultFile=initFile,wildcard=wc,style=wx.SAVE)
        filename=None
        if dlg.ShowModal()==wx.ID_OK:
            filename=dlg.GetPath()
        dlg.Destroy()
        if filename:
            if filename[-3:].lower()!=".mv":
                filename+=".mv"            
        if not filename:
            return
        try:
            self.renderint.createVisualization(filename)
        except Logging.GUIError, ex:
            ex.show()
            return
        self.mvfile.SetValue(filename)

    def loadVisualization(self,event=None):
        """
        Method: loadVisualization()
        Created: 30.11.2004
        Creator: KP
        Description: A callback that is used to load a .mv file for use in the 
                     rendering. This file has been created in MayaVi and had 
                     user defined the camera, module etc. settings
        """
        initFile="settings.mv"
        wc="Mayavi Settings File (*.mv)|*.mv"
        filename=""
        dlg=wx.FileDialog(self,"Create Mayavi Settings file",defaultFile=initFile,wildcard=wc,style=wx.OPEN)
        if dlg.ShowModal()==wx.ID_OK:
            filename=dlg.GetPath()
        dlg.Destroy()

        if not filename:
            return
        else:
            self.mvfile.SetValue(filename)

    def doRendering(self,event=None):
        """
        Method: doRendering
        Created: 10.11.2004
        Creator: KP
        Description: A method that sends the selected frames to be rendered
        """
        if self.rendering:
            Dialogs.showWarning(self,"You are already rendering a dataset","Already rendering")
            return
        self.rendering=1
        Logging.info("Is mayavi running: ",self.renderint.isMayaviRunning())
        if not self.renderint.isMayaviRunning() and not os.path.isfile(
        self.mvfile.GetValue()):
            Dialogs.showWarning(self,
            "You have to load a mayavi settings file before rendering a dataset",
            "Invalid settings file file")
            return
        timepoints=self.getSelectedTimepoints()
        if len(timepoints)==0:
            Dialogs.showError(self,
            "You have not selected any frames to be rendered.\n"
            "Please select at least one frame to be rendered and try again.\n",
            "Select at least one frame to render")
            return
        self.renderint.setDataUnit(self.dataUnit)
        self.renderint.setTimePoints(timepoints)
        self.renderint.setOutputPath(self.rendir.GetValue())
        try:
            if self.renderint.isMayaviRunning():
                Logging.info("Using existing mayavi instance")
                self.renderint.doRendering(use_existing=1)
            else:
                self.renderint.doRendering(visualization=self.mvfile.GetValue())
        except Logging.GUIError, ex:
            ex.show()
        self.rendering=0
