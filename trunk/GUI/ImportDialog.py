4#! /usr/bin/env pythonG
# -*- coding: iso-8859-1 -*-
"""
 Unit: ImportDialog
 Project: BioImageXD
 Created: 16.03.2005
 Creator: KP
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
        wx.Dialog.__init__(self, parent, -1, 'Import Data')
        
        self.sizer=wx.GridBagSizer()
        self.notebook = wx.Notebook(self,-1)
        self.sizer.Add(self.notebook,(0,0),flag=wx.EXPAND|wx.ALL)
        self.createImageImport()
        #self.createVTIImport()
        self.imageInfo = None
        self.pattern=0
        self.resultDataset = None
        self.extMapping = {"tif":"TIFF","tiff":"TIFF","png":"PNG","jpg":"JPEG","jpeg":"JPEG","pnm":"PNM","vti":"XMLImageData","vtk":"DataSet","bmp":"BMP"}
        self.dimMapping={"bmp":2,"tif":2,"tiff":2,"png":2,"jpg":2,"jpeg":2,"pnm":2,"vti":3,"vtk":3}
        
        self.notebook.AddPage(self.imagePanel,"Import dataset")

        self.btnsizer=self.CreateButtonSizer(wx.OK|wx.CANCEL)
        self.sizer.Add(self.btnsizer,(5,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
    
        wx.EVT_BUTTON(self,wx.ID_OK,self.onOkButton)
        self.spacing = (1.0, 1.0, 1.0)
        self.voxelSize = (1.0, 1.0, 1.0)
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
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
        print "convertFiles",outname
        idxs = self.sourceListbox.GetSelections()
        files=[]
        
        if not idxs:
            n = self.sourceListbox.GetCount()
            idxs=range(n)
        print "idxs=",idxs
        for i in idxs:
            files.append(self.sourceListbox.GetString(i))
        print "files=",files
        dirn=os.path.dirname(files[0])
        self.z=int(self.depthEdit.GetValue())
        ext=files[0].split(".")[-1].lower()
        self.rdrstr = "vtk.vtk%sReader()"%(self.extMapping[ext])
        dim = self.dimMapping[ext]
        self.readers=[]
        
        bxdwriter =  DataSource.BXDDataWriter(outname)
        self.resultDataset = bxdwriter.getFilename()

        bxcfilename = bxdwriter.getBXCFileName(outname)
        self.writer = DataSource.BXCDataWriter(bxcfilename)
        bxdwriter.addChannelWriter(self.writer)
        bxdwriter.write()
        
        if dim==3:
            self.tot = len(files)
            self.dlg = wx.ProgressDialog("Importing","Reading dataset %d / %d"%(0,0),maximum = 2*self.tot, parent = self,
            style = wx.PD_ELAPSED_TIME|wx.PD_REMAINING_TIME)        
            for i,file in enumerate(files):   
                rdr = eval(self.rdrstr)
                if ext =="bmp":
                    rdr.Allow8BitBMPOn()
                    
                # This is not required for VTK dataset readers, so 
                # we ignore any errors 0
                Logging.info("Reading ",file,kw="io")
                rdr.SetFileName(file)
                rdr.Update()
                self.readers.append(rdr)
                self.dlg.Update(i,"Reading dataset %d / %d"%(i+1,self.tot))
#                self.writeData(outname,data,i,len(files))
        else:
            #print "IMPORTING..."
            self.tot = len(files) / self.z
            
            
            self.dlg = wx.ProgressDialog("Importing","Reading dataset %d / %d"%(0,0),maximum = 2*self.tot, parent = self,
            style = wx.PD_ELAPSED_TIME|wx.PD_REMAINING_TIME)
            #rdr.SetFileDimensionality(dim)
            pattern = self.patternEdit.GetValue()
            n=pattern.count("%")
            
            Logging.info("Number of %s=",n,kw="io")
            imgAmnt=len(files)
            print "TOT=",self.tot
            if self.tot == 1:
                arr = vtk.vtkStringArray()
                for i in files:
                    arr.InsertNextValue(os.path.join(dirn,i))
                rdr = eval(self.rdrstr)   
                rdr.SetFileNames(arr)
                if ext=="bmp":
                    rdr.Allow8BitBMPOn()
                rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                rdr.SetDataSpacing(self.spacing)
                rdr.SetDataOrigin(0,0,0)
                self.readers.append(rdr)
            elif n==0 and imgAmnt>1:
                #print "FOO"
                Dialogs.showerror(self,"You are trying to import multiple files but have not defined a proper pattern for the files to be imported","Bad pattern")
                return
            elif n==0:
                rdr = eval(self.rdrstr)
                if ext=="bmp":
                    rdr.Allow8BitBMPOn()
                rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                rdr.SetDataSpacing(self.spacing)
                rdr.SetDataOrigin(0,0,0)
                
                rdr.SetFileName(files[0])
                rdr.Update()
                Logging.info("Reader = ",rdr,kw="io")
                self.dlg.Update(0,"Reading dataset 1")
                self.readers.append(rdr)
                #self.writeData(outname,data,j,len(files))
            elif n==1:
                j=0
                Logging.info("self.z=%d",self.z,kw="io")
                start=0
                for i in range(0,imgAmnt):
                    
                    file=dirn+os.path.sep+pattern%i
                    #print "CHecking ",file
                    if os.path.exists(file):
                        start=i
                        Logging.info("Files start at %d"%i)
                        break
                    
                for i in range(start,imgAmnt+start,self.z):
                    rdr = eval(self.rdrstr)
                    if ext =="bmp":
                        rdr.Allow8BitBMPOn()

                    rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                    rdr.SetDataSpacing(self.spacing)
                    rdr.SetDataOrigin(0,0,0)
                    
                    if i:
                        Logging.info("Setting slice offset to ",i,kw="io")
                        rdr.SetFileNameSliceOffset(i)
                    rdr.SetFilePrefix(dirn+os.path.sep)
                    rdr.SetFilePattern("%s"+pattern)
                    rdr.Update()
                    Logging.info("Reader = ",rdr,kw="io")
                    self.dlg.Update(j,"Reading dataset %d / %d"%(j+1,self.tot))
                    self.readers.append(rdr)
                    #self.writeData(outname,data,j,len(files))
                    j=j+1
            elif n==2:
                tps = imgAmnt / self.z
                for i in range(tps):
                    rdr = eval(self.rdrstr)
                    if ext =="bmp":
                        rdr.Allow8BitBMPOn()

                    rdr.SetDataExtent(0,self.x-1,0,self.y-1,0,self.z-1)
                    rdr.SetDataSpacing(self.spacing)
                    rdr.SetDataOrigin(0,0,0)
                    
                    pos=pattern.rfind("%")
                    begin=pattern[:pos-1]
                    end=pattern[pos-1:]
                    currpat=begin%i+end
                    Logging.info("Pattern for timepoint %d is "%i,currpat,kw="io")
                                     
                    rdr.SetFilePrefix(dirn+os.path.sep)
                    rdr.SetFilePattern("%s"+currpat)
                    Logging.info("Reader = ",rdr,kw="io")
                    rdr.Update()
                    #data = rdr.GetOutput()
                    #self.writeData(outname,data,i,len(files))
                    self.readers.append(rdr)
                    self.dlg.Update(i,"Reading dataset %d / %d"%(i+1,self.tot))
        
        self.writeDataUnitFile()
        self.dlg.Destroy()
        
    def writeDataUnitFile(self):
        """
        Created: 25.04.2005, KP
        Description: Writes a .bxd file
        """ 
        settings = DataUnit.DataUnitSettings()
        settings.set("Type","NOOP")
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
        
        ctf = self.colorBtn.getColorTransferFunction()
        settings.set("ColorTransferFunction",ctf)
        
        parser = self.writer.getParser()
        settings.writeTo(parser)
        i=0
        Logging.info("readers (%d)="%len(self.readers),self.readers,kw="io")
        for rdr in self.readers:
            rdr.Update()
            image=rdr.GetOutput()
            #image.SetExtent(0,self.x-1,0,self.y-1,0,self.z-1)
            image.SetSpacing(self.spacing)
            image.SetOrigin(0,0,0)
            self.writer.addImageData(image)
            self.writer.sync()
            self.dlg.Update(self.tot+i,"Writing dataset %d / %d"%(i+1,self.tot))
            i=i+1
        self.writer.write()
            
    
    def writeData(self,outname,data,n,total):
        """
        Created: 21.04.2005, KP
        Description: Writes a data out
        """
        Logging.info("Adding dataset %d"%n,data,kw="io")
        self.writer.addImageData(data)
        
    def createImageImport(self):
        """
        Created: 17.03.2005, KP
        Description: Creates a panel for importing of images as slices of a volume
        """            
        self.imagePanel = wx.Panel(self.notebook,-1,size=(640,480))
        self.imageSizer=wx.GridBagSizer(5,5)
        self.imageSourcebox=wx.StaticBox(self.imagePanel,-1,"Source file")
        self.imageSourceboxsizer=wx.StaticBoxSizer(self.imageSourcebox,wx.VERTICAL)
        
        self.imageSourceboxsizer.SetMinSize((600,100))
        
        conf = Configuration.getConfiguration()       
        initialDir = conf.getConfigItem("ImportDirectory","Paths")
        if not initialDir:
            initialDir="."

        self.browsedir=filebrowse.FileBrowseButton(self.imagePanel,-1,labelText="Source Directory: ",changeCallback=self.loadListOfImages,startDirectory=initialDir)
        
        self.sourcesizer=wx.BoxSizer(wx.VERTICAL)
        
        self.sourcelbl=wx.StaticText(self.imagePanel,-1,"Imported dataset consists of:")
        self.choice= wx.Choice(self.imagePanel,-1,choices=["Files following pattern","All files in same directory"],size=(200,-1))
        self.choice.SetSelection(0)
        self.choice.Bind(wx.EVT_CHOICE,self.setInputType)
        
        self.patternEdit=wx.TextCtrl(self.imagePanel,-1,"",style=wx.TE_PROCESS_ENTER)
        self.patternEdit.Bind(wx.EVT_TEXT_ENTER,self.loadListOfImages)
        self.patternEdit.Bind(wx.EVT_TEXT,self.loadListOfImages)
        
        
        self.patternLbl=wx.StaticText(self.imagePanel,-1,"Pattern:")
        self.patternBox=wx.BoxSizer(wx.HORIZONTAL)
        self.patternBox.Add(self.patternLbl)
        self.patternBox.Add(self.patternEdit,1)

        self.sourceListbox=wx.ListBox(self.imagePanel,-1,size=(550,100),style=wx.LB_ALWAYS_SB|wx.LB_HSCROLL|wx.LB_EXTENDED)
        self.sourceListbox.Bind(wx.EVT_LISTBOX,self.updateSelection)
        
        self.imageSourceboxsizer.Add(self.browsedir,0,wx.EXPAND)
        #self.sourcesizer.Add(self.browsedir,(0,0),flag=wx.EXPAND|wx.ALL)
        self.sourcesizer.Add(self.sourcelbl,0,wx.EXPAND)
        self.sourcesizer.Add(self.choice,0)
        self.sourcesizer.Add(self.patternBox,0,wx.EXPAND)

        self.listlbl=wx.StaticText(self.imagePanel,-1,"List of Input Data:")
        self.sourcesizer.Add(self.listlbl)
        self.sourcesizer.Add(self.sourceListbox)
        
        self.imageSourceboxsizer.Add(self.sourcesizer,1,wx.EXPAND)
        
        self.imageInfoBox=wx.StaticBox(self.imagePanel,-1,"Volume Information")
        self.imageInfoSizer=wx.StaticBoxSizer(self.imageInfoBox,wx.VERTICAL)
        
        self.infosizer=wx.GridBagSizer(5,5)

        self.nameLbl=wx.StaticText(self.imagePanel,-1,"Dataset name:")
        self.nameEdit = wx.TextCtrl(self.imagePanel,-1,"",size=(220,-1))

        self.nlbl=wx.StaticText(self.imagePanel,-1,"Number of datasets:")
        self.imageAmountLbl=wx.StaticText(self.imagePanel,-1,"1")
 
        
        self.dimlbl=wx.StaticText(self.imagePanel,-1,"Dimension of single slice:")
        self.dimensionLbl=wx.StaticText(self.imagePanel,-1,"0 x 0")
    
        
        self.depthlbl=wx.StaticText(self.imagePanel,-1,"Depth of Stack:")
        self.depthEdit=wx.TextCtrl(self.imagePanel,-1,"1")
        self.depthEdit.Bind(wx.EVT_TEXT,self.setNumberOfImages)
        

        self.tpLbl=wx.StaticText(self.imagePanel,-1,"Number of Timepoints:")
        self.timepointLbl=wx.StaticText(self.imagePanel,-1,"1")
        
        self.voxelSizeLbl=wx.StaticText(self.imagePanel,-1,u"Voxel size")
        #self.voxelSizeEdit=wx.TextCtrl(self.imagePanel,-1,"0, 0, 0")
        #self.voxelSizeEdit = masked.TextCtrl(self,-1,u"",
        #mask = u"#{3}.#{4} \u03BCm x #{3}.#{4}\u03BCm x #{3}.#{4}\u03BCm",
        #formatcodes="F-_.")
        box=wx.BoxSizer(wx.HORIZONTAL)
        self.voxelX=wx.TextCtrl(self.imagePanel,-1,"1.0")
        self.voxelY=wx.TextCtrl(self.imagePanel,-1,"1.0")
        self.voxelZ=wx.TextCtrl(self.imagePanel,-1,"1.0")
        
        self.voxelX.Bind(wx.EVT_TEXT,self.onUpdateVoxelSize)
        self.voxelZ.Bind(wx.EVT_TEXT,self.onUpdateVoxelSize)
        self.voxelY.Bind(wx.EVT_TEXT,self.onUpdateVoxelSize)

        self.lblX=wx.StaticText(self.imagePanel,-1,u"\u03BCm x")
        self.lblY=wx.StaticText(self.imagePanel,-1,u"\u03BCm x")
        self.lblZ=wx.StaticText(self.imagePanel,-1,u"\u03BCm")
        box.Add(self.voxelX)
        box.Add(self.lblX)
        box.Add(self.voxelY)
        box.Add(self.lblY)
        box.Add(self.voxelZ)
        box.Add(self.lblZ)

        self.spcLbl=wx.StaticText(self.imagePanel,-1,"Dataset Spacing:")
        self.spacingLbl=wx.StaticText(self.imagePanel,-1,"0.00 x 0.00 x 0.00")
        
        n=0
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
        self.infosizer.Add(self.timepointLbl,(n,1),flag=wx.EXPAND|wx.ALL)
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
        
        self.colorBtn = ColorTransferEditor.CTFButton(self.imagePanel)
        
        self.infosizer.Add(self.colorBtn,(n,0),flag=wx.EXPAND|wx.ALL,span=(1,2))
        
        self.imageInfoSizer.Add(self.infosizer,1,wx.EXPAND|wx.ALL)
        
        self.imageSizer.Add(self.imageInfoSizer,(0,0),flag=wx.EXPAND|wx.ALL,border=5)
        self.imageSizer.Add(self.imageSourceboxsizer,(1,0),flag=wx.EXPAND|wx.ALL,border=5)
        
        self.imagePanel.SetSizer(self.imageSizer)
        self.imagePanel.SetAutoLayout(1)
        self.imageSizer.Fit(self.imagePanel)
        
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
        Method: setInputType
        Created: 17.03.2005, KP
        Description: A method called when the input type is changed
        """        
        if self.choice.GetSelection()!=0:
            self.patternEdit.Enable(0)
        else:
            self.patternEdit.Enable(1)
        self.loadListOfImages()
     
    def updateSelection(self,event):
        """
        Created: 17.03.2005, KP
        Description: This method is called when user selects items in the listbox
        """           
        self.setNumberOfImages(len(self.sourceListbox.GetSelections()))
    
    
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
            val=int(val)
            tps=float(n)/val
            self.timepointLbl.SetLabel("%.2f"%tps)
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
        dir=os.path.dirname(filename)
        if selection==0:
            
            r=re.compile("[0-9]+")
            pat=r.sub("[0-9]*",os.path.basename(filename))
            
            dir=os.path.dirname(filename)
            pat=dir+os.path.sep+"%s"%(pat)
        else:
            pat=dir+os.path.sep+"*.%s"%ext
        Logging.info("Pattern for all in directory is ",pat,kw="io")
        files=glob.glob(pat)
        print "Got files=",files
        self.sourceListbox.Clear()
        files.sort(self.sortNumerically)
        n=0
        if selection==1:
            self.sourceListbox.InsertItems(files,0)
            n=len(files)
        elif selection==0:
            pat=self.patternEdit.GetValue()
            filecount=len(files)
            nformat=pat.count("%")
            if nformat == 0:
                self.sourceListbox.InsertItems(files,0)
                n=len(files)
            elif nformat==1:
                for i in range(filecount+1):
                    try:
                        filename=pat%i
                    except:
                        return
                    for file in files:
                        if file.find(filename)!=-1:
                            self.sourceListbox.Append(file)
                            n+=1
            else:
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
                                n+=1
                                foundone=1
                                everfound=1
                    if everfound and not foundone:break
                                
            #r=re.compile(pat)
            #for file in files:
            #    if r.search(file):
            #        self.sourceListbox.Append(file)
            #        n+=1
        if self.imageInfo != ext:
            self.retrieveImageInfo(files[0])
            self.imageInfo = ext
        self.setNumberOfImages(n)
            
    def retrieveImageInfo(self,filename):
        """
        Created: 21.04.2005, KP
        Description: A method that reads information from an image
        """        
        ext=filename.split(".")[-1].lower()
        if not ext in self.extMapping:
            Dialogs.showerror(self,"Unrecognized file format for file %s"%filename,"Unrecognized file")
            return
        rdr = "vtk.vtk%sReader()"%self.extMapping[ext]
        
        rdr=eval(rdr)
        if ext =="bmp":
            rdr.Allow8BitBMPOn()
        
        rdr.SetFileName(filename)
        rdr.Update()
        data=rdr.GetOutput()
        self.x,self.y,self.z=data.GetDimensions()
        self.dimensionLbl.SetLabel("%d x %d"%(self.x,self.y))
        if self.z>1:
            self.depthEdit.SetValue("%d"%self.z)
        
 
