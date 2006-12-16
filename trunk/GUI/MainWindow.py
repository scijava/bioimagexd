#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MainWindow
 Project: BioImageXD
 Created: 03.11.2004, KP
 Description:

 The main window for the BioImageXD program

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

 You should have received a copy of resathe GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.71 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

VERSION="0.9.0 beta"


import os.path,os,types
import wx
import types
import vtk
import random
import time
import imp
import sys

import wx.lib.buttons as buttons

import messenger

from ConfigParser import *
import TreeWidget

import Logging

import  wx.py as py

import SettingsWindow
import ImportDialog
import ExportDialog
import ScriptEditor
import UndoListBox

import RenderingInterface
import Configuration

import Visualizer

import InfoWidget
import MenuManager

import Dialogs
import AboutDialog
import RescaleDialog
import ResampleDialog

#from DataUnit import *

import Command # Module for classes that implement the Command design pattern
import Modules
import Urmas # The animator, Unified Rendering / Animator
import UIElements

import MaskTray

import scripting as bxd


class MainWindow(wx.Frame):
    """
    Created: 03.11.2004, KP
    Description: The main window for the LSM module
    """
    def __init__(self,parent,id,app,splash):
        """
        Created: 03.11.2004, KP
        Description: Initialization
        Parameters:
            parent    
            id
            app     LSMApplication object
        """
        conf = Configuration.getConfiguration()
        
        Command.mainWindow = self
        self.splash = splash
        
        size=conf.getConfigItem("WindowSize","Sizes")
        if size:
            size=eval(size)
        else:
            size=(1024,768)
                
        wx.Frame.__init__(self,parent,-1,"BioImageXD",size=size,
            style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.Bind(
            wx.EVT_SASH_DRAGGED_RANGE, self.onSashDrag,
            id=MenuManager.ID_TREE_WIN, id2=MenuManager.ID_INFO_WIN,
        )
        self.Bind(wx.EVT_CLOSE,self.quitApp)
        self.progressTimeStamp=0
        self.progressObject=None
        
        self.commands={}
        
        self.tasks={}
        self.help=None
        self.statusbar=None
        self.progress=None
        self.visualizationPanel=None
        self.visualizer=None
        self.nodes_to_be_added=[]
        self.app=app
        self.commandHistory = None
        self.dataunits={}
        self.paths={}
        self.currentVisualizationWindow=None
        self.currentTaskWindow=None
        self.currentTaskWindowName=""
        self.currentTaskWindowType=None

        self.currentTask=""
        self.currentFile=""
        self.currentVisualizationModeName=""
        self.progressCoeff=1.0
        self.progressShift=0.0
        self.taskToId={}
        self.visToId={}
        self.splash.SetMessage("Loading task modules...")
        self.taskPanels = Modules.DynamicLoader.getTaskModules(callback = self.splash.SetMessage)
        self.splash.SetMessage("Loading visualization modes...")
        self.visualizationModes=Modules.DynamicLoader.getVisualizationModes(callback = self.splash.SetMessage)
        self.splash.SetMessage("Loading image readers...")
        self.readers = Modules.DynamicLoader.getReaders(callback = self.splash.SetMessage)
        self.extToSource = {}
        self.datasetWildcards="Volume datasets|"
        
        descs=[]
        self.splash.SetMessage("Initializing application...")
        for modeclass,ign,module in self.readers.values():
            exts = module.getExtensions()
            wcs=""
            for ext in exts:
                self.extToSource[ext]=modeclass
                wcs+="*.%s;"%ext
                wcs+="*.%s;"%ext.upper()
                self.datasetWildcards+=wcs
                descs.append("%s|%s"%(module.getFileType(),wcs[:-1]))
        self.datasetWildcards=self.datasetWildcards[:-1]
        self.datasetWildcards+="|"
        self.datasetWildcards+= "|".join(descs)
        
        for i in self.taskPanels.keys():
            self.taskToId[i] = wx.NewId()
            
        for i in self.visualizationModes.keys():
                self.visToId[i] = wx.NewId()
        
        self.splash.SetMessage("Initializing layout...")
        self.menuManager=MenuManager.MenuManager(self,text=0)
        
        # A window for the file tree
        self.treeWin=wx.SashLayoutWindow(self,MenuManager.ID_TREE_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.treeWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.treeWin.SetAlignment(wx.LAYOUT_LEFT)
        self.treeWin.SetSashVisible(wx.SASH_RIGHT,True)
        self.treeWin.SetDefaultSize((160,768))
        self.treeWin.origSize=(160,768)

        self.treeBtnWin=wx.SashLayoutWindow(self.treeWin,wx.NewId(),style=wx.SW_3D)
        self.treeBtnWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.treeBtnWin.SetAlignment(wx.LAYOUT_BOTTOM)
        self.treeBtnWin.SetSashVisible(wx.SASH_TOP,False)
        self.treeBtnWin.SetDefaultSize((160,32))
        
        self.switchBtn=wx.Button(self.treeBtnWin,-1,"Switch dataset")
        self.switchBtn.Bind(wx.EVT_BUTTON,self.onSwitchDataset)
        self.switchBtn.Enable(0)
    
        # A window for the visualization modes
        self.visWin=wx.SashLayoutWindow(self,MenuManager.ID_VIS_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.visWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.visWin.SetAlignment(wx.LAYOUT_LEFT)
        self.visWin.SetSashVisible(wx.SASH_RIGHT,False)
        self.visWin.SetDefaultSize((500,768))
        #self.visWin=wx.Panel(self,-1,size=(500,768))
        
        # A window for the task panels
        self.taskWin=wx.SashLayoutWindow(self,MenuManager.ID_TASK_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.taskWin.parent=self
        self.taskWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.taskWin.SetAlignment(wx.LAYOUT_RIGHT)
        self.taskWin.SetSashVisible(wx.SASH_LEFT,True)
        self.taskWin.SetSashBorder(wx.SASH_LEFT,True)
        self.taskWin.SetDefaultSize((0,768))
        self.taskWin.origSize=(360,768)
        conf = Configuration.getConfiguration()
        s=conf.getConfigItem("TaskWinSize","Sizes")
        if s:
            s=eval(s)
            self.taskWin.origSize=s
        
        # A window for the task panels
        self.infoWin=wx.SashLayoutWindow(self,MenuManager.ID_INFO_WIN,style=wx.RAISED_BORDER|wx.SW_3D)
        self.infoWin.SetOrientation(wx.LAYOUT_VERTICAL)
        self.infoWin.SetAlignment(wx.LAYOUT_RIGHT)
        self.infoWin.SetSashVisible(wx.SASH_LEFT,True)
        self.infoWin.SetSashBorder(wx.SASH_LEFT,True)
        self.infoWin.SetDefaultSize((300,768))        
        self.infoWin.origSize = (300,768)
        #self.taskWin=wx.Panel(self,-1,size=(0,768))
        
        self.infoWidget=InfoWidget.InfoWidget(self.infoWin)
        
        self.shellWin=wx.SashLayoutWindow(self,MenuManager.ID_SHELL_WIN,style=wx.NO_BORDER)
        self.shellWin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.shellWin.SetAlignment(wx.LAYOUT_BOTTOM)
        #self.shellWin.SetSashVisible(wx.SASH_TOP,False)
        self.shellWin.origSize=(500,128)
        self.shellWin.SetDefaultSize((0,0))
        self.shell=None
        
        
        # Icon for the window
        ico=reduce(os.path.join,[bxd.get_icon_dir(),"logo.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)
        
        messenger.send(None,"update_progress",0.1,"Loading BioImageXD...")        

        
        # Create Menu, ToolBar and Tree
        self.createStatusBar()
        messenger.send(None,"update_progress",0.3,"Creating menus...")        
        self.splash.SetMessage("Creating menus...")
        self.createMenu()
        messenger.send(None,"update_progress",0.6,"Creating toolbars...")        
        self.splash.SetMessage("Creating tool bar...")
        self.createToolBar()
 
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        messenger.send(None,"update_progress",0.9,"Pre-loading visualization views...")        
        
        # Create the file tree
        self.tree=TreeWidget.TreeWidget(self.treeWin)
        
        # Alias for scripting
        self.fileTree = self.tree
        
        self.splash.SetMessage("Loading default visualization mode...")
        self.loadVisualizer(None,"slices",init=1)
        self.onMenuShowTree(None,1)
        try:
            self.splash.Show(False)
            del self.splash
        except:
            pass
        self.Show(True)       
        # Start listening for messenger signals
        messenger.send(None,"update_progress",1.0,"Done.") 
        messenger.connect(None,"set_status",self.onSetStatus)
        messenger.connect(None,"current_task",self.updateTitle)
        messenger.connect(None,"current_file",self.updateTitle)
        messenger.connect(None,"tree_selection_changed",self.onTreeSelectionChanged)
        messenger.connect(None,"get_voxel_at",self.updateVoxelInfo)
        messenger.connect(None,"load_dataunit",self.onMenuOpen)
        messenger.connect(None,"view_help",self.onViewHelp)
        messenger.connect(None,"delete_dataset",self.onDeleteDataset)
        messenger.connect(None,"execute_command",self.onExecuteCommand)        
        messenger.connect(None,"show_error",self.onShowError)
        wx.CallAfter(self.showTip)
        
        
    def loadScript(self, filename):
        """
        Created: 17.07.2006, KP
        Description: Load a given script file
        """   
        print "Loading script...",filename
        f=open(filename)
        module = imp.load_module("script",f,filename,('.py','r',1))
        f.close()
        module.bxd = bxd
        module.mainWindow = self
        module.visualizer = self.visualizer
        module.run()
        
    def loadFiles(self,files):
        """
        Created: 17.07.2006, KP
        Description: Load the given data files
        """         
        for file in files:
            name = os.path.basename(file)
            self.createDataUnit(name, file)            

    def onMenuUndo(self,evt):
        """
        Created: 13.02.2006, KP
        Description: Undo a previous command
        """    
        cmd=self.menuManager.getLastCommand()
        if cmd.canUndo():
            cmd.undo()
            self.menuManager.setUndoedCommand(cmd)
            self.menuManager.enable(MenuManager.ID_REDO)
        
    def onMenuRedo(self,evt):
        """
        Created: 13.02.2006, KP
        Description: Redo a previously undo'd action
        """    
        cmd=self.menuManager.getUndoedCommand()        
        cmd.run()
        self.menuManager.disable(MenuManager.ID_REDO)
        self.menuManager.enable(MenuManager.ID_UNDO)
        
    def onExecuteCommand(self,obj,evt,command,undo=0):
        """
        Created: 13.02.2006, KP
        Description: A command was executed
        """    
        if not undo:
            if command.canUndo():
                undolbl="Undo: %s...\tCtrl-Z"%command.getDesc()
                self.menuManager.menus["edit"].SetLabel(MenuManager.ID_UNDO,undolbl)
        else:
            redolbl="Redo: %s...\tShift-Ctrl-Z"%command.getCategory()
            self.menuManager.menus["edit"].SetLabel(MenuManager.ID_REDO,redolbl)
            self.menuManager.menus["edit"].SetLabel(MenuManager.ID_UNDO,"Undo...\tCtrl-Z")
        self.menuManager.addCommand(command)
        
    def onDeleteDataset(self,obj,evt,arg):
        """
        Created: 12.08.2005, KP
        Description: Remove a dataset from the program
        """        
        close=0
        Logging.info("onDeleteDataset, visualizer dataset=",self.visualizer.dataUnit,"deleted=",arg)
        if self.visualizer.dataUnit == arg:
            close=1
        if self.visualizer.getProcessedMode():
            if arg in self.visualizer.dataUnit.getSourceDataUnits():
                self.onCloseTaskPanel(None)
        if close:
            self.visualizer.closeVisualizer()
            self.loadVisualizer(None,"slices",reload=1)
        
            
        
    def onSwitchDataset(self,evt):
        """
        Created: 11.08.2005, KP
        Description: Switch the datasets used by a task module
        """        
        selectedFiles=self.tree.getSelectedDataUnits()
        messenger.send(None,"switch_datasets",selectedFiles)
        
    def showTip(self):
        """
        Created: 08.08.2005, KP
        Description: Show a tip to the user
        """
        conf = Configuration.getConfiguration()
        showTip=conf.getConfigItem("ShowTip","General")
        #print "showTip=",showTip
        if showTip:
            showTip = eval(showTip)
        tipNumber = int(conf.getConfigItem("TipNumber","General"))
        #print "showtip=",showTip,type(showTip)
        if showTip:
            f=open("Help/tips.txt","r")
            n=len(f.readlines())
            f.close()
            tp = wx.CreateFileTipProvider("Help/tips.txt", random.randrange(n))
            ##tp = MyTP(0)
            showTip = wx.ShowTip(self, tp)
            index = tp.GetCurrentTip()
            conf.setConfigItem("ShowTip","General",showTip)
            conf.setConfigItem("TipNumber","General",index)
            
    def onTreeSelectionChanged(self,obj,evt,data):
        """
        Created: 22.07.2005, KP
        Description: A method for updating the dataset based on tree selection
        """
        selected = self.tree.getSelectedDataUnits()
        dataunits={}
        for i in selected:
            pth = i.dataSource.getPath()
            if pth in dataunits:
                dataunits[pth].append(i)
            else:
                dataunits[pth]=[i]
        names = [i.getName() for i in selected]
        do_cmd="mainWindow.fileTree.unselectAll()"
        for i in dataunits.keys():
            names = [x.getName() for x in dataunits[i]]
            do_cmd+="\n"+"mainWindow.fileTree.selectChannelsByName('%s', %s)"%(i,str(names))
        undo_cmd=""
        cmd=Command.Command(Command.MGMT_CMD,None,None,do_cmd,undo_cmd,desc="Unselect all in file tree")
        cmd.run(recordOnly = 1)          
        
        tb = self.GetToolBar()
        if data.dataSource.getResampleDimensions() != None:            
            tb.EnableTool(MenuManager.ID_RESAMPLING,1)            
        else:
            tb.EnableTool(MenuManager.ID_RESAMPLING,0) 
        # If no task window has been loaded, then we will update the visualizer
        # with the selected dataset
        if not self.currentTaskWindow:
            Logging.info("Setting dataset for visualizer=",data.__class__,kw="dataunit")
            self.visualizer.setDataUnit(data)
            #self.visualizer.updateRendering()
        
    def updateTitle(self,obj,evt,data):
        """
        Created: 22.07.2005, KP
        Description: A method for updating the title of this window
        """
        
        if evt=="current_task":self.currentTask=data
        elif evt=="current_file":self.currentFile=data
        lst=["BioImageXD",self.currentTask,self.currentFile] 
        
        self.SetTitle(lst[0]+" - " + lst[1]+" ("+lst[2]+")")
        
        
    def onSashDrag(self, event):
        """
        Created: 24.5.2005, KP
        Description: A method for laying out the window
        """
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            return

        eID = event.GetId()

        if eID == MenuManager.ID_TREE_WIN:
            w,h=self.treeWin.GetSize()
            newsize=(event.GetDragRect().width,h)
            self.treeWin.SetDefaultSize(newsize)
            #self.tree.SetSize(newsize)
            self.treeWin.origSize=newsize
            #self.tree.SetSize(self.treeWin.GetClientSize())
        #elif eID == MenuManager.ID_VIS_WIN:
        #    w,h=self.visWin.GetSize()
        #    self.visWin.SetDefaultSize((event.GetDragRect().width,h))

        elif eID == MenuManager.ID_INFO_WIN:
            w,h=self.infoWin.GetSize()
            newsize=(event.GetDragRect().width,h)
            self.infoWin.SetDefaultSize(newsize)
            self.infoWin.origSize=newsize
        elif eID == MenuManager.ID_TASK_WIN:
            w,h=self.taskWin.GetSize()
            #Logging.info("Setting task window size",kw="main")
            newsize=(event.GetDragRect().width,h)
            self.taskWin.SetDefaultSize(newsize)
            self.taskWin.origSize=newsize
            
            conf = Configuration.getConfiguration()
            conf.setConfigItem("TaskWinSize","Sizes",str(newsize))
            
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visualizer.OnSize(None)
        self.visWin.Refresh()

    def OnSize(self, event):
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        if self.statusbar:
            rect=self.statusbar.GetFieldRect(2)
            self.progress.SetPosition((rect.x+2,rect.y+2))
            self.progress.SetSize((rect.width-4,rect.height-4))
            rect=self.statusbar.GetFieldRect(1)
            self.colorLbl.SetPosition((rect.x+2,rect.y+2))
            self.colorLbl.SetSize((rect.width-4,rect.height-4))
        #self.tree.SetSize(self.treeWin.GetClientSize())

    def showVisualization(self,window):
        """
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

    def onSetStatus(self,obj,event,arg):
        """
        Created: 04.04.2006, KP
        Description: Set the status text
        """
        self.statusbar.SetStatusText(arg)
    
    def onShowError(self,obj,event,title,msg):
        """
        Created: 04.04.2006, KP
        Description: Show an error message
        """
        Dialogs.showerror(self,msg,title)

    def updateProgressBar(self,obj,event,arg,text=None,allow_gui=1):
        """
        Created: 03.11.2004, KP
        Description: Updates the progress bar
        """
        if self.progressObject and obj != self.progressObject:
            return
        t=time.time()
        if arg not in [1.0, 100] and abs(t-self.progressTimeStamp)<1:
            return

        self.progressTimeStamp=t
        if type(arg)==types.FloatType:
            arg*=100
        # The progress coefficient gives us some amount of control on what range
        arg*=self.progressCoeff
        arg+=self.progressShift
        
        self.progress.SetValue(int(arg))
        if int(arg)>=100:
            self.progress.Show(0)
        else:
            self.progress.Show()
        if text:
            self.statusbar.SetStatusText(text)
        if allow_gui:
            if self.visualizer:
                self.visualizer.in_vtk=0
            wx.GetApp().Yield(1)
        else:            
            if self.visualizer:
                self.visualizer.in_vtk=1        
            wx.SafeYield(None,1)
            
    def updateVoxelInfo(self,obj,event,x,y,z,scalar,rval,gval,bval,r,g,b,a,ctf):
        """
        Created: 22.07.2004, KP
        Description: Update the voxel info in status bar
        """
        #print x,y,z,r,g,b,a
        z+=1
        if scalar!=0xdeadbeef:
            #val=[0,0,0]
            #scalar=r
            #ctf.GetColor(scalar,val)
            #r,g,b=val
            #r*=255
            #g*=255
            #b*=255
            
            if type(scalar)==types.TupleType:
                if len(scalar)>1:
                    lst = map(str,map(int,scalar))
                    
                    scalartxt=", ".join(lst[:-1])
                    scalartxt+=" and "+lst[-1]
                    text="Scalars %s at (%d,%d,%d) map to (%d,%d,%d)"%(scalartxt,x,y,z,r,g,b)
                else:
                    scalar = int(scalar[0])
                    text="Scalar %d at (%d,%d,%d) maps to (%d,%d,%d)"%(scalar,x,y,z,r,g,b)
            else:
                scalar = int(scalar)
                text="Scalar %d at (%d,%d,%d) maps to (%d,%d,%d)"%(scalar,x,y,z,r,g,b)
        else:
            text="Color (%s,%s,%s) at (%d,%d,%d) is (%d,%d,%d)"%(rval,gval,bval,x,y,z,r,g,b)
            if a!=-1:
                text+=" with alpha %d"%a
        self.colorLbl.setLabel(text)
        self.colorLbl.SetToolTip(wx.ToolTip(text))
        fg=255-r,255-g,255-b
            
        bg=r,g,b
        self.colorLbl.setColor(fg,bg)
        wx.GetApp().Yield(1)
        #wx.SafeYield()    
    def sortModes(self,x,y):
        return cmp(x[2].getToolbarPos(),y[2].getToolbarPos())
        
    def createToolBar(self):
        """
        Created: 03.11.2004, KP
        Description: Creates a tool bar for the window
        """
        iconpath=bxd.get_icon_dir()
        self.CreateToolBar(wx.NO_BORDER|wx.TB_HORIZONTAL)
        tb=self.GetToolBar()            
        tb.SetToolBitmapSize((32,32))
        self.taskIds=[]
        self.visIds=[]
        Logging.info("Creating toolbar",kw="init")
        bmp = wx.Image(os.path.join(iconpath,"open_dataset.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_OPEN,"Open",bmp,shortHelp="Open dataset series")
        wx.EVT_TOOL(self,MenuManager.ID_OPEN,self.onMenuOpen)

        bmp = wx.Image(os.path.join(iconpath,"save_snapshot.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SAVE_DATASET,"Save dataset",bmp,shortHelp="Write the processed dataset to disk")
        wx.EVT_TOOL(self,MenuManager.ID_SAVE_DATASET,self.onSaveDataset)

        
        bmp = wx.Image(os.path.join(iconpath,"open_settings.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_OPEN_SETTINGS,"Open settings",bmp,shortHelp="Open settings")
        wx.EVT_TOOL(self,MenuManager.ID_OPEN_SETTINGS,self.onMenuOpenSettings)
        bmp = wx.Image(os.path.join(iconpath,"save_settings.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SAVE_SETTINGS,"Save settings",bmp,shortHelp="Save settings")
        wx.EVT_TOOL(self,MenuManager.ID_SAVE_SETTINGS,self.onMenuSaveSettings)

        bmp = wx.Image(os.path.join(iconpath,"camera.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SAVE_SNAPSHOT,"Save rendered image",bmp,shortHelp="Save a snapshot of the rendered scene")

        bmp = wx.Image(os.path.join(iconpath,"tree.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_SHOW_TREE,"File manager",bmp,kind=wx.ITEM_CHECK,shortHelp="Show file management tree")
        wx.EVT_TOOL(self,MenuManager.ID_SHOW_TREE,self.onMenuShowTree)
        
        #self.visIds.append(MenuManager.ID_SHOW_TREE)


        modules = self.taskPanels.values()
        modules.sort(self.sortModes)

        tb.AddSeparator()
        
        for (moduletype,windowtype,mod) in modules:
            name = mod.getName()
            bmp = wx.Image(os.path.join(iconpath,mod.getIcon())).ConvertToBitmap()
            
            tid = self.taskToId[name]
            tb.DoAddTool(tid,name,bmp,kind=wx.ITEM_CHECK,shortHelp=name)
            wx.EVT_TOOL(self,tid,self.onMenuShowTaskWindow)
            self.taskIds.append(tid)
            
        tb.AddSeparator()
        
        
        modes = self.visualizationModes.values()
        modes.sort(self.sortModes)

        for (mod,settingclass,module) in modes:
            name = module.getName()
            iconName = module.getIcon()
            # Visualization modes that do not wish to appear in the toolbar need to 
            # return None as their icon name
            if not iconName:
                continue
            bmp = wx.Image(os.path.join(iconpath,iconName)).ConvertToBitmap()
            vid = self.visToId[name] 
            
            sepBefore,sepAfter = module.showSeparator()
            if sepBefore: tb.AddSeparator()
            
            tb.DoAddTool(vid, module.getShortDesc(),bmp,kind=wx.ITEM_CHECK,shortHelp = module.getDesc())
            
            if sepAfter: tb.AddSeparator()
            
            wx.EVT_TOOL(self,vid, self.onMenuVisualizer)
            self.visIds.append(vid)
            if module.isDefaultMode():
                tb.ToggleTool(vid,1)
                
        
#        tb.AddSeparator()
        
        bmp = wx.Image(os.path.join(iconpath,"resample.gif")).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_RESAMPLING,"Resampling",bmp,kind=wx.ITEM_CHECK,shortHelp="Enable or disable the resampling of image data")
        wx.EVT_TOOL(self,MenuManager.ID_RESAMPLING,self.onResampleData)
        tb.EnableTool(MenuManager.ID_RESAMPLING,0)
        tb.ToggleTool(MenuManager.ID_RESAMPLING,1)

        bmp = wx.ArtProvider_GetBitmap(wx.ART_QUESTION, wx.ART_TOOLBAR, (32,32))        
        tb.DoAddTool(MenuManager.ID_TOOLBAR_HELP,"Help",bmp,shortHelp="Get help for current task / visualization")
        wx.EVT_TOOL(self, MenuManager.ID_TOOLBAR_HELP, self.onToolbarHelp)
        #self.cBtn = wx.ContextHelpButton(tb,MenuManager.CONTEXT_HELP)
        #self.cBtn.SetSize((32,32))
        #tb.AddControl(self.cBtn)
        #self.cBtn.Bind(wx.EVT_BUTTON,self.onContextHelp)
        
        self.visIds.append(MenuManager.ID_VIS_ANIMATOR)
        tb.Realize()
        self.menuManager.setMainToolbar(tb)

    def onToolbarHelp(self, evt):
        """
        Created: 1.11.2006, KP
        Description: An event handler for the toolbar help button that will launch a help
                     page that depends on what task or visualization mode the user is currently using
                     
        """
        if self.currentTaskWindow:
            messenger.send(None,"view_help",self.currentTaskWindowName)
        else:
            messenger.send(None,"view_help",self.currentVisualizationModeName)
    def onSaveDataset(self,*args):
        """
        Created: 24.05.2006, KP
        Description: Process the dataset
        """
        do_cmd = "mainWindow.processDataset(modal=0)"
        cmd = Command.Command(Command.GUI_CMD,None,None,do_cmd,"",desc="Process the dataset with the current task")
        cmd.run(recordOnly=1)
        self.processDataset()

    def processDataset(self, modal=1):
        bxd.modal = modal
        messenger.send(None,"process_dataset")

    def onContextHelp(self,evt):
        """
        Created: 02.11.2005, KP
        Description: Put the app in a context help mode
        """
        wx.ContextHelp(self)
        
    def createMenu(self):
        """
        Created: 03.11.2004, KP
        Description: Creates a menu for the window
        """
        self.menu = wx.MenuBar()
        mgr=self.menuManager
        self.SetMenuBar(self.menu)
        mgr.setMenuBar(self.menu)
        # We create the menu objects
        mgr.createMenu("file","&File")
        mgr.createMenu("edit","&Edit")
        mgr.createMenu("settings","&Settings")
        mgr.createMenu("processing","&Tasks")
        mgr.createMenu("visualization","&Visualization")
        mgr.createMenu("view","V&iew")
        mgr.createMenu("help","&Help")
        
        mgr.addMenuItem("edit",MenuManager.ID_UNDO,"&Undo\tCtrl-Z",self.onMenuUndo)
        mgr.addMenuItem("edit",MenuManager.ID_REDO,"&Redo\tShift-Ctrl-Z",self.onMenuRedo)
        mgr.addSeparator("edit")
        mgr.addMenuItem("edit",MenuManager.ID_COMMAND_HISTORY,"Command history",self.onShowCommandHistory)
        
        mgr.disable(MenuManager.ID_REDO)
      
        mgr.addMenuItem("settings",MenuManager.ID_PREFERENCES,"&Preferences...",self.onMenuPreferences)
    
        mgr.createMenu("import","&Import",place=0)
        mgr.createMenu("export","&Export",place=0)
        
        mgr.addMenuItem("import",MenuManager.ID_IMPORT_VTIFILES,"&VTK dataset series",self.onMenuImport)
        mgr.addMenuItem("import",MenuManager.ID_IMPORT_IMAGES,"&Stack of images",self.onMenuImport)
   
        mgr.addMenuItem("export",MenuManager.ID_EXPORT_VTIFILES,"&VTK dataset series",self.onMenuExport)
        mgr.addMenuItem("export",MenuManager.ID_EXPORT_IMAGES,"&Stack of images",self.onMenuExport)

        mgr.addMenuItem("file",MenuManager.ID_OPEN,"&Open...\tCtrl-O",self.onMenuOpen)

        mgr.addMenuItem("file",MenuManager.ID_OPEN_SETTINGS,"&Load settings",self.onMenuOpenSettings)
        mgr.addMenuItem("file",MenuManager.ID_SAVE_SETTINGS,"&Save settings",self.onMenuSaveSettings)
#        mgr.disable(MenuManager.ID_OPEN_SETTINGS)
#        mgr.disable(MenuManager.ID_SAVE_SETTINGS)
        
        mgr.addSeparator("file")
        mgr.addSubMenu("file","import","&Import",MenuManager.ID_IMPORT)
        mgr.addSubMenu("file","export","&Export",MenuManager.ID_EXPORT)
        mgr.addSeparator("file")
        mgr.addMenuItem("file",MenuManager.ID_CLOSE_TASKWIN,"&Close task panel\tCtrl-W","Close the task panel",self.onCloseTaskPanel)
        mgr.disable(MenuManager.ID_CLOSE_TASKWIN)
        mgr.addSeparator("file")
        mgr.addMenuItem("file",MenuManager.ID_QUIT,"&Quit\tCtrl-Q","Quit BioImageXD",self.quitApp)


        modules = self.taskPanels.values()
        modules.sort(self.sortModes)

        
        for (moduletype,windowtype,mod) in modules:
            name = mod.getName()
            desc = mod.getDesc()
            tid = self.taskToId[name]
            #tb.DoAddTool(tid,name,bmp,kind=wx.ITEM_CHECK,shortHelp=name)
            mgr.addMenuItem("processing",tid, "&"+name,desc,self.onMenuShowTaskWindow)
            #wx.EVT_TOOL(self,tid,self.onMenuShowTaskWindow)
            
        mgr.addSeparator("processing")
        mgr.addMenuItem("processing",MenuManager.ID_RESAMPLE,"Re&sample dataset...","Resample data to a different resolution",self.onMenuResampleData)
        mgr.addMenuItem("processing",MenuManager.ID_RESCALE,"Res&cale dataset...","Rescale data to 8-bit intensity range",self.onMenuRescaleData)        
        
        modes = self.visualizationModes.values()
        modes.sort(self.sortModes)

        for (mod,settingclass,module) in modes:
            name = module.getName()
            vid = self.visToId[name] 
            sdesc = module.getShortDesc()
            desc = module.getDesc()
            # Visualization modes that do not wish to be in the menu can return None as the desc
            if not desc:
                continue
            mgr.addMenuItem("visualization",vid,"&"+sdesc,desc)


        mgr.addSeparator("visualization")
        mgr.addMenuItem("visualization",MenuManager.ID_LIGHTS,"&Lights...","Configure lightning")
        mgr.addMenuItem("visualization",MenuManager.ID_RENDERWIN,"&Render window","Configure Render Window")
#        mgr.addMenuItem("visualization",MenuManager.ID_RELOAD,"Re-&Load Modules","Reload the visualization modules")
        
        mgr.addSeparator("visualization")
        mgr.addMenuItem("visualization",MenuManager.ID_IMMEDIATE_RENDER,"&Immediate updating","Toggle immediate updating of rendering (when settings that affect the visualization change) on or off.",self.onMenuImmediateRender,check=1,checked=1)
        mgr.addMenuItem("visualization",MenuManager.ID_NO_RENDER,"&No updating","Toggle rendering on or off.",self.onMenuNoRender,check=1,checked=0)        
        mgr.disable(MenuManager.ID_LIGHTS)
        mgr.disable(MenuManager.ID_RENDERWIN)
        #mgr.disable(MenuManager.ID_RELOAD)
        
        
        #wx.EVT_MENU(self,MenuManager.ID_RELOAD,self.onMenuReload)

        mgr.addMenuItem("view",MenuManager.ID_VIEW_TREE,"&File tree","Show or hide the file tree",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.addMenuItem("view",MenuManager.ID_VIEW_CONFIG,"&Configuration panel","Show or hide the configuration panel",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.addMenuItem("view",MenuManager.ID_VIEW_TASKPANEL,"&Task panel","Show or hide task panel",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.disable(MenuManager.ID_VIEW_TASKPANEL)

        mgr.addMenuItem("view",MenuManager.ID_VIEW_TOOLBAR,"T&oolbar","Show or hide toolbar",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.addMenuItem("view",MenuManager.ID_VIEW_HISTOGRAM,"&Histograms","Show or hide channel histograms",self.onMenuToggleVisibility,check=1,checked=0)
        
        mgr.addMenuItem("view",MenuManager.ID_VIEW_INFO,"&Dataset info","Show or hide information about the dataset",self.onMenuToggleVisibility,check=1,checked=1)
        mgr.addMenuItem("view",MenuManager.ID_VIEW_SHELL,"Python &shell","Show a python interpreter",self.onMenuToggleVisibility,check=1,checked=0)
        mgr.addSeparator("view")

        mgr.addMenuItem("view",MenuManager.ID_VIEW_SCRIPTEDIT,"Script &editor","Show the script editor",self.onMenuShowScriptEditor)

        mgr.addMenuItem("view",MenuManager.ID_VIEW_MASKSEL,"&Mask selection","Show mask selection dialog",self.onMenuToggleVisibility)        
        mgr.addSeparator("view")

        mgr.addMenuItem("view",MenuManager.ID_HIDE_INFO,"&Hide info windows\tAlt-Enter","Hide all info windows, giving visualizer maximum screen space",self.onMenuHideInfo)

        mgr.disable(MenuManager.ID_VIEW_TOOLBAR)
        mgr.disable(MenuManager.ID_VIEW_HISTOGRAM)

        mgr.addMenuItem("help",MenuManager.ID_ABOUT,"&About BioImageXD","About BioImageXD",self.onMenuAbout)
        mgr.addSeparator("help")
        mgr.addMenuItem("help",MenuManager.ID_CONTEXT_HELP,"&Context help\tF1","Show help on current task or visualization mode",self.onToolbarHelp)        
        mgr.addMenuItem("help",MenuManager.ID_HELP,"&Help\tCtrl-H","Online Help",self.onMenuHelp)        
    
    def createStatusBar(self):
        """
        Created: 13.7.2006, KP
        Description: Creates a status bar for the window
        """
        self.statusbar=wx.StatusBar(self)
        self.SetStatusBar(self.statusbar)
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([-3,-2,-2])
        self.progress=wx.Gauge(self.statusbar)
        self.progress.SetRange(100)
        self.progress.SetValue(100)
        
        col=self.statusbar.GetBackgroundColour()
        rect=self.statusbar.GetFieldRect(1)

        self.colorLbl=UIElements.NamePanel(self.statusbar,"",col,size=(rect.width-4,rect.height-4))
        self.colorLbl.SetPosition((rect.x+2,rect.y+2))
        messenger.connect(None,"update_progress",self.updateProgressBar)
        messenger.connect(None,"report_progress_only",self.onSetProgressObject)
        
    def onSetProgressObject(self,obj,evt,arg):
        """
        Created: 14.12.2005, KP
        Description: Set the object that is allowed to send progress updates
        """
        if not arg and self.progressObject:
            messenger.disconnect(self.progressObject,"update_progress")
        self.progressObject=arg
        messenger.connect(self.progressObject,"update_progress",self.updateProgressBar)
        
    def onResampleData(self,evt):
        """
        Created: 23.07.2006, KP
        Description: Toggle the resampling on / off
        """
#        flag=self.resampleBtn.GetValue()
        tb=self.GetToolBar()                    
        flag=tb.GetToolState(MenuManager.ID_RESAMPLING)
        bxd.resamplingDisabled = not flag
        self.visualizer.updateRendering()

    def onShowCommandHistory(self,evt=None):
        """
        Created: 13.02.2006, KP
        Description: Show the command history
        """
        # Use a clever contraption in where if we're called from the menu
        # then we create a command object that will call us, but with an
        # empty argument that will trigger the actual dialog to show
        if evt:
            if "show_history" not in self.commands:
                do_cmd = "mainWindow.onShowCommandHistory()"
                undo_cmd="mainWindow.commandHistory.Destroy()\nmainWindow.commandHistory=None"
                
                cmd=Command.Command(Command.MENU_CMD,None,None,do_cmd,undo_cmd,desc="Show command history")
                self.commands["show_history"]=cmd
            self.commands["show_history"].run()
        else:
            if not self.commandHistory:
                self.commandHistory=UndoListBox.CommandHistory(self,self.menuManager)
            
            self.commandHistory.update()
            self.commandHistory.Show()
            
    def onMenuImmediateRender(self,evt):
        """
        Created: 14.02.2006, KP
        Description: Toggle immediate render updates on or off
        """                        
        flag=evt.IsChecked()
        self.visualizer.setImmediateRender(flag)

    def onMenuNoRender(self,evt):
        """
        Created: 14.02.2006, KP
        Description: Toggle immediate render updates on or off
        """                        
        flag=evt.IsChecked()
        self.visualizer.setNoRendering(flag)
        
    def onMenuShowScriptEditor(self,evt):
        """
        Created: 13.02.2006, KP
        Description: Show the script editor
        """                
        if bxd.record:
            self.scriptEditor.Show()
        else:
            self.scriptEditor = ScriptEditor.ScriptEditorFrame(self)
            self.scriptEditor.Show()
        
        
    def onMenuHideInfo(self,evt):
        """
        Method: onMenuHideInfo
        Created: 21.09.2005, KP
        Description: Hide info windows, giving visualizer maximum screen estate
        """        
        self.GetToolBar().ToggleTool(MenuManager.ID_SHOW_TREE,0)
        self.onMenuShowTree(None,0)
        self.menuManager.check(MenuManager.ID_VIEW_INFO,0)
        self.infoWin.SetDefaultSize((0,0))
        self.OnSize(None)
        self.visualizer.OnSize(None)        
        
    def onMenuResampleData(self,evt):
        """
        Created: 1.09.2005, KP
        Description: Resize data to be smaller or larger
        """

        #selectedFiles=self.tree.getSelectedDataUnits()
        selectedFiles,items = self.tree.getSelectionContainer()
        print selectedFiles
        if not selectedFiles:
            return
        dlg=ResampleDialog.ResampleDialog(self)
        dlg.setDataUnits(selectedFiles)
        dlg.ShowModal()
        if dlg.result==1:
            self.tree.markRed(items,"*")
            mode=self.visualizer.mode
            unit=self.visualizer.dataUnit
            self.visualizer.closeVisualizer()
            self.loadVisualizer(unit,mode)
            tb = self.GetToolBar()
            tb.EnableTool(MenuManager.ID_RESAMPLING,1)
            
            self.infoWidget.updateInfo(None,None,None)
        
    def onMenuRescaleData(self,evt):
        """
        Created: 1.09.2005, KP
        Description: Rescale data to 8-bit intensity range
        """

        #selectedFiles=self.tree.getSelectedDataUnits()
        selectedFiles,items = self.tree.getSelectionContainer()
        #print selectedFiles
        if not selectedFiles:
            return
            
        dlg = RescaleDialog.RescaleDialog(self)
        dlg.setDataUnits(selectedFiles)
        wid = dlg.ShowModal()
        dlg.zoomToFit()
        dlg.Destroy()
        
        if wid == wx.ID_OK:                    
            self.tree.markBlue(items,"#")
            self.infoWidget.updateInfo(None,None,None)
            mode=self.visualizer.mode
            unit=self.visualizer.dataUnit
            self.visualizer.closeVisualizer()
            self.loadVisualizer(unit,mode)
            self.infoWidget.showInfo(selectedFiles[0])
#            self.loadVisualizer(None,self.visualizer.mode,reload=1)        



    def onMenuToggleVisibility(self,evt):
        """
        Created: 16.03.2005, KP
        Description: Callback function for menu item "Import"
        """
        eid=evt.GetId()
        flag=evt.IsChecked()
        cmd="hide"
        if flag:cmd="show"
        if eid==MenuManager.ID_VIEW_CONFIG:
            obj="config"
        elif eid==MenuManager.ID_VIEW_TREE:
            print "SHOWING TREE=",flag
            self.onMenuShowTree(None,flag)
            return
        elif eid==MenuManager.ID_VIEW_MASKSEL:
            if self.visualizer:
                masksel = MaskTray.MaskTray(self)
                dataUnit=self.visualizer.getDataUnit()
                for i in self.visualizer.getMasks():
                    print "Adding ",i,"to masksel"
                    masksel.addMask(mask = i)
                masksel.setDataUnit(dataUnit)
                masksel.Show()
                return
        elif eid==MenuManager.ID_VIEW_TOOLBAR:
            obj="toolbar"
        elif eid==MenuManager.ID_VIEW_HISTOGRAM:
            obj="histogram"
        elif eid in [MenuManager.ID_VIEW_INFO,MenuManager.ID_VIEW_TASKPANEL]:
            win=self.taskWin
            if eid== MenuManager.ID_VIEW_INFO:win=self.infoWin
            if cmd=="hide":
                win.origSize=win.GetSize()
                win.SetDefaultSize((0,0))
            else:
                win.SetDefaultSize(win.origSize)
            self.OnSize(None)
            self.visualizer.OnSize(None)
            return
        elif eid==MenuManager.ID_VIEW_SHELL:
            if cmd=="hide":
                self.shellWin.origSize=self.shellWin.GetSize()
                self.shellWin.SetDefaultSize((0,0))
            else:
                if not self.shell:
                    intro = 'BioImageXD interactive interpreter v0.1'
                    self.shell = py.shell.Shell(self.shellWin, -1, introText=intro)
                self.shellWin.SetDefaultSize(self.shellWin.origSize)
            self.OnSize(None)
            self.visualizer.OnSize(None)
            return

        messenger.send(None,cmd,obj)
        
    def onCloseTaskPanel(self,event):
        """
        Created: 14.07.2005, KP
        Description: Called when the user wants to close the task panel
        """
        undo_cmd=""
        do_cmd="mainWindow.closeTaskPanel()"
        cmd=Command.Command(Command.MGMT_CMD,None,None,do_cmd,undo_cmd,desc="Close the current task panel")
        cmd.run()          
        
           
    def closeTaskPanel(self):
        """
        Created: 15.08.2006, KP
        Description: A method that actually clsoes the task panel
        """
        if self.currentTaskWindow:
            self.currentTaskWindow.cacheSettings()
        selectedUnits=self.tree.getSelectedDataUnits()
        self.visualizer.setProcessedMode(0)
        self.visualizer.setDataUnit(selectedUnits[0])        
        #print selectedUnits[0].getSettings().registered
        self.menuManager.clearItemsBar()
        if self.currentTaskWindow:             
            self.currentTaskWindow.Show(0)
            self.currentTaskWindow.Destroy()
            del self.currentTaskWindow
            self.currentTaskWindow=None
            self.currentTaskWindowName=""
            self.currentTaskWindowType=None
        self.switchBtn.Enable(0)            
        self.menuManager.disable(MenuManager.ID_CLOSE_TASKWIN)            
        self.taskWin.SetDefaultSize((0,0))
        
        tb = self.GetToolBar()
        for eid in self.taskIds:
            tb.ToggleTool(eid,0)
        #self.onMenuShowTree(None,1)
        # Set the dataunit used by visualizer to one of the source units
        
        self.infoWin.SetDefaultSize(self.infoWin.origSize)
        self.menuManager.check(MenuManager.ID_VIEW_INFO,1)
        
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()
        
    
    def onMenuImport(self,evt):
        """
        Created: 16.03.2005, KP
        Description: Callback function for menu item "Import"
        """
        if not "show_import" in self.commands:
            import_code="""
    importdlg = GUI.ImportDialog.ImportDialog(mainWindow)
    importdlg.ShowModal()
    datasetName = importdlg.getDatasetName()
    mainWindow.openFile(datasetName)
    """
            command = Command.Command(Command.MENU_CMD,None,None,import_code,"",imports=["GUI.ImportDialog"],desc="Show import dialog")
            self.commands["show_import"]=command
        self.commands["show_import"].run()
        #self.importdlg=ImportDialog.ImportDialog(self)
        #self.importdlg.ShowModal()
        
        
    def onMenuExport(self,evt):
        """
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
        self.exportdlg=ExportDialog.ExportDialog(self,selectedFiles[0],imageMode)
        
        self.exportdlg.ShowModal()
        
    
    def onMenuPreferences(self,evt):
        """
        Created: 09.02.2005, KP
        Description: Callback function for menu item "Preferences"
        """
        self.settingswindow=SettingsWindow.SettingsWindow(self)
        self.settingswindow.ShowModal()

    def onMenuReload(self,evt):
        """
        Created: 24.05.2005, KP
        Description: Callback function for reloading vis modules
        """
        self.visualizer.reloadModules()

    def onMenuVisualizer(self,evt):
        """
        Created: 26.04.2005, KP
        Description: Callback function for launching the visualizer
        """
        # Hide the infowin and toggle the menu item accordingly
        #self.infoWin.SetDefaultSize((0,0))
        #self.menuManager.check(MenuManager.ID_VIEW_INFO,0)
        #wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        eid=evt.GetId()
        mode=""
        for name,vid in self.visToId.items():
            if vid == eid:
                mode = name
                break
        if not name:
            raise "Did not find a visualization mode corresponding to id ",eid
            
        #reload=0
        if self.currentVisualizationModeName==mode:
            # Why would we want to reload?
            #reload=1
            return
        self.currentVisualizationModeName=mode
        messenger.send(None,"update_progress",0.1,"Loading %s view..."%mode)

        modeclass,settingclass,module=self.visualizationModes[mode]
        needUpdate = 0
        if not module.showFileTree():
            self.onMenuShowTree(None,0)
            needUpdate=1
        if not module.showInfoWindow():
            self.infoWin.SetDefaultSize((0,0))
            #self.menuManager.check(MenuManager.ID_VIEW_INFO,0)
            needUpdate=1
        if needUpdate:
            self.OnSize(None)
            
        
        #self.onMenuShowTree(None,0)

        # If a visualizer is already running, just switch the mode
        selectedFiles=self.tree.getSelectedDataUnits()
        if not len(selectedFiles):
            Dialogs.showerror(self,"You need to select a dataset to load in the visualizer.","Please select a dataset")
            return
        self.setButtonSelection(eid)            
        dataunit = selectedFiles[0]
        if self.visualizer:
#            if not self.visualizer.dataUnit:
            hasDataunit=not not self.visualizer.dataUnit
            if not hasDataunit or (not self.visualizer.getProcessedMode() and (self.visualizer.dataUnit != dataunit)):
                Logging.info("Setting dataunit for visualizer",kw="main")
                self.visualizer.setDataUnit(dataunit)
            else:
                if reload:
                    Logging.info("Closing on reload: ",self.visualizer.currMode.closeOnReload())
                    #self.visualizer.currMode.reloadMode()
                    if self.visualizer.currMode.closeOnReload():
                        # close the mode
                        self.loadVisualizer(None,"slices")
                        return
            self.visualizer.setVisualizationMode(mode)
            messenger.send(None,"update_progress",0.3,"Loading %s view..."%mode)
            #self.visualizer.setDataUnit(dataunit)
            self.showVisualization(self.visPanel)
            self.visualizer.enable(1)
            if hasDataunit:
                Logging.info("Forcing visualizer update since dataunit has been changed",kw="visualizer")
                self.visualizer.updateRendering()
            messenger.send(None,"update_progress",1.0,"Loading %s view..."%mode)                
            return
        if len(selectedFiles)>1:
            lst=[]
            for i in selectedFiles:
                lst.append(i.getName())
            Dialogs.showerror(self,
            "You have selected the following datasets: %s.\n"
            "More than one dataset cannot be opened in the Visualizer concurrently.\nPlease "
            "select only one dataset or use the Merge tool."%(", ".join(lst)),
            "Multiple datasets selected")
            return
        if len(selectedFiles)<1:
            Dialogs.showerror(self,
            "You have not selected a dataset to be loaded to Visualizer.\nPlease "
            "select a dataset and try again.\n","No dataset selected")
            return            
            
        dataunit = selectedFiles[0]
        messenger.send(None,"update_progress",0.5,"Loading %s view..."%mode)
        self.loadVisualizer(dataunit,mode,0)
        
    def onMenuOpenSettings(self,event):
        """
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Load settings"
        """
        if self.visualizer:
            dataunit=self.visualizer.getDataUnit()
            if dataunit:
                name=dataunit.getName()
                filenames=Dialogs.askOpenFileName(self,"Open settings for %s"%name,"Settings (*.bxd)|*.bxd")
        
                if not filenames:
                    Logging.info("Got no name for settings file",kw="dataunit")
                    return
                Logging.info("Loading settings for dataset",name," from ",filenames,kw="dataunit")
                parser = RawConfigParser()
                parser.optionxform = str
                parser.read(filenames)
                dataunit.getSettings().readFrom(parser)
                print "Setting parser of ",dataunit
                dataunit.parser = parser
                #self.visualizer.setDataUnit(dataunit)
                messenger.send(None,"update_settings_gui")
            else:
                Logging.info("No dataunit, cannot load settings")

    def onMenuSaveSettings(self,event):
        """
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Save settings"
        """
        if self.visualizer:
            dataunit=self.visualizer.getDataUnit()
            if dataunit:
                name=dataunit.getName()
                filename=Dialogs.askSaveAsFileName(self,"Save settings of %s as"%name,"settings.bxd","Settings (*.bxd)|*.bxd")
        
                if not filename:
                    Logging.info("Got no name for settings file",kw="dataunit")
                    return
                Logging.info("Saving settings of dataset",name," to ",filename,kw="dataunit")
                dataunit.doProcessing(filename,settings_only=1)
            else:
                Logging.info("No dataunit, cannot save settings")
        
    def onMenuOpen(self,evt,evt2=None,*args):
        """
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Open VTK File"
        """
        if not evt2:
            self.onMenuShowTree(None,1)
            asklist=[]
            asklist=Dialogs.askOpenFileName(self,"Open a volume dataset",self.datasetWildcards)
        else:
            asklist=args
        
        for askfile in asklist:
            
            sep=askfile.split(".")[-1]
            fname=os.path.split(askfile)[-1]
            self.SetStatusText("Loading "+fname+"...")
            askfile=askfile.replace("\\","\\\\")
            do_cmd="mainWindow.createDataUnit(\"%s\",\"%s\")"%(fname,askfile)
            
            cmd=Command.Command(Command.OPEN_CMD,None,None,do_cmd,"",desc="Load dataset %s"%fname)
            cmd.run()
            #self.createDataUnit(fname,askfile)
        self.SetStatusText("Done.")

    def openFile(self, filepath):
        """
        Created: 06.11.2006, KP
        Description: Open a file extracting the dataset name from the filename
        """
        self.createDataUnit(os.path.basename(filepath),filepath)
        
    def createDataUnit(self,name,path):
        """
        Created: 03.11.2004, KP
        Description: Creates a dataunit with the given name and path
        Parameters:
            name    Name used to identify this dataunit
            path    Path to the file this dataunit points to
        """
        
        
        ext=path.split(".")[-1]
        dataunit=None
        if self.tree.hasItem(path):
            print "Tree already has item"
            return
        ext=ext.lower()
        
        if ext=='bxd':
            # We check that the file is not merely a settings file
            #try:
            self.parser = SafeConfigParser()
            self.parser.read([path])
            settingsOnly=""
            try:
                # We read the Key SettingsOnly, and check it's value.
                settingsOnly = self.parser.get("SettingsOnly", "SettingsOnly")
            except (NoOptionError,NoSectionError):
                pass
            if settingsOnly.lower()=="true":
                # If this file contains only settings, then we report an 
                # error and do not load it
                Dialogs.showerror(self,
                "The file you selected, %s, contains only settings "
                "and cannot be loaded.\n"
                "Use 'Load settings' from the File menu "
                "to load it."%name,"Trying to load settings file")
                return
            #except:
            #    pass

        if ext not in self.extToSource.keys():
            return
        # We try to load the actual data
        Logging.info("Loading dataset with extension %s, path=%s"%(ext,path),kw="io")
    
        
        datasource=self.extToSource[ext]()
        try:
            datasource=self.extToSource[ext]()
        except KeyError:
#            print self.extToSource.keys()
            Dialogs.showerror(self,"Failed to load file %s: Unrecognized extension %s"%(name,ext),"Unrecognized extension")
            return
        dataunits=[]
        try:
            Logging.info("\n\n\nLoading from data source ",datasource,kw="io")
            dataunits = datasource.loadFromFile(path)
            print "\n\n\nLoaded from file",path
        except Logging.GUIError,ex:
            ex.show()

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
            #Logging.info("Adding to tree ",name,path,ext,dataunits,kw="io")
            conf = Configuration.getConfiguration()
            needToRescale = conf.getConfigItem("RescaleOnLoading","Performance")
            #print "\n\n***** Need to rescale=",needToRescale
            if needToRescale:
                needToRescale = eval(needToRescale)

            
            if needToRescale:
                dlg = RescaleDialog.RescaleDialog(self)
                dlg.setDataUnits(dataunits)
                wid = dlg.ShowModal()
                dlg.zoomToFit()
                if wid != wx.ID_OK:                    
                    del dataunits
                    dlg.Destroy()
                    return
                dlg.Destroy()
            #print dataunits[0].getTimePoint(0).GetDimensions()
            self.tree.addToTree(name,path,ext,dataunits)

    def onMenuShowTaskWindow(self,event):
        """
        Created: 11.1.2005, KP
        Description: A method that shows a taskwindow of given type
        """
        eid = event.GetId()
        tb=self.GetToolBar()
        shown=tb.GetToolState(eid)
        
        taskname=""
        for name,taskid in self.taskToId.items():
            if taskid == eid:
                taskname=name
                break
        if not taskname:
            raise "Couldn't find a task corresponding to id ",eid

        if taskname==self.currentTaskWindowName:
            Logging.info("Task",taskname,"already showing, will close",kw="task")
            tb.ToggleTool(eid,0)
            self.onCloseTaskPanel(None)            
            return
        
        do_cmd = 'mainWindow.loadTask("%s")'%(taskname)
        if self.currentTaskWindowName:
            undo_cmd = 'mainWindow.loadTask("%s")'%(self.currentTaskWindowName)
        else:
            undo_cmd = 'mainWindow.closeTask()'
        cmd=Command.Command(Command.TASK_CMD,None,None,do_cmd,undo_cmd,desc="Load task %s"%taskname)
        cmd.run()
        
    def closeTask(self):
        """
        Created: 16.07.2006, KP
        Description: Close the current task window
        """   
        self.onCloseTaskPanel(None)
        self.onMenuShowTree(None,1)

            
    def loadTask(self, taskname):
        """
        Created: 16.07.2006, KP
        Description: Load the task with the given name
        """   
        moduletype,windowtype,mod=self.taskPanels[taskname]
        filesAtLeast,filesAtMost = mod.getInputLimits()
        
        unittype = mod.getDataUnit()
        action = mod.getName()
        Logging.info("Module type for taskwindow: ",moduletype,kw="task")
        
        selectedFiles = self.tree.getSelectedDataUnits()
        selectedPaths = self.tree.getSelectedPaths()
        if filesAtLeast!=-1 and len(selectedFiles)<filesAtLeast:
            Dialogs.showerror(self,
            "You need to select at least %d source datasets for the task: %s"%(filesAtLeast,action),"Need more source datasets")
            self.setButtonSelection(-1)
            return            
        elif filesAtMost!=-1 and len(selectedFiles)>filesAtMost:
            Dialogs.showerror(self,
            "You can select at most %d source datasets for %s"%(filesAtMost,action),"Too many source datasets")
            self.setButtonSelection(-1)
            return
        self.visualizer.enable(0)
        messenger.send(None,"update_progress",0.1,"Loading task %s..."%action)
        self.onMenuShowTree(None,0)
        # Hide the infowin and toggle the menu item accordingly
        self.infoWin.SetDefaultSize((0,0))
        self.menuManager.check(MenuManager.ID_VIEW_INFO,0)
        self.currentTaskWindowType = windowtype
        
        window = windowtype(self.taskWin,self.menuManager)
        
        messenger.send(None,"update_progress",0.2,"Loading task %s..."%action)
        window.Show()
        
        self.switchBtn.Enable(1)
        if self.currentTaskWindow:
            self.currentTaskWindow.cacheSettings()
            self.currentTaskWindow.Show(0)
            self.currentTaskWindow.Destroy()
            del self.currentTaskWindow                
        
        self.currentTaskWindowName=taskname
        self.currentTaskWindow=window
        self.tasks[taskname] = window
        w,h=self.taskWin.GetSize()
        w,h2=self.taskWin.origSize
        self.taskWin.SetDefaultSize((w,h))
        self.currentTaskWindow.SetSize((w,h))
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        
        names=[i.getName() for i in selectedFiles]
        
        cacheKey = bxd.getCacheKey(selectedPaths, names, taskname)
        
        self.currentTaskWindow.setCacheKey(cacheKey)
        # Sets name for new dataset series
        name="%s (%s)"%(action,", ".join(names))

        #Logging.info(unittype,name,kw="task")
        unit = unittype(name)
        Logging.info("unit = %s(%s)=%s"%(unittype,name,unit),kw="task")
        try:
            for dataunit in selectedFiles:
                unit.addSourceDataUnit(dataunit)
                #Logging.info("ctf of source=",dataunit.getSettings().get("ColorTransferFunction"),kw="ctf")
        except Logging.GUIError,ex:
            ex.show()
            self.closeTask()
            return
        messenger.send(None,"update_progress",0.3,"Loading task %s..."%action)
        Logging.info("Moduletype=",moduletype,kw="dataunit")
        module=moduletype()
        unit.setModule(module)
        unit.setCacheKey(cacheKey)
        
        window.setCombinedDataUnit(unit)
        

        for name,taskid in self.taskToId.items():
            if name == taskname:
                self.setButtonSelection(taskid)
                break        

#        self.setButtonSelection(event.GetId())

        # If visualizer has not been loaded, load it now
        # This is a high time to have a visualization loaded
        self.progressCoeff=0.5
        self.progressShift=30
        self.visualizer.enable(1)
        if not self.visualizer:
            Logging.info("Loading slices view for ",unit,kw="task")
            self.loadVisualizer(unit,"slices",1)
            self.setButtonSelection(MenuManager.ID_VIS_SLICES)

        else:
            if not self.visualizer.getProcessedMode():
                self.visualizer.setProcessedMode(1)

        self.visualizer.setDataUnit(unit)
        
        self.progressCoeff=1.0
        self.progressShift=0
        messenger.send(None,"update_progress",0.9,"Loading task %s..."%action)
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()
        self.menuManager.enable(MenuManager.ID_CLOSE_TASKWIN)
        self.menuManager.enable(MenuManager.ID_VIEW_TASKPANEL)
        messenger.send(None,"update_progress",1.0,"Loading task %s... done"%action)
                    
        
    def onMenuShowTree(self,event,show=-1):
        """
        Created: 21.07.2005, KP
        Description: A method that shows the file management tree
        """
        tb=self.GetToolBar()            
        if show==-1:
            show=tb.GetToolState(MenuManager.ID_SHOW_TREE)
        else:
            tb.ToggleTool(MenuManager.ID_SHOW_TREE,show)
        
        if not show:
            w,h=self.treeWin.GetSize()
            if w and h:
                self.treeWin.origSize=(w,h)
            w=0
        else:
            w,h=self.treeWin.origSize
        self.treeWin.SetDefaultSize((w,h))
        
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visualizer.OnSize(None)
        #self.visWin.Refresh()

    def loadVisualizer(self,dataunit,mode,processed=0,**kws):
        """
        Created: 25.05.2005, KP
        Description: Load a dataunit and a given mode to visualizer
        """          
        if not self.visualizer:
            self.visPanel = wx.SashLayoutWindow(self.visWin,-1)
            self.visualizer=Visualizer.Visualizer(self.visPanel,self.menuManager,self)
            bxd.visualizer = self.visualizer
            Command.visualizer = self.visualizer
            self.menuManager.setVisualizer(self.visualizer)
            self.visualizer.setProcessedMode(processed)
        self.visualizer.enable(0)
        messenger.send(None,"update_progress",0.6,"Loading %s view..."%mode)
        #self.menuManager.menus["visualization"].Enable(MenuManager.ID_RELOAD,1)
        wx.EVT_TOOL(self,MenuManager.ID_SAVE_SNAPSHOT,self.visualizer.onSnapshot)    
            

        if not "init" in kws and dataunit:
            self.visualizer.setDataUnit(dataunit)
        reload=kws.get("reload",0)
        
        self.visualizer.setVisualizationMode(mode,reload=reload)
        # handle icons
        messenger.send(None,"update_progress",0.8,"Loading %s view..."%mode)        

        self.showVisualization(self.visPanel)            
        self.visualizer.enable(1)
        mgr=self.menuManager
        mgr.enable(MenuManager.ID_VIEW_TOOLBAR)
        mgr.enable(MenuManager.ID_VIEW_HISTOGRAM)
        wx.LayoutAlgorithm().LayoutWindow(self, self.visWin)
        self.visWin.Refresh()
        messenger.send(None,"update_progress",1.0,"Loading %s view... done."%mode)        

    def setButtonSelection(self,eid,all=0):
        """
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
        Created: 03.11.2004, KP
        Description: Callback function for menu item "About"
        """
        about=AboutDialog.AboutDialog(self)
        about.ShowModal()
        about.Destroy()
        
    def onViewHelp(self,obj,evt,args):
        """
        Created: 05.08.2004, KP
        Description: A method that shows a help of some item
        """
        if not self.help:
            self.help=wx.html.HtmlHelpController()
            self.help.AddBook("Help\\help.hhp",1)
            self.help.SetTitleFormat("BioImageXD - %s")
        if not args:
            self.help.DisplayContents()
        else:
            self.help.Display(args)
            
    def onMenuHelp(self,evt):
        """
        Created: 02.08.2004, KP
        Description: Callback function for menu item "Help"
        """
        self.onViewHelp(None,None,None)
        
    def saveWindowSizes(self):
        """
        Created: 13.04.2006, KP
        Description: Save window sizes to the settings
        """        
        conf = Configuration.getConfiguration()

        size=str(self.GetSize())
        conf.setConfigItem("WindowSize","Sizes",size)
        conf.writeSettings()
    
    def quitApp(self,evt):
        """
        Created: 03.11.2004, KP
        Description: Possibly queries the user before quitting, then quits
        """
        conf = Configuration.getConfiguration()
        
        askOnQuit = conf.getConfigItem("AskOnQuit","General")
        if askOnQuit and eval(askOnQuit):
            dlg = wx.MessageDialog(self, 'Are you sure you wish to quit BioImageXD?',
                               'Do you really want to quit',
                               wx.OK |wx.CANCEL | wx.ICON_QUESTION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
            answer=dlg.ShowModal()
            dlg.Destroy()            
            if answer != wx.ID_OK:
                return
            
        self.saveWindowSizes()
            
        self.visualizer.enable(0)        
        
        self.visualizer.closeVisualizer()
        
        self.Destroy()
        sys.exit(0)

# 
