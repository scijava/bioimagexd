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
import types
import platform

class AnalyzeObjectsFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	"""		
	name = "Analyze segmented objects"
	category = lib.FilterTypes.SEGMENTATIONANALYSE
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
		self.umcentersofmass = None
		self.avgIntList = None
		self.objAreasUm = None
		self.descs = {"StatisticsFile": "Results file:",
					  "AvgInt": "Calculate average intensities",
					  "AvgDist": "Calculate average distances",
					  "Area": "Calculate areas",
					  "NonZero": "Calculate non-zero voxels"}
		self.reportGUI = None		
		
		self.resultVariables = {"NumberOfObjects":		"Number of discrete objects in the image",
								"ObjAvgVolInVoxels":	"Average object volume, in voxels",
								"ObjAvgVolInVoxelsStdErr": "Standard error of average object volume in voxels",
								"ObjAvgVolInUm":		"Average object volume, in micrometers",
								"ObjAvgVolInUmStdErr":  "Standard error of average object volume in micrometers",
								"ObjAvgIntensity":		"Average intensity of objects",
								"ObjAvgIntensityStdErr": "Standard error of object average intensity",
								"AvgIntOutsideObjs":    "Average intensity of voxels outside the objects",
								"AvgIntOutsideObjsStdErr": "Standard error of average intensity outside objects",
								"AvgIntOutsideObjsNonZero": "Average intensity of voxels outside the objects, excluding voxels of zero intensity",
								"AvgIntOutsideObjsNonZeroStdErr": "Standard error of average intensity outside objects, excluding voxels of zero intensity",
								"AvgIntInsideObjs":		"Average intensity of voxels inside the objects",
								"AvgIntInsideObjsStdErr": "Standard error of average intensity inside objects",
								"NonZeroVoxels":		"The number of non-zero voxels",
								"AverageDistance":		"Average distance between two objects",
								"AvgDistanceStdErr":	"Standard error of the average distance between two objects",
								"ObjAvgAreaInUm":       "Average area of objects, in square micrometers",
								"ObjAvgAreaInUmStdErr": "Standard error of average area of objects in square micrometers",
								"ObjVolSumInUm":        "Sum of volumes of all objects in micrometers",
								"ObjAreaSumInUm":       "Sum of areas of all objects in micrometers"
								}
		
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
		if parameter == "StatisticsFile":
			return "statistics.csv"
		return True
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""
		if parameter == "StatisticsFile":
			return GUI.GUIBuilder.FILENAME
		return types.BooleanType
		
		
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["Measurement results",
		(("StatisticsFile", "Select the file to which the statistics will be written", "*.csv"), )],
				["Analyses", ("AvgInt", "AvgDist", "Area", "NonZero")]]
		
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
		w.writerow(["Object #", "Volume (micrometers)", "Volume (voxels)", "Center of Mass X", \
					"Center of Mass Y", "Center of Mass Z", "Center of Mass X (micrometers)", \
					"Center of Mass Y (micrometers)", "Center of Mass Z (micrometers)",	"Avg. Intensity", "Avg. Intensity std. error",  "Avg. distance to objects", "Avg. distance to objects std. error", "Area (micrometers)"])
		for i, (volume, volumeum) in enumerate(self.values):
			cog = self.centersofmass[i]
			umcog = self.umcentersofmass[i]
			avgint = self.avgIntList[i]
			avgintstderr = self.avgIntStdErrList[i]
			avgdist = self.avgDistList[i]
			avgdiststderr = self.avgDistStdErrList[i]
			areaUm = self.objAreasUm[i]
			w.writerow([str(i + 1), str(volumeum), str(volume), cog[0], cog[1], cog[2], umcog[0], umcog[1], umcog[2], str(avgint), str(avgintstderr), str(avgdist), str(avgdiststderr), str(areaUm)])
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
				avgints, avgintsstd, avgintsstderr = lib.Math.meanstdeverr(self.avgIntList)
				ums = [x[1] for x in self.values]
				sumums = sum(ums, 0.0)
				avgums, avgumsstd, avgumsstderr = lib.Math.meanstdeverr(ums)
				pxs = [x[0] for x in self.values]
				avgpxs, avgpxsstd, avgpxsstderr = lib.Math.meanstdeverr(pxs)
				avgareaums, avgareaumsstd, avgareaumsstderr = lib.Math.meanstdeverr(self.objAreasUm)
				sumareaums = sum(self.objAreasUm, 0.0)
				
				self.totalGUI.setStats([n, avgums, avgumsstderr, avgpxs, avgpxsstderr, avgareaums, avgareaumsstderr, avgints, avgintsstderr, self.avgIntOutsideObjs, self.avgIntOutsideObjsStdErr, self.distMean, self.distStdErr, sumums, sumareaums, self.avgIntOutsideObjsNonZero, self.avgIntOutsideObjsNonZeroStdErr, self.avgIntInsideObjs, self.avgIntInsideObjsStdErr])
				self.reportGUI.setVolumes(self.values)
				self.reportGUI.setAreasUm(self.objAreasUm)
				self.reportGUI.setCentersOfMass(self.centersofmass)
				self.reportGUI.setAverageIntensities(self.avgIntList, self.avgIntStdErrList)
				self.reportGUI.setAverageDistances(self.avgDistList, self.avgDistStdErrList)

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
		if platform.system() == "Windows":
			filename = filename.encode('mbcs')
		else:
			filename = filename.encode(sys.getfilesystemencoding())
		
		if filename and self.taskPanel:
			listOfFilters = self.taskPanel.filterList.getFilters()
			filterIndex = listOfFilters.index(self)
			func = "getFilter(%d)" %(filterIndex)
			n = scripting.mainWindow.currentTaskWindowName
			method = "scripting.mainWindow.tasks['%s'].filterList.%s"%(n,func)
		
			do_cmd = "%s.exportStatistics(r'%s')"%(method,filename)
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

		labelImage = self.getInput(1)
		labelImage.Update()
		origImage = self.getInput(2)
		origImage.Update()
		origRange = origImage.GetScalarRange()

		print "Input for label shape=",self.getInputDataUnit(1)
		print "Orig. dataunit = ",self.getInputDataUnit(2)

		# Do necessary conversions of datatype
		origVTK = origImage
		if self.parameters["AvgInt"] or self.parameters["NonZero"]:
			origITK = self.convertVTKtoITK(origVTK)

		# Cannot have two convertVTKtoITK in same filter
		if self.parameters["AvgInt"] or self.parameters["Area"]:
			labelVTK = self.convertITKtoVTK(labelImage)
		if "itkImage" not in str(labelImage.__class__):
			extent = labelImage.GetWholeExtent()
			if extent[5] - extent[4] == 0:
				dim = 2
			else:
				dim = 3
			scalarType = labelImage.GetScalarType()
			if scalarType != 9: # Convert to unsigned long
				castVTK = vtk.vtkImageCast()
				castVTK.SetOutputScalarTypeToUnsignedLong()
				castVTK.SetInput(labelImage)
				labelImage = castVTK.GetOutput()
				labelImage.Update()
				
			vtkItk = eval("itk.VTKImageToImageFilter.IUL%d.New()"%dim)
			vtkItk.SetInput(labelImage)
			labelITK = vtkItk.GetOutput()
			labelITK.Update()
		else:
			labelITK = labelImage


		x, y, z = self.dataUnit.getVoxelSize()
		x *= 1000000
		y *= 1000000
		z *= 1000000
		vol = x * y * z
		
		voxelSizes = [x, y, z]
		values = []
		centersofmass = []
		umcentersofmass = []
		avgints = []
		avgintsstderrs = []
		avgDists = []
		avgDistsStdErrs = []
		objAreasUm = []

		ignoreLargest = 1
		currFilter = self
		while currFilter:
			if currFilter.ignoreObjects > ignoreLargest:
				ignoreLargest = currFilter.ignoreObjects
			currFilter = currFilter.prevFilter
		
		startIntensity = ignoreLargest
		print "Ignoring",startIntensity,"first objects"
		
		labelShape = itk.LabelShapeImageFilter[labelITK].New()
		labelShape.SetInput(labelITK)
		data = labelShape.GetOutput()
		data.Update()
		numberOfLabels = labelShape.GetNumberOfLabels()
		
		if self.parameters["AvgInt"]:
			avgintCalc = itk.LabelStatisticsImageFilter[origITK,labelITK].New()
			avgintCalc.SetInput(origITK)
			avgintCalc.SetLabelInput(labelITK)
			avgintCalc.Update()

		# Area calculation pipeline
		if self.parameters["Area"]:
			voxelArea = x*y*2 + x*z*2 + y*z*2
			largestSize = labelITK.GetLargestPossibleRegion().GetSize()
			# if 2D image, calculate area using volume
			if largestSize.GetSizeDimension() > 2 and largestSize.GetElement(2) > 1:
				areaSpacing = labelVTK.GetSpacing()
				marchingCubes = vtk.vtkMarchingCubes()
				marchingCubes.SetInput(labelVTK)
				massProperties = vtk.vtkMassProperties()
				massProperties.SetInput(marchingCubes.GetOutput())
				areaDiv = (areaSpacing[0] / x)**2

		tott=0
		voxelSize = voxelSizes[0] * voxelSizes[1] * voxelSizes[2]
		for i in range(startIntensity, numberOfLabels+1):
			if not labelShape.HasLabel(i):
				pass
			else:
				volume = labelShape.GetVolume(i)
				centerOfMass = labelShape.GetCenterOfGravity(i)
				avgInt = 0.0
				avgIntStdErr = 0.0
				areaInUm = 0.0
				
				if self.parameters["AvgInt"]:
					avgInt = avgintCalc.GetMean(i)
					avgIntStdErr = math.sqrt(abs(avgintCalc.GetVariance(i))) / math.sqrt(volume)
				c = []
				c2 = []
				for k in range(0, 3):
					v = centerOfMass.GetElement(k)
					c.append(v)
					c2.append(v * voxelSizes[k])

				# Get area of object
				if self.parameters["Area"]:
					if largestSize.GetSizeDimension() > 2 and largestSize.GetElement(2) > 1:
						#	objectThreshold.ThresholdBetween(i,i)
						marchingCubes.SetValue(0,i)
						polydata = marchingCubes.GetOutput()
						polydata.Update()
						if polydata.GetNumberOfPolys() > 0:
							massProperties.Update()
							areaInUm = massProperties.GetSurfaceArea() / areaDiv
						else:
							areaInUm = voxelArea
					else:
						areaInUm = volume * x * y
				
				centersofmass.append(tuple(c))
				umcentersofmass.append(tuple(c2))
				values.append((volume, volume * vol))
				avgints.append(avgInt)
				avgintsstderrs.append(avgIntStdErr)
				objAreasUm.append(areaInUm)


		t0 = time.time()
		for i, cm in enumerate(umcentersofmass):
			distList = []
			if self.parameters["AvgDist"]:
				for j, cm2 in enumerate(umcentersofmass):
					if i == j: continue
					dx = cm[0] - cm2[0]
					dy = cm[1] - cm2[1]
					dz = cm[2] - cm2[2]
					dist = math.sqrt(dx*dx+dy*dy+dz*dz)
					distList.append(dist)
			avgDist, avgDistStd, avgDistStdErr = lib.Math.meanstdeverr(distList)
			avgDists.append(avgDist)
			avgDistsStdErrs.append(avgDistStdErr)
		print "Distance calculations took", time.time()-t0
		
		self.values = values
		self.centersofmass = centersofmass
		self.umcentersofmass = umcentersofmass
		self.avgIntList = avgints
		self.avgIntStdErrList = avgintsstderrs
		self.avgDistList = avgDists
		self.avgDistStdErrList = avgDistsStdErrs
		self.objAreasUm = objAreasUm

		n = len(self.values)
		avgints, avgintsstd, avgintsstderr = lib.Math.meanstdeverr(self.avgIntList)
		ums = [x[1] for x in values]
		avgums, avgumsstd, avgumsstderr = lib.Math.meanstdeverr(ums)
		sumums = sum(ums, 0.0)
		pxs = [x[0] for x in values]
		avgpxs, avgpxsstd, avgpxsstderr = lib.Math.meanstdeverr(pxs)

		avgIntOutsideObjs = 0.0
		avgIntOutsideObjsStdErr = 0.0
		avgIntOutsideObjsNonZero = 0.0
		avgIntOutsideObjsNonZeroStdErr = 0.0
		nonZeroVoxels = -1

		if self.parameters["AvgInt"]:
			variances = 0.0
			allVoxels = 0
			for i in range(0,startIntensity):
				if labelShape.HasLabel(i):
					voxelAmount = labelShape.GetVolume(i)
					allVoxels += voxelAmount
					avgIntOutsideObjs += avgintCalc.GetMean(i) * voxelAmount
					variances += voxelAmount * abs(avgintCalc.GetVariance(i))

			if allVoxels > 0:
				avgIntOutsideObjs /= allVoxels
				avgIntOutsideObjsStdErr = math.sqrt(variances / allVoxels) / math.sqrt(allVoxels)
			labelAverage = vtkbxd.vtkImageLabelAverage()
			labelAverage.AddInput(origVTK)
			labelAverage.AddInput(labelVTK)
			labelAverage.SetBackgroundLevel(startIntensity)
			labelAverage.Update()
			avgIntOutsideObjsNonZero = labelAverage.GetAverageOutsideLabels()
			avgIntOutsideObjsNonZeroStdErr = labelAverage.GetOutsideLabelsStdDev() / math.sqrt(labelAverage.GetVoxelsOutsideLabels())
			# Get also non zero voxels here that there is no need to recalculate
			nonZeroVoxels = labelAverage.GetNonZeroVoxels()
			
		
		avgIntInsideObjs = 0.0
		avgIntInsideObjsStdErr = 0.0
		if self.parameters["AvgInt"]:
			variances = 0.0
			allVoxels = 0
			for i in range(startIntensity, numberOfLabels):
				if labelShape.HasLabel(i):
					voxelAmount = labelShape.GetVolume(i)
					allVoxels += voxelAmount
					avgIntInsideObjs += avgintCalc.GetMean(i) * voxelAmount
					variances += voxelAmount * abs(avgintCalc.GetVariance(i))

			if allVoxels > 0:
				avgIntInsideObjs /= allVoxels
				avgIntInsideObjsStdErr = math.sqrt(variances / allVoxels) / math.sqrt(allVoxels)

		if self.parameters["NonZero"] and nonZeroVoxels < 0:
			labelShape = itk.LabelShapeImageFilter[origITK].New()
			labelShape.SetInput(origITK)
			labelShape.Update()
			for i in range(1, int(origRange[1]) + 1):
				if labelShape.HasLabel(i):
					nonZeroVoxels += labelShape.GetVolume(i)
		
		distMean, distStd, distStdErr = lib.Math.meanstdeverr(self.avgDistList)
		self.avgIntInsideObjs = avgIntInsideObjs
		self.avgIntInsideObjsStdErr = avgIntInsideObjsStdErr
		self.avgIntOutsideObjs = avgIntOutsideObjs
		self.avgIntOutsideObjsStdErr = avgIntOutsideObjsStdErr
		self.avgIntOutsideObjsNonZero = avgIntOutsideObjsNonZero
		self.avgIntOutsideObjsNonZeroStdErr = avgIntOutsideObjsNonZeroStdErr
		self.distMean = distMean
		self.distStdErr = distStdErr
		avgAreaUm, avgAreaUmStd, avgAreaUmStdErr = lib.Math.meanstdeverr(objAreasUm)
		areaSumUm = sum(objAreasUm, 0.0)

		self.setResultVariable("NumberOfObjects",len(values))
		self.setResultVariable("ObjAvgVolInVoxels",avgpxs)
		self.setResultVariable("ObjAvgVolInUm",avgums)
		self.setResultVariable("ObjVolSumInUm",sumums)
		self.setResultVariable("ObjAvgAreaInUm",avgAreaUm)
		self.setResultVariable("ObjAreaSumInUm",areaSumUm)
		self.setResultVariable("ObjAvgIntensity",avgints)
		self.setResultVariable("AvgIntOutsideObjs", avgIntOutsideObjs)
		self.setResultVariable("AvgIntOutsideObjsNonZero", avgIntOutsideObjsNonZero)
		self.setResultVariable("AvgIntInsideObjs", avgIntInsideObjs)
		self.setResultVariable("NonZeroVoxels", nonZeroVoxels)
		self.setResultVariable("AverageDistance", distMean)
		self.setResultVariable("AvgDistanceStdErr", distStdErr)
		self.setResultVariable("ObjAvgVolInVoxelsStdErr",avgpxsstderr)
		self.setResultVariable("ObjAvgVolInUmStdErr",avgumsstderr)
		self.setResultVariable("ObjAvgAreaInUmStdErr",avgAreaUmStdErr)
		self.setResultVariable("ObjAvgIntensityStdErr",avgintsstderr)
		self.setResultVariable("AvgIntOutsideObjsStdErr",avgIntOutsideObjsStdErr)
		self.setResultVariable("AvgIntOutsideObjsNonZeroStdErr",avgIntOutsideObjsNonZeroStdErr)
		self.setResultVariable("AvgIntInsideObjsStdErr",avgIntInsideObjsStdErr)
		if self.reportGUI:
			self.reportGUI.DeleteAllItems()
			self.reportGUI.setVolumes(values)
			self.reportGUI.setCentersOfMass(centersofmass)
			self.reportGUI.setAverageIntensities(self.avgIntList, self.avgIntStdErrList)
			self.reportGUI.setAverageDistances(self.avgDistList, self.avgDistStdErrList)
			self.reportGUI.setAreasUm(objAreasUm)
			self.totalGUI.setStats([n, avgums, avgumsstderr, avgpxs, avgpxsstderr, avgAreaUm, avgAreaUmStdErr, avgints, avgintsstderr, avgIntOutsideObjs, avgIntOutsideObjsStdErr, distMean, distStdErr, sumums, areaSumUm, avgIntOutsideObjsNonZero, avgIntOutsideObjsNonZeroStdErr, avgIntInsideObjs, avgIntInsideObjsStdErr])
			
		return self.getInput(1)
