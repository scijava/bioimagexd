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

FILES_FOLLOWING_PATTERN = 0
ALL_FILES_IN_DIRECTORY  = 1

import scripting
from lib.DataSource.BXDDataWriter import BXDDataWriter
from lib.DataSource.BXCDataWriter import BXCDataWriter
import Configuration
from lib.DataUnit.DataUnit import DataUnit
from lib.DataUnit.DataUnitSetting import DataUnitSettings
import wx.lib.filebrowsebutton as filebrowse
import glob
import GUI.ColorTransferEditor
import GUI.Dialogs
import Logging
import os.path
from GUI.PreviewFrame.PreviewFrame import PreviewFrame
import re
import vtk
import wx

import lib.messenger

class ImportDialog(wx.Dialog):
	"""
	Created: 16.03.2005, KP
	Description: A dialog for importing various forms of data to create a .bxd file
	"""
	def __init__(self, parent, imageMode = 1):
		"""
		Created: 17.03.2005, KP
		Description: Initialize the dialog
		"""    
		scripting.registerDialog("import", self)
		self.dataUnit = DataUnit()

		self.dataSource = parent.typeToSource["filelist"]()
		
		lib.messenger.connect(self.dataSource, "upate_dimensions", self.updateImageInfo)
		self.dataUnit.setDataSource(self.dataSource)
		self.settings = DataUnitSettings()
		self.settings.set("Type", "NOOP")
		
		self.ctfInitialized = 0
		
		wx.Dialog.__init__(self, parent, -1, 'Import image stack', style = wx.RESIZE_BORDER | wx.CAPTION)
		self.inputFile = ""
		self.importDirectory = ""

		self.numRE = re.compile("[0-9]+")

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.createImageImport()
		self.imageInfo = None
		self.resultDataset = None
		
		self.btnsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)

		self.sizer.Add(self.imageSizer, 1, wx.EXPAND)
		self.sizer.Add(self.btnsizer, 0, wx.EXPAND)
		wx.EVT_BUTTON(self, wx.ID_OK, self.onOkButton)
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
		if not os.path.exists(filename):
			GUI.Dialogs.showerror(self, "The specified file (%s) does not exist."%os.path.basename(filename), "File does not exist")
			return
						
		self.inputFile = filename
		self.browsedir.SetValue(filename)
		
	def getDatasetName(self):
		"""
		Created: 6.11.2006, KP
		Description: Return the name of the resultant dataset
		"""
		return self.resultDataset
		
	def onOkButton(self, event):
		"""
		Created: 21.04.2005, KP
		Description: Executes the procedure
		"""
		if not self.spacing:
			GUI.Dialogs.showerror(self, "Please define the size of the voxels in the dataset", "No voxel size defined")
			return
			
		name = self.nameEdit.GetValue()
		name = name.replace(" ", "_")
		filename = GUI.Dialogs.askSaveAsFileName(self, "Save imported dataset as", "%s.bxd" \
													% name, "BioImageXD Dataset (*.bxd)|*.bxd", "import_save")
		self.Close()
		
		self.convertFiles(filename)
		scripting.unregisterDialog("import")
		self.EndModal(wx.ID_OK)

	def convertFiles(self, outname):
		"""
		Created: 21.04.2005, KP
		Description: Method that reads the files that user has selected
		"""          
		idxs = self.sourceListbox.GetSelections()
		files = []
		
		if not idxs:
			n = self.sourceListbox.GetCount()
			idxs = range(n)
		for i in idxs:
			files.append(self.sourceListbox.GetString(i))
		try:
			self.dataSource.setFilenames(files)
		except Logging.GUIError, ex:
			ex.show()
			self.Close()
			return
		bxdwriter = BXDDataWriter(outname)
		self.resultDataset = bxdwriter.getFilename()
		print "Result dataset=", self.resultDataset

		bxcfilename = bxdwriter.getBXCFileName(outname)
		self.writer = BXCDataWriter(bxcfilename)
		bxdwriter.addChannelWriter(self.writer)
		bxdwriter.write()
		self.tot = self.dataSource.getDataSetCount()
		self.dlg = wx.ProgressDialog("Importing", "Reading dataset %d / %d" \
										% (0, 0), maximum = 2 * self.tot, parent = self,
		style = wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)   
		
		self.writeDataUnitFile()
		self.dlg.Destroy()
		
	def writeDataUnitFile(self):
		"""
		Created: 25.04.2005, KP
		Description: Writes a .bxd file
		""" 
		settings = self.dataUnit.getSettings()

		Logging.info("Spacing for dataset=", self.spacing, kw = "io")
		settings.set("Spacing", self.spacing)
		x, y, z = self.voxelSize
		x /= 1000000.0
		y /= 1000000.0
		z /= 1000000.0
		Logging.info("Writing voxel size as ", x, y, z, kw = "io")
		settings.set("VoxelSize", (x, y, z))

		self.dimensions = (self.x, self.y, self.x) = self.dataSource.getDimensions()
		Logging.info("Writing dimensions as ", self.dimensions, kw = "io")

		settings.set("Dimensions", self.dimensions)
		name = self.nameEdit.GetValue()
		settings.set("Name", name)
		
		parser = self.writer.getParser()
		settings.writeTo(parser)
		i = 0
		for i in range(0, self.tot):
			print "Getting dataset",i
			image = self.dataSource.getDataSet(i, raw = 1)
			image.SetSpacing(self.spacing)
			image.SetOrigin(0, 0, 0)
			self.writer.addImageData(image)
			self.writer.sync()
			self.dlg.Update(self.tot + i, "Writing dataset %d / %d" % (i + 1, self.tot))
			i = i + 1
		self.writer.write()
			
			
	def createImageImport(self):
		"""
		Created: 17.03.2005, KP
		Description: Creates a panel for importing of images as slices of a volume
		"""            
		self.imageSizer = wx.GridBagSizer(5, 5)
		self.imageSourcebox = wx.StaticBox(self, -1, "Source file")
		self.imageSourceboxsizer = wx.StaticBoxSizer(self.imageSourcebox, wx.VERTICAL)
		
#        self.imageSourceboxsizer.SetMinSize((600,100))
		
		conf = Configuration.getConfiguration()       
		initialDir = conf.getConfigItem("ImportDirectory", "Paths")
		if not initialDir:
			initialDir = "."
		
		mask = "Supported image files|*.jpg;*.png;*.tif;*.tiff;*.jpeg;*.vtk;*.vti;*.bmp"
		self.browsedir = filebrowse.FileBrowseButton(self, -1, labelText = "Source Directory: ", \
														changeCallback = self.setSourceFile,
		startDirectory = initialDir, initialValue = self.inputFile, fileMask = mask)
		
		self.sourcesizer = wx.BoxSizer(wx.VERTICAL)
		
		self.sourcelbl = wx.StaticText(self, -1, "Imported dataset consists of:")
		self.choice = wx.Choice(self, \
								-1, \
								choices = ["Files following pattern", "All files in same directory"], \
								size = (200, -1))
		self.choice.SetSelection(1)
		self.choice.Bind(wx.EVT_CHOICE, self.setInputType)
		
		self.patternEdit = wx.TextCtrl(self, -1, "", style = wx.TE_PROCESS_ENTER, size = (400, -1))
		
		self.patternEdit.Enable(0)
		
		self.patternUpdateBtn = wx.Button(self, -1, "Update")
		self.patternUpdateBtn.Bind(wx.EVT_BUTTON, self.updateListOfImages)
		
		self.patternLbl = wx.StaticText(self, -1, "Pattern:")
		self.patternBox = wx.BoxSizer(wx.HORIZONTAL)
		self.patternBox.Add(self.patternLbl)
		self.patternBox.Add(self.patternEdit)
		self.patternBox.Add(self.patternUpdateBtn)
		
		self.sourceListbox = wx.ListBox(self, -1, size = (600, 100), \
										style = wx.LB_ALWAYS_SB | wx.LB_HSCROLL | wx.LB_EXTENDED)
		self.sourceListbox.Bind(wx.EVT_LISTBOX, self.updateSelection)
		
		self.imageSourceboxsizer.Add(self.browsedir, 0, wx.EXPAND)
		self.sourcesizer.Add(self.sourcelbl, 0, wx.EXPAND)
		self.sourcesizer.Add(self.choice, 0)
		self.sourcesizer.Add(self.patternBox, 0, wx.EXPAND)

		self.listlbl = wx.StaticText(self, -1, "List of Input Data:")
		self.sourcesizer.Add(self.listlbl)
		self.sourcesizer.Add(self.sourceListbox, 1, wx.EXPAND)
		
		self.imageSourceboxsizer.Add(self.sourcesizer, 1, wx.EXPAND)
		
		
		self.previewBox = wx.StaticBox(self, -1, "Volume preview")
		self.imageInfoBox = wx.StaticBox(self, -1, "Volume Information")
		self.imageInfoSizer = wx.StaticBoxSizer(self.imageInfoBox, wx.VERTICAL)
		
		previewBox = wx.BoxSizer(wx.VERTICAL)
		self.zslider = wx.Slider(self, value = 1, minValue = 1, maxValue = 1, \
									style = wx.SL_VERTICAL | wx.SL_LABELS | wx.SL_AUTOTICKS)
		self.timeslider = wx.Slider(self, value = 1, minValue = 1, maxValue = 1, \
									style = wx.SL_LABELS | wx.SL_AUTOTICKS)

		self.zslider.Bind(wx.EVT_SCROLL, self.onChangeZSlice)
		self.timeslider.Bind(wx.EVT_SCROLL, self.onChangeTimepoint)
				
		self.preview = PreviewFrame(self, previewsize = (384, 384), scrollbars = False)
#		self.preview.setPreviewType("")
		self.preview.disableAnnotations()
		
		previewBox.Add(self.preview)
		previewBox.Add(self.timeslider, 1, wx.EXPAND)
		
		
		self.previewSizer = wx.StaticBoxSizer(self.previewBox, wx.HORIZONTAL)
		self.previewSizer.Add(previewBox)
		self.previewSizer.Add(self.zslider, 1, wx.EXPAND)        
	  
		self.infosizer = wx.GridBagSizer(5, 5)

		self.nameLbl = wx.StaticText(self, -1, "Dataset name:")
		self.nameEdit = wx.TextCtrl(self, -1, "", size = (220, -1))

		self.nlbl = wx.StaticText(self, -1, "Number of datasets:")
		self.imageAmountLbl = wx.StaticText(self, -1, "1")
 
		
		self.dimlbl = wx.StaticText(self, -1, "Dimension of single slice:")
		self.dimensionLbl = wx.StaticText(self, -1, "")
	
		
		self.depthlbl = wx.StaticText(self, -1, "Depth of Stack:")
		self.depthEdit = wx.TextCtrl(self, -1, "1", style = wx.TE_PROCESS_ENTER)
#        self.depthEdit.Bind(wx.EVT_TEXT,self.setNumberOfImages)
		self.depthEdit.Bind(wx.EVT_TEXT_ENTER, self.setNumberOfImages)
		self.depthEdit.Bind(wx.EVT_KILL_FOCUS, self.setNumberOfImages)
		

		self.tpLbl = wx.StaticText(self, -1, "Number of Timepoints:")
		#self.timepointLbl=wx.StaticText(self,-1,"1")
		self.timepointEdit = wx.TextCtrl(self, -1, "1", style = wx.TE_PROCESS_ENTER)
		self.timepointEdit.Bind(wx.EVT_TEXT, self.setNumberOfTimepoints)
		self.timepointEdit.Bind(wx.EVT_TEXT_ENTER, self.setNumberOfTimepoints)
		self.timepointEdit.Bind(wx.EVT_KILL_FOCUS, self.setNumberOfTimepoints)

		
		self.voxelSizeLbl = wx.StaticText(self, -1, u"Voxel size")
		#self.voxelSizeEdit=wx.TextCtrl(self,-1,"0, 0, 0")
		#self.voxelSizeEdit = masked.TextCtrl(self,-1,u"",
		#mask = u"#{3}.#{4} \u03BCm x #{3}.#{4}\u03BCm x #{3}.#{4}\u03BCm",
		#formatcodes="F-_.")
		box = wx.BoxSizer(wx.HORIZONTAL)
		self.voxelX = wx.TextCtrl(self, -1, "1.0", size = (50, -1))
		self.voxelY = wx.TextCtrl(self, -1, "1.0", size = (50, -1))
		self.voxelZ = wx.TextCtrl(self, -1, "1.0", size = (50, -1))
		
		self.voxelX.Bind(wx.EVT_TEXT, self.onUpdateVoxelSize)
		self.voxelZ.Bind(wx.EVT_TEXT, self.onUpdateVoxelSize)
		self.voxelY.Bind(wx.EVT_TEXT, self.onUpdateVoxelSize)

		self.lblX = wx.StaticText(self, -1, u"\u03BCm x")
		self.lblY = wx.StaticText(self, -1, u"\u03BCm x")
		self.lblZ = wx.StaticText(self, -1, u"\u03BCm")
		box.Add(self.voxelX)
		box.Add(self.lblX)
		box.Add(self.voxelY)
		box.Add(self.lblY)
		box.Add(self.voxelZ)
		box.Add(self.lblZ)

		self.spcLbl = wx.StaticText(self, -1, "Dataset Spacing:")
		self.spacingLbl = wx.StaticText(self, -1, "0.00 x 0.00 x 0.00")
		
		n = 0
		msglbl = wx.StaticText(self, -1,
"""You are opening images from which we cannot read certain pieces of information,
such as voxel sizing and number of slices in a single timepoint. This information 
is important for the correct visualization and processing of the images. Please 
enter the information below.""")
		self.infosizer.Add(msglbl, (n, 0), span = (1, 2))
		n += 1
	  
		self.infosizer.Add(self.nameLbl, (n, 0))
		self.infosizer.Add(self.nameEdit, (n, 1), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		n += 1
		self.infosizer.Add(self.dimlbl, (n, 0))
		self.infosizer.Add(self.dimensionLbl, (n, 1), flag = wx.EXPAND | wx.ALL)
		n += 1
		self.infosizer.Add(self.nlbl, (n, 0))
		self.infosizer.Add(self.imageAmountLbl, (n, 1), flag = wx.EXPAND | wx.ALL)
		n += 1
		self.infosizer.Add(self.tpLbl, (n, 0))
		self.infosizer.Add(self.timepointEdit, (n, 1), flag = wx.EXPAND | wx.ALL)
		n += 1
		self.infosizer.Add(self.voxelSizeLbl, (n, 0))
		#self.infosizer.Add(self.voxelSizeEdit,(n,1),flag=wx.EXPAND|wx.ALL)
		self.infosizer.Add(box, (n, 1), flag = wx.EXPAND | wx.ALL, span = (1, 2))
		n += 1
		self.infosizer.Add(self.spcLbl, (n, 0))
		self.infosizer.Add(self.spacingLbl, (n, 1))
		n += 1
		self.infosizer.Add(self.depthlbl, (n, 0))
		self.infosizer.Add(self.depthEdit, (n, 1), flag = wx.EXPAND | wx.ALL)
		n += 1
		
		self.colorBtn = GUI.ColorTransferEditor.CTFButton(self)
		
		self.infosizer.Add(self.colorBtn, (n, 0), span = (1, 2))
		n += 1
		self.updateBtn = wx.Button(self, -1, "Update preview")
		
		self.infosizer.Add(self.updateBtn, (n, 0), span = (1, 2))
		
		self.updateBtn.Bind(wx.EVT_BUTTON, self.onUpdatePreview)
		
		self.imageInfoSizer.Add(self.infosizer, 1, wx.EXPAND | wx.ALL)
		
		
		self.imageSizer.Add(self.imageSourceboxsizer, (0, 0), flag = wx.EXPAND | wx.ALL, border = 5, span = (1, 2) )
		self.imageSizer.Add(self.imageInfoSizer, (1, 0), flag = wx.EXPAND | wx.ALL, border = 5)
		self.imageSizer.Add(self.previewSizer, (1, 1), border = 5)
		
		if self.inputFile:
			self.browsedir.SetValue(self.inputFile)
			
	def onUpdatePreview(self, event = None):
		"""
		Created: 04.07.2007, KP
		Description: Update the preview based on the user input
		"""
		try:
			slices = int(float(self.depthEdit.GetValue()))
		except:
			GUI.Dialogs.showerror(self, "Could not get the number of slices", \
									"Malformed number of slices per timepoint")
			return
		print "Setting slices per timepoint to ", slices
		self.dataSource.setSlicesPerTimepoint(slices)
		currentZ = self.zslider.GetValue()
		self.zslider.SetRange(1, slices)
		
		if currentZ < 1:
			currentZ = 1
		if currentZ > slices:
			currentZ = slices
		self.zslider.SetValue(currentZ)
		self.updateSelection(None, updatePreview = 1)
		

	def onChangeZSlice(self, event):
		"""
		Created: 07.05.2007, KP
		Description: Set the zslice displayed in the preview
		"""             
		assert self.zslider.GetValue() > 0, "Cannot set negative slide"
		self.preview.setZSlice(self.zslider.GetValue() - 1)
		print "Setting slice to ",self.zslider.GetValue()-1
		self.preview.updatePreview()
		
	def onChangeTimepoint(self, event):
		"""
		Created: 07.05.2007, KP
		Description: Set the timepoint displayed in the preview
		"""
		assert self.timeslider.GetValue() > 0, "Cannot set negative timepoint"
		self.preview.setTimepoint(self.timeslider.GetValue() - 1)
		self.preview.updatePreview()
		
	def onUpdateVoxelSize(self, filename):
		"""
		Created: 21.04.2005, KP
		Description: A method to update the spacing depending on the voxel size
		"""                       
		try:
			vx = float(self.voxelX.GetValue())
			vy = float(self.voxelY.GetValue())
			vz = float(self.voxelZ.GetValue())
		except:
			GUI.Dialogs.showerror(self, "Bad voxel size", "All voxel sizes were not valid.")
			return
		Logging.info("Voxel sizes = ", vx, vy, vz, kw = "io")
		self.voxelSize = (vx, vy, vz)
		self.spacing = (1.0, vy / vx, vz / vx)
		self.dataSource.setVoxelSize(self.voxelSize)
		Logging.info("Setting spacing to ", self.spacing, kw = "io")
		sx, sy, sz = self.spacing
		self.spacingLbl.SetLabel("%.2f x %.2f x %.2f" % (sx, sy, sz))
 
 	def getPatternFromFilename(self, filename):
 		"""
 		Created: 22.10.2007, KP
 		Description: convert a filename into a pattern that matches the filename
 		"""
		r = re.compile("z[0-9]+", re.IGNORECASE)
		ret = filename
		if not r.search(filename):
			r = re.compile("[0-9]+")
			items = r.findall(filename)
			n = len(items[-1])
			s = "%%.%dd" % n
		else:
			items = r.findall(filename)
			n = len(items[-1])
			firstLetter = items[0][0]                       
			s = "%s%%.%dd" % (firstLetter, n - 1)       
		if items:
			i = filename.rfind(items[-1])
			ret = filename[:i] + s + filename[i + n:]
		return ret
 
	def setInputType(self, event):
		"""
		Created: 17.03.2005, KP
		Description: A method called when the input type is changed
		"""        
		self.patternEdit.Enable(self.choice.GetSelection() == 0)
	 
	def updateSelection(self, event, updatePreview = 0):
		"""
		Created: 17.03.2005, KP
		Description: This method is called when user selects items in the listbox
		"""   
		# Disable the feature of selecting the files for now
		return
		idxs = self.sourceListbox.GetSelections()
		files = []
		
		if not idxs:
			n = self.sourceListbox.GetCount()
			idxs = range(n)
		for i in idxs:
			files.append(self.sourceListbox.GetString(i))
		if updatePreview:
			try:
				self.dataSource.setFilenames(files)
			except Logging.GUIError, ex:
				ex.show()
				self.sourceListbox.Clear()
				self.setNumberOfImages(0)
				return
#		if not self.sourceListBox.GetSelections():	20.7.07, MB. Only used here
#			n = self.sourceListBox.GetCount()
#		else:
#			n = len(self.sourceListBox.GetSelections())
#	
#		self.setNumberOfImages(n)
		
	def setNumberOfTimepoints(self, evt):
		"""
		Created: 07.05.2007, KP
		Description: set the number of timepoints, and adjust the number of slices per timepoint accordingly
		"""
		n = int(float(self.timepointEdit.GetValue()))
		currentTime = self.timepointEdit.GetValue()
		self.timeslider.SetRange(1, n)
		if currentTime < 1:
			currentTime = 1
		if currentTime > n:
			currentTime = n
		self.timeslider.SetValue(currentTime)

		totalAmnt = int(self.imageAmountLbl.GetLabel())
		if n and totalAmnt:
			slices = float(totalAmnt) / n
			if self.dataSource.is3DImage():
				x, y, slices = self.dataUnit.getDimensions()
							
			self.depthEdit.SetValue("%d" % slices)
#            self.dataSource.setSlicesPerTimepoint(slices)
#            self.zslider.SetRange(1,slices)
		
		
	def setNumberOfImages(self, n = -1):
		"""
		Created: 17.03.2005, KP
		Description: Sets the number of images we're reading
		"""
		Logging.backtrace()
		if type(n) != type(0):
			n = int(self.imageAmountLbl.GetLabel())
		Logging.info("n=", n, kw = "io")
		self.imageAmountLbl.SetLabel("%d" % n)#"
		
		val = self.depthEdit.GetValue()
		try:
			if not self.dataSource.is3DImage():
				val = int(val)
				print "Setting number of timepoints to ", n, "/", val
				tps = float(n) / val
			else:
				tps = n
			self.timepointEdit.SetValue("%d" % tps)
			currentTime = self.timeslider.GetValue()
			self.timeslider.SetRange(1, tps)
			if currentTime < 1:
				currentTime = 1
			if currentTime > tps:
				currentTime = tps
		except:
			pass
				
	
	def sortNumerically(self, item1, item2):
		"""
		Created: 17.03.2005, KP
		Description: A method that compares two filenames and sorts them by the number in their filename
		"""        
		r = self.numRE
		s = r.findall(item1)
		s2 = r.findall(item2)
		if len(s) != len(s2):
			return len(s).__cmp__(len(s2))
		if len(s) == 1:
			n = int(s[0])
			n2 = int(s2[0])
			return n.__cmp__(n2)
		else:
			for i in range(len(s)):
				i1 = int(s[i])
				i2 = int(s2[i])
				if len(s[i]) < len(s2[i]):
					return - 1
				c = i1.__cmp__(i2)
				if c != 0:
					return c
		return cmp(item1, item2)
		
	def loadAllFilesBasedOnFile(self, filename):
		"""
		Created: 22.10.2007, KP
		Description: load all files from a directory based on a given filename
		"""
		ext = filename.split(".")[-1]
		dirn = os.path.dirname(filename)
		pat = dirn + os.path.sep + "*.%s" % ext
		fail = 0
		files = glob.glob(pat)
		files.sort(self.sortNumerically)
		
		print "Checking ",files
		if not self.dataSource.checkImageDimensions(files):
			GUI.Dialogs.showmessage(self, \
									 "Some of the selected images have differing dimensions. \
										Therefore it is not possible to use the \"All files in directory\" selection.",
										"Images have differing dimensions",)
			self.choice.SetSelection(FILES_FOLLOWING_PATTERN)
			return		

		self.sourceListbox.InsertItems(files, 0)
		n = len(files)
		print "Setting number of images to ",n
		self.setNumberOfImages(n)
		try:
			self.dataSource.setFilenames(files)
		except Logging.GUIError, ex:
			ex.show()
			self.sourceListbox.Clear()
			return
		
	def matchSingleDigitPattern(self, fileList, pattern, startFrom, endTo):
		"""
		Created: 22.10.2007, KP
		Description: find files following given numbering pattern, having numbers in certain range
		"""
		print "trying range", startFrom,"-", endTo, "pattern=", pattern
		matches = []
		for i in range(startFrom, endTo):
			try:
				filename = pattern % i
			except:
				return []
			for file in fileList:
				if file.find(filename) != -1:
					matches.append(file)
		return matches
		
	def matchDoubleDigitPattern(self, fileList, pattern, fileCount):
		"""
		Created: 22.10.2007, KP
		Description: find files following given numbering pattern with two different numbers, from a given amount of files
		"""
		matches = []
		everfound = 0
		for i in range(fileCount):
			foundone = 0
			for j in range(fileCount):
				try:
					filename = pattern % (i, j)
				except:
					return
				for file in files:
					if file.find(filename) != -1:
						matches.append(file)
						n += 1
						foundone = 1
						everfound = 1
			if everfound and not foundone:
				break
		return matches
		
	def setSourceFile(self, event = None):
		"""
		Created: 17.03.2005, KP
		Description: Set the file used to determine which images to import
		"""       
		filename = self.browsedir.GetValue()

		if not filename:
			return

		self.importDirectory = os.path.dirname(filename)
		self.fileExtension = filename.split(".")[-1]
		
		# Store the directory where files were last imported from for later use
		conf = Configuration.getConfiguration()
		conf.setConfigItem("ImportDirectory", "Paths", self.importDirectory)
		conf.writeSettings()
		
		
		pattern = self.getPatternFromFilename(os.path.basename(filename))
		self.patternEdit.SetValue(pattern)
		self.updateListOfImages()
		
	def updateListOfImages(self, event = None):
		"""
		Created: 23.10.2007, KP
		Description: update the list of images based on the selected method (all files in directory, files following pattern)
		"""
		# clear the box with filenames since we're going to repopulate it		
		self.sourceListbox.Clear()
		
		# If the user has selected to load all files in the directory, then 
		# handle that case
		if self.choice.GetSelection() == ALL_FILES_IN_DIRECTORY:
			filename = self.browsedir.GetValue()
			if filename:
				self.loadAllFilesBasedOnFile(filename)
		else:
			self.loadFilesBasedOnPattern()
		self.updateImageInfo()
		self.preview.setDataUnit(self.dataUnit)
		self.preview.zoomToFit()
		self.preview.updatePreview()
	
	def loadFilesBasedOnPattern(self):
		"""
		Created: 23.10.2007, KP
		Description: update the file list based on a pattern modified by user, or calculated from file name
		"""
		pattern = self.patternEdit.GetValue()
		# First see that we find files using the extension in the pattern
		ext = pattern.split(".")[-1]
		if not glob.glob(os.path.join(self.importDirectory, "*.%s"%ext)):
			# if no files are found using that extension, then use the one taken from the initial file
			ext = self.fileExtension
			
		pat = self.importDirectory + os.path.sep + "*.%s" % ext
		files = glob.glob(pat)
		files.sort(self.sortNumerically)
		
		try:
			r = re.compile("[0-9]*")
			startfrom = min(map(int, r.findall(files[0])))
		except:
			startfrom = 0
		print "Starting from ", startfrom
		n = 0
		filecount = len(files)
		nformat = pattern.count("%")        
		# If we're using all files in directory, just add them to the list
		# Also, if there are no format specifiers (%) in the pattern, then
		# just give the whole list
		if nformat == 0:
			self.sourceListbox.InsertItems(files, 0)
			n = len(files)
			pat = ""
			try:
				self.dataSource.setFilenames(files)
			except Logging.GUIError, ex:
				ex.show()
				self.sourceListbox.Clear()
				return
		# If there is one specifier, then try to find files that correspond to that
		if nformat == 1:
			filelist = self.matchSingleDigitPattern(files, pattern, startfrom,startfrom + filecount + 1)
		if nformat == 2:
			filelist = self.matchDoubleDigitPattern(files, pattern, filecount)
		for file in filelist:
			self.sourceListbox.Append(file)
		try:
			self.dataSource.setFilenames(filelist)                                
		except Logging.GUIError, ex:
			ex.show()
			self.sourceListbox.Clear()
			return
		n = len(filelist)
		print "Setting number of images to ",n
		self.setNumberOfImages(n)
		#if self.imageInfo != ext:
		#	self.retrieveImageInfo()
		#	self.imageInfo = ext


			
	def updateImageInfo(self, obj = None, event = ""):
		"""
		Created: 21.04.2005, KP
		Description: A method that reads information from an image
		"""                
		print "Getting dimensions..."
		self.dimensions = (self.x, self.y, self.z) = self.dataSource.getDimensions()
		print "Got dims", self.dimensions
		self.dimensionLbl.SetLabel("%d x %d" % self.dimensions[0:2])
		self.depthEdit.SetValue("%d" % self.dimensions[2])
		currentZ = self.zslider.GetValue()
		
		self.zslider.SetRange(1, self.dimensions[2]) 
		if currentZ < 1:
			currentZ = 1
		if currentZ > self.z:
			currentZ = self.z
		self.zslider.SetValue(currentZ)

		if not self.ctfInitialized:
			x0, x1 = self.dataSource.getScalarRange()
			bd = self.dataSource.getSingleComponentBitDepth()
			self.ctf = vtk.vtkColorTransferFunction()
			self.ctf.AddRGBPoint(0, 0, 0, 0)
			self.ctf.AddRGBPoint((2 ** bd) - 1, 0, 1, 0)
			self.colorBtn.setColorTransferFunction(self.ctf)
			self.dataSource.setColorTransferFunction(self.ctf)
			self.settings.set("ColorTransferFunction", self.ctf)
			self.ctfInitialized = 1
			self.dataUnit.setSettings(self.settings)
