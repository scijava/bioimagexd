#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ThreeDimensionalROI.py
 Project: BioImageXD
 Description:

 A module containing the 3D crop filter for the processing task.

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
__author__ = "BioImageXD Project <http://www.bioimagexd.net/>"
__version__ = "$Revision$"
__date__ = "$Date$"

import GUI.GUIBuilder
import lib.ProcessingFilter
import lib.FilterTypes
import math
import scripting
import types
import vtk

class ThreeDimensionalROIFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	ThreeDimensionalROIFilter class
	"""
	name = "3D ROI"
	category = lib.FilterTypes.ROI

	def __init__(self, inputs = (1, 1)):
		"""
		Initializes new object
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, inputs)
		self.descs = {"3D ROI": "3D region of interest",
					  "Interpolate": "ROI interpolation",
					  "StartOfROIInterpolation": "From where the ROI interpolation starts:",
					  "EndOfROIInterpolation": "The end of the ROI interpolation:",
					  "InvertROI": "Invert the ROI",
					  "SmallestPossibleROI": "Crop to smallest possible ROI"}

	def getDefaultValue(self, param):
		"""
		Return default value of parameter
		"""
		if param == "3D ROI":
			n = scripting.visualizer.getRegionsOfInterest()
			if n:
				return (0, n[0])
			return 0
		if param == "StartOfROIInterpolation" or param == "EndOfROIInterpolation":
			return 1
		if param == "InvertROI" or param == "Interpolate" or param == "SmallestPossibleROI":
			return False

	def getRange(self, param):
		"""
		Returns range of list parameter
		@param param Parameter name
		"""
		if param == "StartOfROIInterpolation" or param == "EndOfROIInterpolation":
			return (1, self.dataUnit.getDimensions()[2])

	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""
		if parameter == "3D ROI":
			return GUI.GUIBuilder.ROISELECTION
		
		if parameter == "StartOfROIInterpolation" or parameter == "EndOfROIInterpolation":
			return GUI.GUIBuilder.SLICE

		if parameter == "InvertROI" or parameter == "Interpolate" or parameter == "SmallestPossibleROI":
			return types.BooleanType

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""
		return [["", ("3D ROI",)], ["Interpolation", ("Interpolate", "StartOfROIInterpolation", "EndOfROIInterpolation")], ["", ("InvertROI",)], ["", ("SmallestPossibleROI",)]]

	def execute(self, inputs, update = 0, last = 0):
		"""
		Executes registration process and returns translated result
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		# Get the data.
		scripting.wantWholeDataset = 1
		input = self.getInput(1)
		input.SetUpdateExtent(input.GetWholeExtent())
		input.Update()
		
		# Sliders start from 1, list starts from 0. Interpolation code.
		annotations = self.parameters["3D ROI"][1].parent.GetAnnotations()
		
		if self.parameters["Interpolate"]:
			start = self.parameters["StartOfROIInterpolation"] - 1
			end = self.parameters["EndOfROIInterpolation"] - 1
			diff = end - start
			if diff < 0:
				raise Exception("The starting point for the ROI interpolation must be greater than its end point.")

			startAnnotation = annotations[start]
			endAnnotation = annotations[end]

			crop1 = []
			crop2 = []

			if isinstance(startAnnotation, GUI.OGLAnnotations.MyCircle) or isinstance(startAnnotation, GUI.OGLAnnotations.MyRectangle):
				startW, startH = startAnnotation.GetBoundingBoxMin()
				startX, startY = startAnnotation.GetX(), startAnnotation.GetY()

				endW, endH = endAnnotation.GetBoundingBoxMin()
				endX, endY = endAnnotation.GetX(), endAnnotation.GetY()

				sizes = self.InterpolateBetweenCrops([(startW, startH)], [(endW, endH)], diff - 1)
				coordinates = self.InterpolateBetweenCrops([(startX, startY)], [(endX, endY)], diff - 1)

				if len(sizes) != len(coordinates):
					errorString = "The number of size dimensions (%d) and coordinates (%d) are different. Cannot proceed with the 3D crop." % (len(sizes), len(coordinates))
					raise Exception(errorString)

				for i in range(0, len(sizes)):
					annotation = annotations[i]
					# The difference between handling interpolation with polygons and rectangles/circles,
					# is that polygons can have several points, (x, y)-pairs, that define a single polygon.
					# Rectangles/circles only have one (x, y)-pair per crop (what we define as "crop" in
					# the method at least). These pairs are size (width and height) and coordinates (x and y).
					# And since the "crops" only have one pair, we can safely access the [0] element all the time.
					x, y = coordinates[i][0]
					w, h = sizes[i][0]
					annotation.SetX(x)
					annotation.SetY(y)
					annotation.SetWidth(w)
					annotation.SetHeight(h)

			elif isinstance(startAnnotation, GUI.OGLAnnotations.MyPolygon):
			        startPoints = startAnnotation._points
				endPoints = endAnnotation._points

				x1 = startAnnotation.GetX()
				y1 = startAnnotation.GetY()

				x2 = endAnnotation.GetX()
				y2 = endAnnotation.GetY()

				for point in startPoints:
					crop1.append((point[0] + x1, point[1] + y1))

				for point in endPoints:
					crop2.append((point[0] + x2, point[1] + y2))

				# diff - 1, because the InterpolateBetweenCrops function
				# takes as its third parameter a "points inbetween" integer.
				# If we want to interpolate between 1 and 15, then that's 13
				# points inbetween, not 14.
				points = self.InterpolateBetweenCrops(crop1, crop2, diff - 1)
				for i in range(0, len(points)):
					point = points[i]
					annotation = annotations[start + i]
					# shape._offset = (self.xoffset, self.yoffset)
					for p in range(len(annotation.GetPoints())):
						annotation.DeletePolygonPoint(p)
					pts = []
					mx, my = annotation.polyCenter(point)
					for x, y in point:
						pts.append((((x - mx)), ((y - my))))
					annotation.Create(pts)
					annotation.SetX(mx)
					annotation.SetY(my)

		# Split the image into slices, easier to process the ROI.
		slices = self.SplitIntoSlices(input)

		# Number of slices must be equal to the number of polygons.
		if len(annotations) != len(slices):
			errorString = "The number of slices, %d, are unequal to the number of polygons (annotations), %d. Cannot proceed with the 3D crop." % (len(slices), len(annotations))
			raise Exception(errorString)

		outsideValue = 0
		insideValue = 1
		lowerThreshold = 1
		upperThreshold = 255
		for i in range(0, len(annotations)):
			# The result of the getAsMaskImage is an 1 and 0 image,
			# and we want to invert those values so the mask
			# excludes the pixels inside the crop.
			annotationMask = annotations[i].getAsMaskImage()
			vtkImageMask = vtk.vtkImageMask()
			if self.parameters["InvertROI"]:
				invertedAnnotationMask = self.ApplyThreshold(annotations[i].getAsMaskImage(), outsideValue = insideValue, insideValue = outsideValue, lowerThreshold = lowerThreshold, upperThreshold = upperThreshold)
				vtkImageMask.SetMaskInput(invertedAnnotationMask)
			else:
				vtkImageMask.SetMaskInput(annotationMask)
			vtkImageMask.SetImageInput(slices[i])
			slices[i] = vtkImageMask.GetOutput()
			slices[i].Update()
			del vtkImageMask

		# Create the volume from the processed slices.
		volume = self.CreateVolumeFromSlices(slices, input.GetSpacing())

		# Calculate the smallest possible rectangle that encapsulates
		# the ROI.
		if self.parameters["SmallestPossibleROI"]:
			north, east, south, west = 0, 0, 100000, 100000
			for i in range(0, len(annotations)):
				annotation = annotations[i]
				if isinstance(annotation, GUI.OGLAnnotations.ShapeAnnotation):
					minX, minY, maxX, maxY = annotation.getROICoordinates()
				else:
					errorString = "Invalid annotation chosen for 3D crop. Cannot proceed."
					raise Exception(errorString)				
				if minX < west:
					west = minX
				if maxX > east:
					east = maxX
				if minY < south:
					south = minY
				if maxY > north:
					north = maxY

			vtkExtractVOI = vtk.vtkExtractVOI()
			vtkExtractVOI.SetInput(volume)
			# Cast to int. All these floats are always x.0, so no
			# round off is necessary.
			vtkExtractVOI.SetVOI(int(west), int(east), int(south), int(north), 0, volume.GetDimensions()[2] - 1)
			voi = vtkExtractVOI.GetOutput()
			vtkImageChangeInformation = vtk.vtkImageChangeInformation()
			vtkImageChangeInformation.SetOutputOrigin(0, 0, 0)
			vtkImageChangeInformation.SetInput(voi)
			output = vtkImageChangeInformation.GetOutput()
			output.Update()
			del vtkExtractVOI
			del vtkImageChangeInformation
			return  output
		else:
			return volume

	def CheckCrops(self, crops):
		"""
		crop
		- crop1
		.- point1 = (x1, y1)
		-- point2 = (x2, y2)
		-- point3 = (x3, y3)
		...
		"""
		# First we need to check that are an equal amount of points in every crop.		# We only do this once.
		for crop in crops:
			if len(crop) != len(crops[0]):
				raise Exception
			for point in crop:
				# The points needs to contain two components only (x and y).
				if len(point) != 2:
					raise Exception
				# They cannot be negative either.
				for p in point:
					if p < 0:
						raise Exception

	def CreateCropsFromInterpolatedPoints(self, points):
		"""
		points
		- interpolated points (Z direction)
		-- point1 = (x1, y1)
		-- ...
		-- pointN = (xN, yN)
		...

		So we want to pair every point1 in all the inpolated points.
		Thus we create a polygon, that can be used for cropping at a
		certain Z level.
		"""
		crops = []
		for i in range(0, len(points[0])):
			crop = []
			for k in range(0, len(points)):
				crop.append(points[k][i])
			crops.append(crop)
		return crops

	def InterpolateBetweenCrops(self, crop1, crop2, pointsInBetween):
		if pointsInBetween < 0 or type(pointsInBetween) != int:
			raise Exception("Invalid amount of points inbetween crops.")
		self.CheckCrops([crop1, crop2])
		# We know they're equal in length if they passed CheckCrops().
		interpolatedPoints = []
		for i in range(0, len(crop1)):
			interpolatedPoints.append(self.InterpolateBetweenPoints(crop1[i], crop2[i], pointsInBetween))
		return self.CreateCropsFromInterpolatedPoints(interpolatedPoints)

	# Notice that this is done in Z direction.
	def InterpolateBetweenPoints(self, point1, point2, pointsInBetween):
		# Make sure we're using float.
		x1, y1 = float(point1[0]), float(point1[1])
		x2, y2 = float(point2[0]), float(point2[1])
		pointsInBetween = float(pointsInBetween)

		if pointsInBetween == 1:
			x = round(0.5 * (x1 + x2))
			y = round(0.5 * (y1 + y2))
			return [(x, y)]

		# Differences between the two points.
		xDiff = math.fabs(x1 - x2)
		yDiff = math.fabs(y1 - y2)

		# Increments.
		xInc = xDiff / (pointsInBetween + 1.0)
		yInc = yDiff / (pointsInBetween + 1.0)

		# Store the points.
		inBetweenPoints = []
		inBetweenPoints.append(point1)

		# Add the increment to the x and y coordinates with a lesser value.
		for i in range(1, int(pointsInBetween) + 1):
			x = round(x1 + float(i) * xInc) if (x1 < x2) else round(x1 - float(i) * xInc)
			y = round(y1 + float(i) * yInc) if (y1 < y2) else round(y1 - float(i) * yInc)
			inBetweenPoints.append((x, y))

		inBetweenPoints.append(point2)
		return inBetweenPoints

	def SplitIntoSlices(self, vtkImage):
		vtkClipFilter = vtk.vtkImageClip()
		vtkClipFilter.SetInput(vtkImage)
		vtkClipFilter.ClipDataOn()
		dimensions = vtkImage.GetDimensions()
		slices = []
		for z in range(0, dimensions[2]):
			vtkClipFilter.SetOutputWholeExtent(0, dimensions[0], 0, dimensions[1], z, z)
			slice = vtk.vtkImageData()
			vtkClipFilter.Update()
			slice.DeepCopy(vtkClipFilter.GetOutput())
			slices.append(slice)
		del vtkClipFilter
		return slices

	def ApplyThreshold(self, vtkImage, outsideValue, insideValue, lowerThreshold, upperThreshold):
		vtkThresholdFilter = vtk.vtkImageThreshold()
		vtkThresholdFilter.SetInput(vtkImage)
		vtkThresholdFilter.SetOutValue(outsideValue)
		vtkThresholdFilter.SetInValue(insideValue)
		vtkThresholdFilter.ThresholdBetween(lowerThreshold, upperThreshold)
		output = vtkThresholdFilter.GetOutput()
		output.Update()
		del vtkThresholdFilter
		return output

	def CreateVolumeFromSlices(self, vtkImages, spacing):
		vtkAppendFilter = vtk.vtkImageAppend()
		vtkAppendFilter.SetAppendAxis(2)
		for sliceIndex in range(0, len(vtkImages)):
			vtkAppendFilter.SetInput(sliceIndex, vtkImages[sliceIndex])

		output = vtkAppendFilter.GetOutput()
		output.SetSpacing(spacing)
		output.Update()
		del vtkAppendFilter
		return output
