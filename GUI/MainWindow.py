#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MainWindow.py
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 The main window for the LSM module.

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
__version__ = "$Revision: 1.71 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path,os,types
import wx
import types
import vtk
#from enthought.tvtk import messenger
import messenger

from ConfigParser import *
from TreeWidget import *
from Logging import *

import SettingsWindow
import ImportDialog
import ExportDialog
import RenderingInterface

import Visualizer

import InfoWidget
import MenuManager

import Dialogs
import AboutDialog

from DataUnit import *
from DataSource import *

import Modules
import Urmas

class MainWindow(wx.Frame):
    """
    Class: MainWindow
    Created: 03.11.2004, KP
    Description: The main window for the LSM module
    """
    def __init__(self,parent,id,app,splash):
        """
        Method: __init__(parent,id,app)
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
            parent    
            id
            app     LSMApplication object
        """
        #Toplevel.__init__(self,root)
        wx.Frame.__init__(self,parent,-1,"BioImageXD",size=(1024,768),
            style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.Bind(
            wx.EVT_SASH_DRAGGED_RANGE, self.onSashDrag,
            id=MenuManager.ID_TREE_WIN, id2=MenuManager.ID_TASK_WIN,
        )
        self.statusbar=None
        self.progress=None
        self.menuManager=MenuManager.MenuManager(self,text=0)

        self.visWin=wx.SashLayoutWindow(self,MenuManager.ID_VIS_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.visWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.visWin.SetAlignment(wx.LAYOUT_LEFT)
        self.visWin.SetSashVisible(wx.SASH_RIGHT,False)
        self.visWin.SetDefaultSize((500,768))
        #self.visWin=wx.Panel(self,-1,size=(500,768))
        
        self.taskWin=wx.SashLayoutWindow(self,MenuManager.ID_TASK_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.taskWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.taskWin.SetAlignment(wx.LAYOUT_RIGHT)
        self.taskWin.SetSashVisible(wx.SASH_LEFT,True)
        self.taskWin.SetSashBorder(wx.SASH_LEFT,True)
        self.taskWin.SetDefaultSize((0,768))
        #self.taskWin=wx.Panel(self,-1,size=(0,768))
        
        self.visualizationPanel=None
        self.visualizer=None
        self.nodes_to_be_added=[]
        self.app=app
        
        # Icon for the window
        ico=reduce(os.path.join,["Icons","logo.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        messenger.send(None,"update_progress",0.1,"Loading BioImageXD...")        

        
        # Create Menu, ToolBar and Tree
        self.createStatusBar()
        messenger.send(None,"update_progress",0.3,"Creating menus...")        

        self.createMenu()
        messenger.send(None,"update_progress",0.6,"Creating toolbars...")        
        self.createToolBar()
        self.dataunits={}
        self.paths={}
        self.currentVisualizationWindow=None
        self.currentTaskWindow=None
        self.currentTaskWindowType=None

        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        messenger.send(None,"update_progress",0.9,"Pre-loading visualization views...")        
        self.preloadWindows()
        self.loadVisualizer(None,"info")
        # HACK
        self.tree = self.visualizer.currMode.tree

        self.taskPanels = Modules.DynamicLoader.getTaskModules()

        splash.Show(False)
        self.Show(True)            
        
        messenger.send(None,"update_progress",1.0,"Done.")        


    def preloadWindows(self):
        """
        Method: preloadWindows()
        Created: 03.6.2005, KP
        Description: A method for preloading renderer so that it won't be as slow to
                     show it
        """
        messenger.send(None,"update_progress",0.93,"Pre-loading slices view")        
        
        self.loadVisualizer(None,"slices",0,preload=1)
        messenger.send(None,"update_progress",0.96,"Pre-loading gallery view")        
        self.loadVisualizer(None,"gallery",0,preload=1)
        messenger.send(None,"update_progress",0.99,"Pre-loading 3D view")        
        self.loadVisualizer(None,"3d",0,preload=1)
        
    def onSashDrag(self, event):
        """
        Method: onSashDrag
        Created: 24.5.2005, KP
        Description: A method for laying out the window
        """
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            return

        eID = event.GetId()

        if eID == MenuManager.ID_TREE_WIN:
            w,h=self.treeWin.GetSize()
            self.treeWin.SetDefaultSize((event.GetDragRect().width,h))
        #elif eID == MenuManager.ID_VIS_WIN:
        #    w,h=self.visWin.GetSize()
        #    self.visWin.SetDefaultSize((event.GetDragRect().width,h))

        elif eID == MenuManager.ID_TASK_WIN:
            w,h=self.taskWin.GetSize()
            Logging.info("Setting task window size",kw="main")
            self.taskWin.SetDefaultSize((event.GetDragRect().width,h))
        
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()

    def OnSize(self, event):
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        if self.statusbar:
            rect=self.statusbar.GetFieldRect(1)
            self.progress.SetPosition((rect.x+2,rect.y+2))
            self.progress.SetSize((rect.width-4,rect.height-4))
        

    def showVisualization(self,window):
        """
        Method: showVisualization
        Created: 20.5.2005, KP
        Description: Changes the window to show in the split window
        """
        if window==self.currentVisualizationWindow:
            return
        if self.currentVisualizationWindow:     
            if self.currentVisualizationWindow != self.visWin:
                Logging.info("Hiding ",self.currentVisualizationWindow,kw="main")
                self.currentVisualizationWindow.Show(0)
            Logging.info("Showing",window,kw="main")
            window.Show()
            window.SetSize((self.currentVisualizationWindow.GetSize()))
            self.currentVisualizationWindow=window
        else:
            Logging.info("Showing",window,kw="main")
            self.currentVisualizationWindow = window
            window.Show()
            
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()
        
    def createStatusBar(self):
        """
        Method: createStatusBar()
        Created: 13.7.2006, KP
        Description: Creates a status bar for the window
        """
        self.statusbar=wx.StatusBar(self)
        self.SetStatusBar(self.statusbar)
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths([-3,-1])
        self.progress=wx.Gauge(self.statusbar)
        self.progress.SetRange(100)
        self.progress.SetValue(100)

        messenger.connect(None,"update_progress",self.updateProgressBar)
        
        
        
    def updateProgressBar(self,obj,event,arg,text=None):
        """
        Method: updateProgressBar()
        Created: 03.11.2004, KP
        Description: Updates the progress bar
        """
        if type(arg)==types.FloatType:
            arg*=100
        self.progress.SetValue(int(arg))
        if text:
            self.statusbar.SetStatusText(text)
        wx.GetApp().Yield(1)
        #wx.SafeYield()

    def createToolBar(self):
        """
        Method: createToolBar()
        Created: 03.11.2004, KP
        Description: Creates a tool bar for the window
        """
        iconpath=reduce(os.path.join,["Icons"])
        self.CreateToolBar(wx.NO_BORDER|wx.TB_HORIZONTAL)#|wx.TB_TEXT)
        tb=self.GetToolBar()            
        tb.SetToolBitmapSize((32,32))
        self.taskIds=[]
        self.visIds=[]
        Logging.info("Creating toolbar",kw="init")
        bmp = wx.Image(os.path.join(iconpath,"open_dataset.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_OPEN,"Open",bmp,shortHelp="Open dataset series")
        wx.EVT_TOOL(self,MenuManager.ID_OPEN,self.onMenuOpen)

        bmp = wx.Image(os.path.join(iconpath,"save_snapshot.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SAVE_SNAPSHOT,"Save rendered image",bmp,shortHelp="Save a snapshot of the rendered scene")
    
        
        bmp = wx.Image(os.path.join(iconpath,"open_settings.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_OPEN_SETTINGS,"Open settings",bmp,shortHelp="Open settings")
        wx.EVT_TOOL(self,MenuManager.ID_OPEN_SETTINGS,self.onMenuOpenSettings)
        bmp = wx.Image(os.path.join(iconpath,"save_settings.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SAVE_SETTINGS,"Save settings",bmp,shortHelp="Save settings")
        wx.EVT_TOOL(self,MenuManager.ID_SAVE_SETTINGS,self.onMenuSaveSettings)
        bmp = wx.Image(os.path.join(iconpath,"tree.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SHOW_TREE,"File manager",bmp,kind=wx.ITEM_CHECK,shortHelp="Show file management tree")
        wx.EVT_TOOL(self,MenuManager.ID_SHOW_TREE,self.onMenuVisualizer)
        
        self.visIds.append(MenuManager.ID_SHOW_TREE)

        tb.AddSeparator()
        
        bmp = wx.Image(os.path.join(iconpath,"task_merge.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_COLORMERGING,"Merge",bmp,kind=wx.ITEM_CHECK,shortHelp="Merge multiple datasets")        
        wx.EVT_TOOL(self,MenuManager.ID_COLORMERGING,self.onMenuShowTaskWindow)       

        self.taskIds.append(MenuManager.ID_COLORMERGING)
        
        bmp = wx.Image(os.path.join(iconpath,"task_colocalization.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_COLOCALIZATION,"Colocalization",bmp,kind=wx.ITEM_CHECK,shortHelp="Calculate colocalization between channels")
        wx.EVT_TOOL(self,MenuManager.ID_COLOCALIZATION,self.onMenuShowTaskWindow)       

        self.taskIds.append(MenuManager.ID_COLOCALIZATION)
        #tb.AddSimpleTool(MenuManager.ID_VSIA,
        #wx.Image(os.path.join(iconpath,"HIV.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Visualization of sparse intensity aggregations","Visualization of sparse intensity aggregations")
        #wx.EVT_TOOL(self,MenuManager.ID_VSIA,onMenuShowTaskWindow)

        bmp = wx.Image(os.path.join(iconpath,"task_adjust.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_ADJUST,"Adjust",bmp,kind=wx.ITEM_CHECK,shortHelp="Adjust a dataset")        
        wx.EVT_TOOL(self,MenuManager.ID_ADJUST,self.onMenuShowTaskWindow)

        self.taskIds.append(MenuManager.ID_ADJUST)

        bmp = wx.Image(os.path.join(iconpath,"task_process.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_RESTORE,"Process",bmp,kind=wx.ITEM_CHECK,shortHelp="Improve dataset quality")
        wx.EVT_TOOL(self,MenuManager.ID_RESTORE,self.onMenuShowTaskWindow)

        self.taskIds.append(MenuManager.ID_RESTORE)
        tb.AddSeparator()

        #tb.AddSimpleTool(MenuManager.ID_RESLICE,
        #wx.Image(os.path.join(iconpath,"Reslice.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Re-edit dataset series","Re-edit a dataset series")
        #wx.EVT_TOOL(self,MenuManager.ID_RESLICE,onMenuShowTaskWindow)


        bmp = wx.Image(os.path.join(iconpath,"view_slices.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_VIS_SLICES,"Slices",bmp,kind=wx.ITEM_CHECK,shortHelp="Preview dataset slice by slice")                
        wx.EVT_TOOL(self,MenuManager.ID_VIS_SLICES,self.onMenuVisualizer)

        self.visIds.append(MenuManager.ID_VIS_SLICES)

        bmp = wx.Image(os.path.join(iconpath,"view_gallery.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_VIS_GALLERY,"Gallery",bmp,kind=wx.ITEM_CHECK,shortHelp="Gallery of dataset slices")                
        wx.EVT_TOOL(self,MenuManager.ID_VIS_GALLERY,self.onMenuVisualizer)

        self.visIds.append(MenuManager.ID_VIS_GALLERY)

        bmp = wx.Image(os.path.join(iconpath,"view_sections.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_VIS_SECTIONS,"Sections",bmp,kind=wx.ITEM_CHECK,shortHelp="Preview sections of dataset")
        wx.EVT_TOOL(self,MenuManager.ID_VIS_SECTIONS,self.onMenuVisualizer)

        self.visIds.append(MenuManager.ID_VIS_SECTIONS)

        bmp = wx.Image(os.path.join(iconpath,"view_rendering.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_VIS_3D,"3D",bmp,kind=wx.ITEM_CHECK,shortHelp="Render dataset in 3D")                
        wx.EVT_TOOL(self,MenuManager.ID_VIS_3D,self.onMenuVisualizer)

        self.visIds.append(MenuManager.ID_VIS_3D)

        tb.AddSeparator()
        
        bmp = wx.Image(os.path.join(iconpath,"task_animator.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_RENDER,"Animator",bmp,shortHelp="Render the dataset using Animator")                
        #wx.EVT_TOOL(self,MenuManager.ID_RENDER,self.onMenuAnimator)
        wx.EVT_TOOL(self,MenuManager.ID_RENDER,self.onMenuVisualizer)

        tb.Realize()
        
    def createMenu(self):
        """
        Method: createMenu()
        Created: 03.11.2004, KP
        Description: Creates a menu for the window
        """
        self.menu = wx.MenuBar()
        mgr=self.menuManager
        self.SetMenuBar(self.menu)
        mgr.setMenuBar(self.menu)
        # We create the menu objects
        mgr.createMenu("file","&File")
        mgr.createMenu("settings","&Settings")
        mgr.createMenu("processing","&Processing")
        mgr.createMenu("visualization","&Visualization")
        mgr.createMenu("view","V&iew")
        mgr.createMenu("help","&Help")
      
        mgr.addMenuItem("settings",MenuManager.ID_PREFERENCES,"&Preferences...",self.onMenuPreferences)
    
        mgr.createMenu("import","&Import",place=0)
        mgr.createMenu("export","&Export",place=0)
        
        mgr.addMenuItem("import",MenuManager.ID_IMPORT_VTIFILES,"&VTK Dataset Series",self.onMenuImport)
        mgr.addMenuItem("import",MenuManager.ID_IMPORT_IMAGES,"&Stack of Images",self.onMenuImport)
   
        mgr.addMenuItem("export",MenuManager.ID_EXPORT_VTIFILES,"&VTK Dataset Series",self.onMenuExport)
        mgr.addMenuItem("export",MenuManager.ID_EXPORT_IMAGES,"&Stack of Images",self.onMenuExport)

        mgr.addMenuItem("file",MenuManager.ID_OPEN,"&Open...\tCtrl-O",self.onMenuOpen)

        mgr.addMenuItem("file",MenuManager.ID_OPEN_SETTINGS,"&Load settings",self.onMenuOpenSettings)
        mgr.addMenuItem("file",MenuManager.ID_SAVE_SETTINGS,"&Save settings",self.onMenuSaveSettings)
#        mgr.disable(MenuManager.ID_OPEN_SETTINGS)
#        mgr.disable(MenuManager.ID_SAVE_SETTINGS)
        
        mgr.addSeparator("file")
        mgr.addSubMenu("file","import","&Import",MenuManager.ID_IMPORT)
        mgr.addSubMenu("file","export","&Export",MenuManager.ID_EXPORT)
        mgr.addSeparator("file")
        mgr.addMenuItem("file",MenuManager.ID_CLOSE_TASKWIN,"&Close\tCtrl-W","Close the task panel",self.onCloseTaskPanel)
        mgr.disable(MenuManager.ID_CLOSE_TASKWIN)
        mgr.addSeparator("file")
        mgr.addMenuItem("file",MenuManager.ID_QUIT,"&Quit\tCtrl-Q","Quit the application",self.quitApp)

        
        mgr.addMenuItem("processing",MenuManager.ID_COLOCALIZATION,"&Colocalization...","Create a colocalization map",self.onMenuShowTaskWindow)
        mgr.addMenuItem("processing",MenuManager.ID_COLORMERGING,"Color &Merging...","Merge dataset series",self.onMenuShowTaskWindow)
        mgr.addMenuItem("processing",MenuManager.ID_ADJUST,"&Adjust...","Adjust dataset series",self.onMenuShowTaskWindow)
        mgr.addMenuItem("processing",MenuManager.ID_RESTORE,"&Restore...","Restore dataset series",self.onMenuShowTaskWindow)

        mgr.addMenuItem("visualization",MenuManager.ID_VIS_SLICES,"&Slices","Visualize individual optical slices")
        mgr.addMenuItem("visualization",MenuManager.ID_VIS_SECTIONS,"S&ections","Visualize xy- xz- and yz- planes")
        mgr.addMenuItem("visualization",MenuManager.ID_VIS_GALLERY,"&Gallery","Visualize all the optical slices")
        mgr.addMenuItem("visualization",MenuManager.ID_VIS_3D,"&Visualize in 3D","Visualize the dataset in 3D")
        mgr.addSeparator("visualization")
        mgr.addMenuItem("visualization",MenuManager.ID_LIGHTS,"&Lights...","Configure lightning")
        mgr.addMenuItem("visualization",MenuManager.ID_RENDERWIN,"&Render window","Configure Render Window")
        mgr.addMenuItem("visualization",MenuManager.ID_RELOAD,"Re-&Load Modules","Reload the visualization modules")
        
        mgr.disable(MenuManager.ID_LIGHTS)
        mgr.disable(MenuManager.ID_RENDERWIN)
        mgr.disable(MenuManager.ID_RELOAD)
        
        wx.EVT_MENU(self,MenuManager.ID_RENDER,self.onMenuAnimator)
        wx.EVT_MENU(self,MenuManager.ID_RELOAD,self.onMenuReload)

        mgr.addMenuItem("view",MenuManager.ID_VIEW_CONFIG,"View &Configuration Panel","Show or hide the configuration panel",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.addMenuItem("view",MenuManager.ID_VIEW_TASKPANEL,"View &Task Panel","Show or hide task panel",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.disable(MenuManager.ID_VIEW_TASKPANEL)

        mgr.addMenuItem("view",MenuManager.ID_VIEW_TOOLBAR,"View &Toolbar","Show or hide toolbar",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.addMenuItem("view",MenuManager.ID_VIEW_HISTOGRAM,"View &Histograms","Show or hide channel histograms",self.onMenuToggleVisibility,check=1,checked=0)
        mgr.disable(MenuManager.ID_VIEW_TOOLBAR)
        mgr.disable(MenuManager.ID_VIEW_HISTOGRAM)

        mgr.addMenuItem("help",MenuManager.ID_ABOUT,"&About BioImageXD","About BioImageXD",self.onMenuAbout)
        mgr.addSeparator("help")
        mgr.addMenuItem("help",MenuManager.ID_HELP,"&Help\tCtrl-H","Online Help")        
    
    def onMenuToggleVisibility(self,evt):
        """
        Method: onMenuToggleVisibility()
        Created: 16.03.2005, KP
        Description: Callback function for menu item "Import"
        """
        eid=evt.GetId()
        cmd="hide"
        if evt.IsChecked():cmd="show"
        if eid==MenuManager.ID_VIEW_CONFIG:
            obj="config"
        elif eid==MenuManager.ID_VIEW_TOOLBAR:
            obj="toolbar"
        elif eid==MenuManager.ID_VIEW_HISTOGRAM:
            obj="histogram"
        elif eid==MenuManager.ID_VIEW_TASKPANEL:
            if cmd=="hide":
                self.taskWin.origSize=self.taskWin.GetSize()
                self.taskWin.SetDefaultSize((0,0))
            else:
                self.taskWin.SetDefaultSize(self.taskWin.origSize)
            self.OnSize(None)
            return

        messenger.send(None,cmd,obj)
        
    def onCloseTaskPanel(self,event):
        """
        Method: onCloseTaskPanel(event)
        Created: 14.07.2005, KP
        Description: Called when the user wants to close the task panel
        """
        if self.currentTaskWindow: 
            self.currentTaskWindow.Show(0)
            self.currentTaskWindow.Destroy()
            del self.currentTaskWindow
            self.currentTaskWindow=None
        self.menuManager.disable(MenuManager.ID_CLOSE_TASKWIN)            
        self.taskWin.SetDefaultSize((0,0))
        self.loadVisualizer(None,"info")
        self.setButtonSelection(MenuManager.ID_SHOW_TREE,1)
        # Set the dataunit used by visualizer to one of the source units
        selectedUnits=self.tree.getSelectedDataUnits()
        self.visualizer.setProcessedMode(0)
        self.visualizer.setDataUnit(selectedUnits[0])
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()
        
    
    def onMenuImport(self,evt):
        """
        Method: onMenuImport()
        Created: 16.03.2005, KP
        Description: Callback function for menu item "Import"
        """
        self.importdlg=ImportDialog.ImportDialog(self)
        self.importdlg.ShowModal()
        
    def onMenuExport(self,evt):
        """
        Method: onMenuExport()
        Created: 20.04.2005, KP
        Description: Callback function for menu item "Export"
        """
        selectedFiles=self.tree.getSelectedDataUnits()
        if len(selectedFiles)>1:
            Dialogs.showerror(self,"You can only export one dataunit at a time","Cannot export multiple datasets")
            return
        elif len(selectedFiles)<1:
            Dialogs.showerror(self,"You need to select a dataunit to be exported.","Select dataunit to be exported")
            return
        eid = evt.GetId()
        imageMode = 0
        if eid == MenuManager.ID_EXPORT_IMAGES:
            imageMode = 1
        self.importdlg=ExportDialog.ExportDialog(self,selectedFiles[0],imageMode)
        
        self.importdlg.ShowModal()
        
    
    def onMenuPreferences(self,evt):
        """
        Method: menuPreferences()
        Created: 09.02.2005, KP
        Description: Callback function for menu item "Preferences"
        """
        self.settingswindow=SettingsWindow.SettingsWindow(self)
        self.settingswindow.ShowModal()

    def onMenuReload(self,evt):
        """
        Method: onMenuReload()
        Created: 24.05.2005, KP
        Description: Callback function for reloading vis modules
        """
        self.visualizer.reloadModules()

    def onMenuVisualizer(self,evt):
        """
        Method: onMenuVisualizer()
        Created: 26.04.2005, KP
        Description: Callback function for launching the visualizer
        """
        eid=evt.GetId()
        if eid==MenuManager.ID_VIS_GALLERY:
            mode="gallery"
        elif eid==MenuManager.ID_VIS_SLICES:
            mode="slices"
        elif eid==MenuManager.ID_VIS_SECTIONS:
            mode="sections"
        elif eid==MenuManager.ID_SHOW_TREE:
            mode="info"
        elif eid==MenuManager.ID_RENDER:
            mode="animator"
        else:
            mode="3d"


        self.setButtonSelection(eid)

        # If a visualizer is already running, just switch the mode
        selectedFiles=self.tree.getSelectedDataUnits()
        dataunit = selectedFiles[0]
        if self.visualizer:
#            if not self.visualizer.dataUnit:
            hasDataunit=not not self.visualizer.dataUnit
            if not hasDataunit or (not self.visualizer.getProcessedMode() and (self.visualizer.dataUnit != dataunit)):
                Logging.info("Setting dataunit for visualizer",kw="main")
                self.visualizer.setDataUnit(dataunit)
            self.visualizer.setVisualizationMode(mode)
            #self.visualizer.setDataUnit(dataunit)
            self.showVisualization(self.visPanel)
            self.visualizer.enable(1)
            if hasDataunit:
                Logging.info("Forcing visualizer update since dataunit has been changed",kw="visualizer")
                self.visualizer.updateRendering()
            return
        if len(selectedFiles)>1:
            lst=[]
            for i in selectedFiles:
                lst.append(i.getName())
            Dialogs.showerror(self,
            "You have selected the following datasets: %s.\n"
            "More than one dataset cannot be opened in the visualizer concurrently.\nPlease "
            "select only one dataset or use the merging tool."%(", ".join(lst)),
            "Multiple datasets selected")
            return
        if len(selectedFiles)<1:
            Dialogs.showerror(self,
            "You have not selected a dataset series to be loaded to mayavi.\nPlease "
            "select a dataset series and try again.\n","No dataset selected")
            return            
            
        dataunit = selectedFiles[0]
        self.loadVisualizer(dataunit,mode,0)
        
    def loadVisualizer(self,dataunit,mode,processed=0,**kws):
        """
        Method: loadVisualizer
        Created: 25.05.2005, KP
        Description: Load a dataunit and a given mode to visualizer
        """
        preload=0
        if kws.has_key("preload"):
            Logging.info("Preloading",kw="init")
            preload=kws["preload"]
            
        if not self.visualizer:
            self.visPanel = wx.SashLayoutWindow(self.visWin,-1)
            self.visualizer=Visualizer.Visualizer(self.visPanel,self.menuManager,self)
            self.menuManager.setVisualizer(self.visualizer)
            self.visualizer.setProcessedMode(processed)
        self.visualizer.enable(0)

        self.menuManager.menus["visualization"].Enable(MenuManager.ID_RELOAD,1)
        wx.EVT_TOOL(self,MenuManager.ID_SAVE_SNAPSHOT,self.visualizer.onSnapshot)    
            
        self.visualizer.enable(0,preload=preload)

        if not preload and dataunit:
            self.visualizer.setDataUnit(dataunit)

        self.visualizer.setVisualizationMode(mode)
        # handle icons

        if not preload:
            self.showVisualization(self.visPanel)            
            self.visualizer.enable(1)
            mgr=self.menuManager
            mgr.enable(MenuManager.ID_VIEW_TOOLBAR)
            mgr.enable(MenuManager.ID_VIEW_HISTOGRAM)


    def onMenuAnimator(self,evt):
        """
        Method: onMenuAnimator()
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Render"
        """
        # Check if one dataset (node) is selected from the tree
        selectedFiles=self.tree.getSelectedDataUnits()
        if len(selectedFiles)>1:
            Dialogs.showerror(self,
            "You have selected the following datasets: %s.\n"
            "More than one dataset cannot be rendered concurrently.\nPlease "
            "select only one dataset and try again."%(", ".join(selectedFiles)),"Multiple datasets selected")
            return
        if len(selectedFiles)<1:
            Dialogs.showerror(self,
            "You have not selected a dataset series to be rendered.\nPlease "
            "select a dataset series and try again.\n","No dataset selected")
            return
        Logging.info("Creating urmas window",kw="animator")
        self.renderWindow=Urmas.UrmasWindow(self)
        
        dataunit=selectedFiles[0]
        Logging.info("Setting dataunit for animator",kw="animator")
        self.renderWindow.setDataUnit(dataunit)
        self.renderWindow.Show()
        #self.renderWindow.startWizard()

    def onMenuOpenSettings(self,event):
        """
        Method: onMenuOpenSettings()
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Load settings"
        """
        if self.visualizer:
            dataunit=self.visualizer.getDataUnit()
            if dataunit:
                name=dataunit.getName()
                filenames=Dialogs.askOpenFileName(self,"Open settings for %s"%name,"Settings (*.du)|*.du")
        
                if not filenames:
                    Logging.info("Got no name for settings file",kw="dataunit")
                    return
                Logging.info("Loading settings for dataset",name," from ",filenames,kw="dataunit")
                parser = RawConfigParser()
                parser.read(filenames)
                dataunit.getSettings().readFrom(parser)
                self.visualizer.setDataUnit(dataunit)
            else:
                Logging.info("No dataunit, cannot load settings")

    def onMenuSaveSettings(self,event):
        """
        Method: onMenuSaveSettings()
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Save settings"
        """
        if self.visualizer:
            dataunit=self.visualizer.getDataUnit()
            if dataunit:
                name=dataunit.getName()
                filename=Dialogs.askSaveAsFileName(self,"Save settings of %s as"%name,"settings.du","Settings (*.du)|*.du")
        
                if not filename:
                    Logging.info("Got no name for settings file",kw="dataunit")
                    return
                Logging.info("Saving settings of dataset",name," to ",filename,kw="dataunit")
                dataunit.doProcessing(filename,settings_only=1)
            else:
                Logging.info("No dataunit, cannot save settings")
        
    def onMenuOpen(self,evt):
        """
        Method: onMenuOpen()
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Open VTK File"
        """
        asklist=[]
        wc="LSM Files (*.lsm)|*.lsm;*.LSM|Leica TCS-NT Files (*.txt)|*.txt;*.TXT|Dataset Series (*.du)|*.du;*.DU|VTK Image Data (*.vti)|*.vti;*.VTI"
        asklist=Dialogs.askOpenFileName(self,"Open dataset series or LSM File",wc)
        
        for askfile in asklist:
            sep=askfile.split(".")[-1]
            fname=os.path.split(askfile)[-1]
            self.SetStatusText("Loading "+fname+"...")
            self.createDataUnit(fname,askfile)
        self.SetStatusText("Done.")

    def createDataUnit(self,name,path):
        """
        Method: createDataUnit(name,path)
        Created: 03.11.2004
        Creator: KP
        Description: Creates a dataunit with the given name and path
        Parameters:
            name    Name used to identify this dataunit
            path    Path to the file this dataunit points to
        """
        ext=path.split(".")[-1]
        dataunit=None
        if self.tree.hasItem(path):
            return
        ext=ext.lower()
        if ext=='du':
            # We check that the file is not merely a settings file
            try:
                self.parser = SafeConfigParser()
                self.parser.read([path])
                # We read the Key SettingsOnly, and check it's value.
                settingsOnly = self.parser.get("Settings", "SettingsOnly")
                if settingsOnly.lower()=="true":
                    # If this file contains only settings, then we report an 
                    # error and do not load it
                    Dialogs.showerror(self,
                    "The file that you selected, %s, contains only settings "
                    "and cannot be loaded.\n"
                    "Use 'Load settings' button from an operation window "
                    "to load it."%name,"Trying to load settings file")
                    return
            except:
                pass

        # We try to load the actual data
        Logging.info("Loading dataset with extension %s, path=%s"%(ext,path),kw="io")
    
        extToSource={"du":VtiDataSource,"lsm":LsmDataSource,"txt":LeicaDataSource}
        try:
            datasource=extToSource[ext]()
        except KeyError,ex:
            Dialogs.showerror(self,"Failed to load file %s: Unrecognized extension %s"%(name,ext),"Unrecognized extension")
            return
        #try:
        #    Logging.info("Loading from data source ",datasource,kw="io")
        dataunits = datasource.loadFromFile(path)
        #except:
        #    Dialogs.showerror(self,"Failed to load file %s."%(name),"Failed to load file")
        #    return

        #print dataunits[0].getSettings().get("Type")
        if not dataunits:
            raise "Failed to read dataunit %s"%path
        
        # We might get tuples from leica
        d={}
        if type(dataunits[0])==types.TupleType:
            for (name,unit) in dataunits:
                if d.has_key(name):d[name].append(unit)
                else:d[name]=[unit]
            for key in d.keys():
                Logging.info("Adding dataunit %s %s %s"%(key,path,ext),kw="io")
                self.tree.addToTree(key,path,ext,d[key])
        else:
            # If we got data, add corresponding nodes to tree
            Logging.info("Adding to tree ",name,path,ext,dataunits,kw="io")
            self.tree.addToTree(name,path,ext,dataunits)

    def onMenuShowTaskWindow(self,event):
        """
        Method: showTaskWindow
        Created: 11.1.2005, KP
        Description: A method that shows a taskwindow of given type
        """
        self.setButtonSelection(event.GetId())
        eid = event.GetId()
        if eid==MenuManager.ID_COLOCALIZATION:
            moduletype,windowtype,mod=self.taskPanels["Colocalization"]
            unittype=mod.getDataUnit()
            filesAtLeast=2
            filesAtMost=-1
            action="Colocalization"
        elif eid==MenuManager.ID_RESLICE:
            moduletype,windowtype,mod=self.taskPanels["Reslice"]
            unittype=mod.getDataUnit()
            filesAtLeast=1
            filesAtMost=1
            action="Reslice"
        elif eid==MenuManager.ID_COLORMERGING:
            moduletype,windowtype,mod=self.taskPanels["Merging"]
            unittype=mod.getDataUnit()
            filesAtLeast=2
            filesAtMost=-1
            action="Merging"
        elif eid==MenuManager.ID_ADJUST:
            moduletype,windowtype,mod=self.taskPanels["Adjust"]
            unittype=mod.getDataUnit()
            filesAtLeast=1
            filesAtMost=1
            action="Adjusted"
        elif eid==MenuManager.ID_RESTORE:
            moduletype,windowtype,mod=self.taskPanels["Process"]
            unittype=mod.getDataUnit()
            filesAtLeast=1
            filesAtMost=1
            action="Restored"
        elif eid==MenuManager.ID_VSIA:
            moduletype,windowtype,mod=self.taskPanels["SurfaceConstruction"]
            unittype=mod.getDataUnit()
            filesAtLeast=1
            filesAtMost=1
            action="VSIA'd"
        Logging.info("Module type for taskwindow: ",moduletype,kw="task")
        selectedFiles=self.tree.getSelectedDataUnits()
        if filesAtLeast!=-1 and len(selectedFiles)<filesAtLeast:
            Dialogs.showerror(self,
            "You need to select at least %d source data units for %s"%(filesAtLeast,action),"Select more datasets")
            return            
        elif filesAtMost!=-1 and len(selectedFiles)>filesAtMost:
            Dialogs.showerror(self,
            "You can select at most %d source data units for %s"%(filesAtMost,action),"Select fewer datasets")
            return

        names=[i.getName() for i in selectedFiles]
        # Sets name for new dataset series
        name="%s (%s)"%(action,", ".join(names))

        Logging.info(unittype,name,kw="task")
        unit = unittype(name)
        Logging.info("unit = %s(%s)=%s"%(unittype,name,unit),kw="task")
        for dataunit in selectedFiles:
            unit.addSourceDataUnit(dataunit)
            Logging.info("ctf of source=",dataunit.getSettings().get("ColorTransferFunction"),kw="ctf")

        Logging.info("Moduletype=",moduletype,kw="dataunit")
        module=moduletype()
        unit.setModule(module)

        if windowtype==self.currentTaskWindowType:
            Logging.info("Window of type ",windowtype,"already showing",kw="task")
            return
        self.currentTaskWindowType=windowtype
        
        
        # If visualizer has not been loaded, load it now
        # This is a high time to have a visualization loaded
        if not self.visualizer:
            Logging.info("Loading slices view for ",unit,kw="task")
            self.loadVisualizer(unit,"slices",1)
            self.setButtonSelection(MenuManager.ID_VIS_SLICES)

        else:
            if not self.visualizer.getProcessedMode():
                self.visualizer.setProcessedMode(1)

        self.visualizer.setDataUnit(unit)
            
        if self.visualizer.mode=="info":
            Logging.info("Switching to slices from info",kw="task")
            self.visualizer.setVisualizationMode("slices")
            self.setButtonSelection(MenuManager.ID_VIS_SLICES)
            self.visualizer.enable(1)

        window=windowtype(self.taskWin,self.menuManager)
        window.setCombinedDataUnit(unit)

        if self.currentTaskWindow:          
            self.currentTaskWindow.Show(0)
            self.currentTaskWindow.Destroy()
            del self.currentTaskWindow
            window.Show()
            self.currentTaskWindow=window
        else:
            self.currentTaskWindow = window
        w,h=self.taskWin.GetSize()
        self.taskWin.SetDefaultSize((350,h))
            
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()
        self.menuManager.enable(MenuManager.ID_CLOSE_TASKWIN)
        self.menuManager.enable(MenuManager.ID_VIEW_TASKPANEL)
       
    def setButtonSelection(self,eid,all=0):
        """
        Method: showButtonSelection(eid)
        Created: 01.06.2005, KP
        Description: Select only the selected button
        """
        lst=[]
        if all:
            lst.extend(self.visIds)
            lst.extend(self.taskIds)
        else:
            if eid in self.visIds:
                lst.extend(self.visIds)
            else:
                lst.extend(self.taskIds)
        tb=self.GetToolBar()
        for i in lst:
            flag=(i == eid)
            tb.ToggleTool(i,flag)        

    def onMenuAbout(self,evt):
        """
        Method: onMenuAbout()
        Created: 03.11.2004, KP
        Description: Callback function for menu item "About"
        """
        about=AboutDialog.AboutDialog(self)
        about.ShowModal()
        about.Destroy()
        

    def quitApp(self,evt):
        """
        Method: quitApp()
        Created: 03.11.2004, KP
        Description: Quits the application
        """
        self.Close(True)
        
