#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: BioImageXD
 Project: BioImageXD
 Created: 01.11.2004, KP
 Description:

 BioImageXD main program

 Copyright (C) 2005, 2006  BioImageXD Project
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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import sys
import StringIO
import os.path
import os
import getopt
import codecs
import platform
# We need to import VTK here so that it is imported before wxpython.
# if wxpython gets imported before vtk, the vtkExtTIFFReader will not read the olympus files
# DO NOT ask me why that is!
import vtk
import wx
import Configuration
import scripting
import Logging
import glob
import GUI.MainWindow
import GUI.SplashScreen

try:
	import profile
except ImportError:
	profile = None

todir = scripting.get_main_dir()
if todir:
	os.chdir(todir)

if not todir:
	todir = os.getcwd()
if platform.system()=="Windows":
	itkpkg = os.path.join(todir, "ITK-pkg")
	if os.path.exists(itkpkg):
		itklibdir = os.path.join(itkpkg, "lib")
		itkpydir = os.path.join(itkpkg, "Python")
		sys.path.insert(0, itklibdir)
		sys.path.insert(0,itkpydir)
		path = os.getenv("PATH")
		path = path + os.path.pathsep + itklibdir
		os.putenv("PATH", path)
		
if scripting.main_is_frozen() and platform.system()=="Darwin":
	import site
	site.addsitedir(os.environ["RESOURCEPATH"]+"/InsightToolkit/WrapITK/Python")
	site.addsitedir(os.environ["RESOURCEPATH"]+"/InsightToolkit/WrapITK/lib")

# This will fix the VTK paths using either values from the
# configuration file, or sensible defaults

conffile = os.path.join(scripting.get_config_dir(), "BioImageXD.ini")
conf = Configuration.Configuration(conffile)

w = vtk.vtkOutputWindow()
i = w.GetInstance()

def exceptHook(type, value, traceback):
	"""
	Created: 16.10.2007, KP
	Description: mark an unhandled exception as happened
	"""
	scripting.unhandledException = 1
	sys.__excepthook__(type, value, traceback)
	
sys.excepthook = exceptHook

def onWarning(obj, evt, *args):
	"""
	Created: Unknown date, KP
	Description: Show VTK error messages
	"""
	Logging.backtrace()
	print "VTK message:\n", evt

w.AddObserver("WarningEvent", onWarning)
w.AddObserver("ErrorEvent", onWarning)

class LSMApplication(wx.App):
	"""
	Created: 03.11.2004, KP
	Description: Encapsulates the wxPython initialization and mainwindow creation
	"""
	def OnInit(self):
		"""
		Created: 10.1.2005, KP
		Description: Create the application's main window
		"""
		self.SetAppName("BioImageXD")
		iconpath = scripting.get_icon_dir()

		splashimage = os.path.join(iconpath, "splash2.jpg")
		self.splash = GUI.SplashScreen.SplashScreen(None, duration = 99000, bitmapfile = splashimage)
		self.splash.Show()
		self.splash.SetMessage("Loading BioImageXD...")
		provider = wx.SimpleHelpProvider()
		wx.HelpProvider_Set(provider)

		self.mainwin = GUI.MainWindow.MainWindow(None, -1, self, self.splash)
		self.mainwin.config = wx.Config("BioImageXD", style = wx.CONFIG_USE_LOCAL_FILE)
		scripting.app = self
		scripting.mainWindow = self.mainwin

		self.mainwin.Show(True)
		self.SetTopWindow(self.mainwin)

		return True

	def macOpenFile(self, filename):
		"""
		Created: 14.03.2007, KP
		Description: open a file that was dragged on the app
		"""
		self.mainwin.loadFiles([filename])

	def run(self, files, scriptfile):
		"""
		Created: 03.11.2004, KP
		Description: Run the wxPython main loop
		"""
		if files:
			self.mainwin.loadFiles(files)

		if scriptfile:
			self.splash.SetMessage("Loading script file %s..."%scriptfile)
			self.mainwin.loadScript(scriptfile)
		self.MainLoop()

def usage():
	"""
	Created: Unknown, KP
	Description: Prints command line usage of program
	"""
	print "Usage: BioImageXD [-h|--help] | [-x script.bxs|--execute=script.bxs] [-i file|--input=file]\
[-d directory|--directory=directory]"
	print ""
	print "-x | --execute\tExecute the given script file"
	print "-i | --input\tLoad the given file as default input"
	print "-d | --directory\tLoad all files from given directory"
	print "-t | --tofile\tLog all messages to a log file"
	print "-l | --logfile\tLog all messages to given file"
	print "-p | --profile\tProfile the execution of the program"
	print "-P | --interpret\tInterpret the results of the profiling"

	sys.exit(2)

if __name__ == '__main__':
	if "py2exe" in sys.argv or "py2app" in sys.argv:
		import build_app
		build_app.build()
		#from build_app import *
		#build()
	else:
		try:
			parameterList = ["help", "execute=", "input=", "directory=", "tofile", "profile", "interpret", "logfile"]
			opts, args = getopt.getopt(sys.argv[1:], 'hx:i:d:tpPl', parameterList)
		except getopt.GetoptError:
			usage()

		toFile = 0
		doProfile = 0
		doInterpret = 0
		scriptFile = ""
		logfile = ""
		logdir = ""
		dataFiles = []
		for opt, arg in opts:
			if opt in ["-h", "--help"]:
				usage()
			elif opt in ["-x", "--execute"]:
				scriptFile = arg
			elif opt in ["-d", "--directory"]:
				dataFiles = glob.glob(os.path.join(arg, "*"))
			elif opt in ["-i", "--input"]:
				dataFiles = [arg]
			elif opt in ["-t", "--tofile"]:
				toFile = 1
			elif opt in ["-p", "--profile"]:
				doProfile = 1
			elif opt in ["-P", "--interpret"]:
				doInterpret = 1
			elif opt in ["-l", "--logfile"]:
				logfile = arg
		dataFiles.extend(args)
		# If the main application is frozen, then we redirect logging
		# to  a log file
		#TODO: Why create a new variable logFile in scripting? Shouldn't it just be logFile
		captureOutput = StringIO.StringIO()
		scripting.logFile = captureOutput
		if toFile or scripting.main_is_frozen():
			import time
			if not logfile:
				logfile = time.strftime("output_%d.%m.%y@%H%M.log")

				logdir = scripting.get_log_dir()
				if not os.path.exists(logdir):
					os.mkdir(logdir)
				logfile = os.path.join(logdir, logfile)
			timestampedLogfile = codecs.open(logfile, "w","utf-8")
			if logdir:
				logfile2 = os.path.join(logdir, "latest.log")
				latestLogfile = codecs.open(logfile2, "w","utf-8")
				logFiles = Logging.Tee(timestampedLogfile, latestLogfile, captureOutput)
			clean = eval(conf.getConfigItem("CleanExit", "General"))
			if not clean:
				scripting.uncleanLog = conf.getConfigItem("LastLogFile", "General")
			else:
				scripting.uncleanLog = None

			conf.setConfigItem("LastLogFile", "General", logfile)
			import atexit
			atexit.register(logFiles.flush)
			sys.stdout = logFiles
			sys.stderr = logFiles
			Logging.outfile = logFiles
			Logging.enableFull()
		else:
			logFiles = Logging.Tee("encode", sys.stdout, captureOutput)
			sys.stdout = logFiles
			sys.stderr = logFiles
			Logging.outfile = logFiles

		if doInterpret:
			import pstats
			p = pstats.Stats('prof.log')
			p.sort_stats('time', 'cum').print_stats(.5, 'init')
			sys.exit(0)

		conf.setConfigItem("CleanExit", "General", "False")
		conf.writeSettings()
		app = LSMApplication(0)
		toRemove = []
		for datafile in dataFiles:
			if os.path.isdir(datafile):
				toRemove.append(datafile)
		for fileToBeRemoved in toRemove:
			dataFiles.remove(fileToBeRemoved)

		if doProfile and profile:
			profile.run('app.run(dataFiles, scriptFile)', 'prof.log')
		else:
			app.run(dataFiles, scriptFile)
