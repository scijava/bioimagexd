# -*- coding: iso-8859-1 -*-

"""
 Unit: BatchProcessor
 Project: BioImageXD
 Created: 25.11.2007, KP
 Description:

 A batch processor tool for BioImageXD
 
 Copyright (C) 2006	 BioImageXD Project
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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import Logging
import Dialogs
import Modules.DynamicLoader

import lib.messenger
import GUI.MenuManager
import GUI.TimepointSelection

import wx
import wx.grid as gridlib
import wx.lib.mixins.listctrl as listmix
import wx.lib.pubsub as pubsub
import time
import lib.FilterBasedModule
import GUI.FilterEditor
import os
import types
import zipfile
import ConfigParser
import codecs
import csv

PROCESS_SEPARATELY = 0
PROCESS_TOGETHER = 1

class BatchAnalysis:
	"""
	Created: 25.11.2007, KP
	Description: A batch analysis model
	"""
	def __init__(self, filename = ""):
		if filename:
			self.readAnalysisFrom(filename)
		self.filename = filename
		self.dataUnit = None
		
		self.selectedVariables = {}

		self.inputDataUnits = []
		
		self.procedureLists = {}
		self.selectedList = ""
		
		self.channelGrouping = 0
		self.channelProcessing = 0
		
	def renameList(self, name, newName):
		"""
		Created: 04.12.2007, KP
		Description: rename a given procedure list
		"""
		lst = self.procedureLists.get(name, None)
		if lst:
			self.procedureLists[newName] = lst
			del self.procedureLists[name]
			self.selectedList = newName
		
	def getFileName(self):
		"""
		Created: 1.12.2007, KP
		Description: return the filename as which the analysis is being saved
		"""
		return self.filename
		
	def setChannelGrouping(self, value):
		"""
		Created: 1.12.2007, KP
		Description: select whether to group channels or not
		"""
		self.channelGrouping = value
		
	def setChannelProcessing(self, value):
		"""
		Created: 1.12.2007, KP
		Description: Set the way the channnels are processed. Valid values are:
			0	Each channel of a file is processed separately through the procedure lists
			1	All the channels in a single file are passed as input to a procedure list
		"""
		self.channelProcessing = value

	def getGroupedDataUnits(self):
		"""
		Created: 1.12.2007, KP
		Description: return the source data units grouped according to how the user has selected
					 in the GUI
		"""
		if self.channelProcessing == PROCESS_SEPARATELY:
			return [[x] for x in self.inputDataUnits]
		
		return self.getDataUnitsByFilename()
		

	def getDataUnitsByFilename(self):
		"""
		Created: 1.12.2007, KP
		Description: return the dataunits grouped by the filenames
		"""
		perFile = {}
		for dataUnit in self.inputDataUnits:
			filename = dataUnit.getFileName()
			if filename not in perFile:
				perFile[filename] = []
			perFile[filename].append(dataUnit)
			
		return perFile.values()

	def createBXDFile(self, directory, procListName, dataUnits):
		"""
		Created: 1.12.2007, KP
		Description: create a bxd file that groups the selected dataunits
		"""
		bxdFile = procListName+"_"+"_".join([x.getName() for x in dataUnits])+".bxd"
		f = open(os.path.join(directory, bxdFile), "w")
		for dataUnit in dataUnits:
			fileBase = procListName+"_"+dataUnit.getName()
			bxcFile = os.path.join(fileBase, fileBase+".bxc")
			f.write("%s\n"%bxcFile)
		f.close()
			
	def execute(self, csvfile, directory, timepoints):
		"""
		Created: 1.12.2007, KP
		Description: execute the analysis
		"""
		csvfp = codecs.open(csvfile, "wb", "latin-1")
		csvwriter = csv.writer(csvfp, dialect = "excel", delimiter = ";")
		variables = self.getAllSelectedVariables()
		varHeaders = variables.values()
		csvwriter.writerow(["Filename","Channels"]+varHeaders)
		
		for procListName in self.procedureLists.keys():
			procList = self.procedureLists[procListName]

			if self.channelProcessing == PROCESS_SEPARATELY and self.channelGrouping:
				groupedUnits = self.getDataUnitsByFilename()
				for units in groupedUnits:
					self.createBXDFile(directory, procListName, units)

			for dataUnits in self.getGroupedDataUnits():
				self.dataUnit.removeAllInputs()
				
				for du in dataUnits:
					self.dataUnit.addSourceDataUnit(du)
	
				procList.setDataUnit(self.dataUnit)
				self.dataUnit.getSettings().set("FilterList", procList)
				
				filenames = "_".join([x.getName() for x in dataUnits])
				nameBase = procListName+"_"+filenames

				self.dataUnit.getSettings().set("Name",nameBase)
				bxdFile = nameBase+".bxd"
				filename = os.path.join(directory, bxdFile)
				filename = self.dataUnit.doProcessing(filename, timepoints = timepoints)
				padding = [", ".join([os.path.basename(x.getFileName()) for x in dataUnits]), ", ".join(x.getName() for x in dataUnits)]
				self.writeResults(padding, csvwriter, procListName, procList, varHeaders)
		csvfp.close()
				
	def writeResults(self, fileNames, csvwriter, procListName, procedureList, varHeaders):
		"""
		Created: 1.12.2007, KP
		Description: write the csv results out
		"""
		selectedVars = self.getSelectedVariables(procListName)
		row=[""]*len(varHeaders)
		for var in selectedVars.keys():
			varName = selectedVars[var]
			if varName in varHeaders:
				i = varHeaders.index(varName)
				row[i] = procedureList.getResultVariable(var)
		csvwriter.writerow(fileNames + row)
		
		
	def getDataUnit(self):
		"""
		Created: 30.11.2007, KP
		Description: return the dataunit
		"""
		return self.dataUnit
		
	def saveAnalysisAs(self, filename):
		"""
		Created: 30.11.2007, KP
		Description: save the batch analysis with the given filename
		"""
		self.filename = filename
		parser = ConfigParser.RawConfigParser()
		parser.optionxform = str

		parser.add_section("BatchAnalysis")
		parser.add_section("SelectedVariables")

		nameList = self.procedureLists.keys()
		parser.set("BatchAnalysis", "ProcedureLists", str(nameList))
		for procListName in nameList:
			procList = self.procedureLists[procListName]
			parser.add_section(procListName)
			procList.writeOut(parser, prefix = "%s_"%procListName)
			
			for key,value in self.selectedVariables[procListName].items():
				parser.set(procListName, key, value)
		
		fp = open(filename,"w")
		parser.write(fp)
		fp.close()
			
	def readAnalysisFrom(self, filename):
		"""
		Created: 30.11.2007, KP
		Description: read the batch analysis from the given filename
		"""
		parser = ConfigParser.RawConfigParser()
		parser.optionxform = str
		parser.read([filename])
		self.filename = filename
		procedureLists = parser.get("BatchAnalysis", "ProcedureLists")
		if procedureLists:
			procedureLists = eval(procedureLists)
		for procListName in procedureLists:
			self.addProcedureList(procListName)
			procList = self.getProcedureList(procListName)
			
			filterList = parser.get("%s_FilterList"%procListName, "FilterList")
			filterList = eval(filterList)
			procList.populate(filterList)
			procList.readValuesFrom(parser, prefix = "%s_"%(procListName))
			
			variables = parser.options(procListName)
			selectedVariables = {}
			for var in variables:
				selectedVariables[var] = parser.get(procListName, var)
			self.selectedVariables[procListName] = selectedVariables
			
	def getFileNames(self):
		"""
		Created: 29.11.2007
		Description: return the files names loaded into the analysis
		"""
		return [x.getFileName() for x in self.inputDataUnits]
		
	def setSelectedVariables(self, procListName, variables):
		"""
		Created: 27.11.2007, KP
		Description: Set the variables that are selected for retrieval from a given procedure list
		"""
		self.selectedVariables[procListName] = variables
		
	def getProcedureListNames(self):
		"""
		Created: 30.11.2007, KP
		Description: return the names of the procedure lists
		"""
		return self.procedureLists.keys()
		
	def getAllSelectedVariables(self):
		"""
		Created: 1.12.2007, KP
		Description: return the selected variables of all procedure lists
		"""
		ret = {}
		for procListName in self.getProcedureListNames():
			ret.update(self.selectedVariables.get(procListName, {}))
		return ret
		
	def getSelectedVariables(self, procListName):
		"""
		Created: 27.11.2007, KP
		Description: Get the variables that are selected for retrieval from a given procedure list
		"""
		return self.selectedVariables.get(procListName,{})
		
	def addProcedureList(self, name):
		"""
		Created: 27.11.2007, KP
		Description: add a procedure list to the list of analyses
		"""
		filterList = lib.FilterBasedModule.FilterList()
		filterList.setDataUnit(self.dataUnit)
		self.procedureLists[name] = filterList
		
	def getProcedureList(self, name = ""):
		"""
		Created: 27.11.2007, KP
		Description: return the requested procedure list
		"""
		if not name:
			name = self.selectedList
		return self.procedureLists.get(name)
		
	def getSelectedProcedureList(self):
		"""
		Created: 27.11.2007, KP
		Description: return the name of the selected procedure list
		"""
		return self.selectedList
		
	def setSelectedProcedureList(self, name):
		"""
		Creted: 27.11.2007, KP
		Description: Set the currently selected procedure list
		"""
		self.selectedList = name
		
	def getSourceDataUnits(self):
		"""
		Created: 25.11.2007, KP
		Description: return the input data units
		"""
		return self.inputDataUnits
		
	def setInputDataUnits(self, fileList):
		"""
		Created: 25.11.2007, KP
		Description: set the input files used by this model
		"""
		pluginLoader = Modules.DynamicLoader.getPluginLoader()
		taskMod = pluginLoader.getPluginModule("Task", "Process")
		unitType = taskMod.getDataUnit()
		moduleType = pluginLoader.getPluginClass("Task","Process")
		self.dataUnit = unitType()
		
		module = moduleType()
		self.dataUnit.setModule(module)
				
		self.inputDataUnits = fileList
		groupedUnits = self.getDataUnitsByFilename()
		mostChannels = None
		chCount = 0
		for du in groupedUnits:
			if len(du)>chCount:
				chCount = len(du)
				mostChannels = du
		
		for dataUnit in mostChannels:
			print "Adding",dataUnit.getName(),"from file",dataUnit.getFileName()
			self.dataUnit.addSourceDataUnit(dataUnit)
		
		

class BatchAnalysisTable(gridlib.PyGridTableBase):
	"""
	Created: 26.11.2007, KP
	Description: a table model for a wx.lib.gridlib.Grid
	"""
	def __init__(self, analysis):
		gridlib.PyGridTableBase.__init__(self)
		self.analysis = analysis
		self.variables = []
		
	def updateGridValues(self):
		"""
		Created: 30.11.2007, KP
		Description: update the grid values
		"""
		vars = []
		for procList in self.analysis.getProcedureListNames():
			vars += [x for x in self.analysis.getSelectedVariables(procList).values()]
		self.variables = vars
		
	def GetColLabelValue(self, col):
		"""
		Created: 30.11.2007, KP
		Description: return the column label of the given column
		"""
		return "Var%d"%(col+1)
		
	def GetRowLabelValue(self, row):
		"""
		Created: 29.11.2007, KP
		Description: return the row labels of the grid, listing the file names
		"""
		fileNames = [x.getName() for x in self.analysis.getSourceDataUnits()]
		if row < len(fileNames):
			return os.path.basename(fileNames[row])
		return ""

	def GetNumberRows(self):
		"""
		Created: 30.11.2007, KP
		Description: return the number of rows the grid has
		"""
		return len(self.analysis.getSourceDataUnits())+20

	def GetNumberCols(self):
		"""
		Created: 30.11.2007, KP
		Description: return the number of cols the grid has
		"""
		if not self.variables:
			return 10
		return len(self.variables)+10

	def IsEmptyCell(self, row, col):
		return False

	def GetValue(self, row, col):
		"""
		Created: 30.11.2007, KP
		Description: Get the value of a given cell
		"""
		if row==0:
			if col<len(self.variables):
				return self.variables[col]
		return ""

	def SetValue(self, row, col, value):
		pass


class PickVariablesDialog(wx.Dialog):
	"""
	Created: 26.11.2007, KP
	Description: A dialog for picking which variables to retrieve from the procedure lists
	"""
	def __init__(
		self, parent, analysis, id = -1, title = "Select retrieved variables", size=wx.DefaultSize, pos=wx.DefaultPosition, 
		style=wx.DEFAULT_DIALOG_STYLE):
		
		wx.Dialog.__init__(self, parent, id, title, pos, size, style) 
		
		self.analysis = analysis
		
		self.sizer = wx.GridBagSizer()
		
		self.checkListCtrl = CheckListCtrl(self, -1, style = wx.LC_REPORT)
		self.sizer.Add(self.checkListCtrl, (0,0), flag = wx.EXPAND)
		self.sizer.AddGrowableRow(0)
		self.sizer.AddGrowableCol(0)
		
		btnSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		if btnSizer:
			self.sizer.Add(btnSizer, (1,0), flag = wx.EXPAND)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.populateFromAnalysis(self.analysis)
			
	def getSelectedVariables(self):
		"""
		Created: 27.11.2007, KP
		Description: get the selected variables
		"""
		ret = {}
		for i in range(self.checkListCtrl.GetItemCount()):
			if self.checkListCtrl.IsChecked(i):
				varName = self.checkListCtrl.GetItem(i,1).GetText()
				varAs = self.checkListCtrl.GetItem(i,2).GetText()
				ret[varName] = varAs
		return ret
			
	def populateFromAnalysis(self, analysis):
		"""
		Created: 27.11.2007, KP
		Description: populate the list of variables from the given analysis
		"""
		procList = analysis.getProcedureList()
		if not procList:
			Logging.info("No procedure list")
			self.Close(wx.ID_CANCEL)
			return
		filters = procList.getFilters()
		variables = []
		name = analysis.getSelectedProcedureList()
		descs = {}
		for f in filters:
			variables += f.getResultVariables()
			for v in variables:
				descs[v] = f.getResultVariableDesc(v)
		
		alreadySetVariables = analysis.getSelectedVariables(name)
		
		for i, varName in enumerate(variables):
			self.checkListCtrl.InsertStringItem(i, "")
			self.checkListCtrl.SetStringItem(i, 1,varName)
			# Set the name the variable will be known as
			# if this has not been set before, then it will of the form
			# ListNameVarName

			if varName in alreadySetVariables:
				asName = alreadySetVariables.get(varName)
				self.checkListCtrl.CheckItem(i, True)
			else:
				asName = "%s%s"%(name, varName)
				self.checkListCtrl.CheckItem(i, False)
			self.checkListCtrl.SetStringItem(i,2,asName)
			self.checkListCtrl.SetStringItem(i, 3, descs[varName])
			
class CheckListCtrl(wx.ListCtrl,
				   listmix.ListCtrlAutoWidthMixin,
				   listmix.TextEditMixin, listmix.CheckListCtrlMixin):
	"""
	Created: 26.11.2007, KP
	Description: a ListCtrl that allows the selection of different procedure lists and the editing
				 of the variables that should be retrieved from those lists
	"""
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.TextEditMixin.__init__(self)
		listmix.ListCtrlAutoWidthMixin.__init__(self)
		listmix.CheckListCtrlMixin.__init__(self)
		
		
		self.InsertColumn(0, "")
		self.InsertColumn(1, "Variable")
		self.InsertColumn(2, "Name")
		self.InsertColumn(3, "Description")
		self.SetColumnWidth(0, 20)
		self.SetColumnWidth(2, 200)
		self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit)
		
	def OnBeginEdit(self, evt):
		"""
		Created: 26.11.2007, KP
		Description: event handler called when the user edits a label
		"""
		if evt.GetColumn() in [0,1]:
			evt.Veto()
		else:
			evt.Allow()


class ProcedureListCtrl(wx.ListCtrl,
				   listmix.ListCtrlAutoWidthMixin,
				   listmix.TextEditMixin):
	"""
	Created: 26.11.2007, KP
	Description: a ListCtrl that allows the selection of different procedure lists and the editing
				 of the variables that should be retrieved from those lists
	"""
	def __init__(self, parent, ID, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0, analysis = None):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.TextEditMixin.__init__(self)
		listmix.ListCtrlAutoWidthMixin.__init__(self)
		
		self.analysis = analysis
		self.InsertColumn(0, "Procedure list")
		self.InsertColumn(1, "Defined variables")
		self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit)
		
	def OnBeginEdit(self, evt):
		"""
		Created: 1.12.2007, KP
		Description: an event handler for beginning the editing of an entry
		"""
		index = evt.GetIndex()
		col = evt.GetColumn()
		if col==0:
			self.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
		evt.Skip()
		
	def OpenEditor(self, col,row):
		if col==1:
			dlgTitle = "Select retrieved variables from %s"%self.analysis.getSelectedProcedureList()
			dlg = PickVariablesDialog(self, self.analysis, title = dlgTitle, size = (600,200))
			if dlg.ShowModal() == wx.ID_OK:
				selectedVariables = dlg.getSelectedVariables()
				self.analysis.setSelectedVariables(self.analysis.getSelectedProcedureList(), selectedVariables)
				self.updateSelectedVariables(row)
		else:
			listmix.TextEditMixin.OpenEditor(self, col, row)

	def updateSelectedVariables(self, row, listName = ""):
		"""
		Created: 30.11.2007, KP
		Description: update the selected variables on given row
		"""
		if not listName:
			listName = self.analysis.getSelectedProcedureList()
		selectedVariables = self.analysis.getSelectedVariables(listName)
		if selectedVariables:
			vars=", ".join(selectedVariables.values())
			self.SetStringItem(row, 1, vars)
		else:
			self.SetStringItem(row, 1, "(Click to define)")
			
class BatchAnalysisGrid(gridlib.Grid):
	"""
	Created: 25.11.2007, KP
	Description: a grid that can be modified that is used to define how to layout the results of a batch processing
	"""
	def __init__(self, parent, analysis):
		gridlib.Grid.__init__(self, parent, -1)
		self.analysis = analysis
		table = BatchAnalysisTable(analysis)

		# The second parameter means that the grid is to take ownership of the
		# table and will destroy it when done.	Otherwise you would need to keep
		# a reference to it and call it's Destroy method later.
		self.SetTable(table, True)
		self.SetRowLabelSize(120)
		self.SetLabelFont(wx.Font(9, wx.DEFAULT, wx.FONTSTYLE_NORMAL,  wx.NORMAL))
		pubsub.Publisher().subscribe(self.updateGrid, "UpdateGrid")

	def updateGrid(self, message):
		"""
		Created: 30.11.2007, KP
		Description: update the grid
		"""
		self.GetTable().updateGridValues()
		print "Updating grid values"
		self.ForceRefresh()

class ProcedurePanel(wx.ScrolledWindow):
	"""
	Created: 25.11.2007, KP
	Description: a panel used to define the procedures 
	"""
	def __init__(self, parent, model):
		#wx.Panel.__init__(self, parent, -1)
		wx.ScrolledWindow.__init__(self, parent, -1)
		self.SetScrollRate(5,5)
		self.analysis = model
		wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", 1)

		self.createGUI()

	def createGUI(self):
		"""
		Created: 25.11.2007, KP
		Description: create the GUI
		"""
		self.sizer = wx.GridBagSizer()
		
		hdr1Sb = wx.StaticBox(self,-1,"Input datasets")
		hdr1SbSizer = wx.StaticBoxSizer(hdr1Sb, wx.VERTICAL)
		self.fileListBox = wx.ListBox(self,-1, size=(150,50), style = wx.LB_NEEDED_SB | wx.LB_MULTIPLE)
		
		hdr1SbSizer.Add(self.fileListBox, 1, wx.EXPAND)
		
		self.radioBox = wx.RadioBox(self, -1, "Per-file channel processing", 
								choices = ["Each channel separately","All channels as input"], 
								style = wx.RA_SPECIFY_COLS, majorDimension = 2)
								
		self.radioBox.Bind(wx.EVT_RADIOBOX, self.onSelectChannelProcessing)
		
		tip = wx.ToolTip("Select whether the channels in a single file should be processed as "\
						 "separate datasets, or fed into a given procedure list as multiple inputs")
		
		self.radioBox.SetToolTip(tip)
								
		self.groupChannelsCheckbox = wx.CheckBox(self, -1, "Group channels per file")
		self.groupChannelsCheckbox.Bind(wx.EVT_CHECKBOX, self.onCheckGroupChannels)
		tip = wx.ToolTip("If this box is checked, when processing channels of a single file, the output datasets will be grouped under a single BXD file as well.")
		self.groupChannelsCheckbox.SetToolTip(tip)
		
		hdr1SbSizer.Add(self.radioBox)
		hdr1SbSizer.Add(self.groupChannelsCheckbox)
		
		self.populateListBox()
		self.sizer.AddGrowableCol(0)
		
		hdr2Sb = wx.StaticBox(self,-1,"Procedure lists")
		hdr2SbSizer = wx.StaticBoxSizer(hdr2Sb, wx.VERTICAL)
		
		self.procedureSizer = wx.GridBagSizer()
		hdr2SbSizer.Add(self.procedureSizer, 1, wx.EXPAND)
		self.procedureListBox = ProcedureListCtrl(self,-1, analysis = self.analysis, size=(150,100), style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_EDIT_LABELS)
		self.procedureListBox.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectProcedureList)
		self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.onChangeListName)
		self.procedureSizer.Add(self.procedureListBox, (0,0), flag = wx.EXPAND)

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.addBtn = wx.Button(self,-1,"Add")
		self.addBtn.Bind(wx.EVT_BUTTON, self.onAddProcedureList)
		
		self.removeBtn = wx.Button(self, -1, "Remove")
		self.removeBtn.Bind(wx.EVT_BUTTON, self.onRemoveProcedureList)
		
		self.addVarBtn = wx.Button(self, -1, "Place variables")
		self.addVarBtn.Bind(wx.EVT_BUTTON, self.onPlaceVariables)
		
		self.executeBtn = wx.Button(self, -1, "Analyze!")
		self.executeBtn.Bind(wx.EVT_BUTTON, self.onExecuteAnalysis)
		
		btnSizer.Add(self.addBtn)
		btnSizer.Add(self.removeBtn)
		btnSizer.Add(self.addVarBtn) 
		btnSizer.Add(self.executeBtn)
		
		self.filterEditor = GUI.FilterEditor.FilterEditor(self, scriptingId='scripting.dialogs["BatchProcessor"].filterEditor', fbSize = (300, 150))
		self.filterEditor.Enable(0)
		
		self.procedureSizer.Add(btnSizer, (1,0))
		self.procedureSizer.Add(self.filterEditor,(2,0))
		self.procedureSizer.AddGrowableRow(2)
		
	
		self.sizer.Add(hdr1SbSizer, (0,0), flag = wx.EXPAND)
		self.sizer.Add(hdr2SbSizer, (1,0), flag = wx.EXPAND)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		
	def onChangeListName(self, evt):
		"""
		Created: 04.12.2007, KP
		Description: change the name of the current procedure list
		"""
		print "Selected list = ",self.analysis.getSelectedProcedureList()
		print "Renaming to",evt.GetLabel()
		self.analysis.renameList(self.analysis.getSelectedProcedureList(), evt.GetLabel())
		
		
	def onSelectChannelProcessing(self, evt):
		"""
		Created: 1.12.2007, KP
		Description: an event handler for when the user selects how to process file channels
		"""
		selection = self.radioBox.GetSelection()
		self.groupChannelsCheckbox.Enable(selection == 0)
		self.analysis.setChannelProcessing(selection)
		
	def onCheckGroupChannels(self, evt):
		"""
		Created: 1.12.2007, KP
		Description: an event handelr for when the user toggles the channel grouping checkbox
		"""
		self.analysis.setChannelGrouping(evt.IsChecked())
		
	def onExecuteAnalysis(self, evt):
		"""
		Created: 30.11.2007, KP
		Description: execute the analysis
		"""
		filename = Dialogs.askSaveAsFileName(self, "Save batch analysis results as", "analysis.csv", \
												"Batch Analysis Results (*.csv)|*.csv")
		if not filename:
			return
		dirname = os.path.dirname(filename)
		n = max([x.getNumberOfTimepoints() for x in self.analysis.getSourceDataUnits()])
		timepoints = GUI.TimepointSelection.TimepointSelection(self)
		timepoints.setNumberOfTimepoints(n)
		if not dirname:
			return
		if timepoints.ShowModal() == wx.ID_OK:
			tps = timepoints.getSelectedTimepoints()
		if not tps:
			return
		
		self.analysis.execute(filename, dirname, tps)
		
	def onPlaceVariables(self, evt):
		"""
		Created: 30.11.2007, KP
		Description: place the selected variables on the grid
		"""
		pubsub.Publisher().sendMessage('UpdateGrid')
		
	def updateFromAnalysis(self):
		"""
		Created: 30.11.2007, KP
		Description: update the GUI from the analysis
		"""
		self.filterEditor.setDataUnit(self.analysis.getDataUnit())
		procListNames = self.analysis.getProcedureListNames()
		self.procedureListBox.DeleteAllItems()
		for i,name in enumerate(procListNames):
			self.procedureListBox.InsertStringItem(i, name)
			self.procedureListBox.updateSelectedVariables(i, listName = name)
			
		print "populating list box"
		self.populateListBox()

	def onAddProcedureList(self, evt):
		"""
		Created: 26.11.2007, KP
		Description: add a procedure list to the listbox
		"""
		n = self.procedureListBox.GetItemCount()
		k=n+1
		name = "ProcLst%d"%(k)
		while self.procedureListBox.FindItem(-1, name) != -1:
			k += 1
			name = "ProcLst%d"%(k)
			
		self.procedureListBox.InsertStringItem(n,name)
		self.procedureListBox.SetStringItem(n,1,"(Click to define)")
		
		self.analysis.addProcedureList(name)
		self.selectProcedureList(name)
		
	def onSelectProcedureList(self, evt):
		"""
		Created: 27.11.2007, KP
		Description: An event handler that is called when the user selects an item in the procedure list ListCtrl
		"""
		item = evt.GetIndex()
		item = self.procedureListBox.GetItem(item)
		label = item.GetText()
		self.selectProcedureList(label)
		evt.Skip()
		
	def selectProcedureList(self, name):
		"""
		Created: 27.11.2007, KP
		Description: Select a procedure list with the given name
		"""
		self.analysis.setSelectedProcedureList(name)
		procList = self.analysis.getProcedureList(name)
		self.filterEditor.setFilterList(procList)
		self.filterEditor.updateFromFilterList()
		self.filterEditor.Enable(1)
		
		
	def onRemoveProcedureList(self, evt):
		"""
		Created: 26.11.2007, KP
		Description: remove a procedure list from the list box
		"""
		item = self.procedureListBox.FindItem(0, self.analysis.getSelectedProcedureList())
		if item != -1:
			self.procedureListBox.DeleteItem(item)

	def populateListBox(self):
		"""
		Created: 25.11.2007, KP
		Description: populate the list box
		"""
		self.fileListBox.Clear()
		fileNames = []
		for i, dataUnit in enumerate(self.analysis.getSourceDataUnits()):
			fileNames.append(os.path.basename(dataUnit.getFileName()) +": "+dataUnit.getName())
		print fileNames
		self.fileListBox.InsertItems(fileNames, 0)
			
	def onSaveAnalysis(self, evt = None):
		"""
		Created: 25.11.2007, KP
		Description: Save the analysis to a file
		"""
		filename = Dialogs.askSaveAsFileName(self, "Save analysis as", "analysis.bba", \
												"BioImageXD Batch Analysis (*.bba)|*.bba")
		if filename:
			self.analysis.saveAnalysisAs(filename)
			
class BatchProcessor(wx.Frame):
	"""
	Created: 25.11.2007, KP
	Description: A class that implements a batch processor tool for BioImageXD
	""" 
	def __init__(self, parent):
		"""
		Created: 13.02.2006, KP
		Description: Initialize the batch processor
		"""
		self.parent = parent
		wx.Frame.__init__(self, parent, -1, "BioImageXD Batch Processor", size = (1024, 800))
		self.splitter = wx.SplitterWindow(self, -1, style = wx.SP_LIVE_UPDATE)

		
		self.analysis = BatchAnalysis()

		self.grid = BatchAnalysisGrid(self.splitter, self.analysis)

		self.procedurePane = ProcedurePanel(self.splitter, self.analysis)
		self.filterEditor = self.procedurePane.filterEditor
		
		self.splitter.SetMinimumPaneSize(20)
		self.splitter.SplitVertically(self.procedurePane, self.grid, 300)

		self.createMenubar()
		
		self.Layout()
		
	def setInputDataUnits(self, dataUnits):
		"""
		Created: 25.11.2007, KP
		Description: set the input data units for this batch processor
		"""
		self.analysis.setInputDataUnits(dataUnits)
		self.procedurePane.updateFromAnalysis()
		
	def createMenubar(self):
		"""
		Created: 13.02.2006, KP
		Description: Creates the menubar for the script editor
		"""
		self.menu = wx.MenuBar()
		self.SetMenuBar(self.menu)
		
		self.wc = "BioImageXD Batch Analysis (*.bba)|*.bba;*.BBA;"
		
		self.file = wx.Menu()
		
		self.menu.Append(self.file, "&File")
		
		self.file.Append(GUI.MenuManager.ID_SAVE_ANALYSIS, "&Save batch analysis...\tCtrl-S")
		wx.EVT_MENU(self, GUI.MenuManager.ID_SAVE_ANALYSIS, self.procedurePane.onSaveAnalysis)
		
		self.file.Append(GUI.MenuManager.ID_LOAD_ANALYSIS, "&Open batch analysis...\tCtrl-O")
		wx.EVT_MENU(self, GUI.MenuManager.ID_LOAD_ANALYSIS, self.onLoadAnalysis)
		self.file.AppendSeparator()
		self.file.Append(GUI.MenuManager.ID_CLOSE_BATCHPROCESSOR, "&Close...\tAlt-F4")
		wx.EVT_MENU(self, GUI.MenuManager.ID_CLOSE_BATCHPROCESSOR, self.onClose)

	def onClose(self, evt):
		"""
		Created: 25.11.2007, KP
		Description: Close the batch processor
		"""	  
		scripting.unregisterDialog("BatchProcessor")
		self.Destroy()
	
	def onLoadAnalysis(self, evt):
		"""
		Created: 25.11.2007, KP
		Description: Load an analysis form file
		"""
		
		filenames = Dialogs.askOpenFileName(self, "Open analysis file",  \
												"BioImageXD Batch Analysis (*.bba)|*.bba")
		if filenames:
			self.analysis.readAnalysisFrom(filenames[0])
			self.procedurePane.updateFromAnalysis()

