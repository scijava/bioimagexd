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

import types
import Configuration
import vtk
currentPipeline = []
memLimit = None
numberOfDivisions=None
alwaysSplit=0
noLimits=0
conf= None

def optimize(image = None, vtkFilter = None, updateExtent = None, releaseData = 0):
    """
    Created: 11.11.2006, KP
    Description: Execute a pipeline and optimize it
    """
    if image:
        pp = image.GetProducerPort().GetProducer()
        #print "Producerport=",repr(pp)
    else:
        pp = vtkFilter
    #print "Optimizing..."
    val,numFilters = optimizePipeline(pp, releaseData = releaseData)
    
    if updateExtent:
        #print "Setting update extent to ",updateExtent
        val.GetOutput().SetUpdateExtent(updateExtent)
        pass
    #print "Executing limited..."
    if numFilters!=0:
        img=execute_limited(val, updateExtent = updateExtent) 
    else:
        img = val.GetOutput()
    
    #if updateExtent:
    #    #print "Setting update extent again"
    #    img.SetUpdateExtent(updateExtent)
    #print "returning ",repr(img)
    return img
    
def execute_limited(pipeline, updateExtent = None):
    global memLimit,noLimits
    global numberOfDivisions
    
    if not memLimit:
        get_memory_limit()
    if noLimits or  (not memLimit and not alwaysSplit):
        pipeline.Update()
        return pipeline.GetOutput()   
    
    if alwaysSplit:
        #print "Using vtkImageDataStreamer with ",numberOfDivisions,"divisions"
        
        streamer = vtk.vtkImageDataStreamer()
        streamer.SetNumberOfStreamDivisions(numberOfDivisions)
        streamer.GetExtentTranslator().SetSplitModeToZSlab()
    else:
        #print "Using vtkMemoryLimitImageDataStreamer with with limit=%dMB"%memLimit
        streamer = vtk.vtkMemoryLimitImageDataStreamer()
        streamer.SetMemoryLimit(1024*memLimit)
        
        
    streamer.SetInput(pipeline.GetOutput())
    retval = streamer.GetOutput()
    
    if updateExtent:
        retval.SetUpdateExtent(updateExtent)
    #print "Update extent=",retval.GetUpdateExtent()
    #print "Divisions=",streamer.GetNumberOfStreamDivisions()
    streamer.Update()
    return retval

#    print "Failed, will execute unstreamed"
#        pipeline.Update()
#        return pipeline.GetOutput()

def get_memory_limit():
    global conf,memLimit,alwaysSplit, numberOfDivisions,noLimits
    if memLimit:return memLimit
    if not conf:
        conf = Configuration.getConfiguration()
    memLimit = conf.getConfigItem("LimitTo","Performance")
    alwaysSplit = conf.getConfigItem("AlwaysSplit","Performance")
    if alwaysSplit!=None:
        alwaysSplit=eval(alwaysSplit)
    noLimits = conf.getConfigItem("NoLimits","Performance")
    if noLimits!=None:
        noLimits=eval(noLimits)        
    numberOfDivisions = conf.getConfigItem("NumberOfDivisions","Performance")
        
    if numberOfDivisions:
        numberOfDivisions = eval(numberOfDivisions)
    if memLimit:
        memLimit = eval(memLimit)
    return memLimit


def optimizeMipMerge(cfilter):
    """
    Created: 10.11.2006, KP
    Description: Optimize the order of mip and merge
    """    
    filterStack=[]
    mergeSources=[]
    merge=None
    print "OPtimizing merge from ",repr(cfilter)
    while 1:
        if isinstance(cfilter,vtk.vtkImageColorMerge):
            merge = cfilter
            print "Found merge",repr(merge)
            for i in range(0,cfilter.GetNumberOfInputPorts()):
                for j in range(0,cfilter.GetNumberOfInputConnections(i)):            
                    inp=cfilter.GetInputConnection(i,j).GetProducer()
                    if inp:
                        mergeSources.append(inp)
        for i in range(0,cfilter.GetNumberOfInputPorts()):
            for j in range(0,cfilter.GetNumberOfInputConnections(i)):
                inp=cfilter.GetInputConnection(i,j).GetProducer()                
                if inp:                
                    filterStack.append(inp)
        try:
            cfilter = filterStack.pop()            
        except:
            break    
    
        
    merge.RemoveAllInputs()            
    for i in mergeSources:
        mip = vtk.vtkImageSimpleMIP()
        mip.SetInput(i.GetOutput())        
        merge.AddInput(mip.GetOutput())
    return merge

def optimizePipeline(ifilter,n=0, releaseData = 0):
    """
    Created: 10.11.2006, KP
    Description: Optimize the pipeline
    """
    #return ifilter
    stack=[]
    #return ifilter
    
    filterStack = []
    if isinstance(ifilter,vtk.vtkImageSimpleMIP):
        isMip = 1
    cfilter = ifilter
    while 1:
        hasParents=0
        for i in range(0,cfilter.GetNumberOfInputPorts()):
            for j in range(0,cfilter.GetNumberOfInputConnections(i)):
                inp=cfilter.GetInputConnection(i,j).GetProducer()
                if inp:
                    stack.insert(0,inp)
                    filterStack.append(inp)
                    hasParents =1
        try:
            cfilter = filterStack.pop()            
        except:
            break
        if hasParents and releaseData:
            print repr(cfilter),"will release data"
            cfilter.GetOutput().ReleaseDataFlagOn() 

    #print "Stack=",stack
    nfilters=len(stack)
    #for i in stack:
    #    if isinstance(i,vtk.vtkImageColorMerge):
    #        return optimizeMipMerge(ifilter),nfilters
        
                
    return ifilter,nfilters
                

