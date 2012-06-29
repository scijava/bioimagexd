"""
 Unit: AnalyzeObjectsFilter.py
 Project: BioImageXD
 Description:

 A module containing object analyses for processing task.
							
 Copyright (C) 2005	 BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307	 USA

"""
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

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
import lib.ParticleWriter
import sys
import lib.Progress

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
		self.stats = None
		self.values = None
		self.centersofmass = None
		self.umcentersofmass = None
		self.avgIntList = None
		self.objAreasUm = None
		self.objRoundness = None
		self.intSums = None
		self.objMinorLength = None
		self.objMajorLength = None
		self.objElongation = None
		self.objAngleMinX = None
		self.objAngleMinY = None
		self.objAngleMinZ = None
		self.objAngleMajX = None
		self.objAngleMajY = None
		self.objAngleMajZ = None
		self.descs = {"StatisticsFile": "Results file:",
					  "AvgInt": "Calculate intensity averages and sums",
					  "AvgDist": "Calculate average distances",
					  "Area": "Calculate areas and roundness",
					  "NonZero": "Calculate non-zero voxels",
					  "Axes": "Calculate major and minor axes",
					  "Smoothness": "Calculate smoothness factor"}
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
								"ObjIntensitySum": "Sum of intensities of objects",
								"NonZeroVoxels":		"The number of non-zero voxels",
								"AverageDistance":		"Average distance between objects",
								"AvgDistanceStdErr":	"Standard error of the average distance between objects",
								"ObjAvgAreaInUm":       "Average area of objects, in square micrometers",
								"ObjAvgAreaInUmStdErr": "Standard error of average area of objects in square micrometers",
								"ObjVolSumInUm":        "Sum of volumes of all objects in micrometers",
								"ObjAreaSumInUm":       "Sum of areas of all objects in micrometers",
								"ObjAvgRoundness":      "Average roundness of the objects",
								"ObjAvgRoundnessStdErr": "Standard error of average roundness of the objects",
								"ObjAvgMajorAxisLen": "Average major axis length of the objects",
								"ObjAvgMajorAxisLenStdErr": "Standard error of average major axis length",
								"ObjAvgMinorAxisLen": "Average minor axis length of the objects",
								"ObjAvgMinorAxisLenStdErr": "Standard error of average minor axis length",
								"ObjAvgElongation": "Average elongation of the objects",
								"ObjAvgElongationStdErr": "Standard error of average elongation",
								"ObjAvgAngleXMajorAxis": "Average angle between X and major axis",
								"ObjAvgAngleXMajorAxisStdErr": "Standard error of average angle between X and major axis",
								"ObjAvgAngleYMajorAxis": "Average angle between Y and major axis",
								"ObjAvgAngleYMajorAxisStdErr": "Standard error of average angle between Y and major axis",
								"ObjAvgAngleZMajorAxis": "Average angle between Z and major axis",
								"ObjAvgAngleZMajorAxisStdErr": "Standard error of average angle between Z and major axis",
								"ObjAvgAngleXMinorAxis": "Average angle between X and minor axis",
								"ObjAvgAngleXMinorAxisStdErr": "Standard error of average angle between X and minor axis",
								"ObjAvgAngleYMinorAxis": "Average angle between Y and minor axis",
								"ObjAvgAngleYMinorAxisStdErr": "Standard error of average angle between Y and minor axis",
								"ObjAvgAngleZMinorAxis": "Average angle between Z and minor axis",
								"ObjAvgAngleZMinorAxisStdErr": "Standard error of average angle between Z and minor axis",
								"ObjAvgSmoothness": "Average smoothness of the objects",
								"ObjAvgSmoothnessStdErr": "Standard error of average smoothness"
								}
		
		self.filterDesc = "Quantitatively analyzes segmented objects\nInputs: Label image, Grayscale image\nOutput: Results (Label image input for pipeline)";
		self.progressObj = lib.Progress.Progress()

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
		if parameter in ["Area", "Axes", "Smoothness"]:
			return False
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
				["Analyses", ("AvgInt", "AvgDist", "Area", "NonZero", "Axes", "Smoothness")]]
		
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
		settings = dataUnit.getSettings()
		settings.set("StatisticsFile", filename)
		writer = lib.ParticleWriter.ParticleWriter()

		volume = [vol for (vol,volum) in self.values]
		volumeum = [volum for (vol,volum) in self.values]
		writer.setObjectValue('volume', volume)
		writer.setObjectValue('volumeum', volumeum)
		writer.setObjectValue('centerofmass', self.centersofmass)
		writer.setObjectValue('umcenterofmass', self.umcentersofmass)
		writer.setObjectValue('avgint', self.avgIntList)
		writer.setObjectValue('avgintstderr', self.avgIntStdErrList)
		writer.setObjectValue('avgdist', self.avgDistList)
		writer.setObjectValue('avgdiststderr', self.avgDistStdErrList)
		writer.setObjectValue('areaum', self.objAreasUm)
		writer.setObjectValue('roundness', self.objRoundness)
		writer.setObjectValue('intsum', self.intSums)
		writer.setObjectValue('majorlen', self.objMajorLength)
		writer.setObjectValue('minorlen', self.objMinorLength)
		writer.setObjectValue('elongation', self.objElongation)
		writer.setObjectValue('anglemajx', self.objAngleMajX)
		writer.setObjectValue('anglemajy', self.objAngleMajY)
		writer.setObjectValue('anglemajz', self.objAngleMajZ)
		writer.setObjectValue('angleminx', self.objAngleMinX)
		writer.setObjectValue('angleminy', self.objAngleMinY)
		writer.setObjectValue('angleminz', self.objAngleMinZ)
		writer.setObjectValue('smoothness', self.objSmoothness)
		writer.writeObjects(filename,timepoint)

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
			
			if self.stats:
				#n = len(self.values)
				#avgints, avgintsstd, avgintsstderr = lib.Math.meanstdeverr(self.avgIntList)
				#ums = [x[1] for x in self.values]
				#sumums = sum(ums, 0.0)
				#avgums, avgumsstd, avgumsstderr = lib.Math.meanstdeverr(ums)
				#pxs = [x[0] for x in self.values]
				#avgpxs, avgpxsstd, avgpxsstderr = lib.Math.meanstdeverr(pxs)
				#avgareaums, avgareaumsstd, avgareaumsstderr = lib.Math.meanstdeverr(self.objAreasUm)
				#sumareaums = sum(self.objAreasUm, 0.0)
				
				#self.totalGUI.setStats([n, avgums, avgumsstderr, avgpxs, avgpxsstderr, avgareaums, avgareaumsstderr, avgints, avgintsstderr, self.avgIntOutsideObjs, self.avgIntOutsideObjsStdErr, self.distMean, self.distStdErr, sumums, sumareaums, self.avgIntOutsideObjsNonZero, self.avgIntOutsideObjsNonZeroStdErr, self.avgIntInsideObjs, self.avgIntInsideObjsStdErr, self.avgRoundness, self.avgRoundnessStdErr, self.intSum])
				self.totalGUI.setStats(self.stats)
				self.reportGUI.setVolumes(self.values)
				self.reportGUI.setAreasUm(self.objAreasUm)
				self.reportGUI.setCentersOfMass(self.centersofmass)
				self.reportGUI.setAverageIntensities(self.avgIntList, self.avgIntStdErrList)
				self.reportGUI.setAverageDistances(self.avgDistList, self.avgDistStdErrList)
				self.reportGUI.setRoundness(self.objRoundness)
				self.reportGUI.setIntensitySums(self.intSums)

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
		
		self.progressObj.setProgress(0.0)
		self.updateProgress(None, "ProgressEvent")

		labelImage = self.getInput(1)
		labelImage.Update()
		if labelImage.GetScalarType() != 9:
			Logging.error("Incompatible data type", "Please convert the input to label data of type unsigned long. Segmented data can be labeled with 'Connected component labeling' or 'Object separation' in 'Segmentation -> Object Processing'.")
		origImage = self.getInput(2)
		origImage.Update()
		origRange = origImage.GetScalarRange()

		print "Input for label shape=",self.getInputDataUnit(1)
		print "Orig. dataunit = ",self.getInputDataUnit(2)

		diritk = dir(itk)
		if "LabelImageToStatisticsLabelMapFilter" in diritk and "LabelMap" in diritk and "StatisticsLabelObject" and "LabelGeometryImageFilter" in diritk:
			newITKStatistics = 1
		else:
			newITKStatistics = 0

		# Do necessary conversions of datatype
		origVTK = origImage
		if self.parameters["AvgInt"] or self.parameters["NonZero"] or newITKStatistics:
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
			dim = labelITK.GetLargestPossibleRegion().GetSize().GetSizeDimension()

		# Initializations
		spacing = self.dataUnit.getSpacing()
		x, y, z = self.dataUnit.getVoxelSize()
		x *= 1000000
		y *= 1000000
		z *= 1000000
		if z == 0: z = 1.0
		vol = x * y * z
		
		voxelSizes = [x, y, z]
		values = []
		centersofmass = []
		umcentersofmass = []
		avgints = []
		avgintsstderrs = []
		objIntSums = []
		avgDists = []
		avgDistsStdErrs = []
		objAreasUm = []
		objRoundness = []
		objMinorLength = []
		objMajorLength = []
		objElongation = []
		objAngleMinX = []
		objAngleMinY = []
		objAngleMinZ = []
		objAngleMajX = []
		objAngleMajY = []
		objAngleMajZ = []
		objSmoothness = []

		ignoreLargest = 1
		currFilter = self
		while currFilter:
			if currFilter.ignoreObjects > ignoreLargest:
				ignoreLargest = currFilter.ignoreObjects
			currFilter = currFilter.prevFilter
		
		startIntensity = ignoreLargest
		print "Ignoring",startIntensity,"first objects"

		if newITKStatistics: # Change spacing for correct results, or not
			#changeInfoLabel = itk.ChangeInformationImageFilter[labelITK].New()
			#changeInfoLabel.SetInput(labelITK)
			#changeInfoLabel.ChangeSpacingOn()

			#changeInfoOrig = itk.ChangeInformationImageFilter[origITK].New()
			#changeInfoOrig.SetInput(origITK)
			#changeInfoOrig.ChangeSpacingOn()

			if dim == 3:
				lm = itk.LabelMap._3.New()
				#changeInfoLabel.SetOutputSpacing(voxelSizes)
				#changeInfoOrig.SetOutputSpacing(voxelSizes)
			else:
				lm = itk.LabelMap._2.New()
				#changeInfoLabel.SetOutputSpacing(voxelSizes[:2])
				#changeInfoOrig.SetOutputSpacing(voxelSizes[:2])
			
			labelStatistics = itk.LabelImageToStatisticsLabelMapFilter[labelITK,origITK,lm].New()
			#labelStatistics.SetInput1(changeInfoLabel.GetOutput())
			#labelStatistics.SetInput2(changeInfoOrig.GetOutput())
			labelStatistics.SetInput1(labelITK)
			labelStatistics.SetInput2(origITK)
			if self.parameters["Area"]:
				labelStatistics.ComputePerimeterOn()
			labelStatistics.Update()
			labelMap = labelStatistics.GetOutput()
			numberOfLabels = labelMap.GetNumberOfLabelObjects()
		else:
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

		self.progressObj.setProgress(0.2)
		self.updateProgress(None, "ProgressEvent")

		# Area calculation pipeline
		if self.parameters["Area"]:
			voxelArea = x*y*2 + x*z*2 + y*z*2
			largestSize = labelITK.GetLargestPossibleRegion().GetSize()
			# if 2D image, calculate area using volume
			if largestSize.GetSizeDimension() > 2 and largestSize.GetElement(2) > 1:
				areaSpacing = labelVTK.GetSpacing()
				objectThreshold = vtk.vtkImageThreshold()
				objectThreshold.SetInput(labelVTK)
				objectThreshold.SetOutputScalarTypeToUnsignedChar()
				objectThreshold.SetInValue(255)
				objectThreshold.SetOutValue(0)
				marchingCubes = vtk.vtkMarchingCubes()
				#marchingCubes.SetInput(labelVTK)
				marchingCubes.SetInput(objectThreshold.GetOutput())
				massProperties = vtk.vtkMassProperties()
				massProperties.SetInput(marchingCubes.GetOutput())
				areaDiv = (areaSpacing[0] / x)**2
				
				if self.parameters["Smoothness"]:
					smoothDecimate = vtk.vtkDecimatePro()
					smoothProperties = vtk.vtkMassProperties()
					smoothDecimate.SetTargetReduction(0.9)
					smoothDecimate.PreserveTopologyOff()
					smoothDecimate.SetInput(marchingCubes.GetOutput())
					smoothProperties.SetInput(smoothDecimate.GetOutput())

		# Filter needed for axes calculations
		if self.parameters["Axes"] and newITKStatistics:
			labelGeometry = itk.LabelGeometryImageFilter[labelITK,labelITK].New()
			labelGeometry.SetCalculateOrientedBoundingBox(1)
			labelGeometry.SetInput(labelITK)
			labelGeometry.Update()

		# Get results and do some calculations for each object
		tott = 0
		voxelSize = voxelSizes[0] * voxelSizes[1] * voxelSizes[2]
		for i in range(startIntensity, numberOfLabels+1):
			areaInUm = 0.0
			avgInt = 0
			avgIntStdErr = 0.0
			roundness = 0.0
			objIntSum = 0.0
			minorLength = 0.0
			majorLength = 0.0
			elongation = 0.0
			angleMinX = 0.0
			angleMinY = 0.0
			angleMinZ = 0.0
			angleMajX = 0.0
			angleMajY = 0.0
			angleMajZ = 0.0
			smoothness = 0.0
			
			if newITKStatistics:
				try:
					labelObj = labelMap.GetLabelObject(i)
				except:
					continue
				volume = labelObj.GetSize()
				#com = labelObj.GetCenterOfGravity()
				com = labelObj.GetCentroid()
				
				c = []
				c2 = []
				for k in range(0,com.GetPointDimension()):
					v = com[k]
					v /= spacing[k]
					c.append(v)
					c2.append(v * voxelSizes[k])
				if com.GetPointDimension() == 2:
					c.append(0)
					c2.append(0.0)

				if self.parameters["AvgInt"]:
					avgInt = labelObj.GetMean()
					avgIntStdErr = math.sqrt(labelObj.GetVariance()) / math.sqrt(volume)
					objIntSum = avgInt * volume

				#if self.parameters["Area"]:
				#	areaInUm = labelObj.GetPerimeter()
				#	roundness = labelObj.GetRoundness()

				# Get area of object, copied old way because roundness is not
				# working
				if self.parameters["Area"]:
					if largestSize.GetSizeDimension() > 2 and largestSize.GetElement(2) > 1:
						objectThreshold.ThresholdBetween(i,i)
						marchingCubes.SetValue(0,255)
						polydata = marchingCubes.GetOutput()
						polydata.Update()
						if polydata.GetNumberOfPolys() > 0:
							massProperties.Update()
							areaInUm = massProperties.GetSurfaceArea() / areaDiv
						else:
							areaInUm = voxelArea

						# Calculate roundness
						hypersphereR = ((3*volume*vol)/(4*math.pi))**(1/3.0)
						hypersphereArea = 3 * volume * vol / hypersphereR
						roundness = hypersphereArea / areaInUm
					
						# Calculate surface smoothness
						if self.parameters["Smoothness"]:
							# Smooth surface with vtkDecimatePro.
							polydata = smoothDecimate.GetOutput()
							polydata.Update()
							if polydata.GetNumberOfPolys() > 0:
								smoothProperties.Update()
								smoothArea = smoothProperties.GetSurfaceArea() / areaDiv
								smoothness = smoothArea / areaInUm
					else:
						areaInUm = volume * x * y

				if self.parameters["Axes"]:
					vert = labelGeometry.GetOrientedBoundingBoxVertices(i)
					vertices = []
					for vNum in range(vert.size()):
						vertices.append(vert.pop())
					
					boxVect = []
					if dim == 3:
						vertNums = [1,2,4]
					else:
						vertNums = [1,2]
					
					for vertNum in vertNums:
						vertex1 = vertices[0]
						vertex2 = vertices[vertNum]
						boxVect.append([abs(vertex2[dimN]-vertex1[dimN]) * voxelSizes[dimN] for dimN in range(dim)])

					boxVectLen = []
					minAxNum = -1
					majAxNum = -1
					minorLength = -1
					majorLength = -1
					for num,vect in enumerate(boxVect):
						length = 0.0
						for vectComp in vect:
							length += vectComp**2
						length = math.sqrt(length)
						boxVectLen.append(length)
						if length > majorLength:
							majorLength = length
							majAxNum = num
						if length < minorLength or minorLength < 0:
							minorLength = length
							minAxNum = num

					elongation = majorLength / minorLength

					# Calculate angle between major, minor axes and x,y,z axes
					for dimN in range(dim):
						boxVect[minAxNum][dimN] /= minorLength
						boxVect[majAxNum][dimN] /= majorLength
					
					vecX = (1.0, 0.0, 0.0)
					vecY = (0.0, 1.0, 0.0)
					vecZ = (0.0, 0.0, 1.0)

					angleMinX = lib.Math.angle(boxVect[minAxNum], vecX)
					angleMinY = lib.Math.angle(boxVect[minAxNum], vecY)
					angleMinZ = lib.Math.angle(boxVect[minAxNum], vecZ)
					angleMajX = lib.Math.angle(boxVect[majAxNum], vecX)
					angleMajY = lib.Math.angle(boxVect[majAxNum], vecY)
					angleMajZ = lib.Math.angle(boxVect[majAxNum], vecZ)
						
			else:
				if not labelShape.HasLabel(i):
					continue
				else:
					volume = labelShape.GetVolume(i)
					centerOfMass = labelShape.GetCenterOfGravity(i)
				
					if self.parameters["AvgInt"]:
						avgInt = avgintCalc.GetMean(i)
						avgIntStdErr = math.sqrt(abs(avgintCalc.GetVariance(i))) / math.sqrt(volume)
						objIntSum = avgintCalc.GetSum(i)
					
					c = []
					c2 = []
					for k in range(0, dim):
						v = centerOfMass.GetElement(k)
						c.append(v)
						c2.append(v * voxelSizes[k])
					if dim == 2:
						c.append(0)
						c2.append(0.0)

				# Get area of object
				if self.parameters["Area"]:
					if largestSize.GetSizeDimension() > 2 and largestSize.GetElement(2) > 1:
						objectThreshold.ThresholdBetween(i,i)
						marchingCubes.SetValue(0,255)
						polydata = marchingCubes.GetOutput()
						polydata.Update()
						if polydata.GetNumberOfPolys() > 0:
							massProperties.Update()
							areaInUm = massProperties.GetSurfaceArea() / areaDiv
						else:
							areaInUm = voxelArea

						# Calculate roundness
						hypersphereR = ((3*volume*vol)/(4*math.pi))**(1/3.0)
						hypersphereArea = 3 * volume * vol / hypersphereR
						roundness = hypersphereArea / areaInUm
					else:
						areaInUm = volume * x * y

			# Add object results to result arrays
			centersofmass.append(tuple(c))
			umcentersofmass.append(tuple(c2))
			values.append((volume, volume * vol))
			avgints.append(avgInt)
			avgintsstderrs.append(avgIntStdErr)
			objIntSums.append(objIntSum)
			objAreasUm.append(areaInUm)
			objRoundness.append(roundness)
			objMinorLength.append(minorLength)
			objMajorLength.append(majorLength)
			objElongation.append(elongation)
			objAngleMinX.append(angleMinX)
			objAngleMinY.append(angleMinY)
			objAngleMinZ.append(angleMinZ)
			objAngleMajX.append(angleMajX)
			objAngleMajY.append(angleMajY)
			objAngleMajZ.append(angleMajZ)
			objSmoothness.append(smoothness)

		self.progressObj.setProgress(0.7)
		self.updateProgress(None, "ProgressEvent")

		# Do distance calculations
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

		self.progressObj.setProgress(0.8)
		self.updateProgress(None, "ProgressEvent")
		
		# Calculate average values and errors
		n = len(values)
		avgint, avgintstd, avgintstderr = lib.Math.meanstdeverr(avgints)
		intSum = sum(objIntSums, 0.0)
		ums = [x[1] for x in values]
		avgums, avgumsstd, avgumsstderr = lib.Math.meanstdeverr(ums)
		sumums = sum(ums, 0.0)
		pxs = [x[0] for x in values]
		avgpxs, avgpxsstd, avgpxsstderr = lib.Math.meanstdeverr(pxs)
		distMean, distStd, distStdErr = lib.Math.meanstdeverr(avgDists)
		avground, avgroundstd, avgroundstderr = lib.Math.meanstdeverr(objRoundness)
		avgAreaUm, avgAreaUmStd, avgAreaUmStdErr = lib.Math.meanstdeverr(objAreasUm)
		areaSumUm = sum(objAreasUm, 0.0)
		avgminlen, avgminlenstd, avgminlenstderr = lib.Math.meanstdeverr(objMinorLength)
		avgmajlen, avgmajlenstd, avgmajlenstderr = lib.Math.meanstdeverr(objMajorLength)
		avgelon, avgelonstd, avgelonstderr = lib.Math.meanstdeverr(objElongation)
		avgangminx, avgangminxstd, avgangminxstderr = lib.Math.meanstdeverr(objAngleMinX)
		avgangminy, avgangminystd, avgangminystderr = lib.Math.meanstdeverr(objAngleMinY)
		avgangminz, avgangminzstd, avgangminzstderr = lib.Math.meanstdeverr(objAngleMinZ)
		avgangmajx, avgangmajxstd, avgangmajxstderr = lib.Math.meanstdeverr(objAngleMajX)
		avgangmajy, avgangmajystd, avgangmajystderr = lib.Math.meanstdeverr(objAngleMajY)
		avgangmajz, avgangmajzstd, avgangmajzstderr = lib.Math.meanstdeverr(objAngleMajZ)
		avgsmooth, avgsmoothstd, avgsmoothstderr = lib.Math.meanstdeverr(objSmoothness)

		# Calculate average intensity outside objects
		avgIntOutsideObjs = 0.0
		avgIntOutsideObjsStdErr = 0.0
		avgIntOutsideObjsNonZero = 0.0
		avgIntOutsideObjsNonZeroStdErr = 0.0
		nonZeroVoxels = -1

		if self.parameters["AvgInt"]:
			variances = 0.0
			allVoxels = 0
			for i in range(0,startIntensity):
				if newITKStatistics:
					try:
						labelObj = labelMap.GetLabelObject(i)
						voxelAmount = labelObj.GetSize()
						allVoxels += voxelAmount
						avgIntOutsideObjs += labelObj.GetMean() * voxelAmount
						variances += voxelAmount * abs(labelObj.GetVariance())
					except:
						pass
				else:
					if labelShape.HasLabel(i):
						voxelAmount = labelShape.GetVolume(i)
						allVoxels += voxelAmount
						avgIntOutsideObjs += avgintCalc.GetMean(i) * voxelAmount
						if voxelAmount > 1:
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
			if labelAverage.GetVoxelsOutsideLabels() == 0:
				avgIntOutsideObjsNonZeroStdErr = 0.0
			else:
				avgIntOutsideObjsNonZeroStdErr = labelAverage.GetOutsideLabelsStdDev() / math.sqrt(labelAverage.GetVoxelsOutsideLabels())
			# Get also non zero voxels here that there is no need to recalculate
			nonZeroVoxels = labelAverage.GetNonZeroVoxels()

		self.progressObj.setProgress(0.9)
		self.updateProgress(None, "ProgressEvent")

		# Calculate average intensity inside objects
		avgIntInsideObjs = 0.0
		avgIntInsideObjsStdErr = 0.0
		if self.parameters["AvgInt"]:
			variances = 0.0
			allVoxels = 0
			for i in range(startIntensity, numberOfLabels+1):
				if newITKStatistics:
					try:
						labelObj = labelMap.GetLabelObject(i)
						voxelAmount = labelObj.GetSize()
						allVoxels += voxelAmount
						avgIntInsideObjs += labelObj.GetMean() * voxelAmount
						if voxelAmount > 1:
							variances += voxelAmount * abs(labelObj.GetVariance())
					except:
						pass
				else:
					if labelShape.HasLabel(i):
						voxelAmount = labelShape.GetVolume(i)
						allVoxels += voxelAmount
						avgIntInsideObjs += avgintCalc.GetMean(i) * voxelAmount
						variances += voxelAmount * abs(avgintCalc.GetVariance(i))

			if allVoxels > 0:
				avgIntInsideObjs /= allVoxels
				avgIntInsideObjsStdErr = math.sqrt(variances / allVoxels) / math.sqrt(allVoxels)

		# Calculate non-zero voxels
		if self.parameters["NonZero"] and nonZeroVoxels < 0:
			labelShape = itk.LabelShapeImageFilter[origITK].New()
			labelShape.SetInput(origITK)
			labelShape.Update()
			for i in range(1, int(origRange[1]) + 1):
				if labelShape.HasLabel(i):
					nonZeroVoxels += labelShape.GetVolume(i)

		# Set results
		self.values = values
		self.centersofmass = centersofmass
		self.umcentersofmass = umcentersofmass
		self.avgIntList = avgints
		self.avgIntStdErrList = avgintsstderrs
		self.intSums = objIntSums
		self.avgDistList = avgDists
		self.avgDistStdErrList = avgDistsStdErrs
		self.objAreasUm = objAreasUm
		self.objRoundness = objRoundness
		self.objMinorLength = objMinorLength
		self.objMajorLength = objMajorLength
		self.objElongation = objElongation
		self.objAngleMinX = objAngleMinX
		self.objAngleMinY = objAngleMinY
		self.objAngleMinZ = objAngleMinZ
		self.objAngleMajX = objAngleMajX
		self.objAngleMajY = objAngleMajY
		self.objAngleMajZ = objAngleMajZ
		self.intSum = intSum
		self.objSmoothness = objSmoothness
		#self.distMean = distMean
		#self.distStdErr = distStdErr
		#self.avgRoundness = avground
		#self.avgRoundnessStdErr = avgroundstderr
		#self.avgIntInsideObjs = avgIntInsideObjs
		#self.avgIntInsideObjsStdErr = avgIntInsideObjsStdErr
		#self.avgIntOutsideObjs = avgIntOutsideObjs
		#self.avgIntOutsideObjsStdErr = avgIntOutsideObjsStdErr
		#self.avgIntOutsideObjsNonZero = avgIntOutsideObjsNonZero
		#self.avgIntOutsideObjsNonZeroStdErr = avgIntOutsideObjsNonZeroStdErr

		self.setResultVariable("NumberOfObjects",len(values))
		self.setResultVariable("ObjAvgVolInVoxels",avgpxs)
		self.setResultVariable("ObjAvgVolInUm",avgums)
		self.setResultVariable("ObjVolSumInUm",sumums)
		self.setResultVariable("ObjAvgAreaInUm",avgAreaUm)
		self.setResultVariable("ObjAreaSumInUm",areaSumUm)
		self.setResultVariable("ObjAvgIntensity",avgint)
		self.setResultVariable("AvgIntOutsideObjs", avgIntOutsideObjs)
		self.setResultVariable("AvgIntOutsideObjsNonZero", avgIntOutsideObjsNonZero)
		self.setResultVariable("AvgIntInsideObjs", avgIntInsideObjs)
		self.setResultVariable("NonZeroVoxels", nonZeroVoxels)
		self.setResultVariable("AverageDistance", distMean)
		self.setResultVariable("AvgDistanceStdErr", distStdErr)
		self.setResultVariable("ObjAvgVolInVoxelsStdErr",avgpxsstderr)
		self.setResultVariable("ObjAvgVolInUmStdErr",avgumsstderr)
		self.setResultVariable("ObjAvgAreaInUmStdErr",avgAreaUmStdErr)
		self.setResultVariable("ObjAvgIntensityStdErr",avgintstderr)
		self.setResultVariable("AvgIntOutsideObjsStdErr",avgIntOutsideObjsStdErr)
		self.setResultVariable("AvgIntOutsideObjsNonZeroStdErr",avgIntOutsideObjsNonZeroStdErr)
		self.setResultVariable("AvgIntInsideObjsStdErr",avgIntInsideObjsStdErr)
		self.setResultVariable("ObjIntensitySum", intSum)
		self.setResultVariable("ObjAvgRoundness",avground)
		self.setResultVariable("ObjAvgRoundnessStdErr",avgroundstderr)
		self.setResultVariable("ObjAvgMajorAxisLen",avgmajlen)
		self.setResultVariable("ObjAvgMajorAxisLenStdErr",avgmajlenstderr)
		self.setResultVariable("ObjAvgMinorAxisLen",avgminlen)
		self.setResultVariable("ObjAvgMinorAxisLenStdErr",avgminlenstderr)
		self.setResultVariable("ObjAvgElongation",avgelon)
		self.setResultVariable("ObjAvgElongationStdErr",avgelonstderr)
		self.setResultVariable("ObjAvgAngleXMajorAxis",avgangmajx)
		self.setResultVariable("ObjAvgAngleXMajorAxisStdErr",avgangmajxstderr)
		self.setResultVariable("ObjAvgAngleYMajorAxis",avgangmajy)
		self.setResultVariable("ObjAvgAngleYMajorAxisStdErr",avgangmajystderr)
		self.setResultVariable("ObjAvgAngleZMajorAxis",avgangmajz)
		self.setResultVariable("ObjAvgAngleZMajorAxisStdErr",avgangmajzstderr)
		self.setResultVariable("ObjAvgAngleXMinorAxis",avgangminx)
		self.setResultVariable("ObjAvgAngleXMinorAxisStdErr",avgangminxstderr)
		self.setResultVariable("ObjAvgAngleYMinorAxis",avgangminy)
		self.setResultVariable("ObjAvgAngleYMinorAxisStdErr",avgangminystderr)
		self.setResultVariable("ObjAvgAngleZMinorAxis",avgangminz)
		self.setResultVariable("ObjAvgAngleZMinorAxisStdErr",avgangminzstderr)
		self.setResultVariable("ObjAvgSmoothness",avgsmooth)
		self.setResultVariable("ObjAvgSmoothnessStdErr",avgsmoothstderr)

		self.stats = [n, avgums, avgumsstderr, avgpxs, avgpxsstderr, avgAreaUm, avgAreaUmStdErr, avgint, avgintstderr, avgIntOutsideObjs, avgIntOutsideObjsStdErr, distMean, distStdErr, sumums, areaSumUm, avgIntOutsideObjsNonZero, avgIntOutsideObjsNonZeroStdErr, avgIntInsideObjs, avgIntInsideObjsStdErr, nonZeroVoxels, avground, avgroundstderr, intSum, avgmajlen, avgmajlenstderr, avgminlen, avgminlenstderr, avgelon, avgelonstderr, avgangmajx, avgangmajxstderr, avgangmajy, avgangmajystderr, avgangmajz, avgangmajzstderr, avgangminx, avgangminxstderr, avgangminy, avgangminystderr, avgangminz, avgangminzstderr, avgsmooth, avgsmoothstderr]
		
		if self.reportGUI:
			self.reportGUI.DeleteAllItems()
			self.reportGUI.setVolumes(values)
			self.reportGUI.setCentersOfMass(centersofmass)
			self.reportGUI.setAverageIntensities(avgints, avgintsstderrs)
			self.reportGUI.setIntensitySums(objIntSums)
			self.reportGUI.setAverageDistances(avgDists, avgDistsStdErrs)
			self.reportGUI.setAreasUm(objAreasUm)
			self.reportGUI.setRoundness(objRoundness)
			self.reportGUI.setMajorAxisLengths(objMajorLength)
			self.reportGUI.setMinorAxisLengths(objMinorLength)
			self.reportGUI.setElongations(objElongation)
			self.reportGUI.setMajorAngles(objAngleMajX, objAngleMajY, objAngleMajZ)
			self.reportGUI.setMinorAngles(objAngleMinX, objAngleMinY, objAngleMinZ)
			self.reportGUI.setSmoothness(objSmoothness)
			self.totalGUI.setStats(self.stats)

		self.progressObj.setProgress(1.0)
		self.updateProgress(None, "ProgressEvent")

		return self.getInput(1)
