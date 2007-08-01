# -*- coding: iso-8859-1 -*-

"""
 Unit: TimepointSelection.py
 Project: BioImageXD
 Created: 03.02.2005, KP
 Description:

 This is a base widget for all operations that need to let the user select
 the timepoints that are operated upon. Used by rendering and various 
 operation windows 


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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


import wx
import os.path

import sys
import RenderingInterface
import Logging
import Dialogs


import wx.lib.scrolledpanel as scrolled
import wx.lib.buttons as buttons
import vtk

import scripting as bxd
import Command

class TimepointSelectionPanel(scrolled.ScrolledPanel):
	"""
	Created: 10.2.2005, KP
	Description: A class containing the basic timepoint selection functionality
				 in a panel. This is a class separete from TimepointSelection
				 so that this can be also embedded in any other dialog.
	"""
	def __init__(self, parent, parentStr = "bxd.processingManager"):
		#wx.Panel.__init__(self,parent,size=(640,480))
		scrolled.ScrolledPanel.__init__(self, parent, size = (640, 300))
		self.mainsizer = wx.GridBagSizer(10, 10)
		self.configFrame = None
		
		self.parentPath = parentStr

		self.timepointButtonSizer = wx.GridBagSizer()
		#,style=wx.RAISED_BORDER
		#self.buttonFrame = scrolled.ScrolledPanel(self, -1,size=(640,300))
		self.buttonFrame = wx.Panel(self, -1, size = (640, 300))
		self.buttonFrame.SetSizer(self.timepointButtonSizer)
		self.buttonFrame.SetAutoLayout(True)
		#self.buttonFrame.SetupScrolling()
		#self.timepointLbl=wx.StaticText(self,-1,"Select timepoints")
		
		#self.mainsizer.Add(self.timepointLbl,(0,0))        
		
		self.selectbox = wx.StaticBox(self, -1, "Select Timepoints")
		self.selectboxsizer = wx.StaticBoxSizer(self.selectbox, wx.VERTICAL)
		self.selectboxsizer.Add(self.buttonFrame, 1)
		
		#self.mainsizer.Add(self.buttonFrame,(1,0),span=(1,2),flag=wx.EXPAND|wx.ALL)
		self.mainsizer.Add(self.selectboxsizer, (0, 0), flag = wx.EXPAND | wx.ALL)
		
		self.buttonList = []
		self.selectedFrames = {}
		self.createConfigFrame()
	
		self.SetAutoLayout(True)
		self.SetSizer(self.mainsizer)
		self.mainsizer.Fit(self)
		self.SetupScrolling()
		#self.mainsizer.SetSizeHints(self)
				
	def getSelectedTimepoints(self):
		timepoints = []
		for i in self.selectedFrames.keys():
			#print "%d selected: %s"%(i,(self.selectedFrames[i]==1))
			if self.selectedFrames[i]:
				timepoints.append(i)
		return timepoints
		
	def createConfigFrame(self):
		"""
		Created: 17.11.2004, KP
		Description: A callback that is used to close this window
		"""
		self.configFrame = wx.Panel(self)
		self.selectboxsizer.Add(self.configFrame)
		#self.mainsizer.Add(self.configFrame,(2,0),span=(1,2),flag=wx.EXPAND|wx.ALL)
		
		self.configSizer = wx.GridBagSizer()

		box = wx.BoxSizer(wx.HORIZONTAL)
		self.nthLbl = wx.StaticText(self.configFrame, -1, "Select every nth timepoint:")
		box.Add(self.nthLbl)
		self.configSizer.Add(box, (0, 0))

		self.nthEntry = wx.TextCtrl(self.configFrame, -1, "1", size = (50, -1))
		box.Add(self.nthEntry)
		self.nthEntry.Bind(wx.EVT_TEXT, self.updateSelection)
				
		self.configFrame.SetSizer(self.configSizer)
		self.configFrame.SetAutoLayout(True)            
		self.configSizer.Fit(self.configFrame)
		
	def updateSelection(self, event = None):
		"""
		Created: 17.11.2004, KP
		Description: A callback that is used to select every nth button, where
					 N is the value of the nthEntry entry
		"""
		try:
			n = int(self.nthEntry.GetValue())
		except:
			n = 1
		do_cmd = self.parentPath + ".timepointSelection.selectEveryNth(%d)" % n
		undo_cmd = ""
		cmd = Command.Command(Command.GUI_CMD, None, None, do_cmd, undo_cmd, desc = "Select every Nth timepoint for processing")
		cmd.run()        
		
	def selectEveryNth(self, n):
		"""
		Created: 18.07.2006, KP
		Description: Select every nth button
		"""        
		if not n:
			for i in range(len(self.buttonList)):
				self.selectedFrames[i] = 0
				self.setButtonState(self.buttonList[i], 0)
			return
		for i, btn in enumerate(self.buttonList):
			if not (i) % n:
				self.selectedFrames[i] = 1
				self.setButtonState(btn, 1)
			else:
				self.selectedFrames[i] = 0
				self.setButtonState(btn, 0)
		
	def createButtons(self):
		"""
		Created: 10.11.2004, KP
		Description: A method that creates as many buttons as the dataunit
				 has timepoints, so that each button represent one time point
		"""
		nrow = 0
		ncol = 0
		for i in range(self.dataUnit.getNumberOfTimepoints()):
			if ncol == 30:
				nrow += 1
				ncol = 0
			btn = buttons.GenButton(self.buttonFrame, -1, "%d" % i, size = (24, 24))
			btn.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
			btn.Bind(wx.EVT_BUTTON, lambda e, btn = btn, i = i: self.buttonClickedCallback(btn, i))
			btn.origColor = btn.GetBackgroundColour()
			btn.origFgColor = btn.GetForegroundColour()
			self.buttonList.append(btn)
			self.timepointButtonSizer.Add(btn, (nrow, ncol))
			ncol = ncol + 1
		self.buttonFrame.Layout()
		self.timepointButtonSizer.Fit(self.buttonFrame)
		self.mainsizer.Fit(self)

	def buttonClickedCallback(self, button, number):
		"""
		Created: 10.11.2004, KP
		Description: A method called when user clicks a button representing 
					 a time point
		"""
		flag = False
		if number in self.selectedFrames:
			flag = not self.selectedFrames[number]
		do_cmd = self.parentPath + ".timepointSelection.setTimepoint(%d, %s)" % (number, str(flag))
		undo_cmd = self.parentPath + ".timepointSelection.setTimepoint(%d, %s)" % (number, str(not flag))
		
		if flag:
			descstr = "Select timepoint %d for processing" % number
		else:
			descstr = "Unselect timepoint %d for processing" % number
		cmd = Command.Command(Command.GUI_CMD, None, None, do_cmd, undo_cmd, desc = descstr)
		cmd.run()

	def setTimepoint(self, number, flag):
		"""
		Created: 18.07.2006, KP
		Description: Set the given timepoint on or off
		"""   
		if not self.selectedFrames.has_key(number):
			self.selectedFrames[number] = 0
		button = self.buttonList[number]
		
		if self.selectedFrames[number]:
			self.selectedFrames[number] = 0
			self.setButtonState(button, 0)
		else:
			self.selectedFrames[number] = 1
			self.setButtonState(button, 1)

	def setButtonState(self, button, flag):
		"""
		Created: 09.02.2005, KP
		Description: A method to set the state of a button to selected/deselected
		Paremeters:
				button  The button to configure
				flag    Should the button be selected or deselected
		"""
		if not flag:
			button.SetBackgroundColour(button.origColor)
			button.SetForegroundColour(button.origFgColor)
		else:
			button.SetBackgroundColour((51, 51, 51))
			button.SetForegroundColour((255, 255, 255)) 
		button.Refresh()
			
	def setDataUnit(self, dataUnit):
		"""
		Created: 10.11.2004, KP
		Description: A method to set the data unit we use to do the
					 actual rendering
		Paremeters:
			dataUnit    The data unit we use
		"""
		self.dataUnit = dataUnit
		self.createButtons()
		self.updateSelection()
		#data=self.dataUnit.getTimepoint(0)
		self.mainsizer.Fit(self)
		
		

class TimepointSelection(wx.Dialog):
	"""
	Created: 10.11.2004, KP
	Description: A base class for creating windows where the user can select        
				 the timepoints that should be operated upon.
	"""
	def __init__(self, parent, name = "Timepoint selection"):
		"""
		Created: 10.11.2004, KP
		Description: Initialization
		"""
		wx.Dialog.__init__(self, parent, -1, name, style = wx.CAPTION | wx.STAY_ON_TOP | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.RESIZE_BORDER, size = (640, 480))
		self.parent = parent
		
		bxd.registerDialog(name, self)
		
		self.dialogName = name
		self.Bind(wx.EVT_CLOSE, self.closeWindowCallback)
		self.mainsizer = wx.GridBagSizer(10, 10)

		self.rendering = 0
		self.SetTitle("Timepoint Selection")
		ico = reduce(os.path.join, [bxd.get_icon_dir(), "logo.ico"])
		self.icon = wx.Icon(ico, wx.BITMAP_TYPE_ICO)
		self.SetIcon(self.icon)

		self.panel = TimepointSelectionPanel(self, parentStr = "bxd.dialogs['%s']" % self.dialogName)
		self.timepointSelection = self.panel
		
		self.mainsizer.Add(self.panel, (0, 0), flag = wx.EXPAND | wx.ALL)
		
		self.createButtonBox()
		
		self.status = wx.ID_CANCEL

		self.SetSizer(self.mainsizer)
		self.SetAutoLayout(True)
		self.mainsizer.Fit(self)
		#self.mainsizer.SetSizeHints(self)
		
	def setLabel(self, lbl):
		self.panel.timepointLbl.SetLabel(lbl)
		
	def createButtonBox(self):
		"""
		Created: 31.1.2005, KP
		Description: Creates the standard control buttons
		"""
		self.buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.buttonsSizer1 = wx.BoxSizer(wx.HORIZONTAL)
		
		self.actionBtn = wx.Button(self, -1, "Ok")
		self.actionBtn.Bind(wx.EVT_BUTTON, self.onButtonOk)
		self.buttonsSizer1.Add(self.actionBtn, flag = wx.ALIGN_LEFT)

		self.closeBtn = wx.Button(self, -1, "Close")
		self.closeBtn.Bind(wx.EVT_BUTTON, self.closeWindowCallback)
		self.buttonsSizer1.Add(self.closeBtn, flag = wx.ALIGN_LEFT)
		self.buttonsSizer1.AddSizer((100, -1))
		self.buttonsSizer.Add(self.buttonsSizer1, flag = wx.ALIGN_LEFT)
		self.staticLine = wx.StaticLine(self)
		self.mainsizer.Add(self.staticLine, (3, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.mainsizer.Add(self.buttonsSizer, (4, 0))

	def getSelectedTimepoints(self):
		return self.panel.getSelectedTimepoints()
		
	def onButtonOk(self, event):
		"""
		Created: 13.04.2005, KP
		Description: A callback that sets the status of this dialog
		"""
		do_cmd = "bxd.dialogs['%s'].process()" % self.dialogName
		undo_cmd = ""
		
		cmd = Command.Command(Command.GUI_CMD, None, None, do_cmd, undo_cmd, desc = "Process the selected timepoints")
		cmd.run()        

	
	def process(self):
		"""
		Created: 20.07.2006, KP
		Description: Set the status so that the processing will continue and close the window
		"""   
		self.status = wx.ID_OK
		bxd.unregisterDialog(self.dialogName)
		self.Close()
		

	def cancel(self):
		"""
		Created: 20.07.2006, KP
		Description: Set the status so that the processing will cancel and close the window
		"""
		self.status = wx.ID_CANCEL
		bxd.unregisterDialog(self.dialogName)
		self.Close()

	def closeWindowCallback(self, event):
		"""
		Created: 10.11.2004, KP
		Description: A callback that is used to close this window
		"""
		self.EndModal(self.status)
			
	def setDataUnit(self, dataUnit):
		"""
		Created: 10.11.2004, KP
		Description: A method to set the data unit we use to do the
					 actual rendering
		Paremeters:
			dataUnit    The data unit we use
		"""
		self.panel.setDataUnit(dataUnit)
		self.dataUnit = dataUnit
