# -*- coding: iso-8859-1 -*-
"""
 Unit: Dialogs
 Project: BioImageXD
 Created: 28.01.2005
 
 Description:

 Shortcut methods for displaying most of the normal dialogs. 

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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import Configuration
import os.path
import wx

def showmessage(parent, message, title, flags = wx.OK):
	"""
	A method to show a message
	"""
	dlg = wx.MessageDialog(parent, message, title, flags)
	dlg.ShowModal()
	dlg.Destroy()

def showwarning(parent, message, title, flags = wx.OK | wx.ICON_WARNING):
	"""
	A method to show a warning
	"""    
	showmessage(parent, message, title, flags)
	
def showerror(parent, message, title, flags = wx.OK | wx.ICON_ERROR):
	"""
	A method to show an error message
	"""    
	showmessage(parent, message, title, flags)


def askDirectory(parent, title, initialDir = None):
	"""
	A method for showing a directory selection dialog
	"""    
	filepath = ""
	conf = Configuration.getConfiguration()
	remember = conf.getConfigItem("RememberPath", "Paths")
	if not initialDir:
		if remember:
			initialDir = conf.getConfigItem("LastPath", "Paths")
			if not initialDir:
				initialDir = "."
		else:
			initialDir = conf.getConfigItem("DataPath", "Paths")
	dlg = wx.DirDialog(parent, title, initialDir,
					  style = wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
	if dlg.ShowModal() == wx.ID_OK:
		filepath = dlg.GetPath()
		
	if remember:
		conf.setConfigItem("LastPath", "Paths", filepath)
	dlg.Destroy()
	return filepath

def askOpenFileName(parent, title, wc, remember =- 1, filetype = None):
	"""
	A method to show a open file dialog that supports multiple files
	"""
	asklist = []
	if remember == -1:
		conf = Configuration.getConfiguration()
		remember = conf.getConfigItem("RememberPath", "Paths")
	lastpath = ""
	ftype = wc.split("|")[1]
	ftype = ftype.split(".")[1]
	if filetype != None:
		ftype = filetype
	if remember:
		lastpath = conf.getConfigItem("LastPath_%s" % ftype, "Paths")
		if not lastpath:
			lastpath = "."
	dlg = wx.FileDialog(parent, title, lastpath, wildcard = wc, style = wx.OPEN|wx.MULTIPLE)
	if dlg.ShowModal() == wx.ID_OK:
		asklist = dlg.GetPaths()
		asklist = map(unicode, asklist)
		if not asklist:
			return asklist
		if remember:
			filepath = os.path.dirname(asklist[0])
			conf.setConfigItem("LastPath_%s" % ftype, "Paths", filepath)
		
	dlg.Destroy()    
	return asklist
	
def askSaveAsFileName(parent, title, initFile, wc, ftype = None):
	"""
	A method to show a save as dialog
	"""    
	initialDir = None
	conf = Configuration.getConfiguration()
	remember = conf.getConfigItem("RememberPath", "Paths")
	if not ftype:
		ftype = wc.split("|")[1]
		ftype = ftype.split(".")[1]
	
	if not initialDir:
		if remember:
			initialDir = conf.getConfigItem("LastPath_%s" % ftype, "Paths")
			if not initialDir:
				initialDir = "."
		else:
			initialDir = conf.getConfigItem("DataPath", "Paths")
	
	filename = ""
	dlg = wx.FileDialog(parent, title, defaultFile = initFile, \
						defaultDir = initialDir, wildcard = wc, style = wx.FD_SAVE)
	filename = None
	if dlg.ShowModal() == wx.ID_OK:
		filename = dlg.GetPath()
	if remember and filename:
		filepath = os.path.dirname(filename)
		conf.setConfigItem("LastPath_%s" % ftype, "Paths", filepath)
					
	dlg.Destroy()
	if filename:
		currExt = filename.split(".")[-1].lower()
		ext = wc.split(".")[-1]
		if wc.count("*.") <= 2 and wc.find("*.%s" % currExt) == -1:        
			filename += ".%s" % ext
	
	return filename

