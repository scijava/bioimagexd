#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ImportDialog.py
 Project: BioImageXD
 Created: 16.03.2005
 Creator: KP
 Description:

 A dialog for importing different kinds of data to form a .du file
 
 Modified: 16.03.2005 KP - Created the module

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 """
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"
import sys
import os.path,glob
import re
import wx
import  wx.lib.filebrowsebutton as filebrowse


class ImportDialog(wx.Dialog):
    """
    Class: ImportDialog
    Created: 16.03.2005, KP
    Description: A dialog for importing various forms of data to create a .du file
    """
    def __init__(self, parent,imageMode=1):
        """
        Method: __init__
        Created: 17.03.2005, KP
        Description: Initialize the dialog
        """    
        wx.Dialog.__init__(self, parent, -1, 'Import Data')
        
        self.sizer=wx.GridBagSizer()
        self.notebook = wx.Notebook(self,-1)
        self.sizer.Add(self.notebook,(0,0),flag=wx.EXPAND|wx.ALL)
        self.createImageImport()
        #self.createVTIImport()
        
        self.notebook.AddPage(self.imagePanel,"Stack of Images")

        self.btnsizer=self.CreateButtonSizer(wx.OK|wx.CANCEL)
        self.sizer.Add(self.btnsizer,(5,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
       
    def createImageImport(self):
        """
        Method: createImageImport()
        Created: 17.03.2005, KP
        Description: Creates a panel for importing of images as slices of a volume
        """            
        self.imagePanel = wx.Panel(self.notebook,-1,size=(640,480))
        self.imageSizer=wx.GridBagSizer(5,5)
        self.imageSourcebox=wx.StaticBox(self.imagePanel,-1,"Source of Images")
        self.imageSourceboxsizer=wx.StaticBoxSizer(self.imageSourcebox,wx.VERTICAL)
        
        self.imageSourceboxsizer.SetMinSize((600,100))
        
        
        self.browsedir=filebrowse.FileBrowseButton(self.imagePanel,-1,labelText="Image Directory: ",changeCallback=self.setImagePattern)
        
        self.sourcesizer=wx.BoxSizer(wx.VERTICAL)
        
        self.sourcelbl=wx.StaticText(self.imagePanel,-1,"Stack consists of:")
        self.choice= wx.Choice(self.imagePanel,-1,choices=["All images in same directory","Files following pattern"],size=(200,-1))
        self.choice.Bind(wx.EVT_CHOICE,self.setInputType)
        self.patternEdit=wx.TextCtrl(self.imagePanel,-1,"",style=wx.TE_PROCESS_ENTER)
        self.patternEdit.Bind(wx.EVT_TEXT_ENTER,self.loadListOfImages)
        self.patternEdit.Enable(0)
        
        self.patternLbl=wx.StaticText(self.imagePanel,-1,"Pattern:")
        self.patternBox=wx.BoxSizer(wx.HORIZONTAL)
        self.patternBox.Add(self.patternLbl)
        self.patternBox.Add(self.patternEdit,1)

        self.sourceListbox=wx.ListBox(self.imagePanel,-1,size=(400,100),style=wx.LB_ALWAYS_SB|wx.LB_EXTENDED)
        self.sourceListbox.Bind(wx.EVT_LISTBOX,self.updateSelection)
        
        self.imageSourceboxsizer.Add(self.browsedir,0,wx.EXPAND)
        #self.sourcesizer.Add(self.browsedir,(0,0),flag=wx.EXPAND|wx.ALL)
        self.sourcesizer.Add(self.sourcelbl,0,wx.EXPAND)
        self.sourcesizer.Add(self.choice,0)
        self.sourcesizer.Add(self.patternBox,0,wx.EXPAND)

        self.listlbl=wx.StaticText(self.imagePanel,-1,"List of Images:")
        self.sourcesizer.Add(self.listlbl)
        self.sourcesizer.Add(self.sourceListbox)
        
        self.imageSourceboxsizer.Add(self.sourcesizer,1,wx.EXPAND)
        
        self.imageInfoBox=wx.StaticBox(self.imagePanel,-1,"Image Information")
        self.imageInfoSizer=wx.StaticBoxSizer(self.imageInfoBox,wx.VERTICAL)
        
        self.infosizer=wx.GridBagSizer(5,5)

        self.nlbl=wx.StaticText(self.imagePanel,-1,"Number of images:")
        self.imageAmountLbl=wx.StaticText(self.imagePanel,-1,"0")
 
        
        self.dimlbl=wx.StaticText(self.imagePanel,-1,"Image dimensions:")
        self.dimensionLbl=wx.StaticText(self.imagePanel,-1,"0 x 0")
    
        
        self.depthlbl=wx.StaticText(self.imagePanel,-1,"Depth of Stack:")
        self.depthEdit=wx.TextCtrl(self.imagePanel,-1,"")
        self.depthEdit.Bind(wx.EVT_TEXT,self.setNumberOfImages)
        

        self.tpLbl=wx.StaticText(self.imagePanel,-1,"Number of Timepoints:")
        self.timepointLbl=wx.StaticText(self.imagePanel,-1,"0")
        
        
        self.infosizer.Add(self.nlbl,(0,0))
        self.infosizer.Add(self.imageAmountLbl,(0,1),flag=wx.EXPAND|wx.ALL)
        
        self.infosizer.Add(self.dimlbl,(1,0))
        self.infosizer.Add(self.dimensionLbl,(1,1),flag=wx.EXPAND|wx.ALL)
        
        
        self.infosizer.Add(self.tpLbl,(2,0))
        self.infosizer.Add(self.timepointLbl,(2,1),flag=wx.EXPAND|wx.ALL)

        self.infosizer.Add(self.depthlbl,(3,0))
        self.infosizer.Add(self.depthEdit,(3,1),flag=wx.EXPAND|wx.ALL)

        
        self.imageInfoSizer.Add(self.infosizer)
        
        self.imageSizer.Add(self.imageInfoSizer,(0,0),flag=wx.EXPAND|wx.ALL,border=5)
        self.imageSizer.Add(self.imageSourceboxsizer,(1,0),flag=wx.EXPAND|wx.ALL,border=5)
        
        self.imagePanel.SetSizer(self.imageSizer)
        self.imagePanel.SetAutoLayout(1)
        self.imageSizer.Fit(self.imagePanel)
        
        
        
    def setImagePattern(self,event):
        """
        Method: setImagePattern
        Created: 17.03.2005, KP
        Description: A method called when a file is loaded in the filebrowsebutton
        """         
        val=self.browsedir.GetValue()
        
        val=os.path.basename(val)
        r=re.compile("[0123456789]+")
        pattern=r.sub("[0-9]+",val)
        self.patternEdit.SetValue(pattern)
        
        self.loadListOfImages()
 
    def setInputType(self,event):
        """
        Method: setInputType
        Created: 17.03.2005, KP
        Description: A method called when the input type is changed
        """        
        if self.choice.GetSelection()!=1:
            self.patternEdit.Enable(0)
        else:
            self.patternEdit.Enable(1)
        self.loadListOfImages()
     
    def updateSelection(self,event):
        """
        Method: updateSelection
        Created: 17.03.2005, KP
        Description: This method is called when user selects items in the listbox
        """           
        self.setNumberOfImages(len(self.sourceListbox.GetSelections()))
    
    
    def setNumberOfImages(self,n=-1):
        """
        Method: setNumberOfImages(n)
        Created: 17.03.2005, KP
        Description: Sets the number of images we're reading
        """        
        if type(n)!=type(0):
            n=int(self.imageAmountLbl.GetLabel())
        print "n=",n
        self.imageAmountLbl.SetLabel("%d"%n)
        val = self.depthEdit.GetValue()
        try:
            val=int(val)
            tps=float(n)/val
            self.timepointLbl.SetLabel("%.2f"%tps)
        except:
            pass
                
    
    def sortNumerically(self,item1,item2):
        """
        Method: sortNumerically
        Created: 17.03.2005, KP
        Description: A method that compares two filenames and sorts them by the number in their filename
        """        
        r=re.compile("[0-9]+")
        s=r.search(item1)
        s2=r.search(item2)
        n=int(s.group(0))
        n2=int(s2.group(0))
        return n.__cmp__(n2)
        
    
    def loadListOfImages(self,event=None):
        """
        Method: loadListOfImages
        Created: 17.03.2005, KP
        Description: A method that loads a list of images to a listbox based on the selected input type
        """        
        filename=self.browsedir.GetValue()
        if not filename:
            return
        # If the first choice ("All in directory") is selected
        selection=self.choice.GetSelection()
        ext=filename.split(".")[-1]
        dir=os.path.dirname(filename)
        pat=dir+"/*.%s"%ext
        print "Pattern for all in directory is ",pat
        files=glob.glob(pat)
        self.sourceListbox.Clear()
        files.sort(self.sortNumerically)
        n=0
        if selection==0:
            self.sourceListbox.InsertItems(files,0)
            n=len(files)
        elif selection==1:
            pat=self.patternEdit.GetValue()
            r=re.compile(pat)
            for file in files:
                if r.search(file):
                    self.sourceListbox.Append(file)
                    n+=1
        self.setNumberOfImages(n)
            
