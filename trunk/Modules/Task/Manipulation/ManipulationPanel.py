#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationPanel
 Project: BioImageXD
 Created: 10.04.2005, KP
 Description:

 A task that allows the user to process the input data through a chain of different filters.
                            
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx

import os.path
import Dialogs

from PreviewFrame import *
from Logging import *

import sys
import time

#import FilterBasedTaskPanel
from GUI import FilterBasedTaskPanel
import UIElements
import string
import scripting as bxd
import types
import Command

import ManipulationFilters

class ManipulationPanel(FilterBasedTaskPanel.FilterBasedTaskPanel):
    """
    Created: 03.11.2004, KP
    Description: A window for restoring a single dataunit
    """
    def __init__(self,parent,tb):
        """
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.timePoint = 0
        self.operationName="Process"
        self.filtersModule = ManipulationFilters
        FilterBasedTaskPanel.FilterBasedTaskPanel.__init__(self,parent,tb)
        # Preview has to be generated here
        # self.colorChooser=None
        self.timePoint = 0
        self.menus = {}
        self.currentGUI = None
        self.parser = None
        self.onByDefault = 0
        self.Show()
        self.filters = []
        self.currentSelected = -1
        

        self.filtersByCategory={}
        self.filtersByName={}
        self.categories=[]

        for currfilter in ManipulationFilters.getFilterList():
            print "Registering",currfilter.getName(),currfilter.getCategory()
            self.filtersByName[currfilter.getName()] = currfilter
            self.registerFilter(currfilter.getCategory(),currfilter)
      
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)
        
        messenger.connect(None,"timepoint_changed",self.updateTimepoint)
        
    def updateTimepoint(self,obj,event,timePoint):
        """
        Created: 27.04.2006, KP
        Description: A callback function called when the timepoint is changed
        """
        self.timePoint=timePoint
        
    def filterModified(self,filter):
        """
        Created: 14.05.2006, KP
        Description: A callback for when filter parameters change
        """
        self.setModified(1)
        
    def setModified(self,flag):
        """
        Created: 14.05.2006, KP
        Description: A callback for when filter parameters change
        """
        self.dataUnit.module.setModified(1)

    def registerFilter(self,category,currfilter):
        """
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render,
        """
        if category not in self.categories:
            self.categories.append(category)
        if not category in self.filtersByCategory:
            self.filtersByCategory[category]=[]
        self.filtersByCategory[category].append(currfilter)
        
    def createButtonBox(self):
        """
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        FilterBasedTaskPanel.FilterBasedTaskPanel.createButtonBox(self)
        
        #self.ManipulationButton.SetLabel("Manipulation Dataset Series")
        
        messenger.connect(None,"process_dataset",self.doProcessingCallback)        

    def createOptionsFrame(self):
        """
        Created: 03.11.2004, KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        FilterBasedTaskPanel.FilterBasedTaskPanel.createOptionsFrame(self)

        self.panel=wx.Panel(self.settingsNotebook,-1)
        self.panelsizer=wx.GridBagSizer()
    
        self.filtersizer=wx.GridBagSizer()

        
        self.filterLbl=wx.StaticText(self.panel,-1,"Procedure list:")
        self.filterListbox = wx.CheckListBox(self.panel,-1,size=(300,300))
        self.filterListbox.Bind(wx.EVT_LISTBOX,self.onSelectFilter)
        self.filterListbox.Bind(wx.EVT_CHECKLISTBOX,self.onCheckFilter)        
        self.addFilteringBtn = wx.Button(self.panel,-1,u"Filtering \u00BB")
        self.addArithmeticsBtn = wx.Button(self.panel,-1,u"Arithmetics \u00BB")
        self.addSegmentationBtn = wx.Button(self.panel,-1,u"Segmentation \u00BB")
        self.addTrackingBtn = wx.Button(self.panel,-1,u"Tracking \u00BB")

        from ManipulationFilters import FILTERING,FEATUREDETECTION,MATH,LOGIC,SEGMENTATION,WATERSHED,REGION_GROWING,MEASUREMENT,TRACKING
        
        f=lambda evt, btn=self.addFilteringBtn, cats=(FILTERING,FEATUREDETECTION): self.onShowAddMenu(evt,btn,cats)
        self.addFilteringBtn.Bind(wx.EVT_LEFT_DOWN,f)
        
        f=lambda evt, btn=self.addArithmeticsBtn, cats=(MATH, LOGIC): self.onShowAddMenu(evt,btn,cats)
        self.addArithmeticsBtn.Bind(wx.EVT_LEFT_DOWN,f)
        
        f=lambda evt, btn=self.addSegmentationBtn, cats=(SEGMENTATION, REGION_GROWING,WATERSHED,MEASUREMENT): self.onShowAddMenu(evt,btn,cats)
        self.addSegmentationBtn.Bind(wx.EVT_LEFT_DOWN,f)
        
        f=lambda evt, btn=self.addSegmentationBtn, cats=(TRACKING,): self.onShowAddMenu(evt,btn,cats)        
        self.addTrackingBtn.Bind(wx.EVT_LEFT_DOWN,f)
        
        vertbtnBox=wx.BoxSizer(wx.VERTICAL)
        

        bmp = wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_TOOLBAR, (16,16))        
        self.remove = wx.BitmapButton(self.panel,-1,bmp)
        self.remove.Bind(wx.EVT_BUTTON,self.onRemoveFilter)
        
        bmp = wx.ArtProvider_GetBitmap(wx.ART_GO_UP, wx.ART_TOOLBAR, (16,16))        
        self.up = wx.BitmapButton(self.panel,-1,bmp)
        bmp = wx.ArtProvider_GetBitmap(wx.ART_GO_DOWN, wx.ART_TOOLBAR, (16,16))        
        self.up.Bind(wx.EVT_BUTTON,self.onMoveFilterUp)
        self.down = wx.BitmapButton(self.panel,-1,bmp)
        self.down.Bind(wx.EVT_BUTTON,self.onMoveFilterDown)
        vertbtnBox.Add(self.remove)
        vertbtnBox.Add(self.up)
        vertbtnBox.Add(self.down)
        btnBox=wx.BoxSizer(wx.HORIZONTAL)
        btnBox.Add(self.addFilteringBtn)
        btnBox.Add(self.addArithmeticsBtn)
        btnBox.Add(self.addSegmentationBtn)
        btnBox.Add(self.addTrackingBtn)
        
        #btnBox.Add(self.reloadBtn)
    
        box=wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.filterListbox)
        box.Add(vertbtnBox)
        self.filtersizer.Add(self.filterLbl,(0,0))
        #self.filtersizer.Add(self.filterListbox,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.filtersizer.Add(box,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.filtersizer.Add(btnBox,(2,0))
        
        self.panelsizer.Add(self.filtersizer,(0,0))

        self.panel.SetSizer(self.panelsizer)
        self.panel.SetAutoLayout(1)
        self.settingsNotebook.AddPage(self.panel,"Procedure list")
   
   

            
    def getFilters(self, name):
        """
        Created: 21.07.2006, KP
        Description: Retrieve the filters with the given name
        """   
                
        func=lambda f, n=name:f.getName() == n
        return filter(func, self.filters)
        
    def getFilter(self, name, index=0):
        """
        Created: 21.07.2006, KP
        Description: Retrieve the filter with the given name, using optionally an index 
                     if there are more than one filter with the same name
        """   
        return self.getFilters(name)[index]
        
    def onMoveFilterDown(self,event):
        """
        Created: 13.04.2006, KP
        Description: Move a filter down in the list
        """
        index = self.filterListbox.GetSelection()
        if index == -1:
            Dialogs.showerror(self,"You have to select a filter to be moved","No filter selected")
            return 
        n = self.filterListbox.GetCount()
        if index==n-1:
            Dialogs.showerror(self,"Cannot move last filter down","Cannot move filter")
            return
            
        lbl=self.filterListbox.GetString(index)
        chk = self.filterListbox.IsChecked(index)
        self.filterListbox.InsertItems([lbl],index+2)
        self.filterListbox.Check(index+2,chk)
        self.filterListbox.Delete(index)
        
        self.filters[index+1],self.filters[index]=self.filters[index],self.filters[index+1]
        self.setModified(1)
        
    def onMoveFilterUp(self,event):
        """
        Created: 13.04.2006, KP
        Description: Move a filter up in the list
        """
        index = self.filterListbox.GetSelection()
        if index == -1:
            Dialogs.showerror(self,"You have to select a filter to be moved","No filter selected")
            return        
        if index==0:
            Dialogs.showerror(self,"Cannot move first filter up","Cannot move filter")
            return
            
        lbl=self.filterListbox.GetString(index)
        chk = self.filterListbox.IsChecked(index)
        self.filterListbox.InsertItems([lbl],index-1)
        self.filterListbox.Check(index-1,chk)
        self.filterListbox.Delete(index+1)
        
        self.filters[index-1],self.filters[index]=self.filters[index],self.filters[index-1]
        self.setModified(1)
        
    def onRemoveFilter(self,event):
        """
        Created: 13.04.2006, KP
        Description: Remove a filter from the list
        """
        index = self.filterListbox.GetSelection()
        if index == -1:
            Dialogs.showerror(self,"You have to select a filter to be removed","No filter selected")
            return 
        name = self.filters[index].getName()
        undo_cmd=""
        do_cmd="bxd.mainWindow.tasks['Process'].deleteFilter(index=%d, name='%s')"%(index,name)
        cmd=Command.Command(Command.GUI_CMD,None,None,do_cmd,undo_cmd,desc="Remove filter '%s'"%(name))
        cmd.run()
            

        
    def onCheckFilter(self,event):
        """
        Created: 13.04.2006, KP
        Description: Event handler called when user toggles filter on or off
        """
        index = event.GetSelection()
        name = self.filters[index].getName()
        status=self.filterListbox.IsChecked(index)
        cmd="Enable"
        if not status:cmd="Disable"
        undo_cmd="bxd.mainWindow.tasks['Process'].setFilter(index=%d, name='%s', %s)"%(index,name,str(not status))
        do_cmd="bxd.mainWindow.tasks['Process'].setFilter(index=%d, name='%s', %s)"%(index,name,str(not not status))
        cmd=Command.Command(Command.GUI_CMD,None,None,do_cmd,undo_cmd,desc="%s filter '%s'"%(cmd,name))
        cmd.run()
        
    def setFilter(self, status, index = -1, name=""):
        """
        Created: 21.07.2006, KP
        Description: Set the status of a given filter by either it's index, or
                     if index is not given, it's name
        """        
        if index==-1:
            for i in self.filters:
                if i.getName()==name:
                    index=i
                    break
        if index==-1:return False
        self.filters[index].setEnabled(status)
        self.setModified(1)
        
    def removeGUI(self):
        """
        Created: 18.04.2006, KP
        Description: Remove the GUI
        """        
        if self.currentGUI:
            self.panelsizer.Detach(self.currentGUI)
            self.currentGUI.Show(0)

        
    def onSelectFilter(self,event):
        """
        Created: 13.04.2006, KP
        Description: Event handler called when user selects a filter in the listbox
        """
        self.selected = event.GetSelection()
        if self.selected == self.currentSelected:
            return
        self.currentSelected = self.selected
        self.removeGUI()
        
        currfilter = self.filters[self.selected]
        self.currentGUI = currfilter.getGUI(self.panel,self)
        currfilter.sendUpdateGUI()
        
        self.panelsizer.Add(self.currentGUI,(1,0),flag=wx.EXPAND|wx.ALL)
        self.currentGUI.Show(1)
        self.panel.Layout()
        self.Layout()
        self.panelsizer.Fit(self.panel)
        self.FitInside()
        
        
    def loadFilter(self, className):
        """
        Created: 21.07.2006, KP
        Description: Add a filter with the given name to the stack
        """
        filterclass = self.filtersByName[className]
        return self.addFilter(None,filterclass)
        
    def deleteFilter(self, index=-1, name=""):
        """
        Created: 21.07.2006, KP
        Description: Delete a filter by either it's index, or
                     if index is not given, it's name
        """           
        if index==-1:
            for i in self.filters:
                if i.getName()==name:
                    index=i
                    break
        if index==-1:return False
            
        self.filterListbox.Delete(index)
        del self.filters[index]
        self.currentSelected=-1
        self.removeGUI()
        self.currentGUI=None
        self.setModified(1)
        
            
        
    def addFilter(self,event,filterclass):
        """
        Created: 13.04.2006, KP
        Description: Add a filter to the stack
        """        
        addfilter = filterclass()
        addfilter.setTaskPanel(self)
        addfilter.setDataUnit(self.dataUnit)
        name = addfilter.getName()
        n=self.filterListbox.GetCount()
        self.filterListbox.InsertItems([name],n)
        self.filterListbox.Check(n)
        
        self.filters.append(addfilter)
        self.setModified(1)
        self.updateFilterData()
        

    def onShowAddMenu(self,event,btn,categories=()):
        """
        Created: 13.04.2006, KP
        Description: Show a menu for adding filters to the stack
        """
        print "categories=",categories,"self.menus=",self.menus
        print "Filters by category has keys=",self.filtersByCategory.keys()
        if categories not in self.menus:
            menu=wx.Menu()
            for i in categories:
                submenu = wx.Menu()
                if i not in self.filtersByCategory:
                    self.filtersByCategory[i]=[]
                    
                for currfilter in self.filtersByCategory[i]:
                    menuid = wx.NewId()
                    name = currfilter.getName()
                    print "Adding item",menuid,name
                    newitem = wx.MenuItem(submenu, menuid, name)
                    if currfilter.level:
                        newitem.SetBackgroundColour(wx.Colour(*currfilter.level))
                    submenu.AppendItem(newitem)
#                    submenu.Append(menuid,name)
                    n = len(self.filters)
                    undo_cmd="bxd.mainWindow.tasks['Process'].deleteFilter(index=%d, name = '%s')"%(n,name)
                    do_cmd="bxd.mainWindow.tasks['Process'].loadFilter('%s')"%name
                    cmd=Command.Command(Command.GUI_CMD,None,None,do_cmd,undo_cmd,desc="Load filter %s"%name)
                    
                    f=lambda evt, c=cmd: c.run()
                    self.Bind(wx.EVT_MENU,f,id=menuid)
                menu.AppendMenu(-1,i,submenu)
            self.menus[categories] = menu
        btn.PopupMenu(self.menus[categories],event.GetPosition())
        

    def doFilterCheckCallback(self,event=None):
        """
        Created: 14.12.2004, JV
        Description: A callback function called when the neither of the
                     filtering checkbox changes state
        """

    def updateSettings(self,force=0):
        """
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """
        if not force:
            self.settings.set("FilterList",[])
            return
        if self.dataUnit:
            get=self.settings.get
            set=self.settings.set
        flist = self.settings.get("FilterList")
        
        if flist and len(flist):
            
            if type(flist[0]) == types.ClassType:
                for i in flist:
                    print "Adding filter of class",i
                    self.addFilter(None,i)
            for currfilter in self.filters:
                name = currfilter.getName()
                #parser = self.dataUnit.getParser()    
                parser = self.dataUnit.parser
                
                if parser:
                    items = parser.items(name)
                    
                    for item,value in items:            
                        #value=parser.get(name,item)
                        print "Setting",item,"to",value
                        value = eval(value)
                        currfilter.setParameter(item, value)
                    currfilter.sendUpdateGUI()
                    self.parser = None
                
    def updateFilterData(self):
        """
        Created: 13.12.2004, JV
        Description: A method used to set the right values in dataset
                     from filter GUI widgets
        """
        print "Setting filterlist to",self.filters
        self.settings.set("FilterList",self.filters)
        
    def doProcessingCallback(self,*args):
        """
        Created: 03.11.2004, KP
        Description: A callback for the button "Manipulation Dataset Series"
        """
        self.updateFilterData()
        FilterBasedTaskPanel.FilterBasedTaskPanel.doOperation(self)

    def doPreviewCallback(self,event=None,*args):
        """
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        self.updateFilterData()
        FilterBasedTaskPanel.FilterBasedTaskPanel.doPreviewCallback(self,event)

    def createItemToolbar(self):
        """
        Created: 16.04.2006, KP
        Description: Method to create a toolbar for the window that allows use to select processed channel
        """      
        # Pass flag force which indicates that we do want an item toolbar
        # although we only have one input channel
        n=FilterBasedTaskPanel.FilterBasedTaskPanel.createItemToolbar(self,force=1)
        for i,tid in enumerate(self.toolIds):
            self.dataUnit.setOutputChannel(i,0)
            self.toolMgr.toggleTool(tid,0)
        
        
        ctf=vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255,1,1,1)
        #imagedata=ImageOperations.getMIP(self.dataUnit.getSourceDataUnits()[0].getTimePoint(0),ctf)
        imagedata = self.itemMips[0]
        
        
        ctf=vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255,1,1,1)
        #imagedata=ImageOperations.getMIP(coloc.GetOutput(),ctf)
        maptocolor=vtk.vtkImageMapToColors()
        maptocolor.SetInput(imagedata)
        maptocolor.SetLookupTable(ctf)
        maptocolor.SetOutputFormatToRGB()
        maptocolor.Update()
        imagedata=maptocolor.GetOutput()
        
        bmp=ImageOperations.vtkImageDataToWxImage(imagedata).ConvertToBitmap()
#        bmp=bmp.Rescale(30,30).ConvertToBitmap()
        bmp = self.getChannelItemBitmap(bmp,(255,255,255))
        toolid=wx.NewId()
        #n=n+1
        name="Manipulation"
        self.toolMgr.addChannelItem(name,bmp,toolid,lambda e,x=n,s=self:s.setPreviewedData(e,x))        
        
        self.toolIds.append(toolid)
        self.dataUnit.setOutputChannel(len(self.toolIds),1)
        self.toolMgr.toggleTool(toolid,1)

    def setCombinedDataUnit(self,dataUnit):
        """
        Created: 23.11.2004, KP
        Description: Sets the Manipulationed dataunit that is to be Manipulationed.
                     It is then used to get the names of all the source data
                     units and they are added to the menu.
                     This is overwritten from FilterBasedTaskPanel since we only Manipulation
                     one dataunit here, not multiple source data units
        """
        FilterBasedTaskPanel.FilterBasedTaskPanel.setCombinedDataUnit(self,dataUnit)
        n=0
        for i,dataunit in enumerate(dataUnit.getSourceDataUnits()):
            dataUnit.setOutputChannel(i,0)
            n=i
        self.dataUnit.setOutputChannel(n+1,1)
        self.restoreFromCache()        
        self.updateSettings()