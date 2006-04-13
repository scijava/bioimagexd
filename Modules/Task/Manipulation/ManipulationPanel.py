#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationPanel
 Project: BioImageXD
 Created: 10.04.2005, KP
 Description:

 A task window for manipulating the dataset with various filters.
                            
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
from GUI import ColorTransferEditor

from GUI import TaskPanel
import UIElements
import string

import ManipulationFilters

class ManipulationPanel(TaskPanel.TaskPanel):
    """
    Class: ManipulationPanel
    Created: 03.11.2004, KP
    Description: A window for restoring a single dataunit
    """
    def __init__(self,parent,tb):
        """
        Method: __init__(parent)
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
                root    Is the parent widget of this window
        """
        self.timePoint = 0
        self.operationName="Manipulation"
        TaskPanel.TaskPanel.__init__(self,parent,tb)
        # Preview has to be generated here
        # self.colorChooser=None
        
        self.categories=[]
        self.menu = None
        self.currentGUI = None
        self.filtersByCategory={}
        self.Show()
        self.filters = []
        self.currentSelected = -1
        
        for currfilter in ManipulationFilters.getFilterList():
            self.registerFilter(currfilter.getCategory(),currfilter)
      
        self.mainsizer.Layout()
        self.mainsizer.Fit(self)

    def registerFilter(self,category,currfilter):
        """
        Method: createButtonBox()
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
        Method: createButtonBox()
        Created: 03.11.2004, KP
        Description: Creates a button box containing the buttons Render,
                     Preview and Close
        """
        TaskPanel.TaskPanel.createButtonBox(self)
        
        #self.ManipulationButton.SetLabel("Manipulation Dataset Series")
        self.processButton.Bind(wx.EVT_BUTTON,self.doManipulationingCallback)

    def createOptionsFrame(self):
        """
        Method: createOptionsFrame()
        Created: 03.11.2004
        Creator: KP
        Description: Creates a frame that contains the various widgets
                     used to control the colocalization settings
        """
        TaskPanel.TaskPanel.createOptionsFrame(self)

        self.panel=wx.Panel(self.settingsNotebook,-1)
        self.panelsizer=wx.GridBagSizer()
    
        self.filtersizer=wx.GridBagSizer()

        
        self.filterLbl=wx.StaticText(self.panel,-1,"Filter stack:")
        self.filterListbox = wx.CheckListBox(self.panel,-1,size=(300,-1))
        self.filterListbox.Bind(wx.EVT_LISTBOX,self.onSelectFilter)
        self.filterListbox.Bind(wx.EVT_CHECKLISTBOX,self.onCheckFilter)        
        self.addBtn = wx.Button(self.panel,-1,"Add filter")
        self.addBtn.Bind(wx.EVT_LEFT_DOWN,self.onShowAddMenu)

        btnBox=wx.BoxSizer(wx.HORIZONTAL)
        self.remove = wx.Button(self.panel,-1,"Remove")
        self.remove.Bind(wx.EVT_BUTTON,self.onRemoveFilter)
        self.up = wx.Button(self.panel,-1,"Up")
        self.up.Bind(wx.EVT_BUTTON,self.onMoveFilterUp)
        self.down = wx.Button(self.panel,-1,"Down")
        self.down.Bind(wx.EVT_BUTTON,self.onMoveFilterDown)
        btnBox.Add(self.remove)
        btnBox.Add(self.up)
        btnBox.Add(self.down)
        btnBox.Add(self.addBtn)

        self.filtersizer.Add(self.filterLbl,(0,0))
        self.filtersizer.Add(self.filterListbox,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.filtersizer.Add(btnBox,(2,0))
        
        self.panelsizer.Add(self.filtersizer,(0,0))

        self.panel.SetSizer(self.panelsizer)
        self.panel.SetAutoLayout(1)
        self.settingsNotebook.AddPage(self.panel,"Filter stack")
   
    def onMoveFilterDown(self,event):
        """
        Method: onMoveFilterDown
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
        print self.filters
        
    def onMoveFilterUp(self,event):
        """
        Method: onMoveFilterUp
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
        print self.filters
    def onRemoveFilter(self,event):
        """
        Method: onRemoveFilter
        Created: 13.04.2006, KP
        Description: Remove a filter from the list
        """
        index = self.filterListbox.GetSelection()
        if index == -1:
            Dialogs.showerror(self,"You have to select a filter to be removed","No filter selected")
            return        

        self.filterListbox.Delete(index)
        del self.filters[index]
        
    def onCheckFilter(self,event):
        """
        Method: onCheckFilter
        Created: 13.04.2006, KP
        Description: Event handler called when user toggles filter on or off
        """
        index = event.GetSelection()
        status=self.filterListbox.IsChecked(index)
        self.filters[index].setEnabled(status)
        
    def onSelectFilter(self,event):
        """
        Method: onSelectFilter
        Created: 13.04.2006, KP
        Description: Event handler called when user selects a filter in the listbox
        """
        self.selected = event.GetSelection()
        if self.selected == self.currentSelected:
            return
        self.currentSelected = self.selected
        if self.currentGUI:
            self.panelsizer.Detach(self.currentGUI)
            self.currentGUI.Show(0)
        
        currfilter = self.filters[self.selected]
        self.currentGUI = currfilter.getGUI(self.panel)
        
        self.panelsizer.Add(self.currentGUI,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.currentGUI.Show(1)
        self.panel.Layout()
        self.Layout()
        self.panelsizer.Fit(self.panel)
        
        
        
    def addFilter(self,event,filterclass):
        """
        Method: addFilter
        Created: 13.04.2006, KP
        Description: Add a filter to the stack
        """
        print "Request to add filter",filterclass
        addfilter = filterclass()
        name = addfilter.getName()
        n=self.filterListbox.GetCount()
        self.filterListbox.InsertItems([name],n)
        self.filterListbox.Check(n)
        
        self.filters.append(addfilter)
        
        

    def onShowAddMenu(self,event):
        """
        Method: onShowAddMenu
        Created: 13.04.2006, KP
        Description: Show a menu for adding filters to the stack
        """
        if not self.menu:
            menu=wx.Menu()
            for i in self.categories:
                submenu = wx.Menu()
                if i not in self.filtersByCategory:
                    self.filtersByCategory[i]=[]
                for currfilter in self.filtersByCategory[i]:
                    menuid = wx.NewId()
                    name = currfilter.getName()
                    submenu.Append(menuid,name)
                    f=lambda evt, x=currfilter: self.addFilter(evt,x)
                    self.Bind(wx.EVT_MENU,f,id=menuid)
                menu.AppendMenu(-1,i,submenu)
            self.menu = menu
        self.addBtn.PopupMenu(self.menu,event.GetPosition())
        
    def updateTimepoint(self,event):
        """
        Method: updateTimepoint(event)
        Created: 04.04.2005, KP
        Description: A callback function called when the timepoint is changed
        """
        timePoint=event.getValue()
        self.timePoint=timePoint
 

    def doFilterCheckCallback(self,event=None):
        """
        Method: doFilterCheckCallback(self)
        Created: 14.12.2004, JV
        Description: A callback function called when the neither of the
                     filtering checkbox changes state
        """

    def updateSettings(self):
        """
        Method: updateSettings()
        Created: 03.11.2004, KP
        Description: A method used to set the GUI widgets to their proper values
        """

        if self.dataUnit:
            get=self.settings.get
            set=self.settings.set
                
    def updateFilterData(self):
        """
        Method: updateFilterData()
        Created: 13.12.2004, JV
        Description: A method used to set the right values in dataset
                     from filter GUI widgets
        """
        self.settings.set("FilterList",self.filters)
        
    def doManipulationingCallback(self,event=None):
        """
        Method: doManipulationingCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Manipulation Dataset Series"
        """
        self.updateFilterData()
        TaskPanel.TaskPanel.doOperation(self)

    def doPreviewCallback(self,event=None,*args):
        """
        Method: doPreviewCallback()
        Created: 03.11.2004, KP
        Description: A callback for the button "Preview" and other events
                     that wish to update the preview
        """
        self.updateFilterData()
        TaskPanel.TaskPanel.doPreviewCallback(self,event)

    def setCombinedDataUnit(self,dataUnit):
        """
        Method: setCombinedDataUnit(dataUnit)
        Created: 23.11.2004, KP
        Description: Sets the Manipulationed dataunit that is to be Manipulationed.
                     It is then used to get the names of all the source data
                     units and they are added to the menu.
                     This is overwritten from TaskPanel since we only Manipulation
                     one dataunit here, not multiple source data units
        """
        TaskPanel.TaskPanel.setCombinedDataUnit(self,dataUnit)
        self.updateSettings()
