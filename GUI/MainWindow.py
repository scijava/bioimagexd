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

           23.11.2004 JV - Updated menuMergeChannels

           25.11.2004 JV - Added VSIAWindow
           29.11.2004 JV - Added icon
           10.12.2004 JV - Fixed: name setting for colorCombinationDataUnit in 
                           menuMergeChannels
           04.01.2005 JV - Fixed: bug in MenuVSIA
           11.01.2005 JV - Added comments
           20.01.2005 KP - Now using wxPython

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
import os.path,os
import wx

from wxPython.wx import *

import vtk

from ConfigParser import *
from TreeWidget import *
from Logging import *

import ColocalizationWindow
import ColorMergingWindow
import SingleUnitProcessingWindow
import VSIAWindow
import SettingsWindow

import Dialogs


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

class MainWindow(wxFrame):
    """
    Class: MainWindow
    Created: 03.11.2004
    Creator: KP
    Description: The main window for the LSM module
    """
    def __init__(self,parent,id,app):
        """
        Method: __init__(parent,id,app)
        Created: 03.11.2004
        Creator: KP
        Description: Initialization
        Parameters:
            parent    
            id
            app     LSMApplication object
        """
        #Toplevel.__init__(self,root)
        wxFrame.__init__(self,parent,wxID_ANY,"Selli",size=(800,600),
            style=wxDEFAULT_FRAME_STYLE|wxNO_FULL_REPAINT_ON_RESIZE)
        self.splitter=wxSplitterWindow(self,-1)
        self.nodes_to_be_added=[]
        self.app=app

        if os.sys.platform=='linux2':
            self.lastpath="/home/kalpaha/Sovellusprojekti/Data"
        else:
            self.lastpath=r"H:\Data"
        
        # Icon for the window
        ico=reduce(os.path.join,["Icons","Selli.ico"])
        self.icon = wxIcon(ico,wxBITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.renderWindow=None

        self.CreateStatusBar()
        self.SetStatusText("Starting up...")

        # Create Menu, ToolBar and Tree
        self.createMenu()
        self.createToolBar()
        
        self.dataunits={}
        self.paths={}

        self.SetStatusText("Done.")
        self.tree=TreeWidget(self.splitter)        
        #self.infowidget=wxPanel(self.splitter,-1)
        frame = wxPanel(self.splitter, -1,size=wxSize(400,400))# , "wxRenderWindow", size=wxSize(400,400))
        #renWin = wxVTKRenderWindow(frame,-1)
    
        #ren = vtkRenderer()
        #renWin.GetRenderWindow().AddRenderer(ren)
        #cone = vtkConeSource()
        #cone.SetResolution(8)
        #coneMapper = vtkPolyDataMapper()
        #coneMapper.SetInput(cone.GetOutput())
        #coneActor = vtkActor()
        #coneActor.SetMapper(coneMapper)
        #ren.AddActor(coneActor)        
        self.splitter.SplitVertically(self.tree,frame,200)
        self.Show(true)
        
        
    def createToolBar(self):
        """
        --------------------------------------------------------------
        Method: createToolBar()
        Created: 03.11.2004
        Creator: KP
        Description: Creates a tool bar for the window
        -------------------------------------------------------------
        """
        iconpath=reduce(os.path.join,["Icons"])
        self.CreateToolBar()
        tb=self.GetToolBar()
        tb.AddSimpleTool(ID_OPEN,wxImage(os.path.join(iconpath,"OpenLSM.gif"),wxBITMAP_TYPE_GIF).ConvertToBitmap(),"Open","Open dataset series")
        EVT_TOOL(self,ID_OPEN,self.menuOpen)       

        tb.AddSimpleTool(ID_COLORMERGING,
        wxImage(os.path.join(iconpath,"ColorCombination.gif"),wxBITMAP_TYPE_GIF).ConvertToBitmap(),"Merge Channels","Merge dataset series")
        EVT_TOOL(self,ID_COLORMERGING,self.menuMergeChannels)       
    
        tb.AddSimpleTool(ID_COLOCALIZATION,
        wxImage(os.path.join(iconpath,"Colocalization.gif"),wxBITMAP_TYPE_GIF).ConvertToBitmap(),"Colocalization","Create colocalization map")
        EVT_TOOL(self,ID_COLOCALIZATION,self.menuColocalization)       

        tb.AddSimpleTool(ID_VSIA,
        wxImage(os.path.join(iconpath,"HIV.gif"),wxBITMAP_TYPE_GIF).ConvertToBitmap(),"Visualization of sparse intensity aggregations","Visualization of sparse intensity aggregations")
        EVT_TOOL(self,ID_VSIA,self.menuVSIA)
        
        tb.AddSimpleTool(ID_SINGLE,
        wxImage(os.path.join(iconpath,"DataSetSettings2.gif"),wxBITMAP_TYPE_GIF).ConvertToBitmap(),"Process dataset series","Process a single dataset series")
        EVT_TOOL(self,ID_SINGLE,self.menuProcessDataUnit)

        tb.AddSimpleTool(ID_REEDIT,
        wxImage(os.path.join(iconpath,"ReEdit.gif"),wxBITMAP_TYPE_GIF).ConvertToBitmap(),"Re-edit dataset series","Re-edit a dataset series")
        EVT_TOOL(self,ID_REEDIT,self.menuEditDataSet)

        tb.AddSimpleTool(ID_RENDER,
        wxImage(os.path.join(iconpath,"Render.gif"),wxBITMAP_TYPE_GIF).ConvertToBitmap(),"Render","Render a dataset series")
        EVT_TOOL(self,ID_RENDER,self.menuRender)

    def createMenu(self):
        """
        -------------------------------------------------------------
        Method: createMenu()
        Created: 03.11.2004
        Creator: KP
        Description: Creates a menu for the window
        -------------------------------------------------------------
        """
        # This is the menubar object that holds all the menus
        self.menu = wxMenuBar()
        self.SetMenuBar(self.menu)
        
        # We create the menu objects
        self.fileMenu=wxMenu()
        self.taskMenu=wxMenu()
        self.helpMenu=wxMenu()
        
        self.settingsMenu=wxMenu()

         # and add them as sub menus to the menubar
        self.menu.Append(self.fileMenu,"&File")
        self.menu.Append(self.settingsMenu,"&Settings")
        self.menu.Append(self.taskMenu,"&Tasks")
        self.menu.Append(self.helpMenu,"&Help")
      

        self.settingsMenu.Append(ID_PREFERENCES,"&Preferences...")
        EVT_MENU(self,ID_PREFERENCES,self.menuPreferences)
    
        self.importMenu=wxMenu()
        self.importMenu.Append(ID_IMPORT_VTIFILES,"&VTK Dataset Series")
        self.importMenu.Append(ID_IMPORT_IMAGES,"&Stack of Images")
   
        self.exportMenu=wxMenu()
        self.exportMenu.Append(ID_EXPORT_VTIFILES,"&VTK Dataset Series")
        self.exportMenu.Append(ID_EXPORT_IMAGES,"&Stack of Images")
        
    
        
        self.fileMenu.Append(ID_OPEN,"&Open...\tCtrl-O","Open a Data Set")
        EVT_MENU(self,ID_OPEN,self.menuOpen)
        self.fileMenu.AppendSeparator()
        self.fileMenu.AppendMenu(ID_IMPORT,"&Import",self.importMenu)
        self.fileMenu.AppendMenu(ID_EXPORT,"&Export",self.exportMenu)
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(ID_QUIT,"&Quit\tCtrl-Q","Quit the application")
        EVT_MENU(self,ID_QUIT,self.quitApp)

        self.taskMenu.Append(ID_COLOCALIZATION,"&Colocalization...","Create a colocalization map")
        self.taskMenu.Append(ID_COLORMERGING,"Color &Merging...","Merge dataset series")
        self.taskMenu.Append(ID_VSIA,"&Visualize Sparse Intensity Aggregations...","Visualize Sparse Intensity Aggregations with smooth surface")
        self.taskMenu.Append(ID_SINGLE,"&Process Single Dataset Series...","Process Single Dataset Series")
        self.taskMenu.Append(ID_RENDER,"&Render Dataset Series...","Render a dataset series")
        EVT_MENU(self,ID_COLOCALIZATION,self.menuColocalization)
        EVT_MENU(self,ID_COLORMERGING,self.menuMergeChannels)
        EVT_MENU(self,ID_VSIA,self.menuVSIA)
        EVT_MENU(self,ID_SINGLE,self.menuProcessDataUnit)
        EVT_MENU(self,ID_RENDER,self.menuRender)

        self.helpMenu.Append(ID_ABOUT,"&About Selli","About this application")
        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(ID_HELP,"&Help\tCtrl-H","Online Help")
        EVT_MENU(self,ID_ABOUT,self.menuAbout)

    def menuPreferences(self,evt):
        """
        Method: menuPreferences()
        Created: 09.02.2005
        Creator: KP
        Description: Callback function for menu item "Preferences"
        """
        self.settingswindow=SettingsWindow.SettingsWindow(self)
        self.settingswindow.ShowModal()

    def menuRender(self,evt):
        """
        Method: menuRender()
        Created: 03.11.2004
        Creator: KP
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
        self.renderWindow=Urmas.UrmasWindow(self)
        
        dataunit=selectedFiles[0]
        self.renderWindow.setDataUnit(dataunit)
        self.renderWindow.ShowModal()


    def menuOpen(self,evt):
        """
        --------------------------------------------------------------
        Method: menuOpen()
        Created: 03.11.2004
        Creator: KP
        Description: Callback function for menu item "Open VTK File"
        -------------------------------------------------------------
        """
        asklist=[]
        print "lastpath now=",self.lastpath
        wc="LSM Files (*.lsm)|*.lsm|Dataset Series (*.du)|*.du|VTK Image Data (*.vti)|*.vti"
        dlg=wxFileDialog(self,"Open dataset series or LSM File",self.lastpath,wildcard=wc,style=wxOPEN|wxMULTIPLE)
        if dlg.ShowModal()==wxID_OK:
            asklist=dlg.GetPaths()
        dlg.Destroy()
        
        for askfile in asklist:
            sep=askfile.split(".")[-1]
            self.lastpath=os.path.split(askfile)[:-1][0]
            print "lastpath=",self.lastpath
            fname=os.path.split(askfile)[-1]
            self.SetStatusText("Loading "+fname+"...")
            self.createDataUnit(fname,askfile)
        self.SetStatusText("Done.")

    def createDataUnit(self,name,path):
        """
        --------------------------------------------------------------
        Method: createDataUnit(name,path)
        Created: 03.11.2004
        Creator: KP
        Description: Creates a dataunit with the given name and path
        Parameters:
            name    Name used to identify this dataunit
            path    Path to the file this dataunit points to
        -------------------------------------------------------------
        """
        ext=path.split(".")[-1]
        dataunit=None
        if self.tree.hasItem(path):
            return
        # We check that the file is not merely a settings file
        try:
            self.parser = SafeConfigParser()
            self.parser.read([path])
            # We read the Key SettingsOnly, and check it's value.
            settingsOnly = self.parser.get("DataUnit", "SettingsOnly")
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
        try:
            if ext=='du':
                datasource=VtiDataSource()
                dataunits = datasource.loadFromDuFile(path)
            elif ext=='lsm':
                datasource=LsmDataSource()
                dataunits=datasource.loadFromLsmFile(path)
        except GUIError,ex:
            ex.show()
            return

        if not dataunits:
            raise "Failed to read dataunit %s"%path

        # If we got data, add corresponding nodes to tree
        #XXX: Add the dataunit to the tree
        self.tree.addToTree(name,path,ext,dataunits)

    def menuEditDataSet(self,evt):
        """
        --------------------------------------------------------------
        Method: menuEditDataSet
        Created: 11.1.2005
        Creator: KP
        Description: Callback function for menu item "Re-Edit data set"
        -------------------------------------------------------------
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

    def menuAction(self,action,unittype,showmethod,filesAtLeast,filesAtMost):
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
        
        unit=unittype(name)
        for dataunit in selectedFiles:
            unit.addSourceDataUnit(dataunit)

        
        dataunit,filepath=showmethod(unit,self)

        # If user cancelled operation, we do not get a new dataset -> return
        if not dataunit:
            return

        # Add the dataset (node) into tree
        self.tree.addToTree(dataunit.getName(),filepath,'du',[dataunit])        
        
    def menuColocalization(self,evt):
        """
        Method: menuColocalization()
        Created: 03.11.2004
        Creator: KP
        Description: Callback function for menu item "Colocalization"
        """
        return self.menuAction("Colocalization",ColocalizationDataUnit,
        ColocalizationWindow.showColocalizationWindow,2,-1)
        
    def menuMergeChannels(self,evt):
        """
        Method: menuMergeChannels()
        Created: 03.11.2004
        Creator: KP
        Description: Callback function for menu item Merge Channels
        """
        return self.menuAction("Color Merging",ColorMergingDataUnit,
        ColorMergingWindow.showColorMergingWindow,2,-1)

    def menuProcessDataUnit(self,evt):
        """
        Method: menuProcessDataUnit()
        Created: 03.11.2004
        Creator: KP
        Description:
        """
        return self.menuAction("Processing",CorrectedSourceDataUnit,
        SingleUnitProcessingWindow.showSingleUnitProcessingWindow,1,1)

    def menuVSIA(self,evt):
        """
        Method: menuVSIA()
        Created: 25.11.2004
        Creator: JV
        Description:
        """
        return self.menuAction("Visualization of Sparse Intensity Aggregations",
        DataUnit.VSIASourceDataUnit,
        VSIAWindow.showVSIAWindow,1,1)

    def menuAbout(self,evt):
        """
        Method: menuAbout()
        Created: 03.11.2004
        Creator: KP
        Description: Callback function for menu item "About"
        """
        s="Selli - LSCM Data "\
        "Post-Processing Software\nCopyright (c) 2004 Juha Hyytiainen, "\
        "Jaakko Mantymaa, Kalle Pahajoki, Jukka Varsaluoma"
        d=wxMessageDialog(self,s,"About Selli",wxOK)
        d.ShowModal()
        d.Destroy()
        

    def quitApp(self,evt):
        """
        --------------------------------------------------------------
        Method: quitApp()
        Created: 03.11.2004
        Creator: KP
        Description: Quits the application
        -------------------------------------------------------------
        """
        self.Close(true)
        
