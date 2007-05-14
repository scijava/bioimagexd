#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ImportDialog
 Project: BioImageXD
 Created: 16.03.2005, KP
 Description:

 A dialog for importing different kinds of data to form a .bxd file
 
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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"
import sys
import os.path,glob
import re,string
import wx
import  wx.lib.filebrowsebutton as filebrowse
import vtk
import Dialogs
import ColorTransferEditor
import  wx.lib.masked as  masked
import Logging
import DataUnit
import DataSource
import Configuration
import Image

import Dialogs

import PreviewFrame

class ImportDialog(wx.Dialog):
    """
    Created: 16.03.2005, KP
    Description: A dialog for importing various forms of data to create a .bxd file
    """
    def __init__(self, parent,imageMode=1):
        """
        Created: 17.03.2005, KP
        Description: Initialize the dialog
        """    
        self.dataUnit = DataUnit.DataUnit()

        self.dataSource = parent.typeToSource["filelist"]()
        self.dataUnit.setDataSource(self.dataSource)
        self.settings = DataUnit.DataUnitSettings()
        self.settings.set("Type","NOOP")
        
        self.ctfInitialized = 0
        
        wx.Dialog.__init__(self, parent, -1, 'Import image stack', style = wx.RESIZE_BORDER|wx.CAPTION)
        self.inputFile=""

#        self.sizer=wx.GridBagSizer()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.createImageImport()
        #self.createVTIImport()
        self.imageInfo = None
        self.pattern=0
        self.resultDataset = None
        
        self.btnsizer=self.CreateButtonSizer(wx.OK|wx.CANCEL)

        self.sizer.Add(self.imageSizer, 1,wx.EXPAND)
        self.sizer.Add(self.btnsizer, 0, wx.EXPAND)
        wx.EVT_BUTTON(self,wx.ID_OK,self.onOkButton)
        self.spacing = (1.0, 1.0, 1.0)
        self.voxelSize = (1.0, 1.0, 1.0)
        
        self.SetSizer(self.sizer)
        self.sizer.SetSizeHints(self)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

		
    def setInputFile(self, filename):
        """
        Created: 07.05.2007, KP
        Description: Set a file that is used as an initial input for the import
        """        
        self.inputFile = filename
        self.browsedir.SetValue(filename)
        
    def getDatasetName(self):
        """
        Created: 6.11.2006, KP
        Description: Return the name of the resultant dataset
        """
        return self.resultDataset
        
    def onOkButton(self,event):
        """
        Created: 21.04.2005, KP
        Description: Executes the procedure
        """
        if not self.spacing:
            Dialogs.showerror(self,"Please define the size of the voxels in the dataset","No voxel size defined")
            return
            
        name=self.nameEdit.GetValue()
        name=name.replace(" ","_")
        filename=Dialogs.askSaveAsFileName(self,"Save imported dataset as","%s.bxd"%name,"BioImageXD Dataset (*.bxd)|*.bxd","import_save")
        self.Close()
        
        self.convertFiles(filename)

    def convertFiles(self,outname):
        """
        Created: 21.04.2005, KP
        Description: Method that reads the files that user has selected
        """          
        idxs = self.sourceListbox.GetSelections()
        files=[]
        
        if not idxs:
            n = self.sourceListbox.GetCount()
            idxs=range(n)
        for i in idxs:
            files.append(self.sourceListbox.GetString(i))
        try:
            self.dataSource.setFilenames(files)
        except Logging.GUIError, ex:
            ex.show()
            self.Close()
            return
        bxdwriter =  DataSource.BXDDataWriter(outname)
        self.resultDataset = bxdwriter.getFilename()
        print "Result dataset=",self.resultDataset

        bxcfilename = bxdwriter.getBXCFileName(outname)
        self.writer = DataSource.BXCDataWriter(bxcfilename)
        bxdwriter.addChannelWriter(self.writer)
        bxdwriter.write()
        self.dlg = wx.ProgressDialog("Importing","Reading dataset %d / %d"%(0,0),maximum = 2*self.tot, parent = self,
        style = wx.PD_ELAPSED_TIME|wx.PD_REMAINING_TIME)   
        
        
          
        self.writeDataUnitFile()
        self.dlg.Destroy()
        
    def writeDataUnitFile(self):
        """
        Created: 25.04.2005, KP
        Description: Writes a .bxd file
        """ 
        settings = self.dataUnit.getSettings()

        Logging.info("Spacing for dataset=",self.spacing,kw="io")
        settings.set("Spacing",self.spacing)
        x,y,z =self.voxelSize
        x/=1000000.0
        y/=1000000.0
        z/=1000000.0
        Logging.info("Writing voxel size as ",x,y,z,kw="io")
        settings.set("VoxelSize",(x,y,z))
        Logging.info("Writing dimensions as ",self.x,self.y,self.z,kw="io")


        settings.set("Dimensions",(self.x,self.y,self.z))
        name=self.nameEdit.GetValue()
        settings.set("Name",name)

        
        parser = self.writer.getParser()
        settings.writeTo(parser)
        i=0
        Logging.info("readers (%d)="%len(self.readers),self.readers,kw="io")
        #for rdr in self.readers:
        tot = self.dataSource.getDataSetCount()
        for i in range(0, tot):
            image = self.dataSource.getDataSet(i)
            #image.SetExtent(0,self.x-1,0,self.y-1,0,self.z-1)
            image.SetSpacing(self.spacing)
            image.SetOrigin(0,0,0)
            self.writer.addImageData(image)
            self.writer.sync()
            self.dlg.Update(self.tot+i,"Writing dataset %d / %d"%(i+1,self.tot))
            i=i+1
        self.writer.write()
            
            
    def createImageImport(self):
        """
        Created: 17.03.2005, KP
        Description: Creates a panel for importing of images as slices of a volume
        """            
        self.imageSizer=wx.GridBagSizer(5,5)
        self.imageSourcebox=wx.StaticBox(self,-1,"Source file")
        self.imageSourceboxsizer=wx.StaticBoxSizer(self.imageSourcebox,wx.VERTICAL)
        
#        self.imageSourceboxsizer.SetMinSize((600,100))
        
        conf = Configuration.getConfiguration()       
        initialDir = conf.getConfigItem("ImportDirectory","Paths")
        if not initialDir:
            initialDir="."
        
        mask = "Supported image files|*.jpg;*.png;*.tif;*.tiff;*.jpeg;*.vtk;*.vti;*.bmp"
        self.browsedir=filebrowse.FileBrowseButton(self,-1,labelText="Source Directory: ",changeCallback=self.loadListOfImages,startDirectory=initialDir, initialValue = self.inputFile, fileMask = mask)
        
        self.sourcesizer=wx.BoxSizer(wx.VERTICAL)
        
        self.sourcelbl=wx.StaticText(self,-1,"Imported dataset consists of:")
        self.choice= wx.Choice(self,-1,choices=["Files following pattern","All files in same directory"],size=(200,-1))
        self.choice.SetSelection(1)
        self.choice.Bind(wx.EVT_CHOICE,self.setInputType)
        
        self.patternEdit=wx.TextCtrl(self,-1,"",style=wx.TE_PROCESS_ENTER, size=(400,-1))
        self.patternEdit.Bind(wx.EVT_TEXT_ENTER,self.loadListOfImages)
        self.patternEdit.Bind(wx.EVT_TEXT,self.loadListOfImages)
        
        
        self.patternLbl=wx.StaticText(self,-1,"Pattern:")
        self.patternBox=wx.BoxSizer(wx.HORIZONTAL)
        self.patternBox.Add(self.patternLbl)
        self.patternBox.Add(self.patternEdit)

        self.sourceListbox=wx.ListBox(self,-1,size=(600,100),style=wx.LB_ALWAYS_SB|wx.LB_HSCROLL|wx.LB_EXTENDED)
        self.sourceListbox.Bind(wx.EVT_LISTBOX,self.updateSelection)
        
        self.imageSourceboxsizer.Add(self.browsedir,0,wx.EXPAND)
        #self.sourcesizer.Add(self.browsedir,(0,0),flag=wx.EXPAND|wx.ALL)
        self.sourcesizer.Add(self.sourcelbl,0,wx.EXPAND)
        self.sourcesizer.Add(self.choice,0)
        self.sourcesizer.Add(self.patternBox,0,wx.EXPAND)

        self.listlbl=wx.StaticText(self,-1,"List of Input Data:")
        self.sourcesizer.Add(self.listlbl)
        self.sourcesizer.Add(self.sourceListbox, 1, wx.EXPAND)
        
        self.imageSourceboxsizer.Add(self.sourcesizer,1,wx.EXPAND)
        
        
        self.previewBox = wx.StaticBox(self,-1,"Volume preview")
        self.imageInfoBox=wx.StaticBox(self,-1,"Volume Information")
        self.imageInfoSizer=wx.StaticBoxSizer(self.imageInfoBox,wx.VERTICAL)
        
        previewBox = wx.BoxSizer(wx.VERTICAL)
        self.zslider = wx.Slider(self,value=1, minValue=1,maxValue=1, style=wx.SL_VERTICAL|wx.SL_LABELS|wx.SL_AUTOTICKS)
        self.timeslider = wx.Slider(self,value=1, minValue=1,maxValue=1, style=wx.SL_LABELS|wx.SL_AUTOTICKS)

        self.zslider.Bind(wx.EVT_SCROLL,self.onChangeZSlice)
        self.timeslider.Bind(wx.EVT_SCROLL, self.onChangeTimepoint)
                
        self.preview = PreviewFrame.PreviewFrame(self,previewsize=(384,384),scrollbars=False)
        self.preview.setPreviewType("")
        
        previewBox.Add(self.preview)
        previewBox.Add(self.timeslider,1,wx.EXPAND)
        
        
        self.previewSizer = wx.StaticBoxSizer(self.previewBox, wx.HORIZONTAL)
        self.previewSizer.Add(previewBox)
        self.previewSizer.Add(self.zslider,1,wx.EXPAND)        
      
        self.infosizer=wx.GridBagSizer(5,5)

        self.nameLbl=wx.StaticText(self,-1,"Dataset name:")
        self.nameEdit = wx.TextCtrl(self,-1,"",size=(220,-1))

        self.nlbl=wx.StaticText(self,-1,"Number of datasets:")
        self.imageAmountLbl=wx.StaticText(self,-1,"1")
 
        
        self.dimlbl=wx.StaticText(self,-1,"Dimension of single slice:")
        self.dimensionLbl=wx.StaticText(self,-1,"")
    
        
        self.depthlbl=wx.StaticText(self,-1,"Depth of Stack:")
        self.depthEdit=wx.TextCtrl(self,-1,"1")
        self.depthEdit.Bind(wx.EVT_TEXT,self.setNumberOfImages)
        

        self.tpLbl=wx.StaticText(self,-1,"Number of Timepoints:")
        #self.timepointLbl=wx.StaticText(self,-1,"1")
        self.timepointEdit = wx.TextCtrl(self,-1,"1")
        self.timepointEdit.Bind(wx.EVT_TEXT, self.setNumberOfTimepoints)
        
        self.voxelSizeLbl=wx.StaticText(self,-1,u"Voxel size")
        #self.voxelSizeEdit=wx.TextCtrl(self,-1,"0, 0, 0")
        #self.voxelSizeEdit = masked.TextCtrl(self,-1,u"",
        #mask = u"#{3}.#{4} \u03BCm x #{3}.#{4}\u03BCm x #{3}.#{4}\u03BCm",
        #formatcodes="F-_.")
        box=wx.BoxSizer(wx.HORIZONTAL)
        self.voxelX=wx.TextCtrl(self,-1,"1.0",size=(50,-1))
        self.voxelY=wx.TextCtrl(self,-1,"1.0",size=(50,-1))
        self.voxelZ=wx.TextCtrl(self,-1,"1.0",size=(50,-1))
        
        self.voxelX.Bind(wx.EVT_TEXT,self.onUpdateVoxelSize)
        self.voxelZ.Bind(wx.EVT_TEXT,self.onUpdateVoxelSize)
        self.voxelY.Bind(wx.EVT_TEXT,self.onUpdateVoxelSize)

        self.lblX=wx.StaticText(self,-1,u"\u03BCm x")
        self.lblY=wx.StaticText(self,-1,u"\u03BCm x")
        self.lblZ=wx.StaticText(self,-1,u"\u03BCm")
        box.Add(self.voxelX)
        box.Add(self.lblX)
        box.Add(self.voxelY)
        box.Add(self.lblY)
        box.Add(self.voxelZ)
        box.Add(self.lblZ)

        self.spcLbl=wx.StaticText(self,-1,"Dataset Spacing:")
        self.spacingLbl=wx.StaticText(self,-1,"0.00 x 0.00 x 0.00")
        
        n=0
        msglbl = wx.StaticText(self,-1,
"""You are opening images from which we cannot read certain pieces of information,
such as voxel sizing and number of slices in a single timepoint. This information 
is important for the correct visualization and processing of the images. Please 
enter the information below.""")
        self.infosizer.Add(msglbl,(n,0),span=(1,2))
        n+=1
      
        self.infosizer.Add(self.nameLbl,(n,0))
        self.infosizer.Add(self.nameEdit,(n,1),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        n+=1
        self.infosizer.Add(self.dimlbl,(n,0))
        self.infosizer.Add(self.dimensionLbl,(n,1),flag=wx.EXPAND|wx.ALL)
        n+=1
        self.infosizer.Add(self.nlbl,(n,0))
        self.infosizer.Add(self.imageAmountLbl,(n,1),flag=wx.EXPAND|wx.ALL)
        n+=1
        self.infosizer.Add(self.tpLbl,(n,0))
        self.infosizer.Add(self.timepointEdit,(n,1),flag=wx.EXPAND|wx.ALL)
        n+=1
        self.infosizer.Add(self.voxelSizeLbl,(n,0))
        #self.infosizer.Add(self.voxelSizeEdit,(n,1),flag=wx.EXPAND|wx.ALL)
        self.infosizer.Add(box,(n,1),flag=wx.EXPAND|wx.ALL,span=(1,2))
        n+=1
        self.infosizer.Add(self.spcLbl,(n,0))
        self.infosizer.Add(self.spacingLbl,(n,1))
        n+=1
        self.infosizer.Add(self.depthlbl,(n,0))
        self.infosizer.Add(self.depthEdit,(n,1),flag=wx.EXPAND|wx.ALL)
        n+=1
        
        self.colorBtn = ColorTransferEditor.CTFButton(self)
        
        self.infosizer.Add(self.colorBtn,(n,0),span=(1,2))
        
        self.imageInfoSizer.Add(self.infosizer,1,wx.EXPAND|wx.ALL)
        
        
        self.imageSizer.Add(self.imageSourceboxsizer,(0,0),flag=wx.EXPAND|wx.ALL,border=5,span=(1,2) )
        self.imageSizer.Add(self.imageInfoSizer,(1,0),flag=wx.EXPAND|wx.ALL,border=5)
        self.imageSizer.Add(self.previewSizer,(1,1),border=5)
        
        if self.inputFile:
            self.browsedir.SetValue(self.inputFile)
            self.loadListOfFiles()
            
    def onChangeZSlice(self,event):
        """
        Created: 07.05.2007, KP
        Description: Set the zslice displayed in the preview
        """             
        self.preview.setZSlice(self.zslider.GetValue()-1)
        #print "Setting preview to ",self.zslider.GetValue()-1
        self.preview.updatePreview(0)
        
    def onChangeTimepoint(self, event):
        """
        Created: 07.05.2007, KP
        Description: Set the timepoint displayed in the preview
        """
        self.preview.setTimepoint(self.timeslider.GetValue()-1)
        self.preview.updatePreview(0)
        
    def onUpdateVoxelSize(self,filename):
        """
        Created: 21.04.2005, KP
        Description: A method to update the spacing depending on the voxel size
        """                       
        try:
            vx = float(self.voxelX.GetValue())
            vy = float(self.voxelY.GetValue())
            vz = float(self.voxelZ.GetValue())
        except:
            return
        Logging.info("Voxel sizes = ",vx,vy,vz,kw="io")
        self.voxelSize = (vx,vy,vz)
        self.spacing=(1.0,vy/vx,vz/vx)
        self.dataSource.setVoxelSize(self.voxelSize)
        Logging.info("Setting spacing to ",self.spacing,kw="io")
        sx,sy,sz=self.spacing
        self.spacingLbl.SetLabel("%.2f x %.2f x %.2f"%(sx,sy,sz))

        
    def setImagePattern(self,filename):
        """
        Created: 17.03.2005, KP
        Description: A method called when a file is loaded in the filebrowsebutton
        """                 
        r=re.compile("[0-9]+")
        items=r.findall(filename)
        if items:
            s="%%.%dd"%len(items[-1])
            filename=filename.replace(items[-1],s)            
        self.patternEdit.SetValue(filename)
 
    def setInputType(self,event):
        """
        Created: 17.03.2005, KP
        Description: A method called when the input type is changed
        """        
        self.patternEdit.Enable(self.choice.GetSelection()==0)
        self.loadListOfImages()
     
    def updateSelection(self,event):
        """
        Created: 17.03.2005, KP
        Description: This method is called when user selects items in the listbox
        """           
        idxs = self.sourceListbox.GetSelections()
        files=[]
        
        if not idxs:
            n = self.sourceListbox.GetCount()
            idxs=range(n)
        for i in idxs:
            files.append(self.sourceListbox.GetString(i))
        try:
            self.dataSource.setFilenames(files)
        except Logging.GUIError, ex:
            ex.show()
            self.sourceListbox.Clear()
            self.setNumberOfImages(0)
            return
        
        self.setNumberOfImages(len(self.sourceListbox.GetSelections()))
        
    def setNumberOfTimepoints(self, evt):
        """
        Created: 07.05.2007, KP
        Description: set the number of timepoints, and adjust the number of slices per timepoint accordingly
        """
        n = int(float(self.timepointEdit.GetValue()))
        self.timeslider.SetRange(1, n)
        
        totalAmnt = int(self.imageAmountLbl.GetLabel())
        if n and totalAmnt:
            slices = float(totalAmnt)/n
            if self.dataSource.is3DImage():
                x,y,slices = self.dataUnit.getDimensions()
            
            self.depthEdit.SetValue("%.2f"%slices)
            self.dataSource.setSlicesPerTimepoint(slices)
            self.zslider.SetRange(1,slices)
        
    def setNumberOfImages(self,n=-1):
        """
        Created: 17.03.2005, KP
        Description: Sets the number of images we're reading
        """        
        if type(n)!=type(0):
            n=int(self.imageAmountLbl.GetLabel())
        Logging.info("n=",n,kw="io")
        self.imageAmountLbl.SetLabel("%d"%n)
        
        val = self.depthEdit.GetValue()
        try:
            if not self.dataSource.is3DImage():
                val=int(val)
                tps=float(n)/val
            else:
                tps = n
            self.timepointEdit.SetValue("%.2f"%tps)
            self.timeslider.SetRange(1,tps)
        except:
            pass
                
    
    def sortNumerically(self,item1,item2):
        """
        Created: 17.03.2005, KP
        Description: A method that compares two filenames and sorts them by the number in their filename
        """        
        r=re.compile("[0-9]+")
        s=r.findall(item1)
        s2=r.findall(item2)
        if len(s)!=len(s2):
            return len(s).__cmp__(len(s2))
        if len(s)==1:
            n=int(s[0])
            n2=int(s2[0])
            return n.__cmp__(n2)
        else:
            for i in range(len(s)):
                i1=int(s[i])
                i2=int(s2[i])
                if len(s[i])<len(s2[i]):return -1
                c=i1.__cmp__(i2)
                if c!=0:return c
        return item1.__cmp__(item2)
        
    
    def loadListOfImages(self,event=None):
        """
        Created: 17.03.2005, KP
        Description: A method that loads a list of images to a listbox based on the selected input type
        """        
        filename=self.browsedir.GetValue()
        conf = Configuration.getConfiguration()
        conf.setConfigItem("ImportDirectory","Paths",os.path.dirname(filename))
        conf.writeSettings()
        if not filename:
            return
        ext=filename.split(".")[-1]
        if self.pattern != ext:
            self.pattern=ext
            f0=os.path.basename(filename)
            print "imagepattern=",f0
            self.setImagePattern(f0)
            
        # If the first choice ("All in directory") is selected
        selection=self.choice.GetSelection()
        dirn=os.path.dirname(filename)
        if selection==0:
            
            r=re.compile("[0-9]+")
            pat=r.sub("[0-9]*",os.path.basename(filename))
            
            dirn=os.path.dirname(filename)
            pat=dirn+os.path.sep+"%s"%(pat)
        else:
            pat=dirn+os.path.sep+"*.%s"%ext
        Logging.info("Pattern for all in directory is ",pat,kw="io")
        files=glob.glob(pat)
        print "Got files=",files
        self.sourceListbox.Clear()
        files.sort(self.sortNumerically)
        r=re.compile("([0-9]+)")
         
        m = r.search(files[0])
        if m:

            startfrom = int(m.groups(1)[0])
        else:
            startfrom = 0
        print "Starting from ",startfrom
        n=0
        # If we're using all files in directory, just add them to the list
        if selection==1:
            self.sourceListbox.InsertItems(files,0)
            n=len(files)
            try:
                self.dataSource.setFilenames(files, pattern="")
            except Logging.GUIError, ex:
                ex.show()
                self.sourceListbox.Clear()
                return
        # If we're using the pattern
        elif selection==0:
            pat=self.patternEdit.GetValue()
            filecount=len(files)
            nformat=pat.count("%")
            # If there are no format specifiers, just use the files we found
            if nformat == 0:
                self.sourceListbox.InsertItems(files,0)
                n=len(files)
                try:    
                    self.dataSource.setFilenames(files, pattern = pat)
                except Logging.GUIError, ex:
                    ex.show()
                    self.sourceListbox.Clear()            
                    return
            # If there is one specifier, then try to find files that correspond to that
            elif nformat==1:
                filelist=[]
                for i in range(startfrom-1, startfrom+filecount+1):
                    try:
                        filename=pat%i
                    except:
                        return
                    for file in files:
                        if file.find(filename)!=-1:
                            self.sourceListbox.Append(file)
                            filelist.append(file)
                            n+=1
                try:
                    self.dataSource.setFilenames(filelist)
                except Logging.GUIError, ex:
                    ex.show()
                    self.sourceListbox.Clear()
                    return
            else:
                filelist=[]
                everfound=0
                for i in range(filecount):
                    foundone=0
                    for j in range(filecount):
                        try:
                            filename=pat%(i,j)
                        except:
                            return
                        for file in files:
                            if file.find(filename)!=-1:
                                self.sourceListbox.Append(file)
                                filelist.append(file)
                                n+=1
                                foundone=1
                                everfound=1
                    if everfound and not foundone:break
                try:
                    self.dataSource.setFilenames(filelist)                                
                except Logging.GUIError, ex:
                    ex.show()
                    self.sourceListbox.Clear()
                    return
                    
        self.setNumberOfImages(n)
        self.preview.setDataUnit(self.dataUnit)
        self.preview.zoomToFit()
        if self.imageInfo != ext:
            self.retrieveImageInfo()
            self.imageInfo = ext
            
    def retrieveImageInfo(self):
        """
        Created: 21.04.2005, KP
        Description: A method that reads information from an image
        """                
        print "Getting dimensions..."
        self.x,self.y,self.z=self.dataSource.getDimensions()
        print "Got dims",self.x, self.y, self.z
        self.dimensionLbl.SetLabel("%d x %d"%(self.x,self.y))                
        self.depthEdit.SetValue("%.2f"%self.z)
        self.zslider.SetRange(1,self.z) 
        if not self.ctfInitialized:
            x0,x1 = self.dataSource.getScalarRange()
            self.ctf = vtk.vtkColorTransferFunction()
            self.ctf.AddRGBPoint(0, 0, 0, 0)
            self.ctf.AddRGBPoint(x1, 0, 1, 0)
            self.colorBtn.setColorTransferFunction(self.ctf)
            self.settings.set("ColorTransferFunction",self.ctf)
            self.ctfInitialized = 1
            self.dataUnit.setSettings(self.settings)
