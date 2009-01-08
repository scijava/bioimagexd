import lib.ProcessingFilter
import lib.FilterTypes
import scripting

import GUI.GUIBuilder
import itk
import vtk
import vtkbxd
import WatershedStatisticsList
import wx
import os
import codecs
import Logging
import csv
import math
import time

import lib.Math

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
								"NonZeroVoxels":		"The number of non-zero voxels", 
								"AverageDistance":		"Average distance between two objects",
								"AvgDistanceStdDev":		"Standard deviation of the average distance between two objects"
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
		#if not self.dataUnit:
		return "statistics.csv"
		#else:
		#	return self.dataUnit.getName() + ".csv"
		
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
		fileroot = self.parameters["StatisticsFile"]
		if not self.parameters["StatisticsFile"]:
			fileroot = "statistics.csv"
		fileroot = fileroot.split(".")
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
		f = codecs.open(filename, "ab", "latin1")
		Logging.info("Saving statistics to file %s"%filename, kw="processing")
		
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		
		settings = dataUnit.getSettings()
		settings.set("StatisticsFile", filename)
		w.writerow(["Timepoint %d" % timepoint])
		w.writerow(["Object #", "Volume (micrometers)", "Volume (pixels)", "Center of Mass X", \
					"Center of Mass Y", "Center of Mass Z", "Center of Mass X (micrometers)", \
					"Center of Mass Y (micrometers)", "Center of Mass Z (micrometers)",	"Avg. Intensity",  "Avg. distance to objects"])
		for i, (volume, volumeum) in enumerate(self.values):
			cog = self.centersofmass[i]
			umcog = self.umcentersofmass[i]
			avgint = self.avgIntList[i]
			avgdist = self.avgDistList[i]
			w.writerow([str(i + 1), str(volumeum), str(volume), cog[0], cog[1], cog[2], umcog[0], umcog[1], umcog[2], str(avgint), str(avgdist)])
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
				avgints = float(lib.Math.averageValue(self.avgIntList))
				ums = [x[1] for x in self.values]
				
				# Remove the objects 0 and 1 because hey will distort the values
				avgums = float(lib.Math.averageValue(ums))
				pxs = [x[0] for x in self.values]
				avgpxs = float(lib.Math.averageValue(pxs))
				
				self.totalGUI.setStats([n, avgums, avgpxs, avgints, self.avgIntOutsideObjs, self.distMean, self.distSd])
				self.reportGUI.setVolumes(self.values)
				self.reportGUI.setCentersOfMass(self.centersofmass)
				self.reportGUI.setAverageIntensities(self.avgIntList)
				self.reportGUI.setAverageDistances(self.avgDistList)

			sizer = wx.BoxSizer(wx.VERTICAL)
			sizer.Add(self.reportGUI, 1, wx.EXPAND)
			sizer.Add(self.totalGUI, 1, wx.EXPAND)
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
		data = self.itkfilter.GetOutput()
		data.Update()
			
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
		avgDists = []
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
			n = int(vtkimage.GetScalarRange()[1])
			
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
			
		tott=0
		for i in range(startIntensity, n+1):
			if not self.itkfilter.HasLabel(i):
				pass
				#centersofmass.append((0, 0, 0))
				#values.append((0, 0))
				#avgints.append(0.0)
				#umcentersofmass.append((0, 0, 0))
			else:
				volume = self.itkfilter.GetVolume(i)
				centerOfMass = self.itkfilter.GetCenterOfGravity(i)
				avgInt = avgintCalc.GetAverage(i)
				c = []
				c2 = []
				for k in range(0, 3):
					v = centerOfMass.GetElement(k)
					c.append(v)
					c2.append(v * voxelSizes[k])
					
				totDist = 0
				distCount = 0
				centersofmass.append(tuple(c))
				umcentersofmass.append(tuple(c2))
				values.append((volume, volume * vol))
				avgints.append(avgInt)

		t0=time.time()
		for i, cm in enumerate(centersofmass):
			totDist =0
			distCount = 0
			for j, cm2 in enumerate(centersofmass):
				if i==j: continue
				dx = cm[0]-cm2[0]
				dy = cm[1]-cm2[1]
				dz = cm[2]-cm2[2]
				dist = math.sqrt(dx*dx+dy*dy+dz*dz)
				totDist += dist
				distCount+=1
			avgDist = totDist / distCount
			avgDists.append(avgDist)
		print "Distance calculations took", time.time()-t0
		self.values = values
		self.centersofmass = centersofmass
		self.umcentersofmass = umcentersofmass
		self.avgIntList = avgints
		self.avgDistList = avgDists

		n = len(self.values)
		avgints = lib.Math.averageValue(self.avgIntList)
		ums = [x[1] for x in values]
		avgums = lib.Math.averageValue(ums)
		pxs = [x[0] for x in values]
		avgpxs = lib.Math.averageValue(pxs)
		
		avgIntOutsideObjs = self.avgintCalc.GetAverageOutsideLabels()
		avgIntInsideObjs = self.avgintCalc.GetAverageInsideLabels()
		nonZeroVoxels = self.avgintCalc.GetNonZeroVoxels()
		
		distMean, distSd = lib.Math.meanstdev(self.avgDistList)
		
		self.avgIntOutsideObjs = avgIntOutsideObjs
		self.distMean = distMean
		self.distSd = distSd
			
		self.setResultVariable("NumberOfObjects",len(values))
		self.setResultVariable("ObjAvgSizeInPixels",avgpxs)
		self.setResultVariable("ObjAvgSizeInUm",avgums)
		self.setResultVariable("ObjAvgIntensity",avgints)
		self.setResultVariable("AvgIntOutsideObjs", avgIntOutsideObjs)
		self.setResultVariable("AvgIntInsideObjs", avgIntInsideObjs)
		self.setResultVariable("NonZeroVoxels", nonZeroVoxels)
		self.setResultVariable("AverageDistance", distMean)
		self.setResultVariable("AvgDistanceStdDev", distSd)
		if self.reportGUI:
			self.reportGUI.DeleteAllItems()
			self.reportGUI.setVolumes(values)
			self.reportGUI.setCentersOfMass(centersofmass)
			self.reportGUI.setAverageIntensities(self.avgIntList)
			self.reportGUI.setAverageDistances(self.avgDistList)
			self.totalGUI.setStats([n, avgums, avgpxs, avgints, avgIntOutsideObjs, distMean, distSd])
			
		return self.getInput(1)
