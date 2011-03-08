# -*- coding: iso-8859-1 -*-
"""
 Unit: ImageOperations
 Project: BioImageXD
 Description:

 This is a module with functions for various kind of image operations, for example
 conversion from VTK image data to wxPython bitmap

 Copyright (C) 2005  BioImageXD Project
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
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307  USA
"""

__author__ = "BioImageXD Project < http: //www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005 / 01 / 13 13: 42: 03 $"

import vtk
import vtkbxd
import wx
import random
import platform
import math
import struct
import Logging
import GUI.Dialogs 
import optimize

def paintLogarithmicScale(ctfbmp, ctf, vertical = 1):
	"""
	Paint a logarithmic scale on a bitmap that represents the given ctf
	"""
	maxval = ctf.GetRange()[1]
	width, height = ctfbmp.GetWidth(), ctfbmp.GetHeight()
	
	bmp = wx.EmptyBitmap(width + 10, height)
	
	deviceContext = wx.MemoryDC()
	deviceContext.SelectObject(bmp)
	deviceContext.BeginDrawing()
	colour = wx.Colour(255, 255, 255)
	deviceContext.SetBackground(wx.Brush(colour))
	deviceContext.SetPen(wx.Pen(colour, 0))
	deviceContext.SetBrush(wx.Brush(colour))
	deviceContext.DrawRectangle(0, 0, width + 16, height)
   
	deviceContext.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
	deviceContext.DrawBitmap(ctfbmp, 5, 0)
	
	size = max(width, height)
	maxval = max(ctf.originalRange)
	logMaxVal = math.log(maxval)
	scale = size / float(maxval)
	for i in range(3 * int(logMaxVal) + 1, 1, -1):
		i /= 3.0	
		xCoordinate = int(math.exp(i) * scale)
		if not vertical:
			deviceContext.DrawLine(xCoordinate, 0, xCoordinate, 8)
			
		else:
			deviceContext.DrawLine(0, xCoordinate, 4, xCoordinate)
			deviceContext.DrawLine(width + 6, xCoordinate, width + 10, xCoordinate)
		
	deviceContext.EndDrawing()
	deviceContext.SelectObject(wx.NullBitmap)
	deviceContext = None	 
	return bmp	  
	
def paintCTFValues(ctf, width = 256, height = 32, paintScale = 0, paintScalars = 0):
	"""
	Paint a bar representing a CTF
	
	@keyword width: The width of the bitmap
	@keyword height: The height of the bitmap
	@type width: Positive number
	@type height: Positive number
	
	@keyword paintScale: True if a logarithmic scale should be painted on the bitmap
	@type paintScale: Boolean (0,1)

	@keyword paintScalars: True if the max/min values of the range should be painted on the bitmap
	@type paintScalars: Boolean (0,1)
	"""
	vertical = 0
	if height > width:
		vertical = 1
	bmp = wx.EmptyBitmap(width, height, -1)
	deviceContext = wx.MemoryDC()
	deviceContext.SelectObject(bmp)
	deviceContext.BeginDrawing()
	
	size = width
	if vertical: 
		size = height
	
	minval,maxval = ctf.GetRange()
	values = maxval - minval + 1
	colorsPerWidth = float(values) / size
	for xCoordinate in range(0, size):
		val = [0, 0, 0]
		ctf.GetColor(xCoordinate * colorsPerWidth, val)
		red, green, blue = val
		red *= 255
		green *= 255
		blue *= 255
		red = int(red)
		green = int(green)
		blue = int(blue)
		
		deviceContext.SetPen(wx.Pen((red, green, blue)))
		if not vertical:
			deviceContext.DrawLine(xCoordinate, 0, xCoordinate, height)
		else:
			deviceContext.DrawLine(0, height - xCoordinate, width, height - xCoordinate)
			
		ctfLowerBound, ctfUpperBound = ctf.GetRange()
	
	if paintScalars:
		paintBoundaryValues(deviceContext, ctfLowerBound, ctfUpperBound, vertical, height, width)
	
	deviceContext.EndDrawing()
	deviceContext.SelectObject(wx.NullBitmap)
	deviceContext = None	 
	if paintScale:
		bmp = paintLogarithmicScale(bmp, ctf)
	return bmp

def paintBoundaryValues(deviceContext, ctfLowerBound, ctfUpperBound, vertical, height, width): 
	"""
	Paints the boundary values of a ColorTransferFunction on a device context

	@author: Kalle Pahajoki
	@since: 18.04.2005

	@param deviceContext: The device context on which to draw
	@param deviceContext: A object of type deviceContext

	@param ctfLowerBound: The lower bound of the range of the CTF
	@type ctfLowerBound: Positive float
	
	@param ctfUpperBound: The upper bound of the range of the CTF
	@type ctfUpperBound: Positive float
	
	@param vertical: True if the values are to be drawn on a vertical line
	@type vertical: Boolean (0,1)
	"""
	#TODO: The 'magic numbers' could be replaced by clearly named constants
	
	deviceContext.SetTextForeground(wx.Colour(255, 255, 255))
	deviceContext.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
	if vertical:
		deviceContext.SetFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
		deviceContext.DrawText("%d"%ctfLowerBound, 8, height - 20)
		deviceContext.SetFont(wx.Font(6, wx.SWISS, wx.NORMAL, wx.NORMAL))
		deviceContext.SetTextForeground(wx.Colour(0, 0, 0))
		deviceContext.DrawText("%d"%ctfUpperBound, 1, 10)
	else:
		deviceContext.DrawText("%d"%ctfLowerBound, 5, 6)
		deviceContext.SetTextForeground(wx.Colour(0, 0, 0))
		deviceContext.DrawText("%d"%ctfUpperBound, width - 35, 6)

def scaleImage(data, factor = 1.0, zDimension = -1, interpolation = 1, xfactor = 0.0, yfactor = 0.0):
	"""
	Scale an image with cubic interpolation
	"""    
	if zDimension != -1:
		data = getSlice(data, zDimension)
	
	data.SetSpacing(1, 1, 1)
	xDimension, yDimension, zDimension = data.GetDimensions()
	data.SetOrigin(xDimension / 2.0, yDimension / 2.0, 0)
	transform = vtk.vtkTransform()
	xExtent0, xExtent1, yExtent0, yExtent1, zExtent0, zExtent1 = data.GetExtent()
	if xfactor or yfactor:
		xfactor *= factor
		yfactor *= factor
		
	if not (xfactor or yfactor):
		transform.Scale(1 / factor, 1 / factor, 1)
	else:
		transform.Scale(1 / xfactor, 1 / yfactor, 1)
	
	reslice = vtk.vtkImageReslice()
	reslice.SetOutputOrigin(0, 0, 0)
	reslice.SetInputConnection(data.GetProducerPort())

	if not (xfactor or yfactor):
		xfactor = factor
		yfactor = factor
		
	xSize = (xExtent1 - xExtent0 + 1) * xfactor
	xExtent0 *= xfactor
	xExtent1 = xExtent0 + xSize - 1
	ySize = (yExtent1 - yExtent0 + 1) * yfactor
	yExtent0 *= yfactor
	yExtent1 = yExtent0 + ySize - 1

	reslice.SetOutputExtent(int(xExtent0), int(xExtent1), int(yExtent0), int(yExtent1), zExtent0, zExtent1)

	reslice.SetResliceTransform(transform)
	if interpolation == 0:
		reslice.SetInterpolationModeToNearestNeighbor()
	if interpolation == 1:
		reslice.SetInterpolationModeToLinear()
	else:
		reslice.SetInterpolationModeToCubic()
	# XXX: modified, try to get errors out
	
	data = reslice.GetOutput()
	data.Update()
	
	return data
	
def loadNIHLut(data):
	"""
	Load an NIH Image LUT and return it as CTF
	"""    
	if not len(data):
		raise "loadNIHLut got no data"
	dataLength = len(data) - 32
	infoString = "4s2s2s2s2s8s8si%ds" % dataLength
	Logging.info("Unpacking ", infoString, "d = ", dataLength, "len(data) = ", len(data))#, kw = "imageop")
	header, dummy, ncolors, start, end, dummy, dummy, dummy, lut = struct.unpack(infoString, data)

	if header != "ICOL":
		raise "Did not get NIH header!"
	ncolors = ord(ncolors[0]) * (2**8) + ord(ncolors[1])
	start = ord(start[0]) * (2**8) + ord(start[1])
	end = ord(end[0]) * (2**8) + ord(end[1])
	
	reds = lut[: ncolors]
	greens = lut[ncolors: (2 * ncolors)]
	blues = lut[(2 * ncolors): (3 * ncolors)]
	return reds, greens, blues
	
def loadLUT(filename, ctf = None, ctfrange = (0, 255)):
	"""
	Method: loadLUT(filename)
	Load an ImageJ binary LUT and return it as CTF. If a ctf
				 is passed as parameter, it is modified in place
	"""
	if ctf:
		ctf.RemoveAllPoints()
	else:
		ctf = vtk.vtkColorTransferFunction()	  
	fileName = open(filename, "rb")
	lut = fileName.read()
	fileName.close()
	loadLUTFromString(lut, ctf, ctfrange)
	return ctf
	
def loadBXDLutFromString(lut, ctf):
	"""
	Load a BXD format lut from a given string
	"""
	lut = lut[6: ]
	start, end = struct.unpack("ff", lut[0: 8])
	lut = lut[8: ]
	Logging.info("The palette is in range %d-%d" % (start, end), kw = "ctf")
	j = 0
	start = int(start)
	end = int(end)

	handle = vtkbxd.vtkHandleColorTransferFunction()
	handle.SetInputString(lut,len(lut))
	handle.LoadColorTransferFunctionFromString(ctf, start, end)

	#k = ( len(lut) / 3 ) - 1
	#reds = lut[0: k + 1]
	#greens = lut[k + 1: 2 * k + 2]
	#blues = lut[(2 * k) + 2: 3 * k + 3]
			
	#j = 0
	#for i in range(start, end + 1):
	#	red = ord(reds[j])
	#	green = ord(greens[j])
	#	blue = ord(blues[j])
	  
	#	red /= 255.0
	#	green /= 255.0
	#	blue /= 255.0		
	#	ctf.AddRGBPoint(i, red, green, blue)
	#	j += 1

	return 
			
def loadLUTFromString(lut, ctf, ctfrange = (0, 255)):
	"""
	Load an ImageJ binary LUT from string
	Parameters:
		lut		 A binary string representing the lookup table
		ctf		 The CTF to modify
		ctfrange The range to which construct the CTF
	"""		   
	if lut[0: 6] == "BXDLUT":
		return loadBXDLutFromString(lut, ctf)
	
	failed = 1
	if len(lut) != 768:
		try:
			reds, greens, blues = loadNIHLut(lut)
			failed = 0
		except "loadNIHLut got no data":
			failed = 1

	k = ( len(lut) / 3 ) - 1
	if failed:
		reds = lut[0: k + 1]
		greens = lut[k + 1: 2 * k + 2]
		blues = lut[(2 * k) + 2: 3 * k + 3]
		
	step = int(math.ceil(ctfrange[1] / k))
	if step == 0:
		return vtk.vtkColorTransferFunction()
	j = 0
	for i in range(int(ctfrange[0]), int(ctfrange[1])+1, step):
		red = ord(reds[j])
		green = ord(greens[j])
		blue = ord(blues[j])
		red /= 255.0
		green /= 255.0
		blue /= 255.0		
		ctf.AddRGBPoint(i, red, green, blue)
		j += 1
	
def saveLUT(ctf, filename):
	"""
	Save a CTF as ImageJ binary LUT
	"""
	ext = filename.split(".")[-1]
	ltype = "ImageJ"
	if ext.lower() == "bxdlut":
		ltype = "BioImageXD"
	try:
		fileName = open(filename, "wb")
		stringOfLUT = lutToString(ctf, luttype = ltype)
		fileName.write(stringOfLUT)
		fileName.close()
	except:
		pass
	
def lutToString(ctf, luttype = "ImageJ"):
	"""
	Write a lut to a string
	"""
	stringOfLUT = ""
	minval, maxval = ctf.GetRange()
	if luttype == "ImageJ":
		perColor = maxval / 255
	else:
		perColor = 1
	if luttype == "BioImageXD":
		stringOfLUT = "BXDLUT"
		Logging.info("Adding to BXDLUT structure the minval=%f, maxval=%f" % (minval, maxval), kw = "ctf")
		
		stringOfLUT += struct.pack("f", minval)
		stringOfLUT += struct.pack("f", maxval)

	handle = vtkbxd.vtkHandleColorTransferFunction()
	handle.ColorTransferFunctionToString(ctf,int(perColor))
	ctfstr = handle.GetOutputString()
	for i in xrange(0,ctfstr.GetNumberOfTuples()):
		stringOfLUT += chr(ctfstr.GetValue(i))
		
	#for col in range(0, 3):
	#	for i in range(0, int(maxval) + 1, int(perColor)):
	#		val = [0, 0, 0]
			
	#		ctf.GetColor(i, val)
	#		red, green, blue = val
	#		red *= 255
	#		green *= 255
	#		blue *= 255
	#		red = int(red)
	#		green = int(green)
	#		blue = int(blue)
	#		if red < 0: 
	#			red = 0
	#		if blue < 0: 
	#			blue = 0
	#		if green < 0: 
	#			green = 0
	#		if red >= 255: 
	#			red = 255
	#		if green >= 255: 
	#			green = 255
	#		if blue >= 255: 
	#			blue = 255
	#		color = [red, green, blue]
	#		stringOfLUT += chr(color[col])
	return stringOfLUT
		
def getAsParameterList(iTF):
	"""
	Returns a list of iTF parameters
	"""
	lst = [	iTF.GetBrightness(),
			iTF.GetContrast(),
			iTF.GetGamma(),
			iTF.GetMinimumThreshold(),
			iTF.GetMinimumValue(),
			iTF.GetMaximumThreshold(),
			iTF.GetMaximumValue(),
			iTF.GetProcessingThreshold(),
			iTF.GetRangeMax()]
	return lst
	
def setFromParameterList(iTF, listOfValuesToSet):
	"""
	Set the parameters from the input list
	"""
	brightness, contrast, gamma, minimumThreshold, minimumValue, maximumThreshold, \
	maximumValue, processingThreshold, rangemax = listOfValuesToSet
	iTF.SetRangeMax(rangemax)
	iTF.SetContrast(float(contrast))
	iTF.SetGamma(float(gamma))
	iTF.SetMinimumThreshold(int(minimumThreshold))
	iTF.SetMinimumValue(int(minimumValue))
	iTF.SetMaximumThreshold(int(maximumThreshold))
	iTF.SetMaximumValue(int(maximumValue))
	iTF.SetProcessingThreshold(int(processingThreshold))
	iTF.SetBrightness(int(brightness))

def vtkImageDataToWxImage(data, sliceNumber = -1, startpos = None, endpos = None):
	"""
	Converts vtk-ImageData to a WxImage
	"""
	if sliceNumber >= 0:
		data = getSlice(data, sliceNumber, startpos, endpos)
	exporter = vtk.vtkImageExport()
	data.SetUpdateExtent(data.GetWholeExtent())
	data.Update()
	exporter.SetInputConnection(data.GetProducerPort())
	dataMemorySize = exporter.GetDataMemorySize()
	formatString = "%ds" % dataMemorySize
	structString = struct.pack(formatString, "")
	exporter.SetExportVoidPointer(structString)
	exporter.Export()
	width, height = data.GetDimensions()[0:2]
	image = wx.EmptyImage(width, height)
	image.SetData(structString)
	return image
	
def vtkImageDataToPngString(data, sliceNumber = -1, startpos = None, endpos = None):
	"""
	A function that returns a vtkImageData object as png
				 data in a string
	"""    
	if sliceNumber >= 0:
		data = getSlice(data, sliceNumber, startpos, endpos)
		
	pngwriter = vtk.vtkPNGWriter()
	pngwriter.WriteToMemoryOn()
	pngwriter.SetInputConnection(data.GetProducerPort())
	pngwriter.Write()
	result = pngwriter.GetResult()
	data = ""
	for i in range(result.GetNumberOfTuples()):
		data += chr(result.GetValue(i))
	return data
	
def getMIP(imageData, color):
	"""
	A function that will take a volume and do a simple
				 maximum intensity projection that will be converted to a
				 wxBitmap
	"""   
	maxval = imageData.GetScalarRange()[1]
	imageData.SetUpdateExtent(imageData.GetWholeExtent())		 

	if maxval > 255:
		shiftscale = vtk.vtkImageShiftScale()
		shiftscale.SetInputConnection(imageData.GetProducerPort())
		shiftscale.SetScale(255.0 / maxval)
		shiftscale.SetOutputScalarTypeToUnsignedChar()	  
		imageData = shiftscale.GetOutput()
	
	mip = vtkbxd.vtkImageSimpleMIP()
	mip.SetInputConnection(imageData.GetProducerPort())
	
	if color == None:
		output = optimize.execute_limited(mip)
		return output

	if mip.GetOutput().GetNumberOfScalarComponents() == 1:
		ctf = getColorTransferFunction(color)
	
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInputConnection(mip.GetOutputPort())
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		imagedata = optimize.execute_limited(maptocolor)
		
	else:
		imagedata = output = optimize.execute_limited(mip)
	return imagedata

def getColorTransferFunction(color):
	"""
	Convert a color to a ctf and pass a ctf through
	"""
	if isinstance(color, vtk.vtkColorTransferFunction):
		return color
	ctf = vtk.vtkColorTransferFunction()
	red, green, blue = (0, 0, 0)
	ctf.AddRGBPoint(0.0, red, green, blue)
	
	red, green, blue = color
	red /= 255
	green /= 255
	blue /= 255
	ctf.AddRGBPoint(255.0, red, green, blue)	
	return ctf
	
def vtkImageDataToPreviewBitmap(dataunit, timepoint, color, width = 0, height = 0, getvtkImage = 0):
	"""
	A function that will take a volume and do a simple
				 Maximum Intensity Projection that will be converted to a
				 wxBitmap
	"""   
	imagedata = dataunit.getMIP(timepoint, None, small = 1, noColor = 1)
	vtkImg = imagedata

	if not color:
		color = dataunit.getColorTransferFunction()
	
	ctf = getColorTransferFunction(color)
	minval,maxval = ctf.GetRange()
	imax = imagedata.GetScalarRange()[1]
	if maxval > imax:
		step = float((maxval-minval) / imax)
		ctf2 = vtk.vtkColorTransferFunction()
		Logging.info("Creating CTF in range %d, %d with steps %d"%(int(minval), int(maxval), int(step)))
		for i in range(int(minval), int(maxval), int(step)):
			red, green, blue = ctf.GetColor(i)
			ctf2.AddRGBPoint(i / step, red, green, blue)
		ctf = ctf2
	maptocolor = vtk.vtkImageMapToColors()
	maptocolor.SetInputConnection(imagedata.GetProducerPort())
	maptocolor.SetLookupTable(ctf)
	maptocolor.SetOutputFormatToRGB()
	maptocolor.Update()
	imagedata = maptocolor.GetOutput()
	
	image = vtkImageDataToWxImage(imagedata)
	xSize, ySize = image.GetWidth(), image.GetHeight()
	if not width and height:
		aspect = float(xSize) / ySize
		width = aspect * height
	if not height and width:
		aspect = float(ySize) / xSize
		height = aspect * width
	if not width and not height:
		width = height = 64
	image.Rescale(width, height)
	
	bitmap = image.ConvertToBitmap()
	ret = [bitmap]
	if getvtkImage:
		ret.append(vtkImg)
		return ret
	return bitmap
	
	
def watershedPalette(ctfLowerBound, ctfUpperBound, ignoreColors = 2, filename = ""):
	"""
	Returns a randomly created CTF.
	"""
	try:
		ctf = vtk.vtkColorTransferFunction()
		if filename:
			loadLUT(filename, ctf)
	except:
		ctf = vtk.vtkColorTransferFunction()

	ctfFileSize = ctf.GetSize()
	if ctfFileSize > 0:
		for i in range(0, ignoreColors):
			color = ctf.GetColor(i)
			ctf.AddRGBPoint(ctf.GetSize(),color[0],color[1],color[2])
		
	for i in range(0, ignoreColors):
		ctf.AddRGBPoint(i, 0, 0, 0)

	if ctfLowerBound < 1: 
		ctfLowerBound = 1

	if ctfFileSize > 0 and ctf.GetSize() > ctfLowerBound:
		ctfLowerBound = ctf.GetSize()

	handle = vtkbxd.vtkHandleColorTransferFunction()
	handle.CreateRandomColorTransferFunction(ctf, ctfLowerBound, ctfUpperBound, 1.5)
	#for i in range(int(ctfLowerBound), int(ctfUpperBound)):
	#	red = 0
	#	green = 0
	#	blue = 0
	#	while red + green + blue < 1.5:
	#		red = random.random()
	#		green = random.random()
	#		blue = random.random()
	#	ctf.AddRGBPoint(float(i), float(red), float(green), float(blue))

	if ctf.GetSize() > ctfUpperBound:
		for i in xrange(ctfUpperBound, ctf.GetSize()-1):
			ctf.RemovePoint(i)

	return ctf

def fire(ctfLowerBound, ctfUpperBound):
	"""
	return a color transfer function with colors ranging from red to white
	"""
	reds = [
		  0,   0,   1,  25,  49,  73,  98, 122, 
		146, 162, 173, 184, 195, 207, 217, 229, 
		240, 252, 255, 255, 255, 255, 255, 255, 
		255, 255, 255, 255, 255, 255, 255, 255
	]
	greens = [	
		  0,   0,   0,   0,   0,   0,   0,   0, 
		  0,   0,   0,   0,   0,  14,  35,  57, 
		 79, 101, 117, 133, 147, 161, 175, 190, 
		205, 219, 234, 248, 255, 255, 255, 255
	]
	blues = [
		 31,  61,  96, 130, 165, 192, 220, 227, 
		210, 181, 151, 122,  93,  64,  35,   5, 
		  0,   0,   0,   0,   0,   0,   0,   0, 
		  0,   0,   0,  35,  98, 160, 223, 255
	]
	maxColorIndex = min(len(reds), len(greens), len(blues))
	div = ctfUpperBound / float(maxColorIndex-1)

	ctf = vtk.vtkColorTransferFunction()
	ctf.AddRGBPoint(0, 0, 0, 0)
	for colorIndex in range(ctfLowerBound, maxColorIndex):
		red = reds[colorIndex] / 255.0
		green = greens[colorIndex] / 255.0
		blue = blues[colorIndex] / 255.0
		ctf.AddRGBPoint(colorIndex * div, red, green, blue)

	return ctf

def getOverlay(width, height, color, alpha):
	"""
	Method: getOverlay(width, height, color, alpha)
	Create an overlay of given color with given alpha
	"""
	width = abs(width)
	height = abs(height)
	print "Generating overlay",width,height,color
	size = width * height * 3
	formatString = "%ds" % size
	red, green, blue = color
	structStr = chr(red) + chr(green) + chr(blue)
	structStr = (width * height) * structStr
	structString = struct.pack(formatString, structStr)
	img = wx.EmptyImage(width, height)
	img.SetData(structString)
	size = width * height
	structStr = chr(alpha)
	formatString = "%ds" % size
	structStr = size * structStr
	structString = struct.pack(formatString, structStr)
	img.SetAlphaData(structString)
	return img
	
def getOverlayBorders(width, height, color, alpha, lineWidth = 1):
	"""
	Create borders for an overlay that are only very little transparent
	"""
	width = abs(width)
	height = abs(height)
	size = width * height * 3
	formatString = "%ds" % size	
	red, green, blue = color
	structStr = chr(red) + chr(green) + chr(blue)
	structStr = (width * height) * structStr
	structString = struct.pack(formatString, structStr)
	img = wx.EmptyImage(width, height)
	img.SetData(structString)
	size = width * height
	structStr = chr(0)
	formatString = "%ds" % size	
	structStr = size * structStr
	structString = struct.pack(formatString, structStr)
	structString = chr(alpha) * (2 * width) + structString[2 * width: ]
	lengthOfStructStr = len(structString)
	structString = structString[: lengthOfStructStr  - (2 * width)] + chr(alpha) * 2 * width
	twochar = chr(alpha) + chr(alpha)
	for i in range(0, width * height, width):
		if i:
			structString = structString[: i - 2] + 2 * twochar + structString[i + 2: ]
		else:
			structString = structString[: i] + twochar + structString[i + 2: ]
	img.SetAlphaData(structString)
	return img
	
def getImageScalarRange(image):
	"""
	get the minimum and maximum value of an image based on it's datatype
	"""
	x0, x1 = image.GetScalarRange()

	scalarType = image.GetScalarTypeAsString()
	if scalarType == "unsigned char":
		return 0, 255
	if scalarType == "unsigned short": 
		if x1 > 4095:
			return 0, (2**16)-1
		return 0, 4095

	return x0,x1
	
def get_histogram(image, maxval = 0, minval = 0, maxrange = 0):
	"""
	Return the histogram of the image as a list of floats
	"""
	accu = vtk.vtkImageAccumulate()
	accu.SetInputConnection(image.GetProducerPort())

	if maxval == 0:
		x0, x1 = getImageScalarRange(image)
		#x1 = int(math.floor(x1))
		#x0 = int(math.ceil(x0))
	else:
		#x0, x1 = (int(math.ceil(minval)),int(math.floor(maxval)))
		x0, x1 = (minval,maxval)

	#accu.SetComponentExtent(0, x1 - x0, 0, 0, 0, 0)
	#accu.SetComponentSpacing(1, 0, 0)
	if maxrange:
		accu.SetComponentExtent(0, x1-x0, 0, 0, 0, 0)
		accu.SetComponentSpacing(1, 0, 0)
	else:
		accu.SetComponentExtent(0, 255, 0, 0, 0, 0)
		accu.SetComponentSpacing((x1 - x0 + 1) / 256.0, 0, 0)

	accu.SetComponentOrigin(x0, 0, 0)
	accu.Update() 
	data = accu.GetOutput()
	
	values = []
	x0, x1, y0, y1, z0, z1 = data.GetWholeExtent()

	for i in range(x0, x1 + 1):
		c = data.GetScalarComponentAsDouble(i, 0, 0, 0)
		values.append(c)
	return values
	
def histogram(imagedata, colorTransferFunction = None, bg = (200, 200, 200), logarithmic = 1, \
				ignore_border = 0, lower = 0, upper = 0, percent_only = 0, maxval = 255, minval = 0):
	"""
	Draw a histogram of a volume
	"""
	values = get_histogram(imagedata,maxval,minval)
	sum = 0
	xoffset = 10
	sumth = 0
	percent = 0
	for i, c in enumerate(values):
		sum += c
		if (lower or upper):
			if i >= lower and i <= upper:
				sumth += c
	retvals = values[: ]
	Logging.info("lower = %d, upper = %d, total amount of %d values" \
					% (lower, upper, len(values)), sum, kw = "imageop")
	if sumth:
		percent = (float(sumth) / sum)
	if ignore_border:
		ma = max(values[5:])
		mi = min(values[:-5])
		n = len(values)
		for i in range(0, 5):
			values[i] = ma
		for i in range(n - 5, n):
			values[i] = mi
			
	for i, value in enumerate(values):
		if value == 0:
			values[i] = 1
	if logarithmic:
		values = map(math.log, values)

	m = max(values)
	scale = 150.0 / m
	values = [x * scale for x in values]
	w = 256
	x1 = max(values)
	w += xoffset + 5
	
	diff = 0
	if colorTransferFunction:
		diff = 30
	if percent:
		diff += 20
	Logging.info("Creating a %dx%d bitmap for histogram" % (int(w), int(x1) + diff), kw = "imageop")
		
	# Add an offset of 15 for the percentage text
	bmp = wx.EmptyBitmap(int(w), int(x1) + diff)
	dc = wx.MemoryDC()
	dc.SelectObject(bmp)
	dc.BeginDrawing()
	
	blackpen = wx.Pen((0, 0, 0), 1)
	graypen = wx.Pen((80, 80, 80), 1)
	whitepen = wx.Pen((255, 255, 255), 1)
	
	if platform.system()!="Darwin":
		dc.SetBackground(wx.Brush(bg))
		dc.Clear()
	dc.SetBrush(wx.Brush(wx.Colour(200, 200, 200)))
	dc.DrawRectangle(0, 0, 256+xoffset+1, 151)
	
	if not logarithmic:
		points = range(1, 150, 150 / 8)
	else:
		points = [4, 8, 16, 28, 44, 64, 88, 116, 148]
		points = [p + 2 for p in points]
		#points.reverse()
		
	for i in points:
		y = 151-i
		dc.SetPen(blackpen)
		dc.DrawLine(0, y, 5, y)
		dc.SetPen(whitepen)
		dc.DrawLine(0, y - 1, 5, y - 1)
	
	d = (len(values) - 1) / 255.0
	dc.SetPen(blackpen)
	dc.DrawLine(xoffset-1, 0, xoffset-1, 151)
	for i in range(0, 256):
		c = values[int(i * d)]
		if c:
			#c2 = values[int((i * d) + d)]
			dc.SetPen(graypen)
			dc.DrawLine(xoffset + i, x1, xoffset + i, x1 - c)
			#dc.SetPen(blackpen)
			#dc.DrawLine(xoffset + i, x1 - c, xoffset + i, x1 - c-2)
			
	if colorTransferFunction:
		for i in range(minval, maxval + d, d):
			val = [0, 0, 0]
			colorTransferFunction.GetColor(i, val)
			r, g, b = val
			r = int(r * 255)
			b = int(b * 255)
			g = int(g * 255)
			dc.SetPen(wx.Pen(wx.Colour(r, g, b), 1))
			dc.DrawLine(xoffset + i, x1 + 8, xoffset + i, x1 + 30)
		dc.SetPen(whitepen)
		dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL))
		dc.DrawText(str(int(maxval)), xoffset+maxval-25, x1 + 10)
	else:
		Logging.info("Got no ctf for histogram", kw = "imageop")
	
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	dc = None	 
	return bmp, percent, retvals, xoffset

def getMaskFromROIs(rois, mx, my, mz, value = 255):
	"""
	Create a mask that contains all given Regions of Interest
	"""
	insideMap = {}
	for shape in rois:
		print "Getting from shape",shape
		insideMap.update(shape.getCoveredPoints())
	insMap = {}
	coveredPointAmount = len(insideMap.keys())
	for x, y in insideMap.keys():
		insMap[(x, y)] = 1    
	return coveredPointAmount, getMaskFromPoints(insMap, mx, my, mz, value)
	
def getMaskFromPoints(points, mx, my, mz, value = 255):
	"""
	Create a mask where all given points are set to value (between 0-255)
	"""
	if value > 255:
		value = 255
	elif value < 0:
		value = 0

	size = mx * my
	pointStructString = "%dB" % size
	pointData = []
	for y in range(0, my):
		for x in range(0, mx):
			pointData.append(value * points.get((x, y), 0))
	packedPointString = struct.pack(pointStructString, *pointData)
	
	importer = vtk.vtkImageImport()
	importer.CopyImportVoidPointer(packedPointString, mx * my)
	importer.SetDataScalarTypeToUnsignedChar()
	importer.SetNumberOfScalarComponents(1)
	importer.SetDataExtent(0, mx - 1, 0, my - 1, 0, 0)
	importer.SetWholeExtent(0, mx - 1, 0, my - 1, 0, 0)

	importer.Update()
	
	append = vtk.vtkImageAppend()
	append.SetAppendAxis(2)
	for z in range(0, mz):
		append.SetInput(z, importer.GetOutput())
	append.Update()
	image2 = append.GetOutput()
	return image2
	
def equalize(imagedata, ctf):
	"""
	Creates a set of lookup values from a histogram from the imagedata parameter.
	Then creates a color transfer function from these values and returns it.
	"""
	histogram = get_histogram(imagedata)
	maxval = len(histogram)
	
	def weightedValue(x):
		if x < 2:
			return x
		return math.sqrt(x)
	
	intsum = weightedValue(histogram[0])
	for i in range(1, maxval):
		intsum += 2 * weightedValue(histogram[i])
	intsum += weightedValue(histogram[-1])
	
	scale = maxval / float(intsum)
	lut = [0] * (maxval + 1)
	intsum = weightedValue(histogram[0])
	for i in range(1, maxval):
		delta = weightedValue(histogram[i])
		intsum += delta
		ceilValue = math.ceil(intsum * scale)
		floorValue = math.floor(intsum * scale)
# Changed the name of a to colorLookup, maybe not the clearest name yet though
		colorLookup = floorValue
		if abs(ceilValue - intsum * scale) < abs(floorValue - intsum * scale):
			colorLookup = ceilValue
		lut[i] = colorLookup
		intsum += delta
	lut[-1] = maxval
	
	ctf2 = vtk.vtkColorTransferFunction()
	for i, value in enumerate(lut):
		val = [0, 0, 0]
		ctf.GetColor(value, val)
		ctf2.AddRGBPoint(i, *val)
	return ctf2
	
def scatterPlot(imagedata1, imagedata2, z, countVoxels = True, wholeVolume = True, logarithmic = True, bitDepth = 8):
	"""
	Create scatterplot
	"""
	imagedata1.SetUpdateExtent(imagedata1.GetWholeExtent())
	imagedata2.SetUpdateExtent(imagedata1.GetWholeExtent())
		
	imagedata1.Update()
	imagedata2.Update()
	range1 = imagedata1.GetScalarRange()
	range2 = imagedata2.GetScalarRange()

	n = 255
	#n = min(max(sc1max,sc2max),255)
	#d = (n+1) / float(2**bitDepth)
	if bitDepth is None:
		spacing1 = float(abs(range1[1] - range1[0])) / (n+1)
		spacing2 = float(abs(range2[1] - range2[0])) / (n+1)
	else:
		spacing1 = float(2**bitDepth) / (n+1)
		spacing2 = float(2**bitDepth) / (n+1)
	
	app = vtk.vtkImageAppendComponents()
	app.AddInput(imagedata1)
	app.AddInput(imagedata2)
	
	#shiftscale = vtk.vtkImageShiftScale()
	#shiftscale.SetOutputScalarTypeToUnsignedChar()
	#shiftscale.SetScale(d)
	#shiftscale.SetInputConnection(app.GetOutputPort())
	
	acc = vtk.vtkImageAccumulate()
	acc.SetComponentExtent(0, n, 0, n, 0, 0)
	acc.SetComponentOrigin(range1[0], range2[0], 0)
	acc.SetComponentSpacing(spacing1, spacing2, 0)
	#acc.SetInputConnection(shiftscale.GetOutputPort())
	acc.SetInputConnection(app.GetOutputPort())
	acc.Update()
	
	data = acc.GetOutput()
	origData = data
	
	originalRange = data.GetScalarRange()

	if logarithmic:
		Logging.info("Scaling scatterplot logarithmically", kw = "imageop")
		logscale = vtk.vtkImageLogarithmicScale()
		logscale.SetInputConnection(acc.GetOutputPort())
		logscale.Update()
		data = logscale.GetOutput()
		
	x0, x1 = data.GetScalarRange()
	
	if countVoxels:
		Logging.info("Scalar range of scatterplot = ", x0, x1, kw = "imageop")
		ctf = fire(x0, x1)
		ctf = equalize(data, ctf)
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInputConnection(data.GetProducerPort())
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		maptocolor.Update()
		data = maptocolor.GetOutput()
		ctf.originalRange = originalRange
	
	Logging.info("Scatterplot has dimensions: ", data.GetDimensions(), data.GetExtent(), kw = "imageop")						  
	data.SetWholeExtent(data.GetExtent())
	img = vtkImageDataToWxImage(data)
	#w, h = img.GetWidth(), img.GetHeight()
	#if w < 255 or h < 255:
	#	dh = 255-h
	#	img.Resize((255, 255),(0, 0), 0,0,0)
	return img, ctf, origData
	
def getZoomFactor(imageWidth, imageHeight, screenWidth, screenHeight):
	"""
	Calculate a zoom factor so that the image
				 will be zoomed to be as large as possible
				 while fitting to screenWidth, screenHeight
	"""		  
	widthProportion = float(screenWidth) / imageWidth
	heightProportion = float(screenHeight) / imageHeight
	return min(widthProportion, heightProportion)
	
def vtkZoomImage(image, zoomInFactor):
	"""
	Zoom a volume
	"""
	zoomOutFactor = 1.0 / zoomInFactor
	reslice = vtk.vtkImageReslice()
	reslice.SetInputConnection(image.GetProducerPort())
	
	spacing = image.GetSpacing()
	extent = image.GetExtent()
	origin = image.GetOrigin()
	extent = (extent[0], extent[1] / zoomOutFactor, extent[2], extent[3] / zoomOutFactor, extent[4], extent[5])
	
	spacing = (spacing[0] * zoomOutFactor, spacing[1] * zoomOutFactor, spacing[2])
	reslice.SetOutputSpacing(spacing)
	reslice.SetOutputExtent(extent)
	reslice.SetOutputOrigin(origin)

	# These interpolation settings were found to have the
	# best effect:
	# If we zoom out, no interpolation
	if zoomOutFactor > 1:
		reslice.InterpolateOff()
	else:
	# If we zoom in, use cubic interpolation
		reslice.SetInterpolationModeToCubic()
		reslice.InterpolateOn()
	data = optimize.execute_limited(reslice)
	data.Update()
	return data
	
def zoomImageToSize(image, width, height):
	"""
	Scale an image to a given size
	"""			  
	return image.Scale(width, height)
	
def zoomImageByFactor(image, zoomFactor):
	"""
	Scale an image by a given factor
	"""		  
	oldWidth, oldHeight = image.GetWidth(), image.GetHeight()
	newWidth, newHeight = int(zoomFactor * oldWidth), int(zoomFactor * oldHeight)
	return zoomImageToSize(image, newWidth, newHeight)

def getSlice(volume, zslice, startpos = None, endpos = None):
	"""
	Extract a given slice from a volume
	"""
	voi = vtk.vtkExtractVOI()
	voi.SetInputConnection(volume.GetProducerPort())
	if startpos:
		startx, starty = startpos
		endx, endy = endpos
	else:
		#startx, starty = 0, 0
		#endx, endy = volume.GetDimensions()[0:2]
		startx, endx, starty, endy, a,b = map(int, volume.GetExtent())
	voi.SetVOI(startx, endx, starty, endy, zslice, zslice)
	voi.Update()
	data = voi.GetOutput()
	return data
	
def saveImageAs(imagedata, zslice, filename):
	"""
	Save a given slice of a volume
	"""		  
	if not filename:
		return
	ext = filename.split(".")[-1]		   
	extMap = {"tiff": "TIFF", "tif": "TIFF", "jpg": "JPEG", "jpeg": "JPEG", "png": "PNG"}
	if not extMap.has_key(ext):
		GUI.Dialogs.showerror(None, "Extension not recognized: %s" % ext, "Extension not recognized")
		return
	vtkclass = "vtk.vtk%sWriter()" % extMap[ext]
	writer = eval(vtkclass)
	img = getSlice(imagedata, zslice)
	writer.SetInputConnection(img.GetProducerPort())
	writer.SetFileName(filename)
	writer.Write()
	
def imageDataTo3Component(image, ctf):
	"""
	Processes image data to get it to proper 3 component RGB data
	"""			
	image.UpdateInformation()
	ncomps = image.GetNumberOfScalarComponents()
	
	if ncomps == 1:
		maptocolor = vtk.vtkImageMapToColors()
		maptocolor.SetInputConnection(image.GetProducerPort())
		maptocolor.SetLookupTable(ctf)
		maptocolor.SetOutputFormatToRGB()
		imagedata = maptocolor.GetOutput()
	elif ncomps > 3:
		Logging.info("Data has %d components, extracting"%ncomps, kw = "imageop")
		extract = vtk.vtkImageExtractComponents()
		extract.SetComponents(0, 1, 2)
		extract.SetInputConnection(image.GetProducerPort())
		imagedata = extract.GetOutput()

	else:
		imagedata = image
	return imagedata

def castImagesToLargestDataType(images):
	"""
	This function casts a list of images using the vtkImageCast so that they all have the 
	same type that is large enough to hold all of the images
	@param images A list of vtkImageData objects
	"""
	returnValues = []
	largestType = -1
	largestMax = 0
	types = []
	differ=0
	for index, i in enumerate(images):
		types.append(i.GetScalarType())
		if types[index] != types[index-1]:
			differ = 1
		if i.GetScalarTypeMax()>largestMax:
			largestType = i.GetScalarType()
			largestMax = i.GetScalarTypeMax()
				
	if not differ: return images

	for i, image in enumerate(images):
		cast = vtk.vtkImageCast()
		cast.SetOutputScalarType(largestType)
		cast.SetInput(image)
		image = cast.GetOutput()
		returnValues.append(image)
	
	return returnValues

def rescaleDataUnits(dataunits, min, max):
	"""
	Rescales dataunits to some range
	@param dataunits list of dataunits to be rescaled
	@param min Minimum value of the range wanted
	@param max Maximum value of the range wanted
	"""
	for dataunit in dataunits:
		ds = dataunit.getDataSource()
		minval, maxval = ds.getOriginalScalarRange()
		rangeOrig = maxval - minval
		range = max - min
		shift = (rangeOrig / range) * min - minval
		scale = range / rangeOrig
		
		ds.setIntensityScale(shift, scale)
		ds.resetColorTransferFunction()
		dataunit.resetColorTransferFunction()

def CreateVolumeFromSlices(vtkImages, spacing):
        """
        Creates a volume from a set of slices (2D vtkImage objects).
        """
        vtkImageAppend = vtk.vtkImageAppend()
        vtkImageAppend.SetAppendAxis(2)
        for sliceIndex in range(0, len(vtkImages)):
                vtkImageAppend.SetInput(sliceIndex, vtkImages[sliceIndex])
        output = vtkImageAppend.GetOutput()
        output.SetSpacing(spacing)
        output.Update()
        return output

def SplitIntoSlices(vtkImage):
        vtkImageClip = vtk.vtkImageClip()
        vtkImageClip.SetInput(vtkImage)
        vtkImageClip.ClipDataOn()
        dimensions = vtkImage.GetDimensions()
        slices = []
        for z in range(0, dimensions[2]):
                vtkImageClip.SetOutputWholeExtent(0, dimensions[0], 0, dimensions[1], z, z)
                slice = vtk.vtkImageData()
                vtkImageClip.Update()
                slice.DeepCopy(vtkImageClip.GetOutput())
                slices.append(slice)
        del vtkImageClip
        return slices

def CheckCrops(crops):
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

def CreateCropsFromInterpolatedPoints(points):
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

def InterpolateBetweenCrops(crop1, crop2, pointsInBetween):
        if pointsInBetween < 0 or type(pointsInBetween) != int:
                raise Exception("Invalid amount of points (%d)inbetween crops." % pointsInBetween)
        CheckCrops([crop1, crop2])
        # We know they're equal in length if they passed CheckCrops().
        interpolatedPoints = []
        for i in range(0, len(crop1)):
                interpolatedPoints.append(InterpolateBetweenPoints(crop1[i], crop2[i], pointsInBetween))
        return CreateCropsFromInterpolatedPoints(interpolatedPoints)

# Notice that this is done in Z direction.
def InterpolateBetweenPoints(point1, point2, pointsInBetween):
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
