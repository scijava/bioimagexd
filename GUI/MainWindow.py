#! /usr/bin/env python
#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: MainWindow.py
 Project: Selli
 Created: 03.11.2004
 Creator: KP
 Description:

 The main window for the LSM module.

 Modified: 03.11.2004 KP - Now using the DataUnit classes.
           09.11.2004 KP - Now only displaying really opened files
                           Cleared up the hierarchy.
           09.11.2004 KP - Now using datasource to read .du files

           10.11.2004 JV - Added ColorCombination-window

           23.11.2004 JV - Updated onMenuMergeChannels

           25.11.2004 JV - Added VSIAWindow
           29.11.2004 JV - Added icon
           10.12.2004 JV - Fixed: name setting for colorCombinationDataUnit in 
                           onMenuMergeChannels
           04.01.2005 JV - Fixed: bug in MenuVSIA
           11.01.2005 JV - Added comments
           20.01.2005 KP - Now using wx.Python

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.71 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"
import os.path,os,types
import wx


import vtk

from ConfigParser import *
from TreeWidget import *
from Logging import *

from TaskWindow import *

import SettingsWindow
import ImportDialog
import ExportDialog
import RenderingInterface

import Visualization

import InfoWidget

import Dialogs
import AboutDialog

import Reslice

from DataUnit import *
from DataSource import *


from RenderingManager import *
import Urmas
ID_OPEN=101
ID_QUIT=110
ID_ABOUT=111
ID_COLOCALIZATION=1000
ID_COLORMERGING=1001
ID_VSIA=1010
ID_SINGLE=1011
ID_RENDER=1100
ID_REEDIT=1101
ID_TREE=1110
ID_IMPORT=1111
ID_EXPORT=10000
ID_EXPORT_VTIFILES=10001
ID_EXPORT_IMAGES=10010
ID_IMPORT_VTIFILES=10011
ID_IMPORT_IMAGES=10100
ID_HELP=10101
ID_SETTINGS=10110
ID_PREFERENCES=10111
ID_RESLICE=11000
ID_MAYAVI=11001

class MainWindow(wx.Frame):
    """
    Class: MainWindow
    Created: 03.11.2004, KP
    Description: The main window for the LSM module
    """
    def __init__(self,parent,id,app):
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
        wx.Frame.__init__(self,parent,wx.ID_ANY,"BioImageXD",size=(1100,800),
            style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        

        self.splitter=wx.SplitterWindow(self,-1)
        self.nodes_to_be_added=[]
        self.app=app
        
        # Icon for the window
        ico=reduce(os.path.join,["Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.CreateStatusBar()
        self.SetStatusText("Starting up...")

        # Create Menu, ToolBar and Tree
        self.createMenu()
        self.createToolBar()

        self.dataunits={}
        self.paths={}

        self.SetStatusText("Done.")
        self.infowidget=InfoWidget.InfoWidget(self.splitter,size=(400,400))
        self.tree=TreeWidget(self.splitter,self.infowidget.showInfo)        
        self.infowidget.setTree(self.tree)
        self.splitter.SplitVertically(self.tree,self.infowidget,200)

        self.Show(True)

    def createToolBar(self):
        """
        Method: createToolBar()
        Created: 03.11.2004, KP
        Description: Creates a tool bar for the window
        """
        iconpath=reduce(os.path.join,["Icons"])
        self.CreateToolBar()
        tb=self.GetToolBar()            
        tb.SetToolBitmapSize((32,32))

        print "adding tool"
        tb.AddSimpleTool(ID_OPEN,wx.Image(os.path.join(iconpath,"OpenLSM.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Open","Open dataset series")
        wx.EVT_TOOL(self,ID_OPEN,self.onMenuOpen)


        tb.AddSimpleTool(ID_COLORMERGING,
        wx.Image(os.path.join(iconpath,"ColorCombination.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Merge Channels","Merge dataset series")
        wx.EVT_TOOL(self,ID_COLORMERGING,self.onMenuMergeChannels)       
    
        tb.AddSimpleTool(ID_COLOCALIZATION,
        wx.Image(os.path.join(iconpath,"Colocalization.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Colocalization","Create colocalization map")
        wx.EVT_TOOL(self,ID_COLOCALIZATION,self.onMenuColocalization)       

        tb.AddSimpleTool(ID_VSIA,
        wx.Image(os.path.join(iconpath,"HIV.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Visualization of sparse intensity aggregations","Visualization of sparse intensity aggregations")
        wx.EVT_TOOL(self,ID_VSIA,self.menuVSIA)
        
        tb.AddSimpleTool(ID_SINGLE,
        wx.Image(os.path.join(iconpath,"DataSetSettings2.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Process dataset series","Process a single dataset series")
        wx.EVT_TOOL(self,ID_SINGLE,self.onMenuProcessDataUnit)

        tb.AddSimpleTool(ID_REEDIT,
        wx.Image(os.path.join(iconpath,"ReEdit.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Re-edit dataset series","Re-edit a dataset series")
        wx.EVT_TOOL(self,ID_REEDIT,self.onMenuEditDataSet)

        tb.AddSimpleTool(ID_RESLICE,
        wx.Image(os.path.join(iconpath,"Reslice.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Re-edit dataset series","Re-edit a dataset series")
        wx.EVT_TOOL(self,ID_RESLICE,self.onMenuReslice)

        
        tb.AddSimpleTool(ID_RENDER,
        wx.Image(os.path.join(iconpath,"Render.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap(),"Render","Render a dataset series")
        wx.EVT_TOOL(self,ID_RENDER,self.onMenuRender)

        tb.Realize()
        
    def createMenu(self):
        """
        Method: createMenu()
        Created: 03.11.2004, KP
        Description: Creates a menu for the window
        """
        # This is the menubar object that holds all the menus
        self.menu = wx.MenuBar()
        self.SetMenuBar(self.menu)
        
        # We create the menu objects
        self.fileMenu=wx.Menu()
        self.taskMenu=wx.Menu()
        self.helpMenu=wx.Menu()
        self.renderMenu=wx.Menu()
        self.settingsMenu=wx.Menu()

         # and add them as sub menus to the menubar
        self.menu.Append(self.fileMenu,"&File")
        self.menu.Append(self.settingsMenu,"&Settings")
        self.menu.Append(self.taskMenu,"&Processing")
        self.menu.Append(self.renderMenu,"&Rendering")
        self.menu.Append(self.helpMenu,"&Help")
      

        self.settingsMenu.Append(ID_PREFERENCES,"&Preferences...")
        wx.EVT_MENU(self,ID_PREFERENCES,self.menuPreferences)
    
        self.importMenu=wx.Menu()
        self.importMenu.Append(ID_IMPORT_VTIFILES,"&VTK Dataset Series")
        self.importMenu.Append(ID_IMPORT_IMAGES,"&Stack of Images")
   
        self.exportMenu=wx.Menu()
        self.exportMenu.Append(ID_EXPORT_VTIFILES,"&VTK Dataset Series")
        self.exportMenu.Append(ID_EXPORT_IMAGES,"&Stack of Images")
        wx.EVT_MENU(self,ID_IMPORT_VTIFILES,self.onMenuImport)
        wx.EVT_MENU(self,ID_IMPORT_IMAGES,self.onMenuImport)
        
        wx.EVT_MENU(self,ID_EXPORT_IMAGES,self.onMenuExport)
        wx.EVT_MENU(self,ID_EXPORT_VTIFILES,self.onMenuExport)
        
        self.fileMenu.Append(ID_OPEN,"&Open...\tCtrl-O","Open a Data Set")
        wx.EVT_MENU(self,ID_OPEN,self.onMenuOpen)
        self.fileMenu.AppendSeparator()
        self.fileMenu.AppendMenu(ID_IMPORT,"&Import",self.importMenu)
        self.fileMenu.AppendMenu(ID_EXPORT,"&Export",self.exportMenu)
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(ID_QUIT,"&Quit\tCtrl-Q","Quit the application")
        wx.EVT_MENU(self,ID_QUIT,self.quitApp)

        self.taskMenu.Append(ID_COLOCALIZATION,"&Colocalization...","Create a colocalization map")
        self.taskMenu.Append(ID_COLORMERGING,"Color &Merging...","Merge dataset series")
        self.taskMenu.Append(ID_VSIA,"&Visualize Sparse Intensity Aggregations...","Visualize Sparse Intensity Aggregations with smooth surface")
        self.taskMenu.Append(ID_SINGLE,"&Process Single Dataset Series...","Process Single Dataset Series")
        
        self.renderMenu.Append(ID_RENDER,"&Render Dataset Series...","Render a dataset series")
        self.renderMenu.Append(ID_MAYAVI,"&Visualize Dataset","Visualize dataset in Mayavi")
        wx.EVT_MENU(self,ID_COLOCALIZATION,self.onMenuColocalization)
        wx.EVT_MENU(self,ID_COLORMERGING,self.onMenuMergeChannels)
        wx.EVT_MENU(self,ID_VSIA,self.menuVSIA)
        wx.EVT_MENU(self,ID_SINGLE,self.onMenuProcessDataUnit)
        wx.EVT_MENU(self,ID_RENDER,self.onMenuRender)
        wx.EVT_MENU(self,ID_MAYAVI,self.onMenuMayavi)

        self.helpMenu.Append(ID_ABOUT,"&About BioImageXD","About BioImageXD")
        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(ID_HELP,"&Help\tCtrl-H","Online Help")
        wx.EVT_MENU(self,ID_ABOUT,self.onMenuAbout)
    
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
        if eid == ID_EXPORT_IMAGES:
            imageMode = 1
        self.importdlg=ExportDialog.ExportDialog(self,selectedFiles[0],imageMode)
        
        self.importdlg.ShowModal()
        
    
    def menuPreferences(self,evt):
        """
        Method: menuPreferences()
        Created: 09.02.2005, KP
        Description: Callback function for menu item "Preferences"
        """
        self.settingswindow=SettingsWindow.SettingsWindow(self)
        self.settingswindow.ShowModal()
        
    def onMenuMayavi(self,evt):
        """
        Method: onMenuMayavi()
        Created: 26.04.2005, KP
        Description: Callback function for launching mayavi
        """
        selectedFiles=self.tree.getSelectedDataUnits()
        if len(selectedFiles)>1:
            Dialogs.showerror(self,
            "You have selected the following datasets: %s.\n"
            "More than one dataset cannot be opened in mayavi concurrently.\nPlease "
            "select only one dataset and try again."%(", ".join(selectedFiles)),"Multiple datasets selected")
            return
        if len(selectedFiles)<1:
            Dialogs.showerror(self,
            "You have not selected a dataset series to be loaded to mayavi.\nPlease "
            "select a dataset series and try again.\n","No dataset selected")
            return
        dataunit = selectedFiles[0]
##        renderingInterface=RenderingInterface.getRenderingInterface()
##        renderingInterface.setOutputPath(".")
##        renderingInterface.setTimePoints([0])
##        ctf = dataunit.getColorTransferFunction()
##        imagedata = dataunit.getTimePoint(0)
##        renderingInterface.doRendering(preview=imagedata,ctf=ctf)

        vis=Visualization.VisualizationFrame(self)
        vis.setDataUnit(dataunit)
        vis.Show()
        

    def onMenuRender(self,evt):
        """
        Method: onMenuRender()
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
        #self.renderWindow=RenderingManager(self)
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
        wc="LSM Files (*.lsm)|*.lsm|Leica TCS-NT Files (*.txt)|*.txt|Dataset Series (*.du)|*.du|VTK Image Data (*.vti)|*.vti"
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
        if ext.lower()=='du':
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
            dataunits = datasource.loadFromFile(path)
        except GUIError,ex:
            ex.show()
            return

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
            self.tree.addToTree(name,path,ext,dataunits)

    def onMenuEditDataSet(self,evt):
        """
        Method: onMenuEditDataSet
        Created: 11.1.2005, KP
        Description: Callback function for menu item "Re-Edit data set"
        """
        
        # for future use
        selectedFiles=self.tree.getSelectedDataUnits()
        if len(selectedFiles)<1:
            Dialogs.showerror(self,
            "You need to select a dataset that you wish to re-edit.","Need to select a dataset")
            return
        if len(selectedFiles)>1:
            Dialogs.showerrorr(self,
            "You need to select only one dataset that you wish to re-edit.","Select only one dataset")
            return
        dataunit=selectedFiles[0]
        if isinstance(dataunit,ColocalizationDataUnit):
            dataunit,filepath=ColocalizationWindow.showColocalizationWindow(
            dataunit,self)
        elif isinstance(dataunit,ColorMergingDataUnit):
            dataunit,filepath=ColorMergingWindow.showColorMergingWindow(
            dataunit,self)
        elif isinstance(dataunit,CorrectedSourceDataUnit):
            dataunit,filepath=SingleUnitProcessingWindow.showSingleUnitProcessingWindow(
            dataunit,self)            
        if not dataunit:
            return                

    def showTaskWindow(self,action,moduletype,windowtype,filesAtLeast,filesAtMost):
        """
        Method: showTaskWindow
        Created: 11.1.2005, KP
        Description: A method that shows a taskwindow of given type
        """
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

        moduleToClass={DataUnitProcessing.DataUnitProcessing:CorrectedSourceDataUnit,
        Colocalization.Colocalization:ColocalizationDataUnit,
        ColorMerging.ColorMerging:ColorMergingDataUnit,
        Reslice.Reslice:ResliceDataUnit}    

        
        unit = moduleToClass[moduletype](name)
        print "unit=",unit
        for dataunit in selectedFiles:
            print "unit.ctf=",dataunit.getSettings().get("ColorTransferFunction")
            unit.addSourceDataUnit(dataunit)

        module=moduletype()
        unit.setModule(module)
        
        dataunit,filepath=TaskWindow.showTaskWindow(windowtype,unit,self)

        # If user cancelled operation, we do not get a new dataset -> return
        if not dataunit:
            return

        # Add the dataset (node) into tree
        self.tree.addToTree(dataunit.getName(),filepath,'du',[dataunit])        
        
    def onMenuColocalization(self,evt):
        """
        Method: onMenuColocalization()
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Colocalization"
        """
        return self.showTaskWindow("Colocalization",
        Colocalization.Colocalization,
        ColocalizationWindow.ColocalizationWindow,2,-1)
        
    def onMenuReslice(self,evt):
        """
        Method: onMenuReslice()
        Created: 03.11.2004, KP
        Description: Callback function for menu item "Reslice"
        """
        return self.showTaskWindow("Reslice",
        Reslice.Reslice,
        ResliceWindow.ResliceWindow,1,1)        
        
    def onMenuMergeChannels(self,evt):
        """
        Method: onMenuMergeChannels()
        Created: 03.11.2004, KP
        Description: Callback function for menu item Merge Channels
        """
        return self.showTaskWindow("Color Merging",
        ColorMerging.ColorMerging,
        ColorMergingWindow.ColorMergingWindow,2,-1)

    def onMenuProcessDataUnit(self,evt):
        """
        Method: onMenuProcessDataUnit()
        Created: 03.11.2004, KP
        Description:
        """
        return self.showTaskWindow("Processing",
        DataUnitProcessing.DataUnitProcessing,
        SingleUnitProcessingWindow.SingleUnitProcessingWindow,1,1)

    def menuVSIA(self,evt):
        """
        Method: menuVSIA()
        Created: 25.11.2004, JV
        Description:
        """
        return self.showTaskWindow("Visualization of Sparse Intensity Aggregations",
        VSIA.VSIA,
        VSIAWindow.VSIAWindow,1,1)

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
        
