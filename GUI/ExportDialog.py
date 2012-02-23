#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ExportDialog.py
 Project: BioImageXD

 Description:

 A dialog for exporting data

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

import uuid
import Logging
import os.path
import re
import UIElements
import vtk
import vtkbxd
import wx
import wx.lib.filebrowsebutton as filebrowse
import Configuration

class ExportDialog(wx.Dialog):
	"""
	A dialog for export dataset to various formats
	"""
	def __init__(self, parent, dataUnits, imageMode = 1):
		"""
		Initialize the dialog
		"""    
		wx.Dialog.__init__(self, parent, -1, 'Export Data')
		
		self.conf = Configuration.getConfiguration()       

		self.dataUnit = dataUnits[0]
		self.dataUnits = dataUnits
		x, y, z = self.dataUnit.getDimensions()
		self.x, self.y, self.z = x, y, z
		self.t = self.dataUnit.getNumberOfTimepoints()
		self.c = len(dataUnits)
		self.imageMode = imageMode
		if self.imageMode == 1:
			self.imageAmnt = z * self.t * self.c
		else:
			self.imageAmnt = self.t * self.c

		self.sizer = wx.GridBagSizer(5, 5)
		self.createImageExport()
		self.sizer.Add(self.imagePanel, (0, 0), flag = wx.EXPAND | wx.ALL)
		self.btnsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		
		self.sizer.Add(self.btnsizer, (5, 0), flag = wx.EXPAND | wx.RIGHT | wx.LEFT)
		wx.EVT_BUTTON(self, wx.ID_OK, self.onOkButton)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		self.updateListOfImages()
		
		
	def onOkButton(self, event):
		"""
		Executes the procedure
		"""            
		if self.imageMode == 1:
			self.writeImages()
		else:
			self.writeDatasets()
		self.Close()
		
	def writeImages(self):
		"""
		Writes out the images
		"""
		dirname = self.browsedir.GetValue()
		pattern = self.patternEdit.GetValue()
		n = pattern.count("%d")        
		ext = self.outputFormat.menu.GetString(self.outputFormat.menu.GetSelection()).lower()
		writer = "vtk.vtk%sWriter()" % (ext.upper())
		writer = eval(writer)
		if ext == "tiff":
			writer.SetCompressionToNoCompression()
		
		prefix = dirname + os.path.sep
		self.dlg = wx.ProgressDialog("Writing", "Writing image %d / %d" % (0, 0),
		maximum = self.imageAmnt, parent = self, style = wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
		
		if n == 0:
			pattern = pattern + "%d"
			n = 1
		Logging.info("Prefix =", prefix, "pattern =", pattern, kw = "io")
		writer.SetFilePrefix(prefix)

		# Do vertical flip to each image
		flip = vtk.vtkImageFlip()
		flip.SetFilteredAxis(1)
		for c in range(self.c):
			for t in range(self.t):
				Logging.info("Writing timepoint %d" % t, kw = "io")
				# If the numbering uses two separate numbers (one for time point, one for slice)
				# then we modify the pattern to account for the timepoint
				if n == 3:
					end = pattern.rfind("%")
					endstr = pattern[end:]
					middle = pattern.rfind("%",0,end)
					middlestr = pattern[middle:end]
					beginstr = pattern[:middle]
					currpattern = beginstr%c + middlestr%t + endstr
				elif n == 2:
					end = pattern.rfind("%")
					endstr = pattern[end:]
					beginstr = pattern[:end]
					currpattern = beginstr%t + endstr
					currpattern = "_" + currpattern
				else:
					# otherwise we put an underscore (_) in the name then later
					# on it will be renamed to the proper name and underscore
					# removed this is done so that if we write many timepoints,
					# the files can be named with the correct numbers, because
					# the image writer would otherwise write
					# every timepoint with slice numbers from 0 to z
					currpattern = "_" + pattern
				currpattern += ".%s" % ext
				currpattern = "%s" + currpattern
				Logging.info("Setting pattern %s" % currpattern, kw = "io")
				writer.SetFilePattern(currpattern)
				data = self.dataUnits[c].getTimepoint(t)
				data.SetUpdateExtent(data.GetWholeExtent())
				data.Update()
				flip.SetInput(data)
				writer.SetInput(flip.GetOutput())
				writer.SetFileDimensionality(2)

				self.dlg.Update((c+1) * (t+1) * self.z, "Writing image %d / %d" % ((c+1) * (t+1) * self.z, self.imageAmnt))

				Logging.info("Writer = ", writer, kw = "io")
				writer.Update()
				writer.Write()
				overwrite = None

				if n == 1 or n == 2:
					for z in range(self.z):
						if n == 1:
							img = prefix + "_" + pattern % z + ".%s" % ext
						else:
							img = prefix + "_" + pattern%(t,z) + ".%s" % ext

						if n == 1:
							num = c * self.t * self.z + t * self.z + z
							newname = prefix + pattern % num + ".%s" % ext
						else:
							newname = prefix + pattern%(t,z) + ".%s" % ext
						
						fileExists = os.path.exists(newname)
						if fileExists and overwrite == None:
							dlg = wx.MessageDialog(self, 
												   "A file called '%s' already exists. Overwrite?"%os.path.basename(newname),
												   "Overwrite existing file",
												   wx.YES_NO|wx.YES_DEFAULT)
							if dlg.ShowModal()==wx.ID_YES:
								overwrite=1
								os.remove(newname)
							else:
								break
						elif fileExists and overwrite == 1:
							os.remove(newname)
						os.rename(img, newname)
		
		self.dlg.Destroy()
			
	def writeDatasets(self, event = None):
		"""
		A method that writes the datasets
		"""
		dirname = self.browsedir.GetValue()
		pattern = self.patternEdit.GetValue()

		if self.imageMode == 0:
			ext = "ome.tif"
			writer = vtkbxd.vtkOMETIFFWriter()
		elif self.imageMode == 2:
			fext = self.vtkmenu.GetString(self.vtkmenu.GetSelection())		
			if fext.find("XML") != -1:
				ext = "vti"
				writer = vtk.vtkXMLImageDataWriter()
			else:
				ext = "vtk"
				writer = vtk.vtkDataSetWriter()
		else:
			return

		pattern = os.path.join(dirname,pattern) + "." + ext
		self.dlg = wx.ProgressDialog("Writing", "Writing dataset %d / %d" % (0, 0), maximum = self.imageAmnt, parent = self, style = wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)

		filenames = self.sourceListbox.GetItems()
		if len(filenames) != self.c * self.t:
			return

		if self.imageMode == 0: # vtkOMETIFFWriter specific
			writer.SetFileNamePattern(pattern)
			writer.SetTimePoints(self.t)
			writer.SetChannels(self.c)
			# Create uuids
			if self.imageAmnt > 1:
				for i in range(self.imageAmnt):
					uid = uuid.uuid4()
					writer.SetUUID(i,uid.get_urn())
			
			for c in range(self.c):
				ch_name = self.dataUnits[c].getName()
				excitation = self.dataUnits[c].getExcitationWavelength()
				emission = self.dataUnits[c].getEmissionWavelength()
				writer.SetChannelInfo(ch_name, excitation, emission)
		
		i = 0
		for c in range(self.c):
			imageName = self.dataUnits[c].getImageName()
			voxelSize = self.dataUnits[c].getVoxelSize()
			
			for t in range(self.t):
				filenm = filenames[i]
				i += 1
				self.dlg.Update(i, "Writing dataset %d / %d" % (i, self.imageAmnt))
				if self.imageMode == 0:
					writer.SetCurrentChannel(c)
					writer.SetCurrentTimePoint(t)
					writer.SetImageName(imageName)
					writer.SetXResolution(voxelSize[0] * 10**6)
					writer.SetYResolution(voxelSize[1] * 10**6)
					writer.SetZResolution(voxelSize[2] * 10**6)
				writer.SetFileName(filenm)
				data = self.dataUnits[c].getTimepoint(t)
				data.SetUpdateExtent(data.GetWholeExtent())
				data.Update()
				writer.SetInput(data)
				writer.Write()
		self.dlg.Destroy()

	def createImageExport(self):
		"""
		Creates similar parts of every export dialog
		"""
		self.imagePanel = wx.Panel(self, -1, size = (640, 480))
		self.imageSizer = wx.GridBagSizer(5, 5)
		if self.imageMode == 1:
			self.imageSourcebox = wx.StaticBox(self.imagePanel, -1, "Target for Images")
		else:
			self.imageSourcebox = wx.StaticBox(self.imagePanel, -1, "Target for Datasets")
		self.imageSourceboxsizer = wx.StaticBoxSizer(self.imageSourcebox, wx.VERTICAL)
		
		self.imageSourceboxsizer.SetMinSize((600, 100))
		
		initialDir = self.conf.getConfigItem("ExportDirectory", "Paths")
		if not initialDir:
			initialDir = "."

		if self.imageMode == 1:
			self.browsedir = filebrowse.DirBrowseButton(self.imagePanel, -1, labelText = "Image Directory: ", changeCallback = self.updateListOfImages, startDirectory = initialDir)
		else:
			self.browsedir = filebrowse.DirBrowseButton(self.imagePanel, -1, labelText = "Dataset Directory: ", changeCallback = self.updateListOfImages, startDirectory = initialDir)
			
		self.sourcesizer = wx.BoxSizer(wx.VERTICAL)
		
		self.imageSourceboxsizer.Add(self.browsedir, 0, wx.EXPAND)

		if self.c > 1:
			ptr = self.dataUnit.getImageName() + "_C%d"
		else:
			ptr = self.dataUnit.getName()

		if self.t > 1:
			ptr += "_T%d"
			
		if self.imageMode == 1 and self.z > 1:
			ptr += "_Z%d"

		self.patternEdit = wx.TextCtrl(self.imagePanel, -1, ptr, size = (300,-1), style = wx.TE_PROCESS_ENTER)
		self.patternEdit.Bind(wx.EVT_TEXT_ENTER, self.updateListOfImages)
		self.patternEdit.Bind(wx.EVT_TEXT, self.updateListOfImages)
		
		self.patternLbl = wx.StaticText(self.imagePanel, -1, "Filename Pattern: ")
		self.patternBox = wx.BoxSizer(wx.HORIZONTAL)
		self.patternBox.Add(self.patternLbl, 1)
		self.patternBox.Add(self.patternEdit, 0)
		self.sourcesizer.Add(self.patternBox)

		if self.imageMode == 1:
			self.outputFormat = UIElements.getImageFormatMenu(self.imagePanel)
			self.outputFormat.menu.SetSelection(0)
			self.outputFormat.menu.Bind(wx.EVT_CHOICE, self.updateListOfImages)
			self.sourcesizer.Add(self.outputFormat)
		elif self.imageMode == 2:
			sizer = wx.BoxSizer(wx.HORIZONTAL)
			lbl = wx.StaticText(self.imagePanel, -1, "VTK Dataset Format")
			sizer.Add(lbl)
			formats = ["XML Image Data", "VTK Image Data"]
			self.vtkmenu = wx.Choice(self.imagePanel, -1, choices = formats)
			self.vtkmenu.SetSelection(0)
			sizer.Add(self.vtkmenu)
			self.vtkmenu.Bind(wx.EVT_CHOICE, self.updateListOfImages)
			self.sourcesizer.Add(sizer)

		self.sourceListbox = wx.ListBox(self.imagePanel, -1, size = (600, 100), style = wx.LB_ALWAYS_SB | wx.LB_EXTENDED)
		if self.imageMode == 1:
			self.listlbl = wx.StaticText(self.imagePanel, -1, "List of Images:")
		else:
			self.listlbl = wx.StaticText(self.imagePanel, -1, "List of Datasets:")
		
		self.sourcesizer.Add(self.listlbl)
		self.sourcesizer.Add(self.sourceListbox)
		
		self.imageSourceboxsizer.Add(self.sourcesizer, 1, wx.EXPAND)
		
		self.imageInfoBox = wx.StaticBox(self.imagePanel, -1, "Dataset Information")
		self.imageInfoSizer = wx.StaticBoxSizer(self.imageInfoBox, wx.VERTICAL)
		
		self.infosizer = wx.GridBagSizer(5, 5)

		self.imageAmountLbl = wx.StaticText(self.imagePanel, -1, "%d" % self.imageAmnt)
		if self.imageMode == 1:
			self.nlbl = wx.StaticText(self.imagePanel, -1, "Number of Images:")
			self.dimlbl = wx.StaticText(self.imagePanel, -1, "Image Dimensions:")
		else:
			self.nlbl = wx.StaticText(self.imagePanel, -1, "Number of Datasets:")
			self.dimlbl = wx.StaticText(self.imagePanel, -1, "Dataset Dimensions:")

		if self.imageMode == 1:
			self.dimensionLbl = wx.StaticText(self.imagePanel, -1, "%d x %d" % (self.x, self.y))
			self.depthlbl = wx.StaticText(self.imagePanel, -1, "Depth of Stack:")
			self.depthLbl = wx.StaticText(self.imagePanel, -1, "%d" % self.z)
		else:
			self.dimensionLbl = wx.StaticText(self.imagePanel, -1, "%d x %d x %d" %(self.x, self.y, self.z))
		
		self.tpLbl = wx.StaticText(self.imagePanel, -1, "Number of Timepoints:")
		self.timepointLbl = wx.StaticText(self.imagePanel, -1, "%d" % self.t)

		self.cLbl = wx.StaticText(self.imagePanel, -1, "Number of Channels:")
		self.channelLbl = wx.StaticText(self.imagePanel, -1, "%d" % self.c)

		yloc = 0
		self.infosizer.Add(self.nlbl, (yloc, 0))
		self.infosizer.Add(self.imageAmountLbl, (yloc, 1), flag = wx.EXPAND | wx.ALL)
		yloc += 1
		
		self.infosizer.Add(self.dimlbl, (yloc, 0))
		self.infosizer.Add(self.dimensionLbl, (yloc, 1), flag = wx.EXPAND | wx.ALL)
		yloc += 1

		if self.imageMode == 1:
			self.infosizer.Add(self.depthlbl, (yloc, 0))
			self.infosizer.Add(self.depthLbl, (yloc, 1), flag = wx.EXPAND | wx.ALL)
			yloc += 1

		self.infosizer.Add(self.tpLbl, (yloc, 0))
		self.infosizer.Add(self.timepointLbl, (yloc, 1), flag = wx.EXPAND | wx.ALL)
		yloc += 1

		self.infosizer.Add(self.cLbl, (yloc, 0))
		self.infosizer.Add(self.channelLbl, (yloc, 1), flag = wx.EXPAND | wx.ALL)

		self.imageInfoSizer.Add(self.infosizer)
		
		self.imageSizer.Add(self.imageInfoSizer, (0, 0), flag = wx.EXPAND | wx.ALL, border = 5)
		self.imageSizer.Add(self.imageSourceboxsizer, (1, 0), flag = wx.EXPAND | wx.ALL, border = 5)
		
		self.imagePanel.SetSizer(self.imageSizer)
		self.imagePanel.SetAutoLayout(1)
		self.imageSizer.Fit(self.imagePanel)


	def sortNumerically(self, item1, item2):
		"""
		A method that compares two filenames and sorts them by the number in their filename
		"""        
		r = re.compile("[0-9]+")
		s = r.search(item1)
		s2 = r.search(item2)
		n = int(s.group(0))
		n2 = int(s2.group(0))
		return n.__cmp__(n2)
	
	def updateListOfImages(self, event = None):
		"""
		A method that updates a list of images to a listbox based on the selected input type
		"""
		dirname = self.browsedir.GetValue()
		pattern = self.patternEdit.GetValue()
		self.sourceListbox.Clear()
		lstbox = self.sourceListbox

		if self.imageMode == 1:
			ext = self.outputFormat.menu.GetString(self.outputFormat.menu.GetSelection()).lower()
		elif self.imageMode == 2:
			fext = self.vtkmenu.GetString(self.vtkmenu.GetSelection())
			if fext.find("XML") != -1:
				ext = "vti"
			else:
				ext = "vtk"
		else:
			ext = "ome.tif"

		if dirname:
			self.conf.setConfigItem("ExportDirectory", "Paths", dirname)
		self.conf.writeSettings()
		
		n = pattern.count("%")
		if n == 0 and self.imageMode == 1:
			pattern = pattern + "%d"
			n = 1
		
		# If the pattern is not proper, return
		try:
			if n == 1:
				a = pattern %0
			if n == 2:
				a = pattern %(0, 0)
			if n == 3:
				a = pattern %(0, 0, 0)
		except:
			return

		# Check pattern structure
		numPat = 0
		ptr = "("
		if self.c > 1:
			ptr += "c,"
			numPat += 1
		if self.t > 1:
			ptr += "t,"
			numPat += 1
		if self.z > 1 and self.imageMode == 1:
			ptr += "z"
			numPat += 1
		ptr += ")"
		
		if n == 1:
			for i in range(1,self.imageAmnt+1):
				filenm = os.path.join(dirname, pattern%i) + ".%s"%ext
				lstbox.Append(filenm)
		elif numPat == n:
			if self.imageMode == 1:
				slices = self.z + 1
			else:
				slices = 2

			for c in range(1,self.c+1):
				for t in range(1,self.t+1):
					for z in range(1,slices):
						idx = eval(ptr)
						filenm = os.path.join(dirname, pattern%idx) + ".%s" % ext
						lstbox.Append(filenm)
