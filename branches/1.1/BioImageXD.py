#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""
 Unit: BioImageXD
 Project: BioImageXD
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

import uuid # OME-TIFF writer will crash if not imported first
import sys
import StringIO
import os.path
import os
import getopt
import codecs
import platform

# Add path to VTK and ITK libraries if we are running under Linux and this is
# Linux package installation
if platform.system() == "Linux" or platform.system()=="Darwin":
	bxdPath = os.path.dirname(sys.argv[0])
	if len(bxdPath) > 0:
		curdir = os.path.abspath(bxdPath)
	else:
		curdir = os.path.abspath(os.path.curdir)

	if platform.system() == "Linux" and os.path.exists(curdir + "/VTK") and os.path.exists(curdir + "/ITK"):
		sys.path.insert(0,curdir + '/VTK/lib/python2.6/site-packages/VTK-5.6.0-py2.6.egg')
		sys.path.insert(0,curdir + '/VTK/lib/python2.6/site-packages')
		sys.path.insert(0,curdir + '/ITK/lib/InsightToolkit/WrapITK/Python')
	if platform.system()=="Darwin":
		sys.path.insert(0,curdir + '/Libraries/python2.7/site-packages/')
		sys.path.insert(0,curdir + '/Libraries/InsightToolkit/WrapITK/Python/')


# We need to import VTK here so that it is imported before wxpython.
# if wxpython gets imported before vtk, the vtkExtTIFFReader will not read the olympus files
# DO NOT ask me why that is!
import vtk
import Configuration
import scripting
import Logging
import glob


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
		itklibdir = os.path.join(itklibdir, "Release")
		itkpydir = os.path.join(itkpkg, "Python")
		itkpydir = os.path.join(itkpydir, "Release")
		sys.path.insert(0, itklibdir)
		sys.path.insert(0, itkpydir)
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
	mark an unhandled exception as happened
	"""
	scripting.unhandledException = 1
	sys.__excepthook__(type, value, traceback)
	
sys.excepthook = exceptHook

def onWarning(obj, evt, *args):
	"""
	Show VTK error messages
	"""
	Logging.backtrace()
	print "VTK message:\n", evt

w.AddObserver("WarningEvent", onWarning)
w.AddObserver("ErrorEvent", onWarning)


def usage():
	"""
	Prints command line usage of program
	"""
	print "Usage: BioImageXD [options]"
	print ""
	print "General options:"
	print "-x | --execute\tExecute the given script file"
	print "-i | --input\tLoad the given file as default input"
	print "-d | --directory\tLoad all files from given directory"
	print "-t | --tofile\tLog all messages to a log file"
	print "-l | --logfile\tLog all messages to given file"
	print "-p | --profile\tProfile the execution of the program"
	print "-P | --interpret\tInterpret the results of the profiling"
	print "-b | --batch\tExecute the software in batch mode"
	print ""
	print "Options available only in batch mode:"
	print "-f <filter> | --load-filter\tLoad a filter to the procedure stack"
	print "-n <name>   | --name=name\tSet the name of the output dataset"
	print "-s <var>=<val>,<var2>=<val2> | --set-variable\tSet a variable to a value"
	print "-o <file>   | --output=<file>\tOutput the resulting dataset to the given file"
	print "-T 0,1,3-5  | --timepoints=<timepoints>\tSelect the timepoints to process"
	print "-c 0,1	   | --channels=0,1\tSelect the channels to use from the input file"
	print "-B 		   | --bba=<file>\tExecute the selected batch analysis file"
	sys.exit(2)

if __name__ == '__main__':
	if "py2exe" in sys.argv or "py2app" in sys.argv:
		import build_app
		build_app.build()
		#from build_app import *
		#build()
	else:
		try:
			parameterList = ["name=","channels=","help", "batch","execute=", "input=", "directory=", "tofile", "profile", "interpret", "logfile","load-filter","set-variable","output=","timepoints=","bba="]
			opts, args = getopt.getopt(sys.argv[1:], 'n:c:hbx:i:d:tpPlf:s:o:T:B:', parameterList)
		except getopt.GetoptError:
			usage()

		
		toFile, doProfile, doInterpret, doBatch = False, False, False, False
		scriptFile, logfile, logdir, currentFilter = "", "", "", ""
		dataFiles = []
		app = None
		outputFile = "output.bxd"
		currentInputFileName=""
		filterList = []
		filterParams = {}
		selectedChannels = {}
		timepoints = []
		outputName = ""
		batchAnalysis = ""

		for opt, arg in opts:
			if opt in ["-h", "--help"]:
				usage()
			elif opt in ["-n","--name"]:
				outputName = arg
			elif opt in ["-c","--channels"]:
				selectedChannels[currentInputFileName] = arg.split(",")
			elif opt in ["-x", "--execute"]:
				scriptFile = arg
			elif opt in ["-d", "--directory"]:
				dataFiles = glob.glob(3(arg, "*"))
			elif opt in ["-B","--bba"]:
				batchAnalysis = arg
			elif opt in ["-i", "--input"]:
				dataFiles.append(arg)
				currentInputFileName=arg
			elif opt in ["-t", "--tofile"]:
				toFile = 1
			elif opt in ["-p", "--profile"]:
				doProfile = 1
			elif opt in ["-P", "--interpret"]:
				doInterpret = 1
			elif opt in ["-l", "--logfile"]:
				logfile = arg
			elif opt in ["-b","--batch"]:
				doBatch = True
			elif opt in ["-o","--output"]:
				outputFile = arg
			elif opt in ["-T","--timepoints"]:
				tplist = arg.split(",")
				timepoints = []
				for iter in tplist:
					if "-" not in iter:
						timepoints.append(int(iter))
					else:
						interval = map(int,iter.split("-"))
						timepoints.extend(range(interval[0],interval[1]+1))
			elif opt in ["-f","--load-filter"]:
				currentFilter = arg
				filterList.append(arg)
			elif opt in ["-s","--set-variable"]:
				for stmnt in arg.split(","):
					key, val = stmnt.split("=")
					val = eval(val)
					if currentFilter:
						if currentFilter not in filterParams:
							filterParams[currentFilter] = {}
						filterParams[currentFilter][key] = val
				
		
		if doBatch:
			import BatchApplication
			app = BatchApplication.BXDBatchApplication()

		dataFiles.extend(args)
		# If the main application is frozen, then we redirect logging
		# to  a log file
		#TODO: Why create a new variable logFile in scripting? Shouldn't it just be logFile
		captureOutput = StringIO.StringIO()
		scripting.logFile = captureOutput
		
		if toFile or scripting.main_is_frozen():
			import time
			if not logfile:
				logfile = time.strftime("bioimagexd_%d.%m.%y@%H%M.log")

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
		if not app:
			import GUIApplication
			app = GUIApplication.BXDGUIApplication(0)
		toRemove = []
		if doBatch:
			app.setFilters(filterList, filterParams)
			
		for datafile in dataFiles:
			if os.path.isdir(datafile):
				toRemove.append(datafile)
		for fileToBeRemoved in toRemove:
			dataFiles.remove(fileToBeRemoved)


		if doProfile and profile:
			profile.run('app.run(dataFiles, scriptFile)', 'prof.log')
		else:
			params = {}
			if outputName:params["name"] = outputName
			app.run(dataFiles, scriptFile, outputFile = outputFile, timepoints = timepoints,
				selectedChannels = selectedChannels, batchAnalysis = batchAnalysis, **params)
