# -*- coding: iso-8859-1 -*-

"""
 Unit: QuitDialog
 Project: BioImageXD
 Created: 20.02.2009, LP
 Description:

 A dialog for controlling the quit procedure of the program.
 
 Copyright (C) 2006  BioImageXD Project
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

__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import wx

class QuitDialog(wx.MessageDialog):
	"""
	Dialog for asking whether user want to quit BXD and save file tree
	"""
	def __init__(self, parent, title, msg):
		wx.Dialog.__init__(self, parent, -1, size=(400, 150), style=wx.CAPTION | wx.CLOSE_BOX | wx.STAY_ON_TOP, title=title)

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		messageBox = wx.BoxSizer(wx.HORIZONTAL)
		buttonBox = wx.BoxSizer(wx.HORIZONTAL)

		questionIcon = wx.ArtProvider.GetBitmap(wx.ART_QUESTION, wx.ART_MESSAGE_BOX, (32, 32))
		graphic = wx.StaticBitmap(self, -1, questionIcon)
		message = wx.StaticText(self, -1, msg)
		messageBox.Add(graphic, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, 0)
		messageBox.Add(message, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, 10)

		btnSaveAndQuit = wx.Button(self, wx.ID_YES, "&Save and quit")
		btnQuit = wx.Button(self, wx.ID_NO, "&Quit without saving")
		btnCancel = wx.Button(self, wx.ID_CANCEL, "&Cancel")

		buttonBox.Add(btnSaveAndQuit, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.EXPAND, 10)
		buttonBox.Add(btnQuit, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.EXPAND, 10)
		buttonBox.Add(btnCancel, 0, wx.ALIGN_CENTER | wx.BOTTOM | wx.EXPAND, 10)

		wx.EVT_BUTTON(self, wx.ID_YES, self.onYesButton)
		wx.EVT_BUTTON(self, wx.ID_NO, self.onNoButton)

		mainSizer.Add(messageBox, 0, wx.EXPAND)
		mainSizer.Add(buttonBox, 0, wx.EXPAND)
		
		self.SetAutoLayout(True)
		self.SetSizer(mainSizer)
		self.Fit()
		self.Layout()
		self.CentreOnScreen()

	def onYesButton(self, evt):
		"""
		"""
		self.EndModal(wx.ID_YES)

	def onNoButton(self, evt):
		"""
		"""
		self.EndModal(wx.ID_NO)
	
