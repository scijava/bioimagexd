# -*- coding: iso-8859-1 -*-

"""
 Unit: Rendering
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A slices viewing rendering mode for Visualizer
 
 Modified 28.04.2005 KP - Created the class
          23.05.2005 KP - Split the class to a module of it's own
          
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx

import DataUnit

import Visualizer.VisualizationFrame as VisualizationFrame

import Visualizer.VisualizerWindow as VisualizerWindow


import PreviewFrame

import Visualizer.VisualizationModules as vmods

import Visualizer.ModuleConfiguration as ModuleConfiguration

import MenuManager
import Visualizer.Lights as Lights

import Modules

import Dialogs

def getName():return "3d"
def getClass():return RenderingMode
def getImmediateRendering(): return False
def getConfigPanel(): return None
def getRenderingDelay(): return 1000
def showZoomToolbar(): return True

        
class RenderingMode:
    def __init__(self,parent,visualizer):
        """
        Method: __init__
        Created: 24.05.2005, KP
        Description: Initialization
        """
        self.parent=parent
        self.menuManager=visualizer.menuManager
        self.visualizer=visualizer
        self.wxrenwin=None
        self.timepoint=0
        self.mapping=Modules.DynamicLoader.getRenderingModules()
        
        self.lightsManager=None
        self.configPanel=None
        self.dataUnit=None
        
        self.defaultModule = "Volume Rendering"
        self.modules = []
        
    def reloadModules(self):
        """
        Method: reloadModules()
        Created: 24.05.2005, KP
        Description: Reload all the visualization modules.
        """
        for key in self.mapping.keys():
            mod,conf,module=self.mapping[key]
            module=reload(module)
            print "Reloaded visualization module",module
            self.mapping[key]=(mod,conf,module)
        
    def showSideBar(self):
        """
        Method: showSideBar()
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return True
        
    def setStereoMode(self,mode):
        """
        Method: setStereoMode()
        Created: 16.05.2005, KP
        Description: Set the stereo rendering mode
        """
        if mode:
            self.renwin.StereoRenderOn()
            cmd="self.renwin.SetStereoTypeTo%s"%mode
            eval(cmd)
        else:
            self.renwin.StereoRenderOff()        
  
    def activate(self,sidebarwin):
        """
        Method: activate()
        Created: 24.05.2005, KP
        Description: Set the mode of visualization
        """
        self.sidebarWin=sidebarwin
        # If we're preloading, don't create the render window
        # since it will mess up the rendering
        if not self.wxrenwin and not self.visualizer.preload:
            self.wxrenwin = VisualizerWindow.VisualizerWindow(self.parent,size=(512,512))
            self.wxrenwin.Render()
            self.GetRenderWindow=self.wxrenwin.GetRenderWindow
            self.renwin=self.wxrenwin.GetRenderWindow()
    
            self.wxrenwin.Render()
    
            self.getRenderer=self.GetRenderer=self.wxrenwin.getRenderer

        if not self.configPanel:
            # When we embed the sidebar in a sashlayoutwindow, the size
            # is set correctly
            self.container = wx.SashLayoutWindow(self.sidebarWin)
            
            self.configPanel = VisualizationFrame.ConfigurationPanel(self.container,self.visualizer,self)
            self.configPanel.Show()
        else:
            self.configPanel.Show()
            
        if self.visualizer.preload:
            return self.parent
        if not self.lightsManager:
            self.lightsManager = Lights.LightManager(self.parent, self.wxrenwin, self.getRenderer(), mode='raymond')

        mgr=self.menuManager
        
        mgr.enable(MenuManager.ID_LIGHTS,self.configPanel.onConfigureLights)
        mgr.enable(MenuManager.ID_RENDERWIN,self.configPanel.onConfigureRenderwindow)
        
        return self.wxrenwin
        
    def saveSnapshot(self,filename):
        """
        Method: saveSnapshot(filename)
        Created: 05.06.2005, KP
        Description: Save a snapshot of the scene
        """      
        self.wxrenwin.save_screen(filename)
        
    def Render(self):
        """
        Method: Render()
        Created: 24.05.2005, KP
        Description: Update the rendering
        """      
        self.wxrenwin.Render()        
        
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """        
        ren=self.wxrenwin.getRenderer()
        r/=255.0
        g/=255.0
        b/=255.0
        ren.SetBackground(r,g,b)
        
    def updateRendering(self):
        """
        Method: updateRendering
        Created: 26.05.2005, KP
        Description: Update the rendering
        """      
        if not self.visualizer.enabled:
            print "Visualizer not enabled, won't render!"
            return
        for module in self.modules:
            module.showTimepoint(self.timepoint)
            module.updateRendering()
        self.wxrenwin.Render()
        
    def deactivate(self):
        """
        Method: deactivate()
        Created: 24.05.2005, KP
        Description: Unset the mode of visualization
        """
        if self.wxrenwin:
            self.wxrenwin.Show(0)       
        self.configPanel.Show(0) 
        
        mgr=self.menuManager
        
        mgr.disable(MenuManager.ID_LIGHTS)
        mgr.disable(MenuManager.ID_RENDERWIN)
        
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 25.05.2005, KP
        Description: Set the dataunit to be visualized
        """
        self.dataUnit=dataUnit
        if not len(self.modules):
            self.loadModule(self.defaultModule)
            self.configPanel.appendModuleToList(self.defaultModule)
        for module in self.modules:
            module.setDataUnit(dataUnit)
        
            
    def getConfigurationPanel(self,name):
        """
        Method: getConfigurationPanel(name)
        Created: 23.05.2005, KP
        Description: Return the configuration panel of a module
        """
        conf=None
        return self.mapping[name][1]

    def removeModule(self,name):
        """
        Method: removeModule(name)
        Created: 28.04.2005, KP
        Description: Remove a visualization module
        """
        to_be_removed=[]
        for module in self.modules:
            if module.getName()==name:
                to_be_removed.append(module)
        for module in to_be_removed:
            print "Removing module ",module
            module.disableRendering()
            self.modules.remove(module)
            del module

    def setRenderingStatus(self,name,status):
        """
        Method: setRenderingStatus(name,status)
        Created: 15.05.2005, KP
        Description: Enable / disable rendering of a module
        """
        for module in self.modules:
            if module.getName()==name:
                if not status:
                    module.disableRendering()
                else:
                    module.enableRendering()

    def loadModule(self,name,lbl=None):
        """
        Method: loadModule(name,lbl)
        Created: 28.04.2005, KP
        Description: Load a visualization module
        """
        if not lbl:lbl=name
        if not self.dataUnit:
            Dialogs.showerror(self.parent,"No dataset has been loaded for visualization","Cannot load visualization module")
            return
        self.wxrenwin.initializeVTK()
        module = self.mapping[name][0](self,self.visualizer,label=lbl)
        self.modules.append(module)
        module.setDataUnit(self.dataUnit)
        module.showTimepoint(self.timepoint)
            
    def getModules(self):
        """
        Method: getModules()
        Created: 28.04.2005, KP
        Description: Return the modules
        """  
        return self.modules
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 25.05.2005, KP
        Description: Set the timepoint to be visualized
        """
        self.timepoint=tp
        for module in self.modules:
            module.showTimepoint(self.timepoint)


