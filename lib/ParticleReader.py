"""
 Unit: ParticleReader
 Project: BioImageXD
 Description:

 A module containing classes related to reading objects and tracks.
							
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
__author__ = "BioImageXD Project < http://www.bioimagexd.net/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005 / 01 / 13 14:52:39 $"

import csv
import codecs
import Particle
import re
import scripting

class ParticleReader:
	"""
	A class for reading all particle definitions from .CSV files created by the
	segmentation code
	"""
	def __init__(self, filename, filterObjectVolume = 2):
		"""
		Initialize the reader and necessary information for the reader
		"""
		self.rdr = csv.reader(open(filename), dialect = "excel", delimiter = ";")
		print "Reading file",filename
		self.filterObjectVolume = filterObjectVolume
		self.timepoint = -1  
		self.volumes = []
		self.areas = []
		self.cogs = []
		self.avgints = []
		self.objects = []
		self.avgintsstderr = []
		self.avgdists = []
		self.avgdiststderr = []
		
	def getObjects(self):
		"""
		Return the list of object "intensity" values
		"""
		return self.objects
	
	def getVolumes(self):
		"""
		return a list of the object volumes (sorted)
		"""
		return self.volumes

	def getCentersOfMass(self):
		"""
		return a list of the mass centers of the objects (sorted)
		"""
		return self.cogs
		
	def getAverageIntensities(self):
		"""
		return a list of the avereage intensities of the objects (sorted)
		"""
		return (self.avgints,self.avgintsstderr)

	def getAreas(self):
		"""
		Return a list of the areas of the objects (sorted)
		"""
		return self.areas

	def getAverageDistances(self):
		"""
		Return a tuple of lists of the average distances of the objects to other objects
		"""
		return (self.avgdists,self.avgdiststderr)
		
	def read(self, statsTimepoint = 0):
		"""
		Read the particles from the filename and create corresponding instances of Particle class
		"""
		ret = []
		skipNext = 0
		curr = []
		voxelSize = None
		for line in self.rdr:
			if skipNext:
				skipNext = 0
				continue
			if len(line) == 1:
				timePoint = int(line[0].split(" ")[1])
				#print "Current timepoint = ", timePoint
				if curr:
					ret.append(curr)
				curr = []
				self.timepoint = timePoint
				skipNext = 1
				continue
			else:
				try:
					obj, volumemicro, volume, cogX, cogY, cogZ, umcogX, umcogY, umcogZ, avgint, avgintstderr, avgdist, avgdiststderr, areamicro = line[0:14]
				except:
					obj, volumemicro, volume, cogX, cogY, cogZ, umcogX, umcogY, umcogZ, avgint = line[0:10] # Works with old data too
					avgintstderr = 0.0
					avgdist = 0.0
					avgdiststderr = 0.0
					areamicro = 0.0
			try:
				volume = int(volume)
				volumemicro = float(volumemicro)
			except ValueError:
				continue
			obj = int(obj)
			umcog = [float(umcogX), float(umcogY), float(umcogZ)]
			cog = [float(cogX), float(cogY), float(cogZ)]
			if not voxelSize and cog[0] > 0 and cog[1] > 0 and cog[2] > 0:
				voxelSize = [1.0, 1.0, 1.0]
				for i in range(3):
					voxelSize[i] = umcog[i] / cog[i]
			cog = map(int, cog)
			avgint = float(avgint)
			avgintstderr = float(avgintstderr)
			avgdist = float(avgdist)
			avgdiststderr = float(avgdiststderr)
			areamicro = float(areamicro)
			
			if volume >= self.filterObjectVolume and obj != 0: 
				particle = Particle(umcog, cog, self.timepoint, volume, avgint, obj)
				particle.setVoxelSize(voxelSize)
				curr.append(particle)
			if self.timepoint == statsTimepoint:
				self.objects.append(obj)
				self.cogs.append(tuple(cog))
				self.volumes.append((volume, volumemicro))
				self.avgints.append(avgint)
				self.avgintsstderr.append(avgintstderr)
				self.areas.append(areamicro)
				self.avgdists.append(avgdist)
				self.avgdiststderr.append(avgdiststderr)
		if curr:
			ret.append(curr)
		return ret

