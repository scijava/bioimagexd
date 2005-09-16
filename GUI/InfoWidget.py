# -*- coding: iso-8859-1 -*-

"""
 Unit: InfoWidget.py
 Project: BioImageXD
 Created: 21.02.2005, KP
 Description:

 A widget that displays information about channels/dataset series selected in 
 the tree view.
         
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


import os.path
import wx, wx.html

import Logging

import DataUnit

import ColorTransferEditor
import Modules

import messenger



smX="<font size=\"-1\">x</font>"
infoString="""<html><body bgcolor=%(bgcolor)s">
<table>
<tr><td>Dimensions:</td><td>%(xdim)d %(smX)s %(ydim)d %(smX)s %(zdim)d (%(nf)s%(xdimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(ydimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(zdimm).2f%(fe)s&mu;m)</td></tr>
<tr><td>Time Points:</td><td>%(tps)d</td></tr>
<tr><td>Voxel Size:</td><td>%(nf)s%(voxelX).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelY).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelZ).2f%(fe)s&mu;m</td></tr>
<tr><td>Spacing:</td><td>%(spX).2f %(smX)s %(spY).2f %(smX)s %(spZ).2f</td></tr>
<tr><td>Data type:</td><td>%(bitdepth)d bit</td></tr>
<tr><td>Intensity range:</td><td>%(intlower)d - %(intupper)d</td></tr>
</table>
</body></html>
"""
infoStringResample="""<html><body bgcolor=%(bgcolor)s">
<table>
<tr><td>Resampled dimensions:</td><td>%(xdim)d %(smX)s %(ydim)d %(smX)s %(zdim)d (%(nf)s%(xdimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(ydimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(zdimm).2f%(fe)s&mu;m)</td></tr>
<tr><td>Time Points:</td><td>%(tps)d</td></tr>
<tr><td>Voxel Size:</td><td>%(nf)s%(voxelX).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelY).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelZ).2f%(fe)s&mu;m</td></tr>
<tr><td>Spacing:</td><td>%(spX).2f %(smX)s %(spY).2f %(smX)s %(spZ).2f</td></tr>
<tr><td>Data type:</td><td>%(bitdepth)d bit</td></tr>
<tr><td>Intensity range:</td><td>%(intlower)d - %(intupper)d</td></tr>
</table>
</body></html>
"""
#"
class InfoWidget(wx.Panel):
    """
    Class: InfoWidget
    Created: 03.11.2004, KP
    Description: A class for displaying information about selected datasets
                 of given type
    """
    def __init__(self,master,**kws):
        """
        Method: __init__
        Created: 03.11.2004, KP
        Description: Initialization for the Info node
        """
        wx.Panel.__init__(self,master,-1,style=wx.BORDER_RAISED,**kws)
        self.mainsizer=wx.GridBagSizer(5,5)
        
        self.infoNotebook=wx.Notebook(self,-1,size=(280,300))        
        self.mainsizer.Add(self.infoNotebook,(0,1),flag=wx.EXPAND|wx.ALL)

        self.modules=Modules.DynamicLoader.getTaskModules()

        self.createInfoNotebook()
        
        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.mainsizer.SetSizeHints(self)
       
        messenger.connect(None,"tree_selection_changed",self.showInfo) 
        self.SetHelpText("This window shows you information about the selected dataset.")
        self.htmlpage.SetHelpText("This window shows you information about the selected dataset.")
        #messenger.connect(None,"tree_selection_changed",self.updateInfo)
    def enable(self,flag):
        """
        Method: enable(flag)
        Created: 05.06.2005, KP
        Description: Enable/disable widget
        """
        pass
 
    def setTree(self,tree):
        """
        Method: setTree(tree)
        Created: 3.04.2005, KP
        Description: Sets the tree widget
        """
        self.tree=tree
        
    def updateInfo(self,obj,evt,*args):
        """
        Method: updateInfo(obj,evt,args)
        Created: 21.07.2005, KP
        Description: Update the rendering of the MIP
        """
        self.showInfo(None,None,self.dataUnit)
        
    def showInfo(self,obj=None,evt=None,dataunit=None):
        """
        Method: showInfo(object, event, dataunit)
        Created: 21.02.2005, KP
        Description: Sets the infowidget to show info on a given dataunit
        """
        if not dataunit:
            dims=(0,0,0)
            resampledims=(0,0,0)
            spacing=(0,0,0)
            voxelsize=(0,0,0)
            bitdepth=8
            intlower=0
            intupper=255
            tps=0
        else:
            dims=dataunit.getDimensions()
            resampledims=dataunit.dataSource.getResampleDimensions()
            spacing=dataunit.getSpacing()
            voxelsize=dataunit.getVoxelSize()
            bitdepth=dataunit.getBitDepth()
            intlower,intupper=dataunit.getScalarRange()
            Logging.info("Dataset bit depth =",bitdepth,kw="trivial")
            unit = dataunit
            ctf = dataunit.getColorTransferFunction()

            if dataunit.getBitDepth()==32:
                self.colorBtn.Enable(0)
            else:
                self.colorBtn.setColorTransferFunction(ctf)

            self.dataUnit=unit
            self.taskName.SetValue(dataunit.getName())
            # The 0 tells preview to view source dataunit 0
            #self.preview.setDataUnit(self.dataUnit,0)
            tps=dataunit.getLength()
            
            # TODO: Have this data available in dataunit
            #bitdepth=dataunit.getScalarSize()*dataunit.getComponentAmount()
        xdim,ydim,zdim=dims
        voxelX,voxelY,voxelZ=voxelsize
        voxelX*=1000000
        voxelY*=1000000
        voxelZ*=1000000
        spX,spY,spZ=spacing
            
        if resampledims:
            rxdim,rydim,rzdim=resampledims
        else:
            rxdim,rydim,rzdim=0,0,0
        col=self.GetBackgroundColour()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        dict={"smX":smX,"xdim":xdim,"ydim":ydim,"zdim":zdim,
        "voxelX":voxelX,"voxelY":voxelY,"voxelZ":voxelZ,
        "rxdim":rxdim,"rydim":rydim,"rzdim":rzdim,
        "rxdimm":rxdim*voxelX,"rydimm":rydim*voxelY,"rzdimm":rzdim*voxelZ,
        "spX":spX,"spY":spY,"spZ":spZ,"xdimm":xdim*voxelX,
        "ydimm":ydim*voxelY,"zdimm":zdim*voxelZ,"bgcolor":bgcol,
        "fe":"</font>","nf":"<font size=\"normal\">",
        "tps":tps,"bitdepth":bitdepth,"intlower":intlower,"intupper":intupper}
        
        if resampledims and resampledims!=(0,0,0):
            self.htmlpage.SetPage(infoStringResample%dict)
        else:
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
        #self.infoPanel=wx.Panel(self,-1)
        self.infoSizer=wx.GridBagSizer(5,5)

        self.infoNotebook.AddPage(self.infoPanel,"Channel info")
        
        #self.commonSettingsPanel=wx.Panel(self.infoNotebook,-1)
        #self.commonSettingsSizer=wx.GridBagSizer()
        
        n=0
        self.namesizer=wx.BoxSizer(wx.VERTICAL)
        self.infoSizer.Add(self.namesizer,(n,0))
        n+=1
        self.taskNameLbl=wx.StaticText(self.infoPanel,-1,"Dataunit Name:")
        self.taskName=wx.TextCtrl(self.infoPanel,-1,size=(250,-1))
        self.namesizer.Add(self.taskNameLbl)
        self.namesizer.Add(self.taskName)

        #self.commonSettingsPanel.SetSizer(self.commonSettingsSizer)
        #self.commonSettingsPanel.SetAutoLayout(1)

        #self.infoNotebook.AddPage(self.commonSettingsPanel,"Data Unit")
        
        
        self.htmlpage=wx.html.HtmlWindow(self.infoPanel,-1,size=(280,300))
        if "gtk2" in wx.PlatformInfo:
            self.htmlpage.SetStandardFonts()
 
        self.infoSizer.Add(self.htmlpage,(n,0),flag=wx.EXPAND|wx.ALL)
        self.showInfo(None)
        n+=1
        self.paletteLbl = wx.StaticText(self.infoPanel,-1,"Channel palette:")
        self.infoSizer.Add(self.paletteLbl,(n,0))
        n+=1
        
        self.colorBtn = ColorTransferEditor.CTFButton(self.infoPanel)
        self.infoSizer.Add(self.colorBtn,(n,0))
        n+=1
        
        self.infoPanel.SetSizer(self.infoSizer)
        self.infoPanel.SetAutoLayout(1)
        #self.mainsizer.Add(self.infoPanel,(0,1),flag=wx.EXPAND|wx.ALL)        
