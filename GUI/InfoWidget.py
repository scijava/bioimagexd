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



smX="<font size=\"-1\">x</font>"
infoString="""<html><body bgcolor=%(bgcolor)s">
<table>
<tr><td>Dimensions:</td><td>%(xdim)d %(smX)s %(ydim)d %(smX)s %(zdim)d (%(nf)s%(xdimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(ydimm).2f%(fe)s&mu;m %(smX)s %(nf)s%(zdimm).2f%(fe)s&mu;m)</td></tr>
<tr><td>Voxel Size:</td><td>%(nf)s%(voxelX).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelY).2f%(fe)s&mu;m %(smX)s %(nf)s%(voxelZ).2f%(fe)s&mu;m</td></tr>
<tr><td>Spacing:</td><td>%(spX).2f %(smX)s %(spY).2f %(smX)s %(spZ).2f</td></tr>
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

        self.preview=PreviewFrame.SingleUnitProcessingPreview(self,
        previewsize=(384,384),pixelvalue=False,renderingpreview=False,
        zoom=True,timeslider=False)
        
        self.mainsizer.Add(self.preview,(0,0),flag=wx.EXPAND|wx.ALL)
        
        self.infoNotebook=wx.Notebook(self,-1,size=(300,300))        
        self.mainsizer.Add(self.infoNotebook,(0,1),flag=wx.EXPAND|wx.ALL)

        self.createInfoNotebook()
        
        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.mainsizer.SetSizeHints(self)        
        
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
            
        else:
            dims=dataunit.getDimensions()
            spacing=dataunit.getSpacing()
            voxelsize=dataunit.getVoxelSize()
            unit=DataUnit.CorrectedSourceDataUnit("preview")
            unit.addSourceDataUnit(dataunit)
            self.dataUnit=unit
            self.preview.setDataUnit(self.dataUnit)
        #self.setSpacing(spacing)
        #self.setDimensions(dims)
        #self.setVoxelSize(voxelsize)
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
        "fe":"</font>","nf":"<font size=\"normal\">"}
        
        self.htmlpage.SetPage(infoString%dict)
        print "code=",infoString%dict
        
    def setDimensions(self,dims):
        x,y,z=dims
        w,h,l=size=self.dataUnit.getVoxelSize()
        w*=1000000
        h*=1000000
        l*=1000000        
        sizeLbl=u"%d x %d x %d"%(x,y,z)
        sizeLbl2=u"%.2f\u03bcm x %.2f\u03bcm x %.2f\u03bcm"%(x*w,y*h,z*l)
        self.channelSize.SetLabel(sizeLbl)
        self.channelSize2.SetLabel(sizeLbl2)
        
    def setVoxelSize(self,size):
        
        x,y,z=size
        x*=1000000
        y*=1000000
        z*=1000000
        spacingLbl=u"%.2f\u03bcm  x %.2f\u03bcm  x %.2f\u03bcm "%(x,y,z)
        self.channelVoxelSize.SetLabel(spacingLbl)

    def setSpacing(self,spacing):
        x,y,z=spacing
        spacingLbl=u"%d x %d x %d"%(x,y,z)
        self.channelSpacing.SetLabel(spacingLbl)
        
    #def setOrigin(self,orig):
    #    x,y,z=orig
    #    originLbl=u"(%d\u03bcm, %d\u03bcm, %d\u03bcm)"%(x,y,z)
    #    self.channelOrigin.SetLabel(originLbl)        
        
    def makeField(self,name,parent,text,value,size,sizer,row):
        #sizer=wx.BoxSizer(wx.HORIZONTAL)
        lbl=wxStaticText(parent,-1,text)
        sizer.Add(lbl,(row,0),flag=wx.ALIGN_LEFT)
        self.__dict__[name+"Lbl"]=lbl
        val=wxStaticText(parent,-1,value,size=size)
        self.__dict__[name]=val
        sizer.Add(val,(row,1),flag=wx.ALIGN_LEFT)
        #sizer.Add(lbl)
        #sizer.Add(val)
        #self.__dict__[name+"Sizer"]=sizer
    
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
        
        
        #self.makeField("channelName",self.infoPanel,"Name:","n/a",(250,-1),self.infoSizer,0)
        #self.infoSizer.Add(self.channelNameSizer,(0,0))
        #sizeLbl=""
        #self.makeField("channelSize",self.infoPanel,"Size:",sizeLbl,(250,-1),self.infoSizer,1)
        #self.infoSizer.Add(self.channelSizeSizer,(1,0))
        #self.makeField("channelSize2",self.infoPanel,u"in \u03bcm:","",(250,-1),self.infoSizer,2)
        #spacingLbl=""
        #self.makeField("channelSpacing",self.infoPanel,"Spacing:",spacingLbl,(250,-1),self.infoSizer,3)
        
        #self.makeField("channelVoxelSize",self.infoPanel,"Voxel size:","",(250,-1),self.infoSizer,4)
        
        #originLbl=""
        #self.makeField("channelOrigin",self.infoPanel,"Origin:",originLbl,(250,-1),self.infoSizer,3)
        #self.infoSizer.Add(self.channelOriginSizer,(3,0))
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

        self.commonSettingsPanel.SetSizer(self.commonSettingsSizer)
        self.commonSettingsPanel.SetAutoLayout(1)

        self.infoNotebook.AddPage(self.commonSettingsPanel,"Data Unit")
        
        
        
