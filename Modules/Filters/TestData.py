	# -*- coding: iso-8859-1 -*-
"""
 Copyright (C) 2005  BioImageXD Project
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import lib.ProcessingFilter
import vtkbxd
import GUI.GUIBuilder
import lib.FilterTypes
import scripting
import types
import random
import math
import vtk

class TestDataFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	Description: A filter for removing solitary noise pixels
	"""		
	name = "Test data generation"
	category = lib.FilterTypes.FILTERING
	
	def __init__(self):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.descs = {"X":"X:", "Y":"Y:", "Z":"Z:","Time":"Number of timepoints",
		"Coloc":"Create colocalization between channels", 
		"ColocAmountStart":"Coloc. amnt (at start)",
		"ColocAmountEnd":"Coloc. amnt (at end)",
		"Shift":"Create shift in the data",
		"ShiftStart":"Min. shift (in px):",
		"ShiftEnd":"Max. shift (in px)",
		"ShotNoiseAmount":"% of shot noise",
		"ShotNoiseMin":"Min. intensity of shot noise",
		"BackgroundNoiseAmount":"% of background noise",
		"BackgroundNoiseMin":"Min. intensity of bg noise",
		"BackgroundNoiseMax":"Max. intensity of bg noise",
		"NumberOfObjectsStart":"# objects (at least)","NumberOfObjectsEnd":"# of objects (at most)",
		"ObjSizeStart":"Min. size of object (in px)","ObjSizeEnd":"Max. size of object (in px)",
		"ObjectFluctuationStart":"Min. change in object #",
		"ObjectFluctuationEnd":"Max. change in object #",
		"RandomMovement":"Move randomly",
		"MoveTowardsPoint":"Move towards a point",
		"Clustering":"Objects should cluster"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ ["Dimensions",("X","Y","Z","Time")],["Shift", ("Shift","ShiftStart","ShiftEnd")],
			["Noise",("ShotNoiseAmount","ShotNoiseMin","BackgroundNoiseAmount","BackgroundNoiseMin","BackgroundNoiseMax")],
			["Objects",("NumberOfObjectsStart","NumberOfObjectsEnd","ObjSizeStart","ObjSizeEnd","ObjectFluctuationStart","ObjectFluctuationEnd")],
			["Colocalization",("Coloc","ColocAmountStart","ColocAmountEnd")],
			["Movement strategy",("RandomMovement","MoveTowardsPoint","Clustering")],
		]
		
	def setParameter(self, parameter, value):
		"""
		An overriden method for setting the parameter value, used to catch and set the number
		of timepoints
		"""
		if self.parameters.get(parameter)!=value:
			self.modified = 1
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter == "Time":
			if self.dataUnit and self.initDone:
				self.dataUnit.setNumberOfTimepoints(value)
				scripting.visualizer.setTimeRange(1,value)
		
		#if modified and self.initDone:
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["ShotNoiseAmount","BackgroundNoiseAmount"]:
			return types.FloatType
		if parameter in ["X","Y","Z","ShiftStart","ShiftEnd"]:
			return types.IntType
			
		if parameter in ["Coloc","Shift","RandomMovement","MoveTowardsPoint","Clustering"]:
			return types.BooleanType
			
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter in ["X","Y"]:return 512
		if parameter == "Z": return 25
		if parameter == "Time": return 5
		if parameter == "ColocAmountStart": return 1
		if parameter == "ColocAmountEnd": return 50
		if parameter == "ShotNoiseAmount": return 0.1
		if parameter == "ShotNoiseMin": return 128
		if parameter == "BackgroundNoiseAmount": return 5
		if parameter == "BackgroundNoiseMin": return 1
		if parameter == "BackgroundNoiseMax": return 30
		if parameter == "NumberOfObjectsStart":return 20
		if parameter == "NumberOfObjectsEnd": return 200
		if parameter == "ObjectFluctuationStart": return 0
		if parameter == "ObjectFluctuationEnd": return 0
		if parameter == "ObjSizeStart": return 5
		if parameter == "ObjSizeEnd": return 50
		
		# Shift of 1-5% per timepoint
		if parameter == "ShiftStart": return 1
		if parameter == "ShiftEnd": return 15
		return 0
		
	def createTimeSeries(self):
		"""
		Create a time series of configurations that correspond to the current parameters
		"""
		self.modified = 0
		x,y,z = self.parameters["X"],self.parameters["Y"], self.parameters["Z"]
		self.majorAxis = random.randint(int(0.15*y), int(0.85*y))
		
		self.jitters = []
		self.shifts = []
		self.objects = []
		
		shiftDir=[0,0,0]
		shiftAmnt = 0
		for tp in range(0, self.parameters["Time"]):
			if self.parameters["Shift"]:
				# If shifting is requested, then in half the cases, create some jitter
				# meaning shift of 1-5 pixels in X and Y and 0-1 pixels in Z
				if random.random()<0.5:
					jitterx = random.randint(1,5)
					jittery = random.randint(1,5)
					jitterz = random.randint(0,1)
					self.jitters.append((jitterx, jittery, jitterz))
				
				# If we're in the middle of a shift, then continue to that direction
				if shiftAmnt >0:
					shiftx = shiftDir[0]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
					shifty = shiftDir[1]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
					shifty = shiftDir[2]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
					self.shifts.append((shiftx, shifty, shiftz))
					shiftAmnt -= 1
				# If no shift is going on, then create a shift in some direction
				else:
					shiftAmnt = random.randint(2, 4)
					# There's a 50% chance that there's no shift, and 2x25% chance of the shift being
					# in either direction
					shiftDir[0]=random.choice([-1,0,0.1])
					shiftDir[1]=random.choice([-1,0,0,1])
					# there's 60% chance of having shift in z dir
					shiftDir[2] = random.choice([-1,-1,-1,0,0,0,1,1,1])
					
				
				# in 5% of cases, create a jolt of 2 to 5 px in z direction 
				if random.random()<0.05:
					direction = random.choice([-1,1])
					x,y,z = self.shifts[-1]
					z+=random.randint(2,5)*direction
					self.shifts[-1] = (x,y,z)
				
			objs = self.createObjectsForTimepoint(tp)
			self.objects.append(objs)
	
	def createObjectsForTimepoint(self, tp):
		"""
		Create objects for given timepoint
		"""
		
			
	def createData(self):
		"""
		Create a test dataset within the parameters defined
		"""
		if self.modified:
			self.createTimeSeries()
		currentTimePoint = self.getCurrentTimepoint()
		print "\n\nGenerating timepoint %d"%currentTimepoint

		image = vtk.vtkImageData()
		image.SetScalarTypeToUnsignedChar()
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		image.SetDimensions((x,y,z))
		
		print "Initializing image"
		#for iz in range(0,z):
		#	for iy in range(0,y):
		#		for ix in range(0,x):
		#			image.SetScalarComponentFromDouble(ix,iy,iz, 0,0)
		mult = vtk.vtkImageMath()
		mult.SetOperationToMultiplyByK()
		mult.SetConstantK(0)
		mult.SetInput(image)
		image = mult.GetOutput()
		print "Creating shot noise"
		noisePercentage = self.parameters["ShotNoiseAmount"]
		noiseAmount=(noisePercentage/100.0)*(x*y*z)
		while noiseAmount>0:
			rx,ry,rz = random.randint(0,x-1), random.randint(0,y-1), random.randint(0,z-1)
			image.SetScalarComponentFromDouble(rx,ry,rz, 0, random.randint(self.parameters["ShotNoiseMin"],255))
			noiseAmount-=1
		bgnoisePercentage = self.parameters["BackgroundNoiseAmount"]
		noiseAmount=(bgnoisePercentage/100.0)*(x*y*z)
		while noiseAmount>0:
			rx,ry,rz = random.randint(0,x-1), random.randint(0,y-1), random.randint(0,z-1)
			image.SetScalarComponentFromDouble(rx,ry,rz, 0, random.randint(self.parameters["BackgroundNoiseMin"],self.parameters["BackgroundNoiseMax"]))
			noiseAmount-=1

		shiftx, shifty, shiftz = self.shifts[currentTimePoint]
		
		print "Creating objects"
		for i in range(0, random.randint(self.parameters["NumberOfObjectsStart"],self.parameters["NumberOfObjectsEnd"])):
			while 1:
				rx,ry,rz = random.randint(0,x-1), random.randint(0,y-1), random.randint(0,z-1)
				if self.pointInsideEllipse((rx,ry,rz), self.majorAxis):
					break
					
			sizeStart = self.parameters["ObjSizeStart"]
			sizeEnd = self.parameters["ObjSizeEnd"]

			size = random.randint(sizeStart, sizeEnd)
			self.createObjectAt(image, rx,ry,rz, size)
			
		return image
		
	def pointInsideEllipse(self, pt, majorAxis, f1 = None, f2 = None):
		"""
		@param pt Point to be tested
		@param majorAxis Length of the major axis of ellipse
		@param f1, f2 optional focal points of the ellipse
		@return true if given point is inside the ellipse
		"""
		rx, ry,rz = pt
		dx = (y-majorAxis)/2
		if not f1:
			f1y = 2*dx
			f1x = x/2
		else:
			f1x,f1y = f1
		if not f2:
			f2y = y-(2*dx)
			f2x = x/2
		else:
			f2x,f2y = f2
			
		p1= (f1x-rx,f1y-ry)
		p2 = (f2x-rx,f2y-ry)
		d1=math.sqrt(p1[0]*p1[0]+p1[1]*p1[1])+math.sqrt(p2[0]*p2[0]+p2[1]*p2[1])
		return d1<majorAxis
		
	def createObjectAt(self, imageData, x0,y0,z0,size):
		"""
		Create an object in the image at the give position
		@param imageData the image to modify
		@param x0, y0, z0	 the coordinates of the object
		@param size      the size of the object in pixels
		"""
		r = int(math.pow(size*2.3561944901923448, 0.333333))
		#r = int(1+math.sqrt(size/math.pi))
		n = 0
		origr = float(r)
		maxx,maxy,maxz = imageData.GetDimensions()
		xs = x0-r
		ys = y0-r
		zs = z0-r
		if xs<0:xs=0
		if ys<0:ys=0
		if zs<0:zs=0
		xe = x0+r
		ye = y0+r
		ze = z0+r
		if xe>=maxx:xe=maxx-1
		if ye>=maxy:ye=maxy-1
		if ze>=maxz:ze=maxz-1
		

		for x in range(xs,xe):
			for y in range(ys,ye):
				for z in range(zs,ze):
					d=math.sqrt((x0-x)**2+(y0-y)**2+(z0-z)**2)
					if d <= r:
						minval = int(255-(d/float(r)*128))
						imageData.SetScalarComponentFromDouble(x,y,z,0,random.randint(minval,255))
	    	
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""			   
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None
		
		return self.createData()
			
