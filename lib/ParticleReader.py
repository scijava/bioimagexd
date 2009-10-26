"""
 Unit: ParticleReader
 Project: BioImageXD
 Description:

 A module containing classes related to reading and writing tracks
							
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
__author__ = "BioImageXD Project < http://www.bioimagexd.org/>"
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
	def __init__(self, filename, filterObjectSize = 1):
		"""
		Initialize the reader and necessary information for the reader
		"""
		self.rdr = csv.reader(open(filename), dialect = "excel", delimiter = ";")
		self.filterObjectSize = 1#filterObjectSize
		self.timepoint = -1	 
		self.volumes = []
		self.cogs = []
		self.avgints = []
		self.avgintsstderr = []
		self.objects = []
		
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
		return (self.avgints, self.avgintsstderr)
		
	def read(self, statsTimepoint  = 0):
		"""
		Read the particles from the filename and create corresponding instances of Particle class
		"""
		
		ret = []
		skipNext = 0
		curr = []
		for line in self.rdr:
			if skipNext:
				skipNext = 0
				continue
			if len(line) == 1:
				timePoint = int(line[0].split(" ")[1])
				if curr:
					ret.append(curr)
				curr = []
				self.timepoint = timePoint
				skipNext = 1
				continue
			else:
				obj, sizemicro, size, cog, umcog, avgint, avgintstderr = line[0:7]
			try:
				size = int(size)
				sizemicro = float(sizemicro)
			except ValueError:
				continue
			obj = int(obj)
			cog = [float(coordinate) for coordinate in cog[1:-1].split(", ")]
			#cog = eval(cog)
			umcog = [float(coordinate) for coordinate in umcog[1:-1].split(", ")]
			avgint = float(avgint)
			avgintstderr = float(avgintstderr)
			if size >= self.filterObjectSize and obj != 0: 
				particle = Particle.Particle(umcog, cog, self.timepoint, size, avgint, obj)
				curr.append(particle)
			if self.timepoint == statsTimepoint:
				self.objects.append(obj)
				self.cogs.append((int(cog[0]), int(cog[1]), int(cog[2])))
				self.volumes.append((size, sizemicro))
				self.avgints.append(avgint)
				self.avgintsstderr.append(avgintstderr)
		if curr:
			ret.append(curr)
		return ret
		
		
class ParticleWriter:
	"""
	A class for writing particles
	"""
	def __init__(self):
		pass
		
	def writeTracks(self, filename, tracks, minimumTrackLength = 3, timeStamps = []):
		"""
		Write the particles
		"""
		fileToOpen = codecs.open(filename, "wb", "latin1")
			
		writer = csv.writer(fileToOpen, dialect = "excel", delimiter = ";")
		writer.writerow(["Track #", "Object #", "Timepoint", "X", "Y", "Z"])
		try:
			voxelSize = tracks[0][0].voxelSize
		except:
			voxelSize = [1.0,1.0,1.0]
		
		for i, track in enumerate(tracks):
			trackLength = 0
			for particle in track:
				if particle.intval:
					trackLength += 1
			if trackLength < minimumTrackLength:
				continue
			
			for particle in track:
				particleXPos, particleYPos, particleZPos = particle.posInPixels
				voxelSizeX, voxelSizeY, voxelSizeZ = particle.voxelSize
				writer.writerow([str(i), str(particle.intval), str(particle.timePoint), \
				str(particleXPos), str(particleYPos), str(particleZPos)])

		fileToOpen.close()

		try:
			parser = scripting.MyConfigParser()
			if not parser.has_section("TimeStamps"):
				parser.add_section("TimeStamps")
				parser.set("TimeStamps", "TimeStamps", "%s"%timeStamps)
			if not parser.has_section("VoxelSize"):
				parser.add_section("VoxelSize")
				parser.set("VoxelSize", "VoxelSize", "%s"%voxelSize)
		except:
			return

		ext = filename.split(".")[-1]
		pat = re.compile('.%s'%ext)
		filename = pat.sub('.ini', filename)
		try:
			fp = open(filename, "w")
			parser.write(fp)
			fp.close()
		except IOError, ex:
			Logging.error("Failed to write settings", "ParticleWriter failed to open .ini file %s for writing tracking settings (%s)"%(filename,ex))
		
