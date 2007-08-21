# -*- coding: iso-8859-1 -*-
"""
 Unit: Logging
 Project: BioImageXD
 Created: 13.12.2004, KP
 Description:

 A module for reporting and logging errors
 
 Copyright (C) 2005	 BioImageXD Project
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
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2005/01/11 14:36:00 $"

#import sys
#import traceback

import os.path
import sys
import wx

outfile = sys.stdout

# If you wish to see messages from a given debug level, mark it as beginning with two
# hashes (##like this), so that is is immediately obvious, which levels are not hidden
HIDE_DEBUG=["visualizer", "main", "init", "animator", "##io", "task", "##¨preview", "scale",
		"imageop", "modules", "trivial", "ctf", "dataunit", "event", "##processing", 
		"datasource", "iactivepanel", "annotation", "ui", "rendering", "caching", 
		"pipeline", "scripting", "lsmreader"]
		
KWS = ["visualizer", "main", "init", "animator", "io", "task", "preview", "scale",
		"imageop", "modules", "trivial", "ctf", "dataunit", "event", "processing", 
		"datasource", "iactivepanel", "annotation", "ui", "rendering", "caching", 
		"pipeline", "scripting", "lsmreader"]
DO_DEBUG = 1

class Tee:
	"""
	Created: Unknown, KP
	Description: Creates a writable fileobject where the output is tee-ed to all of the individual files.
	"""
	def __init__(self, *optargs):
		self._files = []
		for arg in optargs:
			self.addfile(arg)

	def addfile(self, fileToAdd):
		self._files.append(fileToAdd)

	def remfile(self, fileToRemove):
		fileToRemove.flush()
		self._files.remove(fileToRemove)

	def files(self):
		return self._files

	def write(self, string):
		for eachfile in self._files:
			eachfile.write(string)

	def writelines(self, lines):
		for eachline in lines:
			self.write(eachline)

	def flush(self):
		for eachfile in self._files:
			eachfile.flush()

	def close(self):
		for eachfile in self._files:
			self.remfile(eachfile) # Don't CLOSE the real files.

	def CLOSE(self):
		for eachfile in self._files:
			self.remfile(eachfile)
			#self.eachfile.close()
			eachfile.close()

	def isatty(self):
		return 0

def ignore_all(*args, **kws):
	pass

def possibly_ignore(arg):
	if DO_DEBUG:
		return arg
	return ignore_all
	

def enableFull():
	"""
	Created: Unknown, KP
	Description: Empties the hide_debug list which allows all log messages to be printed.
	"""
	global HIDE_DEBUG
	HIDE_DEBUG = []

class GUIError(Exception):
	"""
	Created: 13.12.2004, KP
	Description: Displays an error message.
	"""
	def __init__(self, title, msg):
		"""
		Created: 13.12.2004, KP
		Description: Constructor
		Parameters:
			title	   Title for the error message
			msg		   The actual error message
		"""
		Exception.__init__(self)
		self.msg = msg
		self.title = title
		self.wx = wx

	def show(self):
		"""
		Created: 13.12.2004, KP
		Description: Displays the error message in a tkMessageBox.
		"""
		dlg = self.wx.MessageDialog(None, self.msg, self.title, wx.OK|wx.ICON_ERROR)
		dlg.ShowModal()
		dlg.Destroy()

	def __str__(self):
		"""
		Created: 13.12.2004, KP
		Description: Returns the error message in a string.
		"""
		return "[Error: %s: %s]" % (self.title, self.msg)

	def __repr__(self):
		"""
		Created: 13.12.2004, KP
		Description: Returns the error message in a string.
		"""
		return str(self)

#@possibly_ignore
def error(title, msg, xframe = sys._getframe()):
	"""
	Created: 13.12.2004, KP
	Description: Raises an GuiError.
	Parameters:
			title	   Title for the error message
			msg		   The actual error message
	"""
	outfile.write("%s: %s" % (xframe.f_code.co_filename, xframe.f_lineno) + " ERROR: %s\n" % msg)
	raise GUIError(title, "%s: %s" % (xframe.f_code.co_filename, xframe.f_lineno) + " " + msg)

#@possibly_ignore
def info(msg, *args, **kws):
	"""
	Function: info
	Created: 13.12.2004, KP
	Description: Prints information
	Parameters:
			msg		   The message
			args	   Arguments to be converted to strings and printed along with message
	"""
	xframe = sys._getframe(1)

	if "kw" in kws and kws["kw"] not in KWS:
		raise Exception("Unknown keyword "+kws["kw"])

	if not ("kw" in kws) or (("kw" in kws) and (kws["kw"] not in HIDE_DEBUG)):
		fileName = os.path.split(xframe.f_code.co_filename)[-1]
		lineno = xframe.f_lineno
		argstring = " ".join([str(arg) for arg in args])
		outfile.write("%s:%d: %s %s\n"%(fileName, lineno, msg, argstring))

#@possibly_ignore
def backtrace():
	"""
	Function: info
	Created: 02.07.2005, KP
	Description: Prints backtrace of callers
	"""
	i = 0
	xframe = sys._getframe(1)
	fileInBackTrace = os.path.split(xframe.f_code.co_filename)[-1]
	lineno = xframe.f_lineno
	outfile.write("%s:%d: Generating backtrace of calls:\n"%(fileInBackTrace, lineno))
	
	indent = -1
	oldfile = None
	while 1:
		try:
			frame = sys._getframe(i)
		except ValueError:
			break
		fileInBackTrace = os.path.split(frame.f_code.co_filename)[-1]
		if fileInBackTrace != oldfile:
			indent += 1
		oldfile = fileInBackTrace
		lineno = frame.f_lineno
		function = frame.f_code.co_name
		indentstr = "  "*indent
		outfile.write("%sFile %s, function %s on line %d\n" % (indentstr, fileInBackTrace, function, lineno))
		i += 1
