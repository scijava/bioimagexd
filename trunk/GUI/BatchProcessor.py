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
import scripting

import lib.messenger
import GUI.MenuManager
import GUI.TimepointSelection

import wx
import wx.grid as gridlib
import wx.lib.mixins.listctrl as listmix
import wx.lib.pubsub as pubsub
import time
import GUI.FilterEditor
import os
import types
import lib.BatchAnalysis


class BatchAnalysisTable(gridlib.PyGridTableBase):
	"""
	Created: 26.11.2007, KP
	Description: a table model for a wx.lib.gridlib.Grid
	"""
	def __init__(self, analysis):
		gridlib.PyGridTableBase.__init__(self)
		self.analysis = analysis
		self.variables = []
		self.values = {}
		
	def updateGridValues(self):
		"""
		update the grid values
		"""
		vars = []
		for procList in self.analysis.getProcedureListNames():
			vars += [x for x in self.analysis.getSelectedVariables(procList).values()]
		self.variables = vars
		
	def GetColLabelValue(self, col):
		"""
		return the column label of the given column
		"""
		return "Var%d"%(col+1)
		
	def GetRowLabelValue(self, row):
		"""
		return the row labels of the grid, listing the file names
		"""
		fileNames = [x.getName() for x in self.analysis.getSourceDataUnits()]
		if row < len(fileNames):
			return os.path.basename(fileNames[row])
		return ""

	def GetNumberRows(self):
		"""
		return the number of rows the grid has
		"""
		return len(self.analysis.getSourceDataUnits())+20

	def GetNumberCols(self):
		"""
		return the number of cols the grid has
		"""
		if not self.variables:
			return 10
		return len(self.variables)+10

	def IsEmptyCell(self, row, col):
		return False

	def GetValue(self, row, col):
		"""
		Get the value of a given cell
		"""
		if row==0:
			if col<len(self.variables):
				return self.variables[col]
		if (row,col) in self.values: return self.values[(row,col)]
		return ""

	def SetValue(self, row, col, value):
		if value == None:value=""
		self.values[(row,col)] = value


class PickVariablesDialog(wx.Dialog):
	"""
	A dialog for picking which variables to retrieve from the procedure lists
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
		
		self.varToIndex = {}
		
		btnSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		if btnSizer:
			self.sizer.Add(btnSizer, (1,0), flag = wx.EXPAND)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		self.populateFromAnalysis(self.analysis)
			
	def getSelectedVariables(self):
		"""
		get the selected variables
		"""
		ret = {}
		for i in range(self.checkListCtrl.GetItemCount()):
			if self.checkListCtrl.IsChecked(i):
				varName = self.checkListCtrl.GetItem(i,1).GetText()
				varAs = self.checkListCtrl.GetItem(i,3).GetText()
				ret[varAs] = varName
		return ret
			
	def populateFromAnalysis(self, analysis):
		"""
		populate the list of variables from the given analysis
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
		varCount = {}
		for f in filters:
			variables += [[f, f.getResultVariables()]]
			for v in f.getResultVariables():
				descs[v] = f.getResultVariableDesc(v)
				c = varCount.get(v, 0)
				varCount[v] = c+1

		alreadySetVariables = analysis.getSelectedVariables(name)
		counts={}
		
		self.filters = []

		i = 0
		for (currFilter, filterVariables) in variables:
			for varName in filterVariables:
				self.checkListCtrl.InsertStringItem(i, "")
				self.checkListCtrl.SetStringItem(i, 1,varName)
				inChs = ", ".join(currFilter.getSelectedInputChannelNames())
				self.checkListCtrl.SetStringItem(i, 2, inChs)
	

				# Set the name the variable will be known as
				# if this has not been set before, then it will of the form
				# ListNameVarName
				for (key,value) in alreadySetVariables.items():
					if varName == value:
						asName = key
						self.checkListCtrl.CheckItem(i, True)
						break
				else:
					asName = "%s%s"%(name, varName)
					if varCount[varName] > 1:
						varIndex = counts.get(varName, 1)
						asName="%s%d"%(asName, varIndex)
						counts[varName] = varIndex+1
						
					self.checkListCtrl.CheckItem(i, False)
				self.checkListCtrl.SetStringItem(i,3,asName)
				self.checkListCtrl.SetStringItem(i, 4, descs[varName])
				i+=1
			
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
		self.InsertColumn(2, "Inputs")
		self.InsertColumn(3, "Name")
		self.InsertColumn(4, "Description")
		self.SetColumnWidth(0, 20)
		self.SetColumnWidth(1, 140)
		self.SetColumnWidth(2, 110)
		self.SetColumnWidth(3, 190)
		self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit)

		self.selectAllMenu = wx.Menu()
		self.ID_SELECT_ALL = wx.NewId()
		item = wx.MenuItem(self.selectAllMenu, self.ID_SELECT_ALL, "Select all")
		self.selectAllMenu.AppendItem(item)
		self.ID_CLEAR_ALL = wx.NewId()
		item = wx.MenuItem(self.selectAllMenu, self.ID_CLEAR_ALL, "Clear all")
		self.selectAllMenu.AppendItem(item)
		
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		self.Bind(wx.EVT_MENU, self.onSelectAll, id = self.ID_SELECT_ALL)
		self.Bind(wx.EVT_MENU, self.onClearAll, id = self.ID_CLEAR_ALL)
		
	def OnBeginEdit(self, evt):
		"""
		event handler called when the user edits a label
		"""
		if evt.GetColumn() in [0,1,2,4]:
			evt.Veto()
		else:
			evt.Allow()

	def onRightClick(self, evt):
		"""
		Event handler called when user pushes right mouse button
		"""
		self.PopupMenu(self.selectAllMenu, evt.GetPosition())

	def onSelectAll(self, evt):
		"""
		Event handler for 'select all' menu choice
		"""
		for i in xrange(self.GetItemCount()):
			self.CheckItem(i, True)

	def onClearAll(self, evt):
		"""
		Event handler for 'clear all' menu choice
		"""
		for i in xrange(self.GetItemCount()):
			self.CheckItem(i, False)


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
		an event handler for beginning the editing of an entry
		"""
		index = evt.GetIndex()
		col = evt.GetColumn()
		if col==0:
			self.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
		evt.Skip()
		
	def OpenEditor(self, col,row):
		if col==1:
			dlgTitle = "Select retrieved variables from %s"%self.analysis.getSelectedProcedureList()
			dlg = PickVariablesDialog(self, self.analysis, title = dlgTitle, size = (750,500))
			if dlg.ShowModal() == wx.ID_OK:
				selectedVariables = dlg.getSelectedVariables()
				print "selected vars=",selectedVariables
				self.analysis.setSelectedVariables(self.analysis.getSelectedProcedureList(), selectedVariables)
				self.updateSelectedVariables(row)
		else:
			listmix.TextEditMixin.OpenEditor(self, col, row)

	def updateSelectedVariables(self, row, listName = ""):
		"""
		update the selected variables on given row
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
		update the grid
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
		create the GUI
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

		self.groupProcListCheckbox = wx.CheckBox(self, -1, "Group output by procedure list")
		self.groupProcListCheckbox.Enable(0)
		self.groupProcListCheckbox.Bind(wx.EVT_CHECKBOX, self.onCheckGroupByProcList)
		tip = wx.ToolTip("If this box is checked, the output images will be grouped by the procedure list that processes them.")
		self.groupProcListCheckbox.SetToolTip(tip)
		checkBoxSizer = wx.BoxSizer(wx.HORIZONTAL)
		checkBoxSizer.Add(self.groupChannelsCheckbox)
		checkBoxSizer.Add(self.groupProcListCheckbox)
		hdr1SbSizer.Add(self.radioBox)
		hdr1SbSizer.Add(checkBoxSizer)
		
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
		change the name of the current procedure list
		"""
		self.analysis.renameList(self.analysis.getSelectedProcedureList(), evt.GetLabel())
		
		
	def onSelectChannelProcessing(self, evt):
		"""
		an event handler for when the user selects how to process file channels
		"""
		selection = self.radioBox.GetSelection()
		self.groupChannelsCheckbox.Enable(selection == 0)
		self.groupProcListCheckbox.Enable(selection == 1)
		self.analysis.setChannelProcessing(selection)
		
	def onCheckGroupChannels(self, evt):
		"""
		an event handler for when the user toggles the channel grouping checkbox
		"""
		self.analysis.setChannelGrouping(evt.IsChecked())
		
	def onCheckGroupByProcList(self, evt):
		"""
		"""
		self.analysis.setChannelGroupingByProcedureList(evt.IsChecked())
		
	def onExecuteAnalysis(self, evt):
		"""
		execute the analysis
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
		place the selected variables on the grid
		"""
		pubsub.Publisher().sendMessage('UpdateGrid')
		
	def updateFromAnalysis(self):
		"""
		update the GUI from the analysis
		"""
		self.filterEditor.setDataUnit(self.analysis.getDataUnit())
		procListNames = self.analysis.getProcedureListNames()
		self.procedureListBox.DeleteAllItems()
		for i,name in enumerate(procListNames):
			self.procedureListBox.InsertStringItem(i, name)
			self.procedureListBox.updateSelectedVariables(i, listName = name)
			
		self.populateListBox()
		chlGrouping = self.analysis.getChannelGrouping()
		procListGrouping = self.analysis.getChannelGroupingByProcedureList()
		channelProc = self.analysis.getChannelProcessing()
		self.groupChannelsCheckbox.SetValue(chlGrouping)
		self.groupProcListCheckbox.SetValue(procListGrouping)
		self.radioBox.SetSelection(channelProc)


	def onAddProcedureList(self, evt):
		"""
		add a procedure list to the listbox
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
		An event handler that is called when the user selects an item in the procedure list ListCtrl
		"""
		item = evt.GetIndex()
		item = self.procedureListBox.GetItem(item)
		label = item.GetText()
		self.selectProcedureList(label)
		evt.Skip()
		
	def selectProcedureList(self, name):
		"""
		Select a procedure list with the given name
		"""
		self.analysis.setSelectedProcedureList(name)
		procList = self.analysis.getProcedureList(name)
		self.filterEditor.resetGUI()
		self.filterEditor.setFilterList(procList)
		self.filterEditor.updateFromFilterList()
		self.filterEditor.Enable(1)
		
		
	def onRemoveProcedureList(self, evt):
		"""
		remove a procedure list from the list box
		"""
		item = self.procedureListBox.FindItem(0, self.analysis.getSelectedProcedureList())
		if item != -1:
			self.procedureListBox.DeleteItem(item)

	def populateListBox(self):
		"""
		populate the list box
		"""
		self.fileListBox.Clear()
		fileNames = []
		for i, dataUnit in enumerate(self.analysis.getSourceDataUnits()):
			fileNames.append(os.path.basename(dataUnit.getFileName()) +": "+dataUnit.getName())
		print fileNames
		self.fileListBox.InsertItems(fileNames, 0)
			
	def onSaveAnalysis(self, evt = None):
		"""
		Save the analysis to a file
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
		Initialize the batch processor
		"""
		self.parent = parent
		wx.Frame.__init__(self, parent, -1, "BioImageXD Batch Processor", size = (1024, 800))
		self.splitter = wx.SplitterWindow(self, -1, style = wx.SP_LIVE_UPDATE)

		
		self.analysis = lib.BatchAnalysis.BatchAnalysis()

		self.grid = BatchAnalysisGrid(self.splitter, self.analysis)

		self.procedurePane = ProcedurePanel(self.splitter, self.analysis)
		self.filterEditor = self.procedurePane.filterEditor
		
		self.splitter.SetMinimumPaneSize(20)
		self.splitter.SplitVertically(self.procedurePane, self.grid, 650)

		self.createMenubar()
		
		self.Layout()
		scripting.visualizer.enable(0)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
	def setInputDataUnits(self, dataUnits):
		"""
		set the input data units for this batch processor
		"""
		self.analysis.setInputDataUnits(dataUnits)
		self.procedurePane.updateFromAnalysis()
		
	def createMenubar(self):
		"""
		Creates the menubar for the script editor
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
		Close the batch processor
		"""
		scripting.unregisterDialog("BatchProcessor")
		scripting.visualizer.enable(1)
		self.Destroy()
	
	def onLoadAnalysis(self, evt):
		"""
		Load an analysis form file
		"""
		
		filenames = Dialogs.askOpenFileName(self, "Open analysis file",  \
												"BioImageXD Batch Analysis (*.bba)|*.bba")
		if filenames:
			self.analysis.readAnalysisFrom(filenames[0])
			self.procedurePane.updateFromAnalysis()

