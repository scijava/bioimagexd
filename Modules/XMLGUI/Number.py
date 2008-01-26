# -*- coding: iso-8859-1 -*-
"""
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import GUI.XMLGUIBuilder


class NumberValidator(wx.PyValidator):
	"""
	Created: 26.01.2008, KP
	Description: a validator class for number input
	"""
	def __init__(self, mode = "Integer", newrange = None):
		wx.PyValidator.__init__(self)
		self.mode = mode
		self.validRange = newrange
		self.digits = {"Integer":"0123456789", "Float":"01234567890.,"}
		
	def SetRange(self, newrange):
		self.validRange = newrange

	def Clone(self):
		return NumberValidator()
	def TransferToWindow(self):
		return True

	def TransferFromWindow(self):
		return True

	def Validate(self, win):
		tc = self.GetWindow()
		val = tc.GetValue()
		for letter in val:
			if letter not in self.digits[self.mode]:
				return False
		val = eval(val)
		if self.validRange and val<self.validRange[0] or val>self.validRange[1]:
			return False

class NumberInput(GUI.XMLGUIBuilder.XMLGUIElement):
	"""
	Created: 26.01.2008, KP
	Description: an input element for reading integer
	"""
	inputTypes = ["Integer","Float"]
	def __init__(self, builder, parent, *args, **kws):
		GUI.XMLGUIBuilder.XMLGUIElement.__init__(self, builder, parent, *args, **kws)
		self.createUI()
		
	def createUI(self):
		"""
		Created: 26.01.2008, KP
		Description: create the user interface element
		"""
		defaultValue = self.builder.getDefaultValue(self.id)
		
		valrange = self.builder.getRange(self.id)
		self.validator = NumberValidator(self.builder.getInputType(self.id))
		if valrange:
			self.validator.SetRange(valrange)
		self.uiElement = wx.TextCtrl(self.parent, -1, str(defaultValue), validator = self.validator)
		
