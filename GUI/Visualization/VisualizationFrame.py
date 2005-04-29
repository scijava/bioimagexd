# -*- coding: iso-8859-1 -*-

"""
 Unit: VisualizationFrame
 Project: BioImageXD
 Created: 28.04.2005, KP
 Description:

 A framework for replacing MayaVi for simple rendering tasks.
 
 Modified 28.04.2005 KP - Created the class
          
 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx

import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from Events import *
import Dialogs
from VisualizationModules import *
from Lights import *

class ConfigurationPanel(wx.Panel):
    """
    Class: ConfigurationPanel
    Created: 28.04.2005, KP
    Description: A panel that can be used to configure the rendering
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """    
        wx.Panel.__init__(self,parent,-1)
        self.sizer = wx.GridBagSizer()
        self.parent = parent
        
        self.moduleLbl = wx.StaticText(self,-1,"Rendering module:")
        self.moduleChoice = wx.Choice(self,-1,choices=["Volume Rendering"])
        self.moduleLoad = wx.Button(self,-1,"Load")
        self.moduleLoad.Bind(wx.EVT_BUTTON,self.onLoadModule)
        self.lightsBtn = wx.Button(self,-1,"Lights")
        self.lightsBtn.Bind(wx.EVT_BUTTON,self.onConfigureLights)
        
        
        self.sizer.Add(self.moduleLbl,(0,0))
        self.sizer.Add(self.moduleChoice,(1,0))
        
        
        box=wx.BoxSizer(wx.HORIZONTAL)
        self.configureBtn = wx.Button(self,-1,"Configure")
        self.configureBtn.Bind(wx.EVT_BUTTON,self.onConfigureModule)
  
        box.Add(self.moduleLoad)
        box.Add(self.configureBtn)
        self.sizer.Add(box,(2,0))
        self.sizer.Add(self.lightsBtn,(3,0))
        
        #self.sizer.Add(self.configureBtn,(3,0))
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def onConfigureLights(self,event):
        """
        Method: onConfigureLights
        Created: 29.04.2005, KP
        Description: Configure the lights
        """            
        ren=self.parent.getRenderer()
        lm = LightManager(self, self.parent.wxrenwin, ren, mode='raymond')
        lm.config()
        
        
    def onLoadModule(self,event):
        """
        Method: onLoadModule
        Created: 28.04.2005, KP
        Description: Load the selected module
        """            
        self.parent.loadModule(self.moduleChoice.GetStringSelection())
        
    def onConfigureModule(self,event):
        """
        Method: onConfigureModule
        Created: 28.04.2005, KP
        Description: Load the selected module
        """            
        self.parent.configureModule(self.moduleChoice.GetStringSelection())        

class VisualizationFrame2(wx.Frame):
    """
    Class: VisualizationFrame
    Created: 28.04.2005, KP
    Description: A window for showing 3D visualizations
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """    
        self.renderer=None
        self.closed=0
        wx.Frame.__init__(self,parent,-1,"BioImageXD Visualization",**kws)
        self.sizer=wx.GridBagSizer()
        
        self.frame=VisualizationPanel(self)
        self.Bind(wx.EVT_CLOSE,self.onClose)
        self.setDataUnit=self.frame.setDataUnit
    
        self.sizer.Add(self.frame,(0,0))
    
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)


class VisualizationFrame(wx.Frame):
    """
    Class: VisualizationFrame
    Created: 28.04.2005, KP
    Description: A window for showing 3D visualizations
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent)
        Created: 28.04.2005, KP
        Description: Initialization
        """    
        self.closed =0
        self.renderer=None
        self.timepoint = -1
        self.mapping= {"Volume Rendering":(VolumeModule,VolumeConfiguration)}#,"Maximum Intensity Projection":MIPModule}
        self.modules = []
        wx.Frame.__init__(self,parent,-1,"BioImageXD Visualization",**kws)
#        wx.Panel.__init__(self,parent,-1)
        self.sizer = wx.GridBagSizer()
        self.wxrenwin = wxVTKRenderWindowInteractor(self,-1,size=(512,512))
        self.renwin=self.wxrenwin.GetRenderWindow()        
        self.GetRenderWindow=self.wxrenwin.GetRenderWindow
                
        self.GetRenderer=self.getRenderer

        self.configPanel = ConfigurationPanel(self)
        self.sizer.Add(self.configPanel,(0,0),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)
        
        self.sizer.Add(self.wxrenwin,(0,1),flag=wx.EXPAND|wx.ALL)
        self.timeslider=wx.Slider(self,value=0,minValue=0,maxValue=1,
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.sizer.Add(self.timeslider,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT,span=(1,2))        
        self.timeslider.Bind(wx.EVT_SCROLL,self.onChangeTimepoint)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    def getRenderer(self):
        """
        Method: getRenderer
        Created: 28.04.2005, KP
        Description: Return the renderer
        """            
        return self.renderer
        
    def onClose(self,event):
        """
        Method: onClose()
        Created: 28.04.2005, KP
        Description: Called when this window is closed
        """            
        self.closed = 1
        
    def isClosed(self):
        """
        Method: isClosed()
        Created: 28.04.2005, KP
        Description: Returns flag indicating the closure of this window
        """            
        return self.closed
        

    def save_png(self,filename):
        """
        Method: save_png(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as png
        """            
        self.saveScreen(vtk.vtkPNGWriter(),filename)
        
    def save_jpeg(self,filename):
        """
        Method: save_jpeg(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as jpeg
        """            
        self.saveScreen(vtk.vtkJPEGWriter(),filename)
    def save_tiff(self,filename):
        """
        Method: save_tiff(self,filename)
        Created: 28.04.2005, KP
        Description: Save the rendered screen as jpeg
        """            
        self.saveScreen(vtk.vtkTIFFWriter(),filename)
        
    def saveScreen(self,writer,filename):
        """
        Method: saveScreen(writer,filename)
        Created: 28.04.2005, KP
        Description: Writes the screen to disk
        """            
        writer.SetFileName(filename)
        filter = vtk.vtkWindowToImageFilter()
        filter.SetInput(self.renwin)
        writer.SetInput(filter.GetOutput())
        writer.Write()
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit(self)
        Created: 28.04.2005, KP
        Description: Sets the dataunit this module uses for visualization
        """            
        self.dataUnit = dataunit
        count=dataunit.getLength()
        self.timeslider.SetRange(0,count-1)

        
    def getModules(self):
        """
        Method: getModules()
        Created: 28.04.2005, KP
        Description: Return the modules
        """  
        return self.modules
        
    def render(self):
        """
        Method: render()
        Created: 28.04.2005, KP
        Description: Render the scene
        """  
        self.wxrenwin.Render()
    
    def configureModule(self,name):
        """
        Method: configureModule(name)
        Created: 28.04.2005, KP
        Description: Configure a visualization module
        """  
        conf = self.mapping[name][1](self)
        conf.Show()

    def loadModule(self,name):
        """
        Method: loadModule(name)
        Created: 28.04.2005, KP
        Description: Load a visualization module
        """  
        self.renderer = vtk.vtkRenderer()
        self.renwin.AddRenderer(self.renderer)
        
        if not self.dataUnit:
            Dialogs.showerror(self,"No dataset has been loaded for visualization","Cannot load visualization module")
            return
        module = self.mapping[name][0](self)
        self.modules.append(module)
        module.setDataUnit(self.dataUnit)
        module.showTimepoint(self.timepoint)
        
    def onChangeTimepoint(self,event):
        """
        Method: onChangeTimepoint
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """  
        tp=self.timeslider.GetValue()
        if self.timepoint != tp:
            self.setTimepoint(tp)
            
    def setRenderWindowSize(self,size):
        """
        Method: setRenderWindowSize(size)
        Created: 28.04.2005, KP
        Description: Set the render window size
        """  
        self.wxrenwin.SetSize((size))
        self.renwin.SetSize((size))
        self.Layout()
        self.Refresh()
        self.render()
        
    def setTimepoint(self,timepoint):
        """
        Method: setTimepoint(timepoint)
        Created: 28.04.2005, KP
        Description: Set the timepoint to be shown
        """  
        if self.timeslider.GetValue()!=timepoint:
            self.timeslider.SetValue(timepoint)
        self.timepoint = timepoint
        for module in self.modules:
            module.showTimepoint(self.timepoint)
