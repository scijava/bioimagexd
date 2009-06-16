# -*- coding: iso-8859-1 -*-

"""
 Unit: bahama
 Project: BioImageXD
 Created: 13.02.2006, KP
 Description:

 BAHAMA - BioimAgexd Highly Advanced Memory Architecture
  
 Copyright (C) 2006  BioImageXD Project
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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import scripting
import Configuration
import Logging
import vtk
import vtkbxd

currentPipeline = []
memLimit = None
numberOfDivisions = None
alwaysSplit = 0
noLimits = 0
conf = None
targetSize = None
executing = 0

def set_target_size(xDimension, yDimension, zDimension = 0):
	"""
	Resizes the target sample
	"""
	assert xDimension > 0 and yDimension > 0 and zDimension > 0,"Target dimensions need to be > 0"
	
	global targetSize, conf
	dataUnit = scripting.visualizer.getDataUnit()
	if zDimension == 0:
		zDimension = dataUnit.getDimensions()[2]
	targetSize = xDimension, yDimension, zDimension
	if not conf:
		conf = Configuration.getConfiguration()
		
	if dataUnit.isProcessed():
		sources = dataUnit.getSourceDataUnits()
	else:
		sources = [dataUnit]
	for dataUnit in sources:
		dataUnit.dataSource.setResampleDimensions((xDimension, yDimension, zDimension))

def optimize(image = None, vtkFilter = None, updateExtent = None, releaseData = 0):
	"""
	Execute a pipeline and optimize it
	"""
	if image:
		filterInUse = image.GetProducerPort().GetProducer()
	else:
		filterInUse = vtkFilter
	
	#val, numFilters = optimizePipeline(filterInUse, releaseData = releaseData)

	if updateExtent and not scripting.wantWholeDataset:
		Logging.info("Using update extent %s"%str(updateExtent),kw="pipeline")
		filterInUse.GetOutput().SetUpdateExtent(updateExtent)
	
	img = execute_limited(filterInUse, updateExtent = updateExtent)
	#if numFilters != 0:
	#	img = execute_limited(val, updateExtent = updateExtent) 
	#else:
	#	img = val.GetOutput()

	return img
	
def execute_limited(pipeline, updateExtent = None):
	"""
	
	"""
	global memLimit, noLimits, alwaysSplit
	global numberOfDivisions
	global executing
	#retval = pipeline.GetOutput()
	#if updateExtent and not scripting.wantWholeDataset:
	#	retval.SetUpdateExtent(updateExtent)
	#pipeline.Update()
	#return pipeline.GetOutput()

	if not memLimit:
		get_memory_limit()
	if noLimits or (not memLimit and not alwaysSplit):
		streamer = vtk.vtkImageDataStreamer()
		streamer.SetNumberOfStreamDivisions(1)

	if alwaysSplit:
		Logging.info("Using vtkImageDataStreamer with %d divisions"%numberOfDivisions, kw = "pipeline")
		streamer = vtk.vtkImageDataStreamer()
		streamer.SetNumberOfStreamDivisions(numberOfDivisions)
	elif (memLimit and not noLimits):
		Logging.info("Using vtkMemoryLimitImageDataStreamer with with limit=%dMB"%memLimit, kw = "pipeline")
		streamer = vtk.vtkMemoryLimitImageDataStreamer()
		streamer.SetMemoryLimit(1024*memLimit)

	streamer.GetExtentTranslator().SetSplitModeToZSlab()		
	
	executing = 1
	streamer.SetInputConnection(pipeline.GetOutputPort())
	retval = streamer.GetOutput()
	
	if updateExtent and not scripting.wantWholeDataset:
		Logging.info("Setting update extent to ", updateExtent, kw = "pipeline")
		retval.SetUpdateExtent(updateExtent)
	
	print "Update extent now=",retval.GetUpdateExtent()
	streamer.Update()
	print "Done"
	executing = 0
	return retval

def get_memory_limit():
	"""
	Get memory limits from configuration
	"""
	global conf, memLimit, alwaysSplit, numberOfDivisions, noLimits
	if memLimit:
		return memLimit
	if not conf:
		conf = Configuration.getConfiguration()
	memLimit = conf.getConfigItem("LimitTo", "Performance")
	alwaysSplit = conf.getConfigItem("AlwaysSplit", "Performance")
	if alwaysSplit != None:
		alwaysSplit = eval(alwaysSplit)
	noLimits = conf.getConfigItem("NoLimits", "Performance")
	if noLimits != None:
		noLimits = eval(noLimits)		   
	numberOfDivisions = conf.getConfigItem("NumberOfDivisions", "Performance")
		
	if numberOfDivisions:
		numberOfDivisions = eval(numberOfDivisions)
	if memLimit:
		memLimit = eval(memLimit)
	return memLimit



def optimizePipeline(ifilter, numberNotUsed = 0, releaseData = 0):
	"""
	Optimize the pipeline
	"""
	stack = []
	
	filterStack = []
	if isinstance(ifilter, vtkbxd.vtkImageSimpleMIP):
		isMip = 1
	cfilter = ifilter
	while 1:
		hasParents = 0
		for i in range(0, cfilter.GetNumberOfInputPorts()):
			for j in range(0, cfilter.GetNumberOfInputConnections(i)):
				inp = cfilter.GetInputConnection(i, j).GetProducer()
				if inp:
					stack.insert(0, inp)
					filterStack.append(inp)
					hasParents = 1
		try:
			cfilter = filterStack.pop()
		except:
			break
		if hasParents and releaseData:
			cfilter.GetOutput().ReleaseDataFlagOn() 

	nfilters = len(stack)

	return ifilter, nfilters
