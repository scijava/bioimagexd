#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ExportDialog.py
 Project: BioImageXD
 Created: 20.03.2005, KP

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

#import glob
#import sys

import Logging
import os.path
import re
import UIElements
import vtk
import wx
import  wx.lib.filebrowsebutton as filebrowse

class ExportDialog(wx.Dialog):
	"""
	Created: 20.03.2005, KP
	Description: A dialog for export dataset to various formats
	"""
	def __init__(self, parent, dataUnit, imageMode = 1):
		"""
		Created: 17.03.2005, KP
		Description: Initialize the dialog
		"""    
		wx.Dialog.__init__(self, parent, -1, 'Export Data')
		
		self.dataUnit = dataUnit
		x, y, z = dataUnit.getDimensions()
		self.x, self.y, self.z = x, y, z
		self.n = dataUnit.getNumberOfTimepoints()
		self.imageAmnt = z * self.n
		self.sizer = wx.GridBagSizer()
#        self.notebook = wx.Notebook(self,-1)
#        self.sizer.Add(self.notebook,(0,0),flag=wx.EXPAND|wx.ALL)
		if imageMode == 1:
			self.createImageExport()
			self.sizer.Add(self.imagePanel, (0, 0), flag = wx.EXPAND | wx.ALL)
		else:
			self.createVTIExport()
			self.sizer.Add(self.vtkPanel, (0, 0), flag = wx.EXPAND | wx.ALL)
		self.imageMode = imageMode
#        self.notebook.AddPage(self.imagePanel,"Stack of Images")
#        self.notebook.AddPage(self.vtkPanel,"VTK Dataset")
		#if not imageMode:
		#    self.notebook.SetSelection(1)

		self.btnsizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		
		self.sizer.Add(self.btnsizer, (5, 0), flag = wx.EXPAND | wx.RIGHT | wx.LEFT)
		wx.EVT_BUTTON(self, wx.ID_OK, self.onOkButton)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.sizer.Fit(self)
		self.updateListOfImages()
		
		
	def onOkButton(self, event):
		"""
		Created: 20.04.2005, KP
		Description: Executes the procedure
		"""            
		if self.imageMode == 1:
			self.writeImages()
		else:
			self.writeDatasets()
		self.Close()
		
	def writeImages(self):
		"""
		Created: 20.04.2005, KP
		Description: Writes out the images
		"""            
		dirname = self.browsedir.GetValue()
		pattern = self.patternEdit.GetValue()
		n = pattern.count("%d")        
		ext = self.outputFormat.menu.GetString(self.outputFormat.menu.GetSelection()).lower()
		writer = "vtk.vtk%sWriter()" % (ext.upper())
		writer = eval(writer)
		prefix = dirname + os.path.sep
		n = pattern.count("%")
		Logging.info("Number of images =", n, kw = "io")
		self.dlg = wx.ProgressDialog("Writing", "Writing image %d / %d" % (0, 0),
		maximum = self.imageAmnt - 1, parent = self, style = wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
		
		if n == 0:
			pattern = pattern + "%d"
			n = 1
		Logging.info("Prefix = ", prefix, "pattern = ", pattern, kw = "io")
		writer.SetFilePrefix(prefix)
		for t in range(self.n):
			Logging.info("Writing timepoint %d" % t, kw = "io")
			if n == 2:
				begin = pattern.rfind("%")
				
				beginstr = pattern[:begin - 1]
				currpattern = beginstr % t + pattern[begin - 1:]
				Logging.info("beginstr=%s, currpattern=%s" % (beginstr, beginstr % t + pattern[begin - 1:]), kw = "io")
			else:
				currpattern = "_" + pattern
			currpattern += ".%s" % ext
			currpattern = "%s" + currpattern
			Logging.info("Setting pattern %s" % currpattern, kw = "io")
			writer.SetFilePattern(currpattern)
			data = self.dataUnit.getTimepoint(t)
			data.Update()
			writer.SetInput(data)
			writer.SetFileDimensionality(2)
			self.dlg.Update(t * self.z, "Writing image %d / %d" % (t * self.z, self.imageAmnt))

			Logging.info("Writer = ", writer, kw = "io")
			writer.Write()
			if n == 1:
				for z in range(self.z):
					img = prefix + "_" + pattern % z + ".%s" % ext
					num = t * self.z + z
					newname = prefix + pattern % num + ".%s" % ext
					os.rename(img, newname)
		self.dlg.Destroy()
			
	def writeDatasets(self, event = None):
		"""
		Created: 20.04.2005, KP
		Description: A method that writes the datasets
		"""        
		dirname = self.vtkbrowsedir.GetValue()
		pattern = self.vtkpatternEdit.GetValue()
		n = pattern.count("%")
		fext = self.vtkmenu.GetString(self.vtkmenu.GetSelection())
		self.dlg = wx.ProgressDialog("Writing", "Writing dataset %d / %d" % (0, 0), maximum = self.n - 1, parent = self,
		style = wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
		if fext.find("XML") != -1:
			ext = "vti"
			writer = vtk.vtkXMLImageDataWriter()
		else:
			ext = "vtk"
			writer = vtk.vtkDataSetWriter()
		if n == 0:
			pattern = pattern + "%d"
			n = 1
		for i in range(self.n):
			try:
				file = os.path.join(dirname, pattern % i) + ".%s" % ext
			except:
				return
			self.dlg.Update(i, "Writing dataset %d / %d" % (i, self.n))
			writer.SetFileName(file)
			data = self.dataUnit.getTimepoint(i)
			writer.SetInput(data)
			writer.Write()
		self.dlg.Destroy()
		 
		
	def createImageExport(self):
		"""
		Created: 17.03.2005, KP
		Description: Creates a panel for importing of images as slices of a volume
		"""            
		self.imagePanel = wx.Panel(self, -1, size = (640, 480))
		self.imageSizer = wx.GridBagSizer(5, 5)
		self.imageSourcebox = wx.StaticBox(self.imagePanel, -1, "Target Directory for Images")
		self.imageSourceboxsizer = wx.StaticBoxSizer(self.imageSourcebox, wx.VERTICAL)
		
		self.imageSourceboxsizer.SetMinSize((600, 100))
		
		
		self.browsedir = filebrowse.DirBrowseButton(self.imagePanel, -1, labelText = "Image Directory: ", changeCallback = self.updateListOfImages)
		
		self.sourcesizer = wx.BoxSizer(wx.VERTICAL)
		
		self.imageSourceboxsizer.Add(self.browsedir, 0, wx.EXPAND)
		ptr = self.dataUnit.getName() + "_%d"
		self.patternEdit = wx.TextCtrl(self.imagePanel, -1, ptr, style = wx.TE_PROCESS_ENTER)
		self.patternEdit.Bind(wx.EVT_TEXT_ENTER, self.updateListOfImages)
		self.patternEdit.Bind(wx.EVT_TEXT, self.updateListOfImages)
		
		self.patternLbl = wx.StaticText(self.imagePanel, -1, "Filename pattern:")
		self.patternBox = wx.BoxSizer(wx.HORIZONTAL)
		self.patternBox.Add(self.patternLbl, 1)
		self.patternBox.Add(self.patternEdit, 1, wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sourcesizer.Add(self.patternBox)        
		
		self.outputFormat = UIElements.getImageFormatMenu(self.imagePanel)
		self.outputFormat.menu.SetSelection(0)
		self.outputFormat.menu.Bind(wx.EVT_CHOICE, self.updateListOfImages)
		self.sourcesizer.Add(self.outputFormat)
		
		


		self.sourceListbox = wx.ListBox(self.imagePanel, -1, size = (400, 100), style = wx.LB_ALWAYS_SB | wx.LB_EXTENDED)
		self.listlbl = wx.StaticText(self.imagePanel, -1, "List of Images:")
		self.sourcesizer.Add(self.listlbl)
		self.sourcesizer.Add(self.sourceListbox)
		
		
#        self.listlbl=wx.StaticText(self.imagePanel,-1,"Images to be written:")
#        self.sourcesizer.Add(self.listlbl)
		
		self.imageSourceboxsizer.Add(self.sourcesizer, 1, wx.EXPAND)
		
		self.imageInfoBox = wx.StaticBox(self.imagePanel, -1, "Image Information")
		self.imageInfoSizer = wx.StaticBoxSizer(self.imageInfoBox, wx.VERTICAL)
		
		self.infosizer = wx.GridBagSizer(5, 5)

		self.nlbl = wx.StaticText(self.imagePanel, -1, "Number of images:")
		self.imageAmountLbl = wx.StaticText(self.imagePanel, -1, "%d" % self.imageAmnt)
 
		
		self.dimlbl = wx.StaticText(self.imagePanel, -1, "Image dimensions:")
		self.dimensionLbl = wx.StaticText(self.imagePanel, -1, "%d x %d" % (self.x, self.y))
	
		
		self.depthlbl = wx.StaticText(self.imagePanel, -1, "Depth of Stack:")
		self.depthLbl = wx.StaticText(self.imagePanel, -1, "%d" % self.z)
		

		self.tpLbl = wx.StaticText(self.imagePanel, -1, "Number of Timepoints:")
		self.timepointLbl = wx.StaticText(self.imagePanel, -1, "%d" % self.n)
		
		
		self.infosizer.Add(self.nlbl, (0, 0))
		self.infosizer.Add(self.imageAmountLbl, (0, 1), flag = wx.EXPAND | wx.ALL)
		
		self.infosizer.Add(self.dimlbl, (1, 0))
		self.infosizer.Add(self.dimensionLbl, (1, 1), flag = wx.EXPAND | wx.ALL)
		
		
		self.infosizer.Add(self.tpLbl, (2, 0))
		self.infosizer.Add(self.timepointLbl, (2, 1), flag = wx.EXPAND | wx.ALL)

		self.infosizer.Add(self.depthlbl, (3, 0))
		self.infosizer.Add(self.depthLbl, (3, 1), flag = wx.EXPAND | wx.ALL)

		
		self.imageInfoSizer.Add(self.infosizer)
		
		self.imageSizer.Add(self.imageInfoSizer, (0, 0), flag = wx.EXPAND | wx.ALL, border = 5)
		self.imageSizer.Add(self.imageSourceboxsizer, (1, 0), flag = wx.EXPAND | wx.ALL, border = 5)
		
		self.imagePanel.SetSizer(self.imageSizer)
		self.imagePanel.SetAutoLayout(1)
		self.imageSizer.Fit(self.imagePanel)
	
	def createVTIExport(self):
		"""
		Created: 20.04.2005, KP
		Description: Creates a panel for exporting data as vtk datasets
		"""            
		self.vtkPanel = wx.Panel(self, -1, size = (640, 480))
		self.vtkSizer = wx.GridBagSizer(5, 5)
		self.vtkSourcebox = wx.StaticBox(self.vtkPanel, -1, "Source of Datasets")
		self.vtkSourceboxsizer = wx.StaticBoxSizer(self.vtkSourcebox, wx.VERTICAL)
		
		self.vtkSourceboxsizer.SetMinSize((600, 100))
		
		
		self.vtkbrowsedir = filebrowse.DirBrowseButton(self.vtkPanel, -1, labelText = "Dataset Directory: ", changeCallback = self.updateListOfDatasets)
		
		self.vtksourcesizer = wx.BoxSizer(wx.VERTICAL)
		
		self.vtkSourceboxsizer.Add(self.vtkbrowsedir, 0, wx.EXPAND)
		ptr = self.dataUnit.getName() + "_%d"
		self.vtkpatternEdit = wx.TextCtrl(self.vtkPanel, -1, ptr, style = wx.TE_PROCESS_ENTER)
		self.vtkpatternEdit.Bind(wx.EVT_TEXT_ENTER, self.updateListOfDatasets)
		self.vtkpatternEdit.Bind(wx.EVT_TEXT, self.updateListOfDatasets)
		
		self.vtkpatternLbl = wx.StaticText(self.vtkPanel, -1, "Filename pattern:")
		self.vtkpatternBox = wx.BoxSizer(wx.HORIZONTAL)
		self.vtkpatternBox.Add(self.vtkpatternLbl, 1)
		self.vtkpatternBox.Add(self.vtkpatternEdit, 1, wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.vtksourcesizer.Add(self.vtkpatternBox)        
		
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		lbl = wx.StaticText(self.vtkPanel, -1, "VTK Dataset Format")
		sizer.Add(lbl)
		formats = ["XML Image Data", "VTK Image Data"]
		self.vtkmenu = wx.Choice(self.vtkPanel, -1, choices = formats)
		self.vtkmenu.SetSelection(0)
		sizer.Add(self.vtkmenu)
		
		self.vtkmenu.Bind(wx.EVT_CHOICE, self.updateListOfDatasets)
		self.vtksourcesizer.Add(sizer)

		self.vtksourceListbox = wx.ListBox(self.vtkPanel, -1, size = (400, 100), style = wx.LB_ALWAYS_SB | wx.LB_EXTENDED)
		self.vtklistlbl = wx.StaticText(self.vtkPanel, -1, "List of Datasets:")
		self.vtksourcesizer.Add(self.vtklistlbl)
		self.vtksourcesizer.Add(self.vtksourceListbox)
		
		
		self.vtkSourceboxsizer.Add(self.vtksourcesizer, 1, wx.EXPAND)
		
		self.vtkInfoBox = wx.StaticBox(self.vtkPanel, -1, "Dataset Information")
		self.vtkInfoSizer = wx.StaticBoxSizer(self.vtkInfoBox, wx.VERTICAL)
		
		self.vtkinfosizer = wx.GridBagSizer(5, 5)
		
		self.vtkdimlbl = wx.StaticText(self.vtkPanel, -1, "Dataset dimensions:")
		self.vtkdimensionLbl = wx.StaticText(self.vtkPanel, -1, "%d x %d x %d" % (self.x, self.y, self.z))
	

		self.vtktpLbl = wx.StaticText(self.vtkPanel, -1, "Number of Timepoints:")
		self.vtktimepointLbl = wx.StaticText(self.vtkPanel, -1, "%d" % self.n)
		
		
		
		self.vtkinfosizer.Add(self.vtkdimlbl, (0, 0))
		self.vtkinfosizer.Add(self.vtkdimensionLbl, (0, 1), flag = wx.EXPAND | wx.ALL)
		
		
		self.vtkinfosizer.Add(self.vtktpLbl, (1, 0))
		self.vtkinfosizer.Add(self.vtktimepointLbl, (1, 1), flag = wx.EXPAND | wx.ALL)
		
		self.vtkInfoSizer.Add(self.vtkinfosizer)
		
		self.vtkSizer.Add(self.vtkInfoSizer, (0, 0), flag = wx.EXPAND | wx.ALL, border = 5)
		self.vtkSizer.Add(self.vtkSourceboxsizer, (1, 0), flag = wx.EXPAND | wx.ALL, border = 5)
		
		self.vtkPanel.SetSizer(self.vtkSizer)
		self.vtkPanel.SetAutoLayout(1)
		self.vtkSizer.Fit(self.vtkPanel)

	
	def sortNumerically(self, item1, item2):
		"""
		Created: 17.03.2005, KP
		Description: A method that compares two filenames and sorts them by the number in their filename
		"""        
		r = re.compile("[0-9]+")
		s = r.search(item1)
		s2 = r.search(item2)
		n = int(s.group(0))
		n2 = int(s2.group(0))
		return n.__cmp__(n2)
	
	def updateListOfImages(self, event = None):
		"""
		Created: 20.04.2005, KP
		Description: A method that updates a list of images to a listbox based on the selected input type
		"""        
		if self.imageMode == 1:
			dirname = self.browsedir.GetValue()
			pattern = self.patternEdit.GetValue()
			self.sourceListbox.Clear()
			lstbox = self.sourceListbox
			ext = self.outputFormat.menu.GetString(self.outputFormat.menu.GetSelection()).lower()    
		else:
			lstbox = self.vtksourceListbox
			dirname = self.vtkbrowsedir.GetValue()
			pattern = self.vtkpatternEdit.GetValue()
			self.vtksourceListbox.Clear()
			fext = self.vtkmenu.GetString(self.vtkmenu.GetSelection())
			if fext.find("XML") != -1:
				ext = "vti"
			else:
				ext = "vtk"
		
		n = pattern.count("%")
		
		
		if n == 0:
			pattern = pattern + "%d"
			n = 1
		# If the pattert is not proper, return
		try:
			if n == 1:
				a = pattern % 0
			if n == 2:
				a = pattern % (0, 0)
		except:
			return
		if n == 1:
			for i in range(self.imageAmnt):
				file = os.path.join(dirname, pattern % i) + ".%s" % ext
				lstbox.Append(file)
		else:
			for t in range(self.n):
				for z in range(self.z):
					file = os.path.join(dirname, pattern % (t, z)) + ".%s" % ext
					lstbox.Append(file)
					
	def updateListOfDatasets(self, event = None):
		"""
		Created: 20.04.2005, KP
		Description: A method that updates a list of datasets to a listbox based on the selected input type
		"""        
		dirname = self.vtkbrowsedir.GetValue()
		pattern = self.vtkpatternEdit.GetValue()
		self.vtksourceListbox.Clear()
		n = pattern.count("%")
		fext = self.vtkmenu.GetString(self.vtkmenu.GetSelection())
		if fext.find("XML") != -1:
			ext = "vti"
			writer = vtk.vtkXMLImageDataWriter()
		else:
			ext = "vtk"
			writer = vtk.vtkDataSetWriter()
		if n == 0:
			pattern = pattern + "%d"
			n = 1
		for i in range(self.n):
			try:
				file = os.path.join(dirname, pattern % i) + ".%s" % ext
			except:
				return
			self.vtksourceListbox.Append(file)
			
