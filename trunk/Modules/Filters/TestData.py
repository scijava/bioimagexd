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
import os
import codecs
import Logging
import csv
import lib.ParticleReader
import lib.Particle

class TestDataFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
	A filter for generating test data
	"""		
	name = "Test data generation"
	category = lib.FilterTypes.SIMULATION

	def __init__(self):
		"""
		Initialization
		"""
		lib.ProcessingFilter.ProcessingFilter.__init__(self, (1, 1))
		self.objects = []
		self.readObjects = []
		self.polydata = None
		self.imageCache = {}
		self.spacing = (1,1,1)
		self.modified = 1
		self.descs = {"X":"X:", "Y":"Y:", "Z":"Z:","Time":"Number of timepoints",
		"Coloc":"Create colocalization between channels", 
		"ColocAmountStart":"Coloc. amnt (at start)",
		"ColocAmountEnd":"Coloc. amnt (at end)",
		"Shift":"Create shift in the data",
		"ShiftStart":"Min. shift (in x,y px size):",
		"ShiftEnd":"Max. shift (in x,y px size)",
		"ShotNoiseAmount":"% of shot noise",
		"ShotNoiseMin":"Min. intensity of shot noise",
		"BackgroundNoiseAmount":"% of background noise",
		"BackgroundNoiseMin":"Min. intensity of bg noise",
		"BackgroundNoiseMax":"Max. intensity of bg noise",
		"NumberOfObjectsStart":"# objects (at least)",
		"NumberOfObjectsEnd":"# of objects (at most)",
		"ObjSizeStart":"Min. size of object (in px)",
		"ObjSizeEnd":"Max. size of object (in px)",
		"ObjectFluctuationStart":"Min. change in object #",
		"ObjectFluctuationEnd":"Max. change in object #",
		"RandomMovement":"Move randomly",
		"MoveTowardsPoint":"Move towards a point",
		"TargetPoints":"# of target points",
		"Clustering":"Objects should cluster",
		"SpeedStart":"Obj. min speed (in x,y px size)",
		"SpeedEnd":"Obj. max speed (in x,y px size)",
		"SizeChange":"Size change (in %)",
		"ClusterPercentage":"% of objects cluster",
		"ClusterDistance":"Min. distance for clustering (in x,y px size)",
		"Cache":"Cache timepoints",
		"CacheAmount":"# of timepoints cached",
		"CreateAll":"Create all timepoints at once",
		"CreateNoise":"Create noise",
		"ReadObjects":"Read sizes and number from",
		"ObjectsCreateSource":"Create objects close to surface from source",
		"SigmaDistSurface":"Sigma of Gaussian distance to surface (in x,y px size)"}
	
	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""			   
		return [ ["Caching",("Cache","CacheAmount","CreateAll")],["Dimensions",("X","Y","Z","Time")],["Shift", ("Shift","ShiftStart","ShiftEnd")],
			["Noise",("CreateNoise","ShotNoiseAmount","ShotNoiseMin","BackgroundNoiseAmount","BackgroundNoiseMin","BackgroundNoiseMax")],
			["Objects",(("ReadObjects", "Select object statistics file", "*.csv"),"NumberOfObjectsStart","NumberOfObjectsEnd","ObjSizeStart","ObjSizeEnd","ObjectFluctuationStart","ObjectFluctuationEnd","SizeChange", "ObjectsCreateSource", "SigmaDistSurface")],
			#["Colocalization",("Coloc","ColocAmountStart","ColocAmountEnd")],
			["Movement strategy",("RandomMovement","MoveTowardsPoint","TargetPoints","SpeedStart","SpeedEnd")],
			["Clustering",("Clustering","ClusterPercentage","ClusterDistance")],
		]
		
	def setParameter(self, parameter, value):
		"""
		An overriden method for setting the parameter value, used to catch and set the number
		of timepoints
		"""
		if self.parameters.get(parameter)!=value:
			self.modified = 1
		lib.ProcessingFilter.ProcessingFilter.setParameter(self, parameter, value)
		if parameter in ["Time", "X", "Y", "Z"]:
			if self.dataUnit:
				self.dataUnit.setNumberOfTimepoints(self.parameters["Time"])
				self.dataUnit.setModifiedDimensions((self.parameters["X"], self.parameters["Y"], self.parameters["Z"]))
				lib.messenger.send(None, "update_dataset_info")
				
	def onRemove(self):
		"""
		A callback for stuff to do when this filter is being removed.
		"""
		if self.dataUnit:
			self.dataUnit.setModifiedDimensions(None)
				
	def getLongDesc(self, parameter):
		"""
		Return a long description of the parameter
		""" 
		return ""
		
	def getType(self, parameter):
		"""
		Return the type of the parameter
		"""	   
		if parameter in ["ShotNoiseAmount","BackgroundNoiseAmount","ClusteringPercentage","SigmaDistSurface"]:
			return types.FloatType
		if parameter in ["X","Y","Z","ShiftStart","ShiftEnd"]:
			return types.IntType
			
		if parameter in ["CreateNoise","Coloc","Shift","RandomMovement","MoveTowardsPoint","Clustering","Cache","CreateAll","ObjectsCreateSource"]:
			return types.BooleanType
		if parameter == "ReadObjects":
			return GUI.GUIBuilder.FILENAME
			
		return types.IntType
		
	def getDefaultValue(self, parameter):
		"""
		Return the default value of a parameter
		"""		
		if parameter in ["X","Y"]: return 512
		if parameter == "Cache": return True
		if parameter == "CacheAmount": return 15
		if parameter == "CreateAll": return True
		if parameter == "Z": return 25
		if parameter == "TargetPoints": return 1
		if parameter == "Time": return 15
		if parameter == "Clustering": return True
		if parameter == "ColocAmountStart": return 1
		if parameter == "ClusterPercentage": return 20
		if parameter == "ClusterDistance":return 30
		if parameter == "ColocAmountEnd": return 50
		if parameter == "MoveTowardsPoint":return True
		if parameter == "ShotNoiseAmount": return 0.1
		if parameter == "ShotNoiseMin": return 128
		if parameter == "SizeChange": return 5
		if parameter == "SpeedStart": return 2
		if parameter == "SpeedEnd": return 10
		if parameter == "BackgroundNoiseAmount": return 5
		if parameter == "BackgroundNoiseMin": return 1
		if parameter == "BackgroundNoiseMax": return 30
		if parameter == "NumberOfObjectsStart":return 20
		if parameter == "NumberOfObjectsEnd": return 200
		if parameter == "ObjectFluctuationStart": return 0
		if parameter == "ObjectFluctuationEnd": return 0
		if parameter == "ObjSizeStart": return 5
		if parameter == "ObjSizeEnd": return 50
		if parameter == "ReadObjects": return "statistics.csv"
		if parameter == "ObjectsCreateSource": return False
		if parameter == "SigmaDistSurface": return 5.0
		
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
		self.majorAxis = random.randint(int(0.55*y), int(0.85*y))
		
		for image in self.imageCache.values():
			image.ReleaseData()
		
		self.imageCache = {}
		self.jitters = []
		self.shifts = []
		self.objects = []
		
		shiftDir=[0,0,0]
		shiftAmnt = 0
		for tp in range(0, self.parameters["Time"]):
			if self.parameters["Shift"]:
				print "Creating shift amounts for timepoint %d"%tp
				# If shifting is requested, then in half the cases, create some jitter
				# meaning shift of 1-5 pixels in X and Y and 0-1 pixels in Z
				if random.random() < 0.5:
					jitterx = random.randint(1,5)
					jittery = random.randint(1,5)
					jitterz = random.randint(0,1)
					self.jitters.append((jitterx, jittery, jitterz))
				
				# If we're in the middle of a shift, then continue to that direction
				if shiftAmnt > 0:
					shiftx = shiftDir[0]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
					shifty = shiftDir[1]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
					shiftz = shiftDir[2]*random.randint(self.parameters["ShiftStart"], self.parameters["ShiftEnd"])
					self.shifts.append((shiftx, shifty, shiftz))
					shiftAmnt -= 1
				# If no shift is going on, then create a shift in some direction
				else:
					shiftAmnt = random.randint(2, 4)
					# There's a 50% chance that there's no shift, and 2x25% chance of the shift being
					# in either direction
					shiftDir[0] = random.choice([-1,0,0.1])
					shiftDir[1] = random.choice([-1,0,0,1])
					# there's 60% chance of having shift in z dir
					shiftDir[2] = random.choice([-1,-1,-1,0,0,0,0,1,1,1])
					
				
				# in 5% of cases, create a jolt of 2 to 5 px in z direction 
				if random.random() < 0.05:
					direction = random.choice([-1,1])
					x,y,z = self.shifts[-1]
					z += random.randint(2,5)*direction
					self.shifts[-1] = (x,y,z)
			else:
				self.shifts.append((0,0,0))
				
			print "Creating objects for timepoint %d"%tp
			objs = self.createObjectsForTimepoint(tp)

			if self.parameters["ObjectFluctuationEnd"]:
				print "Adding fluctuations to object numbers"
				objs = self.createFluctuations(objs)
			self.objects.append(objs)
			
		self.tracks = []
		for tp, objs in enumerate(self.objects):
			for i, (objN, (x,y,z), size) in enumerate(objs):
				if len(self.tracks) < objN:
					self.tracks.append([])
				p = lib.Particle.Particle((x,y,z), (x,y,z), tp, size, 20, objN)
				self.tracks[objN-1].append(p)
		if self.parameters["Clustering"]:
			print "Introducing clustering"
			self.clusterObjects(self.objects)
	
	def clusterObjects(self, objects):
		"""
		Create clustering of objects
		"""
		combine = []
		clustered = {}
		clusteredObjN = {}
		
		for tp,objs in enumerate(objects):
			for i, (objN, (x,y,z), size) in enumerate(objs):
				for j, (objN2, (x2,y2,z2), size) in enumerate(objs):
					if objN == objN2: continue
					if objN in clusteredObjN: continue
					if objN2 in clusteredObjN: continue
					if (tp,objN) in clustered or (tp,objN2) in clustered: continue
					d = math.sqrt(((x2-x) * self.spacing[0])**2 + ((y2-y) * self.spacing[1])**2 + ((z2-z) * self.spacing[2])**2)
					if d < self.parameters["ClusterDistance"]:
						if random.random()*100 < self.parameters["ClusterPercentage"]:
							combine.append((tp,objN,i,objN2,j))
							clustered[(tp,objN2)]=1
							clustered[(tp,objN)]=1
							clusteredObjN[objN]=1
							clusteredObjN[objN2]=1

		toremove=[]
		for tp,objN,i,objN2,j in combine:
			ob1 = objects[tp][i]
			ob2 = objects[tp][j]
			if len(self.tracks[objN-1]) > tp and len(self.tracks[objN2-1]) > tp:
				self.tracks[objN-1].remove(self.tracks[objN-1][tp])
				self.tracks[objN2-1].remove(self.tracks[objN2-1][tp])
			toremove.append((tp,ob1,ob2))
			objN,(x1,y1,z1),s1 = ob1
			objN2,(x2,y2,z2),s2 = ob2
			s3 = int((s1+s2)*0.7)
			x3 = (x1+x2)/2
			y3 = (y1+y2)/2
			z3 = (z1+z2)/2
			objects[tp].append((objN,(x3,y3,z3), s3))
			self.tracks[objN-1].insert(tp, lib.Particle.Particle((x3,y3,z3), (x3,y3,z3), tp, size, 20, objN))

		for tp,ob1,ob2 in toremove:
			objects[tp].remove(ob1)
			objects[tp].remove(ob2)
		
	
	def createFluctuations(self, objects):
		"""
		Create fluctuations in the number of objects
		"""
		removeN = random.randint(self.parameters["ObjectFluctuationStart"],self.parameters["ObjectFluctuationEnd"])
		addN = random.randint(self.parameters["ObjectFluctuationStart"],self.parameters["ObjectFluctuationEnd"])
		
		for i in range(0, removeN):
			obj = random.choice(objects)
			objects.remove(obj)
		print "Removed",removeN,"objects"
		for i in range(0, addN):
			objects.append(self.createObject())
		print "Added",addN,"objects"
		
	def createObjectsForTimepoint(self, tp):
		"""
		Create objects for given timepoint
		"""
		objs = []
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		coeff = z/float(x)
		if tp == 0:
			if self.parameters["MoveTowardsPoint"]:
				self.towardsPoints = []
				for c in range(0, self.parameters["TargetPoints"]):
					print "Getting point toward which to move"
					rx, ry, rz = self.getPointInsideCell()
					print "it's",rx,ry,rz
					self.towardsPoints.append((rx,ry,rz))

			if self.readObjects:
				self.numberOfObjects = len(self.readObjects)
			else:
				self.numberOfObjects = random.randint(self.parameters["NumberOfObjectsStart"],self.parameters["NumberOfObjectsEnd"])
			
			for obj in range(1, self.numberOfObjects+1):
				print "Creating object %d"%obj
				(rx,ry,rz), size = self.createObject(obj)
				objs.append((obj, (rx,ry,rz), size))
		else:
			for objN, (rx,ry,rz), size in self.objects[tp-1]:
				if self.parameters["RandomMovement"]:
					speedx = random.choice([-1,1])*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					speedy = random.choice([-1,1])*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					speedz = random.choice([-1,1])*coeff*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
				elif self.parameters["MoveTowardsPoint"]:
					nearest = None
					smallest = 2**31
					for (x,y,z) in self.towardsPoints:
						d = math.sqrt(((x-rx) * self.spacing[0])**2 + ((y-ry) * self.spacing[1])**2 + ((z-rz) * self.spacing[2])**2)
						if d < smallest:
							smallest = d
							nearest = (x,y,z)
					speedx = random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					speedy = random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					speedz = coeff*random.randint(self.parameters["SpeedStart"], self.parameters["SpeedEnd"])
					if rx > nearest[0]:
						speedx *= -1
					if ry > nearest[1]:
						speedy *= -1
					if ry > nearest[2]:
						speedz *= -1
				rx += speedx
				ry += speedy
				rz += speedz
				if rx < 0: x = 0
				if ry < 0: y = 0
				if rz < 0: z = 0
				if rx >= self.parameters["X"]: rx = self.parameters["X"] - 1
				if ry >= self.parameters["Y"]: rx = self.parameters["Y"] - 1
				if rz >= self.parameters["Z"]: rx = self.parameters["Z"] - 1
				
				if self.parameters["SizeChange"]:
					maxchange = int(size*(self.parameters["SizeChange"]/100.0))
					change = random.randint(0, maxchange)
					if random.random() < 0.5: change *= -1
					size += change
				objs.append((objN, (rx,ry,rz), size))
		return objs
		
	def createObject(self, objNum):
		if self.readObjects:
			size = self.readObjects[objNum][0][0]
		else:
			sizeStart = self.parameters["ObjSizeStart"]
			sizeEnd = self.parameters["ObjSizeEnd"]
			size = random.randint(sizeStart, sizeEnd)

		if self.parameters["ObjectsCreateSource"]:
			rx, ry, rz = self.getPointCloseToSurface()
		else:
			rx, ry, rz = self.getPointInsideCell()

		return ((rx,ry,rz),size)
		
	def getPointInsideCell(self):
		x,y,z = self.parameters["X"],self.parameters["Y"], self.parameters["Z"]
		while 1:
			rx,ry,rz = random.randint(0,x-1), random.randint(0,y-1), random.randint(0,z-1)
			if self.pointInsideEllipse((rx,ry,rz), self.majorAxis):
				break
		return rx,ry,rz
		
	def createData(self, currentTimepoint):
		"""
		Create a test dataset within the parameters defined
		"""
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		if self.modified:
			print "Creating the time series data"
			self.createTimeSeries()
			if self.parameters["CreateAll"]:
				n = min(self.parameters["CacheAmount"], self.parameters["Time"])
				for i in range(0, n):
					if i == currentTimepoint: 
						print "Won't create timepoint %d, it'll be last"%i
						continue
					self.createData(i)

		print "\n\nGenerating timepoint %d"%currentTimepoint
		
		if currentTimepoint in self.imageCache:
			print "Returning cached image"
			return self.imageCache[currentTimepoint]
		
		image = vtk.vtkImageData()
		image.SetScalarTypeToUnsignedChar()
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		image.SetDimensions((x,y,z))
		image.AllocateScalars()
		image.SetSpacing(self.spacing)
		
		print "Initializing image"
		for iz in range(0,z):
			for iy in range(0,y):
				for ix in range(0,x):
					image.SetScalarComponentFromDouble(ix,iy,iz,0,0)

		print "Creating shot noise"
		if self.parameters["CreateNoise"]:
			noisePercentage = self.parameters["ShotNoiseAmount"]
			noiseAmount = (noisePercentage/100.0) * (x*y*z)
			bgnoisePercentage = self.parameters["BackgroundNoiseAmount"]
			bgNoiseAmount = (bgnoisePercentage/100.0) * (x*y*z)
		else:
			noiseAmount = 0
			bgNoiseAmount = 0
			
		while noiseAmount > 0:
			rx,ry,rz = random.randint(0,x-1), random.randint(0,y-1), random.randint(0,z-1)
			image.SetScalarComponentFromDouble(rx,ry,rz,0,random.randint(self.parameters["ShotNoiseMin"],255))
			noiseAmount -= 1
		
		while bgNoiseAmount > 0:
			rx,ry,rz = random.randint(0,x-1), random.randint(0,y-1), random.randint(0,z-1)
			image.SetScalarComponentFromDouble(rx,ry,rz, 0, random.randint(self.parameters["BackgroundNoiseMin"],self.parameters["BackgroundNoiseMax"]))
			noiseAmount -= 1

		shiftx, shifty, shiftz = self.shifts[currentTimepoint]
		
		print "Creating objects"
		for objN, (rx,ry,rz), size in self.objects[currentTimepoint]:
			rx += shiftx
			ry += shifty
			rz += shiftz
			self.createObjectAt(image, rx,ry,rz, size)
		
		n = len(self.imageCache.items())
		if n > self.parameters["CacheAmount"]:
			items = self.imageCache.keys()
			items.sort()
			print "Removing ", items[0], "from cache"
			self.imageCache[items[0]].ReleaseData()
			del self.imageCache[items[0]]
		self.imageCache[currentTimepoint] = image
		return image
		
	def pointInsideEllipse(self, pt, majorAxis, f1 = None, f2 = None):
		"""
		@param pt Point to be tested
		@param majorAxis Length of the major axis of ellipse
		@param f1, f2 optional focal points of the ellipse
		@return true if given point is inside the ellipse
		"""
		rx,ry,rz = pt
		x,y,z = self.parameters["X"], self.parameters["Y"], self.parameters["Z"]
		dx = (y-majorAxis)/2
		#print "Testing",rx,ry,rz,"major axis=",self.majorAxis
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
			
		p1 = (f1x-rx,f1y-ry)
		p2 = (f2x-rx,f2y-ry)
		d1 = math.sqrt(p1[0]*p1[0]+p1[1]*p1[1])+math.sqrt(p2[0]*p2[0]+p2[1]*p2[1])
		return d1 < majorAxis
		
	def createObjectAt(self, imageData, x0, y0, z0, size):
		"""
		Create an object in the image at the give position
		@param imageData the image to modify
		@param x0, y0, z0	 the coordinates of the object
		@param size      the size of the object in pixels
		"""
		origr = math.pow(size*2.3561944901923448, 0.333333)
		#r = int(1+math.sqrt(size/math.pi))
		n = 0
		r = int(origr)
		maxx,maxy,maxz = imageData.GetDimensions()
		xs = x0-r
		ys = y0-r
		zs = z0-r
		if xs < 0: xs = 0
		if ys < 0: ys = 0
		if zs < 0: zs = 0
		xe = x0+r
		ye = y0+r
		ze = z0+r
		if xe >= maxx: xe = maxx-1
		if ye >= maxy: ye = maxy-1
		if ze >= maxz: ze = maxz-1
		
		count = 0
		for x in range(xs,xe):
			for y in range(ys,ye):
				for z in range(zs,ze):
					# Do not use spacing to get real looking objects
					d = math.sqrt((x0-x)**2 + (y0-y)**2 + (z0-z)**2)
					if d <= r:
						#minval = int(255-(d/float(r)*128))
						minval = 220
						imageData.SetScalarComponentFromDouble(x,y,z,0,random.randint(minval,255))
						count += 1
#		print "Size %d yields %d voxels"%(size, count)

	def getPointCloseToSurface(self):
		"""
		Select random point close to surface provided by user as parameter
		"""
		numOfPolys = self.polydata.GetNumberOfPolys()
		randPolyID = random.randint(0, numOfPolys-1)
		pdata = self.polydata.GetPolys().GetData()
		pointIDs = [int(pdata.GetTuple1(i)) for i in range(4*randPolyID+1,4*randPolyID+4)]
		points = [self.polydata.GetPoint(i) for i in pointIDs]
		# Calculate center of random polygon
		center = [0.0, 0.0, 0.0]
		for point in points:
			for i in range(3):
				center[i] += point[i]

		for i in range(3):
			center[i] /= 3

		sigma = self.parameters["SigmaDistSurface"]
		randomCOM = [int(random.gauss(center[i], sigma) / self.spacing[i]) for i in range(3)]
		dims = (self.parameters["X"], self.parameters["Y"], self.parameters["Z"])

		for i in range(3):
			if randomCOM[i] < 0:
				randomCOM[i] = 0
			elif randomCOM[i] > dims[i] - 1:
				randomCOM[i] = dims[i] - 1

		return tuple(randomCOM)
		

	def writeOutput(self, dataUnit, timepoint):
		"""
		Optionally write the output of this module during the processing
		"""
		fileroot = self.dataUnit.getName()
		bxddir = dataUnit.getOutputDirectory()
		fileroot = os.path.join(bxddir, fileroot)
		filename = "%s.csv" % fileroot
		self.writeToFile(filename, dataUnit, timepoint)
		
	def writeToFile(self, filename, dataUnit, timepoint):
		"""
		write the objects from a given timepoint to file
		"""
		# Make own writer for this and Analyze objects
		f = codecs.open(filename, "ab", "latin1")
		Logging.info("Saving statistics to file %s"%filename, kw="processing")
		
		w = csv.writer(f, dialect = "excel", delimiter = ";")
		
		settings = dataUnit.getSettings()
		settings.set("StatisticsFile", filename)
		w.writerow(["Timepoint %d" % timepoint])
		w.writerow(["Object #", "Center of Mass X", "Center of Mass Y", "Center of Mass Z", "Volume (voxels)"])
		for obj in self.objects[timepoint]:
			objN, com, volume = obj
			w.writerow([str(objN), str(cog[0]), str(cog[1]), str(cog[2]), str(volume)])
		f.close()
					
		if timepoint == self.parameters["Time"]-1:
			trackWriter = lib.ParticleReader.ParticleWriter()
			trackWriter.writeTracks(filename, self.tracks, 3)
		
	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None

		currentTimepoint = self.getCurrentTimepoint()
		inputImage = self.getInput(1)
		self.spacing = list(inputImage.GetSpacing())
		for i in range(3):
			self.spacing[i] /= self.spacing[0]
		self.spacing = tuple(self.spacing)

		if os.path.exists(self.parameters["ReadObjects"]) and self.modified:
			reader = lib.Particle.ParticleReader(self.parameters["ReadObjects"], 0)
			objects = reader.read()
			volumes = reader.getVolumes()
			intensities = reader.getAverageIntensities()
			objCount = min(len(volumes),len(intensities[0]))
			self.readObjects = []
			for i in range(objCount):
				self.readObjects.append((volumes[i], intensities[0][i]))

		if self.parameters["ObjectsCreateSource"] and self.modified:
			# Update first dims of result data
			wholeExtent = inputImage.GetWholeExtent()
			x = wholeExtent[1] - wholeExtent[0] + 1
			y = wholeExtent[3] - wholeExtent[2] + 1
			z = wholeExtent[5] - wholeExtent[4] + 1
			if self.dataUnit:
				self.parameters["X"] = x
				self.parameters["Y"] = y
				self.parameters["Z"] = z
				self.dataUnit.setModifiedDimensions((x, y, z))
				lib.messenger.send(None, "update_dataset_info")

			polydata = self.getPolyDataInput(1)
			if polydata:
				self.polydata = polydata
			else:
				Logging.error("No polydata in source", "Cannot create objects close to surface of input as there is no polydata in input.")
				return inputImage
		
		return self.createData(currentTimepoint)
	
