#! /usr/bin/env python
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

import vtk

from ConfigParser import *
from TreeWidget import *
from Logging import *
from GUI import Events

from TaskWindow import TaskWindow,ColorMergingWindow,ColocalizationWindow
from TaskWindow import AdjustmentWindow,RestorationWindow

import SettingsWindow
import ImportDialog
import ExportDialog
import RenderingInterface

import Visualization


import InfoWidget
import MenuManager

import Dialogs
import AboutDialog

import Reslice

from DataUnit import *
from DataSource import *

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
        

        self.sashPos=200
        self.Bind(
            wx.EVT_SASH_DRAGGED_RANGE, self.onSashDrag,
            id=MenuManager.ID_TREE_WIN, id2=MenuManager.ID_TASK_WIN,
        )

        self.menuManager=MenuManager.MenuManager(self,text=0)
        
        print MenuManager.ID_TREE_WIN
#        self.treeWin=wx.SashLayoutWindow(self,MenuManager.ID_TREE_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
#        self.treeWin.SetOrientation(wx.LAYOUT_VERTICAL)
#        self.treeWin.SetAlignment(wx.LAYOUT_LEFT)
#        self.treeWin.SetSashVisible(wx.SASH_RIGHT,True)
#        self.treeWin.SetSashBorder(wx.SASH_RIGHT,True)
#        self.treeWin.SetDefaultSize((200,768))
        
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

        self.CreateStatusBar()
        self.SetStatusText("Starting up...")

        # Create Menu, ToolBar and Tree
        self.createMenu()
        self.createToolBar()

        self.dataunits={}
        self.paths={}
        self.currentVisualizationWindow=None
        self.currentTaskWindow=None
        self.currentTaskWindowType=None

        self.SetStatusText("Done.")
        
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.preloadWindows()
        self.loadVisualizer(None,"info")
        # HACK
        self.tree = self.visualizer.currMode.tree

        splash.Show(False)
        self.Show(True)

    def preloadWindows(self):
        """
        Method: preloadWindows()
        Created: 03.6.2005, KP
        Description: A method for preloading renderer so that it won't be as slow to
                     show it
        """
        self.loadVisualizer(None,"slices",0,preload=1)
        self.loadVisualizer(None,"gallery",0,preload=1)
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
            print "Setting task win size"
            self.taskWin.SetDefaultSize((event.GetDragRect().width,h))
        
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()

    def OnSize(self, event):
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        

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
                print "hiding",self.currentVisualizationWindow
                self.currentVisualizationWindow.Show(0)
            print "showing",window
            window.Show()
            window.SetSize((self.currentVisualizationWindow.GetSize()))
            self.currentVisualizationWindow=window
        else:
            print "Showing ",window
            self.currentVisualizationWindow = window
            window.Show()
            
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()


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
        print "adding tool"
        bmp = wx.Image(os.path.join(iconpath,"open_dataset.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_OPEN,"Open",bmp,shortHelp="Open dataset series")
        wx.EVT_TOOL(self,MenuManager.ID_OPEN,self.onMenuOpen)

        bmp = wx.Image(os.path.join(iconpath,"save_snapshot.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SAVE_SNAPSHOT,"Save rendered image",bmp,shortHelp="Save a snapshot of the rendered scene")
    
        
        bmp = wx.Image(os.path.join(iconpath,"open_settings.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_OPEN_SETTINGS,"Open settings",bmp,shortHelp="Open settings")
#        wx.EVT_TOOL(self,MenuManager.ID_OPEN_SETTINGS,self.onMenuOpenSettings)
        bmp = wx.Image(os.path.join(iconpath,"save_settings.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_OPEN_SETTINGS,"Save settings",bmp,shortHelp="Save settings")
#        wx.EVT_TOOL(self,MenuManager.ID_OPEN_SETTINGS,self.onMenuOpenSettings)
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
        mgr.createMenu("help","&Help")
      
        mgr.addMenuItem("settings",MenuManager.ID_PREFERENCES,"&Preferences...",self.onMenuPreferences)
    
        mgr.createMenu("import","&Import",place=0)
        mgr.createMenu("export","&Export",place=0)
        
        mgr.addMenuItem("import",MenuManager.ID_IMPORT_VTIFILES,"&VTK Dataset Series",self.onMenuImport)
        mgr.addMenuItem("import",MenuManager.ID_IMPORT_IMAGES,"&Stack of Images",self.onMenuImport)
   
        mgr.addMenuItem("export",MenuManager.ID_EXPORT_VTIFILES,"&VTK Dataset Series",self.onMenuExport)
        mgr.addMenuItem("export",MenuManager.ID_EXPORT_IMAGES,"&Stack of Images",self.onMenuExport)

        mgr.addMenuItem("file",MenuManager.ID_OPEN,"&Open...\tCtrl-O",self.onMenuOpen)

        mgr.addMenuItem("file",MenuManager.ID_OPEN_SETTINGS,"&Load settings")
        mgr.addMenuItem("file",MenuManager.ID_SAVE_SETTINGS,"&Save settings")
        mgr.disable(MenuManager.ID_OPEN_SETTINGS)
        mgr.disable(MenuManager.ID_SAVE_SETTINGS)
        
        mgr.addSeparator("file")
        mgr.addSubMenu("file","import","&Import",MenuManager.ID_IMPORT)
        mgr.addSubMenu("file","export","&Export",MenuManager.ID_EXPORT)
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

        mgr.addMenuItem("help",MenuManager.ID_ABOUT,"&About BioImageXD","About BioImageXD",self.onMenuAbout)
        mgr.addSeparator("help")
        mgr.addMenuItem("help",MenuManager.ID_HELP,"&Help\tCtrl-H","Online Help")        
    
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
            self.visualizer.enable(0)
#            if not self.visualizer.dataUnit:
            if not self.visualizer.dataUnit or (not self.visualizer.getProcessedMode() and (self.visualizer.dataUnit != dataunit)):
                self.visualizer.setDataUnit(dataunit)
            self.visualizer.setVisualizationMode(mode)
            self.visualizer.setDataUnit(dataunit)
            self.showVisualization(self.visPanel)
            self.visualizer.enable(1)
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
            print "Preloading!"
            preload=kws["preload"]
            
        if not self.visualizer:
            self.visPanel = wx.SashLayoutWindow(self.visWin,-1)
            self.visualizer=Visualization.Visualizer(self.visPanel,self.menuManager,self)
            self.menuManager.setVisualizer(self.visualizer)
            self.visualizer.setProcessedMode(processed)
        self.visualizer.enable(0)

        self.menuManager.menus["visualization"].Enable(MenuManager.ID_RELOAD,1)
        wx.EVT_TOOL(self,MenuManager.ID_SAVE_SNAPSHOT,self.visualizer.onSnapshot)    
            
        self.visualizer.enable(0,preload=preload)

        if not preload and dataunit:
            self.visualizer.setDataUnit(dataunit)

        self.visualizer.setVisualizationMode(mode)

        if not preload:
            self.showVisualization(self.visPanel)
            print "visualizer.enable(1)"
            self.visualizer.enable(1)

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
        
        print "Creating urmas window"
        self.renderWindow=Urmas.UrmasWindow(self)
        
        dataunit=selectedFiles[0]
        #correctedUnit=CorrectedSourceDataUnit("Rendered dataunit")
        #correctedUnit.addSourceDataUnit(dataunit)
        print "Setting dataunit"
        self.renderWindow.setDataUnit(dataunit)
        print "SHowing..."
        self.renderWindow.Show()
        #self.renderWindow.startWizard()


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
        print "ext=",ext
        extToSource={"du":VtiDataSource,"lsm":LsmDataSource,"txt":LeicaDataSource}
        try:
            datasource=extToSource[ext]()
        except KeyError,ex:
            Dialogs.showerror(self,"Failed to load file %s: Unrecognized extension %s"%(name,ext),"Unrecognized extension")
            return
        #try:
        #    print "Loading from datasource ",datasource
        dataunits = datasource.loadFromFile(path)
        #    print "Got ",dataunits
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
                print "Adding %s %s %s"%(key,path,ext)
                self.tree.addToTree(key,path,ext,d[key])
        else:
            # If we got data, add corresponding nodes to tree
            print "adding to tree ",name,path,ext,dataunits
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
            moduletype=Colocalization.Colocalization
            windowtype=ColocalizationWindow.ColocalizationWindow
            unittype=ColocalizationDataUnit
            filesAtLeast=2
            filesAtMost=-1
            action="Colocalization"
        elif eid==MenuManager.ID_RESLICE:
            moduletype=Reslice.Reslice
            windowtype=ResliceWindow.ResliceWindow
            unittype=ResliceDataUnit
            filesAtLeast=1
            filesAtMost=1
            action="Reslice"
        elif eid==MenuManager.ID_COLORMERGING:
            moduletype=ColorMerging.ColorMerging
            windowtype=ColorMergingWindow.ColorMergingWindow
            unittype=ColorMergingDataUnit
            filesAtLeast=2
            filesAtMost=-1
            action="Merging"
        elif eid==MenuManager.ID_ADJUST:
            moduletype=DataUnitProcessing.DataUnitProcessing
            windowtype=AdjustmentWindow.AdjustmentWindow
            unittype=CorrectedSourceDataUnit
            filesAtLeast=1
            filesAtMost=1
            action="Adjusted"
        elif eid==MenuManager.ID_RESTORE:
            moduletype=DataUnitProcessing.DataUnitProcessing
            windowtype=RestorationWindow.RestorationWindow
            unittype=CorrectedSourceDataUnit
            filesAtLeast=1
            filesAtMost=1
            action="Restored"
        elif eid==MenuManager.ID_VSIA:
            moduletype=VSIA.VSIA
            windowtype=VSIAWindow.VSIAWindow
            filesAtLeast=1
            filesAtMost=1
            action="VSIA'd"
        print "got moduletype",moduletype
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

        print unittype,dir(unittype),name
        unit = unittype(name)
        print unit
        print "unit = %s(%s)=%s"%(unittype,name,unit)
        for dataunit in selectedFiles:
            unit.addSourceDataUnit(dataunit)

        module=moduletype()
        unit.setModule(module)

        if windowtype==self.currentTaskWindowType:
            return
        self.currentTaskWindowType=windowtype
        
        
        # If visualizer has not been loaded, load it now
        # This is a high time to have a visualization loaded
        if not self.visualizer:
            print "Loading visualizer for ",unit
            self.loadVisualizer(unit,"slices",1)
        else:
            if not self.visualizer.getProcessedMode():
                self.visualizer.setProcessedMode(1)

        self.visualizer.setDataUnit(unit)
            
        if self.visualizer.mode=="info":
            print "Switching to slices"
            self.visualizer.setVisualizationMode("slices")
            self.visualizer.enable(1)
            

        window=windowtype(self.taskWin,self.menuManager)
        window.setCombinedDataUnit(unit)

        self.visWin.Bind(Events.EVT_ZSLICE_CHANGED,window.updateZSlice)
        self.visWin.Bind(Events.EVT_TIMEPOINT_CHANGED,window.updateTimepoint)
        window.Bind(Events.EVT_DATA_UPDATE,self.visualizer.updateRendering,id=window.GetId())
        window.Bind(Events.EVT_TIMEPOINT_CHANGED,self.visualizer.onSetTimepoint,id=window.GetId())
        if self.currentTaskWindow:          
            self.currentTaskWindow.Show(0)
            window.Show()
            self.currentTaskWindow=window
        else:
            self.currentTaskWindow = window
        w,h=self.taskWin.GetSize()
        self.taskWin.SetDefaultSize((300,h))
            
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()

#        dataunit,filepath=TaskWindow.showTaskWindow(windowtype,unit,self)

        # If user cancelled operation, we do not get a new dataset -> return
        if not dataunit:
            return

        # Add the dataset (node) into tree
        #self.tree.addToTree(dataunit.getName(),filepath,'du',[dataunit])        
        
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
        
