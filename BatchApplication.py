import lib.FilterBasedModule
import Modules.DynamicLoader
import os
import scripting

class BatchMainWindow:
	"""
	Created: 03.01.2008, KP
	Description: a MainWindow object for handling the required user interface i/o like progress events
	"""
	def __init__(self):
		"""
		Created: 03.01.2008, KP
		Description: initialize
		"""
	def updateProgressBar(self, obj, evt, progress, text, *args):
		"""
		Created: 03.01.2008, KP
		Description: print progress report
		"""
		print "%d%% %s"%(int(100*progress), text)
		
class BXDBatchApplication:
	"""
	Created: 01.01.2008, KP
	Description: Initialize the batch processor app
	"""
	def __init__(self):
		pluginLoader = Modules.DynamicLoader.getPluginLoader()
		taskMod = pluginLoader.getPluginModule("Task", "Process")
		unitType = taskMod.getDataUnit()
		moduleType = pluginLoader.getPluginClass("Task","Process")
		self.dataUnit = unitType()
		self.readers = Modules.DynamicLoader.getReaders()
		self.extToSource = {}
		for modeclass, ign, module in self.readers.values():
			exts = module.getExtensions()
			for ext in exts:
				self.extToSource[ext] = modeclass
		module = moduleType()
		self.dataUnit.setModule(module)
		
		self.mainwin = BatchMainWindow()
		scripting.app = self
		scripting.mainWindow = self.mainwin
		
	def setFilters(self, filterList, filterParams):
		"""
		Created: 01.01.2008, KP
		Description: set the list of filters in the procedure stack, and 
					 their corresponding parameters
		"""
		self.filterList = filterList
		self.filterParams = filterParams

				
	def loadFiles(self, filelist, selectedChannels = {}):
		"""
		Created: 02.01.2008, KP
		Description: load a list of files
		"""
		dataunits = []
		for filename in filelist:
			chls = []
			try:
				intchls = map(int,chls)
			except:
				intchls = []

			if filename in selectedChannels:
				chls = selectedChannels[filename]
			name, ext = os.path.splitext(filename)
			if ext:
				ext=ext[1:].lower()
			if ext not in self.extToSource: 
				continue
			datasource = self.extToSource[ext]()
			newDataunits = datasource.loadFromFile(filename)
			selectedUnits = []
			if intchls:
				for index in intchls and len(newDataunits)<=index:
					print "Selecting ch",index,newDataunits[index].getName()
					selectedUnits.append(newDataunits[index])
			if chls:
				for unit in newDataunits:
					if unit.getName() in chls:
						print "Selecting ch by name",unit.getName(),chls
						selectedUnits.append(unit)
					
			if not selectedUnits: selectedUnits = newDataunits
			dataunits += selectedUnits
		return dataunits

	def run(self, files, scriptfile, name = "", outputFile = "output.bxd", timepoints = [], selectedChannels = {}):
		"""
		Created: 01.01.2008
		Description: Run the procedure list
		"""
		dataunits = self.loadFiles(files, selectedChannels)
		for dataunit in dataunits:
			self.dataUnit.addSourceDataUnit(dataunit)
		filterList = lib.FilterBasedModule.FilterList()
		filterList.setDataUnit(self.dataUnit)
		filterList.populate(self.filterList)
		
		for fname in self.filterList:
			if fname not in self.filterParams:
				continue
			
			for key,val in self.filterParams[fname].items():
				filterIndex = filterList.getIndexForName(fname)
				currentFilter = filterList.getFilter(filterIndex)
				currentFilter.setParameter(key, val)

		self.dataUnit.getSettings().set("FilterList", filterList)
		if not name:
			name, ext = os.path.splitext(outputFile)
			name = os.path.basename(name)
		self.dataUnit.getSettings().set("Name",name)
		print "Output file name",outputFile
		if not timepoints:
			timepoints = range(0, max([x.getNumberOfTimepoints() for x in dataunits]))
		filename = self.dataUnit.doProcessing(outputFile, timepoints = timepoints)
		print "Created",filename
	