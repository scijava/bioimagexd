"""
 Unit: ParticleWriter
 Project: BioImageXD
 Description:

 A module containing class related to writing objects and tracks.
							
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
__version__ = "$Revision$"
__date__ = "$Date$"

import codecs
import csv
import re
import scripting
import Logging

class ParticleWriter:
	"""
	A class for writing particles
	"""
	def __init__(self):
		self.objects = {}
		
	def writeTracks(self, filename, tracks, minimumTrackLength = 3, timeStamps = []):
		"""
		Write the particles
		"""
		fileToOpen = codecs.open(filename, "wb", "latin1")
			
		writer = csv.writer(fileToOpen, dialect = "excel", delimiter = ";")
		writer.writerow(["Track #", "Object #", "Timepoint", "X", "Y", "Z"])

		try:
			voxelSize = list(tracks[0][0].voxelSize)
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

	def setObjectValue(self, name, value):
		"""
		Sets object values to be written
		"""
		self.objects[name] = value

	def writeObjects(self, filename, timepoint):
		"""
		Write analyzed objects
		"""
		f = codecs.open(filename, "ab", "latin1")
		Logging.info("Saving statistics to file %s"%filename, kw="processing")
		
		w = csv.writer(f, dialect = "excel", delimiter = ";")		
		w.writerow(["Timepoint %d" % timepoint])
		w.writerow(["Object #", "Volume (micrometers)", "Volume (voxels)", "Center of Mass X", \
					"Center of Mass Y", "Center of Mass Z", "Center of Mass X (micrometers)", \
					"Center of Mass Y (micrometers)", "Center of Mass Z (micrometers)",	"Avg. Intensity", "Avg. Intensity std. error",  "Avg. distance to objects", "Avg. distance to objects std. error", "Area (micrometers)"])
		
		for i, volume in enumerate(self.objects['volume']):
			volumeum = self.objects['volumeum'][i]
			cog = self.objects['centerofmass'][i]
			umcog = self.objects['umcenterofmass'][i]
			avgint = self.objects['avgint'][i]
			avgintstderr = self.objects['avgintstderr'][i]
			avgdist = self.objects['avgdist'][i]
			avgdiststderr = self.objects['avgdiststderr'][i]
			areaUm = self.objects['areaum'][i]
			w.writerow([str(i + 1), str(volumeum), str(volume), cog[0], cog[1], cog[2], umcog[0], umcog[1], umcog[2], str(avgint), str(avgintstderr), str(avgdist), str(avgdiststderr), str(areaUm)])
		
		f.close()
