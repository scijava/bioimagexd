# -*- coding: iso-8859-1 -*-

"""
 Unit: BatchAnalysis
 Project: BioImageXD
 Created: 25.11.2007, KP
 Description:

 The batch analysis model class for the BioImageXD Batch Analyzer
 
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

import Modules.DynamicLoader
import lib.FilterBasedModule
import codecs
import csv
import ConfigParser
import zipfile
import os
import re
import scripting

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
		self.numRE = re.compile("[0-9]+")
		
		self.procedureLists = {}
		self.selectedList = ""
		
		self.channelGrouping = 0
		self.channelProcessing = 0
		self.procListGrouping = 0
		self.filterIndexes = {}
		
	def renameList(self, name, newName):
		"""
		Created: 04.12.2007, KP
		Description: rename a given procedure list
		"""
		if name == newName:
			return
		lst = self.procedureLists.get(name, None)
		if lst:
			self.procedureLists[newName] = lst
			del self.procedureLists[name]
			self.selectedList = newName
			if name in self.selectedVariables:
				selectedVars = self.selectedVariables[name]
				self.selectedVariables[newName] = selectedVars
				del self.selectedVariables[name]
		else:
			raise Logging.GUIError("Could not rename procedure list",
			"""Failed to rename the procedure list. No list with
the name '%s' was found. Existing lists are: %s"""%(name, ", ".join(self.procedureLists.keys())))
	def getFileName(self):
		"""
		Created: 1.12.2007, KP
		Description: return the filename as which the analysis is being saved
		"""
		return self.filename
		
	def setProcedureListGrouping(self, value):
		"""
		Created: 1.12.2007, KP
		Description: select whether to group the processed channels by the procedure list or not
		"""
		self.procListGrouping = value
		
	def setChannelGrouping(self, value):
		"""
		Created: 1.12.2007, KP
		Description: select whether to group channels or not
		"""
		self.channelGrouping = value
		
	def setChannelGroupingByProcedureList(self, value):
		"""
		Created: 07.12.2007, KP
		Description: Set the grouping of channels of a single file that are
					 processed by different procedure lists
		"""
		self.procListGrouping = value
		
	def setChannelProcessing(self, value):
		"""
		Created: 1.12.2007, KP
		Description: Set the way the channnels are processed. Valid values are:
			0	Each channel of a file is processed separately through the procedure lists
			1	All the channels in a single file are passed as input to a procedure list
		"""
		self.channelProcessing = value
		
	def sortNumerically(self, item1, item2):
		"""
		Created: 17.03.2005, KP
		Description: A method that compares two filenames and sorts them by the number in their filename
		"""   
		r = self.numRE
		s = r.findall(item1)
		s2 = r.findall(item2)
		if len(s) != len(s2):
			return len(s).__cmp__(len(s2))
		if len(s) == 1:
			n = int(s[0])
			n2 = int(s2[0])
			return n.__cmp__(n2)
		else:
			for i in range(len(s)):
				i1 = int(s[i])
				i2 = int(s2[i])
				if len(s[i]) < len(s2[i]):
					return - 1
				c = i1.__cmp__(i2)
				if c != 0:
					return c
		return cmp(item1, item2)

	def getGroupedDataUnits(self):
		"""
		Created: 1.12.2007, KP
		Description: return the source data units grouped according to how the user has selected
					 in the GUI
		"""
		if self.channelProcessing == PROCESS_SEPARATELY:
			def s(x,y): return self.sortNumerically(x.getFileName(), y.getFileName())
			self.inputDataUnits.sort(s)
			return [[x] for x in self.inputDataUnits]
		
		return self.getDataUnitsByFilename()
		

	def getDataUnitsByFilename(self):
		"""
		Created: 1.12.2007, KP
		Description: return the dataunits grouped by the filenames
		"""
		perFile = {}
		filenames = []
		for dataUnit in self.inputDataUnits:
			filename = dataUnit.getFileName()
			filenames.append(filename)
			if filename not in perFile:
				perFile[filename] = []
			perFile[filename].append(dataUnit)
			
		filenames.sort(self.sortNumerically)
		return [perFile[x] for x in filenames]
#		return perFile.values()

	def createSingleGroupedBXDFile(self, directory, procListName, dataUnits):
		"""
		Created: 1.12.2007, KP
		Description: Create a bxd file that groups the selected dataunits.
					 This is used when the option to process each channel separately is selected,
					 instead of having all channels as input
		"""
		bxdFile = procListName+"_"+"_".join([x.getName() for x in dataUnits])+".bxd"
		f = open(os.path.join(directory, bxdFile), "w")
		for dataUnit in dataUnits:
			fileBase = procListName+"_"+os.path.basename(dataUnit.getFileName())+"_"+dataUnit.getName()
			bxcFile = os.path.join(fileBase, fileBase+".bxc")
			f.write("%s\n"%bxcFile)
		f.close()
			
			
	def createProcListGroupedBXDFile(self, directory, writtenOutFilenames):
		"""
		Created: 07.12.2007, KP
		Description: Write out a bxd file that groups together all the channels of the source datasets.
					 This is used when the option to use all channels as input is selected
		"""
		origFileToOutput = {}
		for origFile, outputFile in writtenOutFilenames:
			lst = origFileToOutput.get(origFile, [])
			lst.append(outputFile)
			origFileToOutput[origFile] = lst
		
		for origFile in origFileToOutput.keys():
			print "From file",origFile,"there are",origFileToOutput[origFile]
			fileparts = os.path.basename(origFile).split(".")
			bxdFile=".".join(fileparts[:-1])+".bxd"
			bxdFile = os.path.join(directory, bxdFile)
			fp = open(bxdFile, "w")
			print "Writing output to",bxdFile
			for fileName in origFileToOutput[origFile]:
				bxcDir = os.path.basename(os.path.dirname(fileName))
				bxcFile = os.path.basename(fileName)
				parts = bxcFile.split(".")
				if parts[-1].lower()=="bxd":
					bxcFile = ".".join(parts[:-1])+".bxc"
				
				fp.write("%s\n"%os.path.join(bxcDir,bxcFile))
			
	def execute(self, csvfile, directory, timepoints):
		"""
		Created: 1.12.2007, KP
		Description: execute the analysis
		"""
		# Create a CSV file writer
		csvfp = codecs.open(csvfile, "wb", "latin-1")
		csvwriter = csv.writer(csvfp, dialect = "excel", delimiter = ";")
		
		# Get the selected variables
		variables = self.getAllSelectedVariables()
		# variables is a dict where keys are the user assigned names of the result variables
		# and the values are the variables' real names.  We use as headers for the csv file the
		# user given names
		varHeaders = variables.keys()
		# we also write the filename and channels used to produce each of the variables
		csvwriter.writerow(["Filename","Channels"]+varHeaders)
		
		writtenOutDataunits = []
		# Go through each procedure list
		for procListName in self.procedureLists.keys():
			# get the procedure list
			procList = self.procedureLists[procListName]

			# If each of the channels of an image are processed separately, but they are
			# grouped to resulting BXD files that have similiar channel structure as the input
			# files, then we sort the dataunits according to the filenames (getDataUnitsByFilename())
			# and write out a .bxd file for each filename
			if self.channelProcessing == PROCESS_SEPARATELY and self.channelGrouping:
				groupedUnits = self.getDataUnitsByFilename()
				for units in groupedUnits:
					self.createSingleGroupedBXDFile(directory, procListName, units)

			# then go through each dataunit and apply the procedure list
			for dataUnits in self.getGroupedDataUnits():
				self.dataUnit.removeAllInputs()
				
				# The division of what channels should be used as source dataunits is
				# affected by the channel processing option, and determined in getGroupedDataUnits()
				# here we just add the selected dataunits as source dataunits
				for du in dataUnits:
					print "Adding",du,"as input"
					self.dataUnit.addSourceDataUnit(du)
	
				scripting.combinedDataUnit = self.dataUnit
				# We pass a flag directing the procedure list to not re-intialize the filters
				# since that would reset their settings
				procList.setDataUnit(self.dataUnit, initializeFilters = 0)
				self.dataUnit.getSettings().set("FilterList", procList)
				self.dataUnit.getSettings().set("ColorTransferFunction", self.determineColorTransferFunction(procList, dataUnits))

				if self.channelProcessing == PROCESS_TOGETHER:
					nameBase = procListName+"_"+os.path.basename(dataUnits[0].getFileName())

				else:				
					filenames = "_".join([x.getName() for x in dataUnits])
					nameBase = procListName+"_"+os.path.basename(dataUnits[0].getFileName())+"_"+filenames

				self.dataUnit.getSettings().set("Name",nameBase)
				bxdFile = nameBase+".bxd"
				filename = os.path.join(directory, bxdFile)
				
				# Then we do the actual processing
				filename = self.dataUnit.doProcessing(filename, timepoints = timepoints)
				# Store the filename we got as a result along with the filename of the source
				# dataunit. This is done to make it possible to apply the second grouping action
				# where the output of the procedure lists are grouped to bxd files based on
				# their original channel layout. This is done to facilitate, for example,
				# processing each channel with separate procedure list
				writtenOutDataunits.append((dataUnits[0].getFileName(), filename))
		
				# padding is the filename and channel information
				padding = [", ".join([os.path.basename(x.getFileName()) for x in dataUnits]), ", ".join(x.getName() for x in dataUnits)]
				self.writeResults(padding, csvwriter, procListName, procList, varHeaders)

		# If the channels are processed so that all the channels of a file are given as input
		# to a procedure list, and the results should be grouped  so that the output of the
		# different procedure lists follow the original channel layout, then create the 
		# necessary .bxd files (calling createProcListGroupedBXDFile())
		if self.channelProcessing == PROCESS_TOGETHER and self.procListGrouping:
			self.createProcListGroupedBXDFile(directory, writtenOutDataunits)
			
		csvfp.close()
		scripting.combinedDataUnit = None
				
	def writeResults(self, fileNames, csvwriter, procListName, procedureList, varHeaders):
		"""
		Created: 1.12.2007, KP
		Description: write the csv results out
		"""
		selectedVars = self.getSelectedVariables(procListName)
		row=[""]*len(varHeaders)
		for var in selectedVars.keys():
			varName = selectedVars[var]
			if var in varHeaders:
				i = varHeaders.index(var)
				
				reg = re.compile("([0-9]+)$")
				
				try:
					match = reg.search(var)
					n = int(match.groups(0)[0])
				except:
					n= 1
				value = procedureList.getResultVariable(varName, nth = n-1)
				row[i] = value
			else:
				print var,"not found"
		csvwriter.writerow(fileNames + row)
		
		
	def getDataUnit(self):
		"""
		Created: 30.11.2007, KP
		Description: return the dataunit
		"""
		return self.dataUnit
		
	def determineColorTransferFunction(self, procedureList, dataunits):
		"""
		Created: 08.12.2007, KP
		Description: determine the color transfer function out of the source dataunits
		"""
		if len(dataunits)==1:
			return dataunits[0].getColorTransferFunction()
		if len(procedureList.getFilters())==0:
			return dataunits[0].getColorTransferFunction()
		firstFilter = procedureList.getFilters()[0]
		dataUnit = firstFilter.getInputDataUnit(1)
		return dataUnit.getColorTransferFunction()
		
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
			
			if procListName in self.selectedVariables:
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
		print "Setting selected variables to",variables
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
		print "procedure lists=",self.procedureLists
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
		print "\n\n---> Grouped units = ",groupedUnits
		for dataunit in fileList:
			print dataunit.getName(),"has filename",dataunit.getFileName()
		mostChannels = None
		chCount = 0
		for du in groupedUnits:
			if len(du)>chCount:
				chCount = len(du)
				mostChannels = du
		
		for dataUnit in mostChannels:
			print "Adding",dataUnit.getName(),"as input"
			self.dataUnit.addSourceDataUnit(dataUnit)
			