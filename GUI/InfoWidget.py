# -*- coding: iso-8859-1 -*-

"""
 Unit: InfoWidget.py
 Project: BioImageXD
 Created: 21.02.2005
 Creator: KP
 Description:

 A widget that displays information about channels/dataset series selected in 
 the tree view.

 Modified 21.02.2005 KP - Created the class
          
 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import os.path
import wx, wx.html

from Logging import *

import DataUnit
import PreviewFrame
import DataUnitProcessing
import ColorMerging

import ColorTransferEditor



smX="<font size=\"-1\">x</font>"
infoString="""<html><body bgcolor=%(bgcolor)s">
<table>
<tr><td>Dimensions:</td><td>%(xdim)d %(smX)s %(ydim)d %(smX)s %(zdim)d (%(nf)s%(xdimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(ydimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(zdimm).2f%(fe)s&mu;m)</td></tr>
<tr><td>Time Points:</td><td>%(tps)d</td></tr>
<tr><td>Voxel Size:</td><td>%(nf)s%(voxelX).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelY).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelZ).2f%(fe)s&mu;m</td></tr>
<tr><td>Spacing:</td><td>%(spX).2f %(smX)s %(spY).2f %(smX)s %(spZ).2f</td></tr>
<tr><td>Data type:</td><td>%(bitdepth)s bit</td></tr>
</table>
</body></html>
"""

class InfoWidget(wx.Panel):
    """
    Class: InfoWidget
    Created: 03.11.2004
    Creator: KP
    Description: A class for displaying information about selected datasets
                 of given type
    """
    def __init__(self,master,**kws):
        """
        Method: __init__
        Created: 03.11.2004
        Creator: KP
        Description: Initialization for the Info node
        """
        wx.Panel.__init__(self,master,-1,**kws)
        self.mainsizer=wx.GridBagSizer(5,5)

        
        self.preview=PreviewFrame.IntegratedPreview(self,
        previewsize=(384,384),pixelvalue=False,renderingpreview=False,
        zoom=False,timeslider=False,scrollbars=False,zoom_factor=PreviewFrame.ZOOM_TO_FIT)
        self.mainsizer.Add(self.preview,(0,0),flag=wx.EXPAND|wx.ALL)
        
        self.infoNotebook=wx.Notebook(self,-1,size=(300,300))        
        self.mainsizer.Add(self.infoNotebook,(0,1),flag=wx.EXPAND|wx.ALL)

        self.createInfoNotebook()
        
        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.mainsizer.SetSizeHints(self) 
 
    def setTree(self,tree):
        """
        Method: setTree(tree)
        Created: 3.04.2005
        Creator: KP
        Description: Sets the tree widget
        """
        self.tree=tree
        
    def showInfo(self,dataunit):
        """
        Method: showInfo(dataunit)
        Created: 21.02.2005
        Creator: KP
        Description: Sets the infowidget to show info on a given dataunit
        """
        if not dataunit:
            dims=(0,0,0)
            spacing=(0,0,0)
            voxelsize=(0,0,0)
            bitdepth=8
            tps=0
        else:
            dims=dataunit.getDimensions()
            spacing=dataunit.getSpacing()
            voxelsize=dataunit.getVoxelSize()
            
            list=self.tree.getSelectedDataUnits()
            if len(list)>1:
                self.preview.setPreviewType("ColorMerging")
                unit=DataUnit.ColorMergingDataUnit()
                for i in list:
                    #setting=DataUnit.ColorMergingSettings()
                    #setting.initialize(unit,len(list),1)
                    #i.setSettings(setting)
                    unit.addSourceDataUnit(i)
                unit.setModule(ColorMerging.ColorMerging())                                    
            else:
                self.preview.setPreviewType("")
                
                unit=DataUnit.CorrectedSourceDataUnit("preview")
                unit.addSourceDataUnit(dataunit)
                unit.setModule(DataUnitProcessing.DataUnitProcessing())
                ctf = dataunit.getColorTransferFunction()
                print "Setting ctf=",ctf
                self.colorBtn.setColorTransferFunction(ctf)
            print "datasource=",dataunit.dataSource
            print "ctf is",dataunit.getSettings().get("ColorTransferFunction")
            self.dataUnit=unit
            self.taskName.SetValue(dataunit.getName())
            # The 0 tells preview to view source dataunit 0
            self.preview.setDataUnit(self.dataUnit,0)
            tps=dataunit.getLength()
            
            bitdepth="8"
            # TODO: Have this data available in dataunit
            #bitdepth=dataunit.getScalarSize()*dataunit.getComponentAmount()
        xdim,ydim,zdim=dims
        voxelX,voxelY,voxelZ=voxelsize
        voxelX*=1000000
        voxelY*=1000000
        voxelZ*=1000000
        spX,spY,spZ=spacing
        
        col=self.GetBackgroundColour()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        dict={"smX":smX,"xdim":xdim,"ydim":ydim,"zdim":zdim,
        "voxelX":voxelX,"voxelY":voxelY,"voxelZ":voxelZ,
        "spX":spX,"spY":spY,"spZ":spZ,"xdimm":xdim*voxelX,
        "ydimm":ydim*voxelY,"zdimm":zdim*voxelZ,"bgcolor":bgcol,
        "fe":"</font>","nf":"<font size=\"normal\">",
        "tps":tps,"bitdepth":bitdepth}
        
        self.htmlpage.SetPage(infoString%dict)
    
    def createInfoNotebook(self):
        """
        Method: createInfoNotebook()
        Created: 21.02.2005
        Creator: KP
        Description: Creates the fields for showing information about the
                     dataunit
        """
        self.infoPanel=wx.Panel(self.infoNotebook,-1)
        self.infoSizer=wx.GridBagSizer(5,5)
        self.htmlpage=wx.html.HtmlWindow(self.infoPanel,-1,size=(350,400))
        if "gtk2" in wx.PlatformInfo:
            self.htmlpage.SetStandardFonts()
 
        self.infoSizer.Add(self.htmlpage,(0,0),flag=wx.EXPAND|wx.ALL)
        self.showInfo(None)
        
        self.infoPanel.SetSizer(self.infoSizer)
        self.infoPanel.SetAutoLayout(1)

        self.infoNotebook.AddPage(self.infoPanel,"Channel info")
        
        self.commonSettingsPanel=wx.Panel(self.infoNotebook,-1)
        self.commonSettingsSizer=wx.GridBagSizer()
        
        self.namesizer=wx.BoxSizer(wx.VERTICAL)
        self.commonSettingsSizer.Add(self.namesizer,(0,0))
        
        self.taskNameLbl=wx.StaticText(self.commonSettingsPanel,-1,"Dataunit Name:")
        self.taskName=wx.TextCtrl(self.commonSettingsPanel,-1,size=(250,-1))
        self.namesizer.Add(self.taskNameLbl)
        self.namesizer.Add(self.taskName)

        self.paletteLbl = wx.StaticText(self.commonSettingsPanel,-1,"Channel palette:")
        self.commonSettingsSizer.Add(self.paletteLbl,(1,0))
        
        self.colorBtn = ColorTransferEditor.CTFButton(self.commonSettingsPanel)
        self.commonSettingsSizer.Add(self.colorBtn,(2,0))
        
        self.commonSettingsPanel.SetSizer(self.commonSettingsSizer)
        self.commonSettingsPanel.SetAutoLayout(1)

        self.infoNotebook.AddPage(self.commonSettingsPanel,"Data Unit")
        
        
        
