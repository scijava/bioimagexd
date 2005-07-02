# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationModules
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A module containing the various Rendering modules for the visualization
 
 Modified 28.04.2005 KP - Created the class
          24.05.2005 KP - Combined base class for config objects to this mod
          
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

import vtk
from GUI import Events
import ColorTransferEditor
import Dialogs

import glob
import os,sys

def getModules():
    path=reduce(os.path.join,["GUI","Visualization","Modules","*.py"])
    spath=reduce(os.path.join,[os.getcwd(),"GUI","Visualization","Modules"])

    sys.path=sys.path+[spath]

    modules=glob.glob(path)
    moddict={}
    for file in modules:
        mod=file.split(".")[0:-1]
        mod=".".join(mod)
        mod=mod.replace("/",".")
        mod=mod.replace("\\",".")
        frompath=mod
        mod=mod.split(".")[-1]
        print "importing %s from %s"%(mod,frompath)
        module = __import__(mod,globals(),locals(),mod)
        print "module=",module
        name=module.getName()
        modclass=module.getClass()
        settingclass=module.getConfig()
        moddict[name]=(modclass,settingclass,module)
    return moddict

class VisualizationModule:
    """
    Class: VisualizationModule
    Created: 28.04.2005, KP
    Description: A class representing a visualization module
    """
    def __init__(self,parent,visualizer,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """    
        #self.name="Module"
        self.name=kws["label"]
        self.timepoint = -1
        self.parent = parent
        self.visualizer=visualizer
        self.wxrenwin = parent.wxrenwin
        self.renWin = self.wxrenwin.GetRenderWindow()    
        self.renderer = self.parent.getRenderer()
        
    
    def getName(self):
        """
        Method: getName()
        Created: 28.04.2005, KP
        Description: Return the name of this module
        """            
        return self.name
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """            
        self.dataUnit = dataunit
        
    def getDataUnit(self):
        """
        Method: getDataUnit()
        Created: 28.04.2005, KP
        Description: Returns the dataunit this module uses for visualization
        """     
        return self.dataUnit

    def updateData(self):
        """
        Method: updateData()
        Created: 26.05.2005, KP
        Description:"OK Update the data that is displayed
        """          
        self.showTimepoint(self.timepoint)

    def showTimepoint(self,value):
        """
        Method: showTimepoint(tp)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be displayed
        """          
        self.timepoint = value
        
        if self.visualizer.getProcessedMode():
            print "Will render processed data instead"
            self.data = self.dataUnit.doPreview(-1,1,self.timepoint)
        else:
            print "Using timepoint data for tp",value
            self.data = self.dataUnit.getTimePoint(value)

        self.updateRendering()
        
    def disableRendering(self):
        """
        Method: disableRendering()
        Created: 30.04.2005, KP
        Description: Disable the Rendering of this module
        """          
        self.renderer.RemoveActor(self.actor)

        self.wxrenwin.Render()
        
    def enableRendering(self):
        """
        Method: enableRendering()
        Created: 15.05.2005, KP
        Description: Enable the Rendering of this module
        """          
        self.renderer.AddActor(self.actor)
        self.wxrenwin.Render()
        
    def setProperties(self, ambient,diffuse,specular,specularpower):
        """
        Method: setProperties(ambient,diffuse,specular,specularpower)
        Created: 16.05.2005, KP
        Description: Set the ambient, diffuse and specular lighting of this module
        """          
        property=self.actor.GetProperty()
        property.SetAmbient(ambient)
        property.SetDiffuse(diffuse)
        property.SetSpecular(specular)
        property.SetSpecularPower(specularpower)
        
    def setShading(self,shading):
        """
        Method: setShading(shading)
        Created: 16.05.2005, KP
        Description: Set shading on / off
        """          
        property=self.actor.GetProperty()
        if shading:
            property.ShadeOn()
        else:
            property.ShadeOff()
    


class ModuleConfiguration(wx.MiniFrame):
    """
    Class: ModuleConfiguration
    Created: 28.04.2005, KP
    Description: A base class for module configuration dialogs
    """    
    def __init__(self,parent,name):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """     
        wx.MiniFrame.__init__(self,parent.parent,-1,"Configure: %s"%name)
           
        
class ModuleConfigurationPanel(wx.Panel):
    """
    Class: ModuleConfigurationPanel
    Created: 23.05.2005, KP
    Description: A base class for module configuration dialogs
    """    
    def __init__(self,parent,visualizer,name,**kws):
        """
        Method: __init__(parent).parent
        Created: 28.04.2005, KP
        Description: Initialization
        """
        #scrolled.ScrolledPanel.__init__(self,parent.parent,-1)
        self.mode=kws["mode"]
        del kws["mode"]
        wx.Panel.__init__(self,parent,-1,**kws)
        self.sizer = wx.GridBagSizer()
        self.visualizer=visualizer
        self.parent = parent
        self.name = name
        
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        #self.okButton = wx.Button(self,-1,"Ok")
        self.applyButton = wx.Button(self,-1,"Apply")
        #self.cancelButton = wx.Button(self,-1,"Cancel")
        
        #self.okButton.Bind(wx.EVT_BUTTON,self.onOk)
        self.applyButton.Bind(wx.EVT_BUTTON,self.onApply)
        #self.cancelButton.Bind(wx.EVT_BUTTON,self.onCancel)
        
        
        #self.buttonBox.Add(self.okButton)
        self.buttonBox.Add(self.applyButton)
        #self.buttonBox.Add(self.cancelButton)
        
        self.contentSizer = wx.GridBagSizer()
        self.sizer.Add(self.contentSizer,(0,0))
        
        self.toggleBtn=wx.ToggleButton(self,-1,"Lighting>>")
        self.toggleBtn.SetValue(0)
        self.toggleBtn.Bind(wx.EVT_TOGGLEBUTTON,self.onMaterial)
        self.sizer.Add(self.toggleBtn,(1,0))
        
        self.lightPanel=wx.Panel(self,-1)
        self.lightSizer=wx.GridBagSizer()
        self.ambientLbl=wx.StaticText(self.lightPanel,-1,"Ambient lighting:")
        self.diffuseLbl=wx.StaticText(self.lightPanel,-1,"Diffuse lighting:")
        self.specularLbl=wx.StaticText(self.lightPanel,-1,"Specular lighting:")
        self.specularPowerLbl=wx.StaticText(self.lightPanel,-1,"Specular power:")
            
        self.ambientEdit=wx.TextCtrl(self.lightPanel,-1,"0.1")
        self.diffuseEdit=wx.TextCtrl(self.lightPanel,-1,"0.7")
        self.specularEdit=wx.TextCtrl(self.lightPanel,-1,"0.2")
        self.specularPowerEdit=wx.TextCtrl(self.lightPanel,-1,"10.0")
        
        self.lightSizer.Add(self.ambientLbl,(0,0))
        self.lightSizer.Add(self.ambientEdit,(0,1))
        self.lightSizer.Add(self.diffuseLbl,(1,0))
        self.lightSizer.Add(self.diffuseEdit,(1,1))
        self.lightSizer.Add(self.specularLbl,(2,0))
        self.lightSizer.Add(self.specularEdit,(2,1))
        self.lightSizer.Add(self.specularPowerLbl,(3,0))
        self.lightSizer.Add(self.specularPowerEdit,(3,1))
        self.lightPanel.SetSizer(self.lightSizer)
        self.lightSizer.Fit(self.lightPanel)
        
        self.sizer.Add(self.lightPanel,(2,0))
        
        self.line = wx.StaticLine(self,-1)
        self.sizer.Add(self.line,(3,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.sizer.Add(self.buttonBox,(4,0))
        
        self.sizer.Show(self.lightPanel,0)
        self.initializeGUI()
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
        self.findModule()
        
    def onMaterial(self,event):
        """
        Method: onMaterial
        Created: 23.05.2005, KP
        Description: Toggle material configuration
        """     
        val=self.toggleBtn.GetValue()
        lbl="Lighting>>"
        if val:lbl="Lighting<<"
            
        self.toggleBtn.SetLabel(lbl)
        self.sizer.Show(self.lightPanel,val)
        self.Layout()
        self.parent.Layout()
        self.parent.FitInside()
        #self.parent.SetupScrolling()
        
    def onCancel(self,event):
        """
        Method: onCancel()
        Created: 28.04.2005, KP
        Description: Close this dialog
        """     
        #self.Close()
        pass
        
    def onOk(self,event):
        """
        Method: onApply()
        Created: 28.04.2005, KP
        Description: Apply changes and close
        """ 
        self.onApply(None)
        #self.Close()
        
    def onApply(self,event):
        """
        Method: onApply()
        Created: 16.05.2005, KP
        Description: Apply the changes
        """     
        try:
            ambient=float(self.ambientEdit.GetValue())
            diffuse=float(self.diffuseEdit.GetValue())
            specular=float(self.specularEdit.GetValue())
            specularpwr=float(self.specularPowerEdit.GetValue())
        except:
            return
        self.module.setProperties(ambient,diffuse,specular,specularpwr)
        
    def findModule(self):
        """
        Method: findModule()
        Created: 28.04.2005, KP
        Description: Refresh the modules affected by this configuration
        """     
        modules = self.mode.getModules()
        j=0
        for module in modules:
            if module.getName() == self.name:
                self.setModule(module)
                print "Configuring module",module
                return

    def setModule(self,module):
        """
        Method: setModule(module)
        Created: 28.04.2005, KP
        Description: Set the module to be configured
        """  
        print "Module is",module
        self.module = module

