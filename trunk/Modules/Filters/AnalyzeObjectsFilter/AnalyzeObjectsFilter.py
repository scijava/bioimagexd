import lib.ProcessingFilter
import lib.FilterTypes
import scripting

import GUI.GUIBuilder
import itk
import vtkbxd
import WatershedStatisticsList
import wx
import os
import codecs
import Logging
import csv

class AnalyzeObjectsFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	"""		
	name = "Analyze objects"
	category = lib.FilterTypes.MEASUREMENT
	level = scripting.COLOR_BEGINNER
	def __init__(self, inputs = (2, 2)):
		"""
		Initialization
		"""		   
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.itkFlag = 1
		self.descs = {}		 
		self.values = None
		self.centersofmass = None
		self.avgintCalc = None
		self.umcentersofmass = None
		self.avgIntList = None
		self.descs = {"StatisticsFile": "Results file:"}
		
		
		self.resultVariables = {"NumberOfObjects":		"Number of discrete objects in the image",
								"ObjAvgSizeInPixels":	"Average object size, in pixels",
								"ObjAvgSizeInUm":		"Average object size, in micrometers",
								"ObjAvgIntensity":		"Average intensity of objects",
								"AvgIntOutsideObjs":    "Average intensity of voxels outside the objects",
								"AvgIntInsideObjs":		"Average intensity of voxels inside the objects",
								"NonZeroVoxels":		"The number of non-zero voxels"
								}
		
		self.reportGUI = None
		self.itkfilter = None
		
	def getInputName(self, n):
		"""
		Return the name of the input #n
		"""			 
		if n == 1: return "Segmented image"
		return "Source dataset" 
		
	def setDataUnit(self, dataUnit):
		"""
		a method to set the dataunit used by this filter
		"""
		lib.ProcessingFilter.ProcessingFilter.setDataUnit(self, dataUnit)
		self.parameters["StatisticsFile"] = self.getDefaultValue("StatisticsFile")
			
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""	   
		if not self.dataUnit:
			return "statistics.csv"
		else:
			return self.dataUnit.getName() + ".csv"
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		return GUI.GUIBuilder.FILENAME
		
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Measurement results",
		(("StatisticsFile", "Select the file to which the statistics will be writen", "*.csv"), )]]
		
	def writeOutput(self, dataUnit, timepoint):
		"""
		Optionally write the output of this module during the processing
		"""
		fileroot = self.parameters["StatisticsFile"].split(".")
		fileroot = ".".join(fileroot[:-1])
		dircomp = os.path.dirname(fileroot)
		if not dircomp:
			bxddir = dataUnit.getOutputDirectory()
			fileroot = os.path.join(bxddir, fileroot)
		filename = "%s.csv" % fileroot
		self.writeToFile(filename, dataUnit, timepoint)
		
	def writeToFile(self, filename, dataUnit, timepoint):
		"""
		write the objects from a given timepoint to file
		"""
		f = codecs.open(filename, "awb", "latin1")
		Logging.info("Saving statistics to file %s"%filename, kw="processing")
		
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		
		settings = dataUnit.getSettings()
		settings.set("StatisticsFile", filename)
		w.writerow(["Timepoint %d" % timepoint])
		w.writerow(["Object #", "Volume (micrometers)", "Volume (pixels)", "Center of Mass", \
					"Center of Mass (micrometers)", "Avg. Intensity"])
		for i, (volume, volumeum) in enumerate(self.values):
			cog = self.centersofmass[i]
			umcog = self.umcentersofmass[i]
			avgint = self.avgIntList[i]
			w.writerow([str(i + 1), str(volumeum), str(volume), str(cog), str(umcog), str(avgint)])
		f.close()

	def getGUI(self, parent, taskPanel):
		"""
		Return the GUI for this filter
		"""
		gui = lib.ProcessingFilter.ProcessingFilter.getGUI(self, parent, taskPanel)
		
		if not self.reportGUI:
			self.reportGUI = WatershedStatisticsList.WatershedObjectList(self.gui, -1)
			
			self.totalGUI =  WatershedStatisticsList.WatershedTotalsList(self.gui, -1)
			
			self.exportBtn = wx.Button(self.gui, -1, "Export statistics")
			self.exportBtn.Bind(wx.EVT_BUTTON, self.onExportStatistics)
			if self.values:
	
				n = len(self.values)
				avgints = float(AnalyzeObjectsFilter.averageValue(self.avgIntList))
				ums = [x[1] for x in self.values]
				
				# Remove the objects 0 and 1 because hey will distort the values
				avgums = float(AnalyzeObjectsFilter.averageValue(ums))
				pxs = [x[0] for x in self.values]
				avgpxs = float(AnalyzeObjectsFilter.averageValue(pxs))
				
				self.totalGUI.setStats([n, avgums, avgpxs, avgints, self.avgIntOutsideObjs])
				self.reportGUI.setVolumes(self.values)
				self.reportGUI.setCentersOfMass(self.centersofmass)
				self.reportGUI.setAverageIntensities(self.avgIntList)
			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.reportGUI, 1)
			sizer.Add(self.totalGUI, 1)
			sizer.AddSpacer((5,5))
			sizer.Add(self.exportBtn)
			sizer.AddSpacer((5,5))
			gui.sizer.Add(sizer, (1, 0), flag = wx.EXPAND | wx.ALL)
		return gui


	def onExportStatistics(self, evt):
		"""
		export the statistics from the objects list
		"""
		name = self.dataUnit.getName()
		filename = GUI.Dialogs.askSaveAsFileName(self.taskPanel, "Save segmentation statistics as", \
													"%s.csv" % name, "CSV File (*.csv)|*.csv")
		if filename and self.taskPanel:
			listOfFilters = self.taskPanel.filterList.getFilters()
			filterIndex = listOfFilters.index(self)
			func = "getFilter(%d)" %(filterIndex)
			n = scripting.mainWindow.currentTaskWindowName
			method="scripting.mainWindow.tasks['%s'].filterList.%s"%(n,func)
		
			do_cmd = "%s.exportStatistics('%s')" % ( method, filename )
			cmd = lib.Command.Command(lib.Command.GUI_CMD, None, None, do_cmd, "", \
										desc = "Export segmented object statistics")
			cmd.run()

	@staticmethod
	def averageValue(lst):
		"""
		"""
		if len(lst) == 0:
			return 0.0	
		return sum(lst) / len(lst)
		
	def exportStatistics(self, filename):
		"""
		write the statistics from the current timepoint to a csv file
		"""
		timepoint = scripting.visualizer.getTimepoint()
		self.writeToFile(filename, self.dataUnit, timepoint)
   
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		image = self.getInput(1)
		image = self.convertVTKtoITK(image)
		print "Input for label shape=",self.getInputDataUnit(1)
		print "Orig. dataunit = ",self.getInputDataUnit(2)
		self.itkfilter = itk.LabelShapeImageFilter[image].New()
		self.itkfilter.SetInput(image)
		self.itkfilter.Update()
		data = self.itkfilter.GetOutput()
			
		x, y, z = self.dataUnit.getVoxelSize()
		x *= 1000000
		y *= 1000000
		z *= 1000000
		vol = x * y * z
		
		voxelSizes = [x, y, z]
		n = self.itkfilter.GetNumberOfLabels()
		values = []
		centersofmass = []
		umcentersofmass = []
		avgints = []
		
		vtkimage = self.convertITKtoVTK(image, force = 1)
		origInput = self.getInput(2)
		origInput.Update()
		
		if self.avgintCalc:
			del self.avgintCalc
		self.avgintCalc = avgintCalc = vtkbxd.vtkImageLabelAverage()

		# We require unsigned long input data
		if vtkimage.GetScalarType() != 9:
			cast = vtk.vtkImageCast()
			cast.SetInput(vtkimage)
			cast.SetOutputScalarTypeToUnsignedLong()
			cast.Update()
			vtkimage = cast.GetOutput()
			n = int(vtkimage.GetScalarRange()[1])+1
			
		avgintCalc.AddInput(origInput)
		avgintCalc.AddInput(vtkimage)

		avgintCalc.Update()
		ignoreLargest = 0
		currFilter = self
		while currFilter:
			if currFilter.ignoreObjects > ignoreLargest:
				ignoreLargest = currFilter.ignoreObjects
			currFilter = currFilter.prevFilter
		
		startIntensity = ignoreLargest
		print "Ignoring",startIntensity,"first objects"
		self.avgintCalc.SetBackgroundLevel(startIntensity)
			
		for i in range(startIntensity, n):
			if not self.itkfilter.HasLabel(i):
				centersofmass.append((0, 0, 0))
				values.append((0, 0))
				avgints.append(0.0)
				umcentersofmass.append((0, 0, 0))
			else:
				volume = self.itkfilter.GetVolume(i)
				centerOfMass = self.itkfilter.GetCenterOfGravity(i)
				avgInt = avgintCalc.GetAverage(i)
				c = []
				c2 = []
				for i in range(0, 3):
					v = centerOfMass.GetElement(i)
					c.append(v)
					c2.append(v * voxelSizes[i])
				centersofmass.append(tuple(c))
				umcentersofmass.append(tuple(c2))
				values.append((volume, volume * vol))
				avgints.append(avgInt)
		self.values = values
		self.centersofmass = centersofmass
		self.umcentersofmass = umcentersofmass
		self.avgIntList = avgints

		n = len(self.values)
		avgints = AnalyzeObjectsFilter.averageValue(self.avgIntList)
		ums = [x[1] for x in values]
		avgums = AnalyzeObjectsFilter.averageValue(ums)
		pxs = [x[0] for x in values]
		avgpxs = AnalyzeObjectsFilter.averageValue(pxs)
		
		avgIntOutsideObjs = self.avgintCalc.GetAverageOutsideLabels()
		avgIntInsideObjs = self.avgintCalc.GetAverageInsideLabels()
		nonZeroVoxels = self.avgintCalc.GetNonZeroVoxels()
		
		self.avgIntOutsideObjs = avgIntOutsideObjs
			
		self.setResultVariable("NumberOfObjects",len(values))
		self.setResultVariable("ObjAvgSizeInPixels",avgpxs)
		self.setResultVariable("ObjAvgSizeInUm",avgums)
		self.setResultVariable("ObjAvgIntensity",avgints)
		self.setResultVariable("AvgIntOutsideObjs", avgIntOutsideObjs)
		self.setResultVariable("AvgIntInsideObjs", avgIntInsideObjs)
		self.setResultVariable("NonZeroVoxels", nonZeroVoxels)
		
		if self.reportGUI:
			self.reportGUI.DeleteAllItems()
			self.reportGUI.setVolumes(values)
			self.reportGUI.setCentersOfMass(centersofmass)
			self.reportGUI.setAverageIntensities(self.avgIntList)

			print "avgints=",avgints
			print "avgIntOutsidebjs=",avgIntOutsideObjs
			print "avgIntInsideObjs=",avgIntInsideObjs
			self.totalGUI.setStats([n, avgums, avgpxs, avgints, avgIntOutsideObjs])
			
		return self.getInput(1)
