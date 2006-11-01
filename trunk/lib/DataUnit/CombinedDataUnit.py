# -*- coding: iso-8859-1 -*-
"""
 Unit: CombinedDataUnit
 Project: BioImageXD
 Created: 03.11.2004, JM
 Description: Classes for managing combined 4D data.
                            
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
 Foundatiocan, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""

__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.74 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import DataUnit
from DataUnitSetting import *
import DataSource
import vtk
import Logging
import messenger
import scripting as bxd

class CombinedDataUnit(DataUnit.DataUnit):
    """
    Created: 03.11.2004, JM
    Description: Base class for combined 4d data.
    """

    def __init__(self, name=""):
        """
        Created: 03.11.2004, JM
        Description: Constructor
        """
        DataUnit.DataUnit.__init__(self, name)
        self.sourceunits=[]
        self.doOrig=0
        self.merging = 0
        settingclass=self.getSettingsClass()
        Logging.info("Settings class =",settingclass,kw="dataunit")
        self.settings = settingclass()
        self.byName={}
        self.module = None
        self.outputChls={}
        self.cacheKey = None
        
    def setCacheKey(self,key):
        """
        Created: 23.10.2006, KP
        Description: Set the key under which this dataunit is stored in the cache
        """
        self.cacheKey = key
        
    def getCacheKey(self):
        """
        Created: 23.10.2006, KP
        Description: Get the key under which this dataunit is stored in the cache
        """
        return self.cacheKey
        
    def isProcessed(self):
        """
        Created: 31.05.2005, KP
        Description: A method for querying whether this dataset is a processed one
        """    
        return 1
        
    def setOutputChannel(self,ch,flag):
        """
        Created: 22.07.2005, KP
        Description: Mark a channel as being part of the output
        """
        self.outputChls[ch]=flag
        #Logging.info("output channels now=",self.outputChls,kw="dataunit")
        
    def getOutputChannel(self, ch):
        """
        Created: 23.10.2006, KP
        Description: Return the status of the given output channel
        """
        print "getting",ch,"from",self.outputChls
        return self.outputChls.get(ch,1)
    def getDimensions(self): 
        if self.sourceunits:
            return self.sourceunits[0].getDimensions()
    def getSpacing(self): 
        if self.sourceunits:
            return self.sourceunits[0].getSpacing()
    def getVoxelSize(self): 
        if self.sourceunits:
            return self.sourceunits[0].getVoxelSize()
    def getBitDepth(self): 
        if self.sourceunits:
            return self.sourceunits[0].getBitDepth()


    
    def setModule(self,module):
        """
        Created: 27.03.2005, KP
        Description: Sets the module that does the calculations for
                     this dataunit
        """
        self.module = module

    def getSettings(self):
        """
        Created: 27.03.2005, KP
        Description: Returns the settings object of this dataunit
        """
        return self.settings

    def setSettings(self,settings):
        """
        Created: 27.03.2005, KP
        Description: Sets the settings object of this dataunit
        """
        self.settings = settings
        self.settings.initialize(self,len(self.sourceunits),self.length)
        

    def getSourceUnit(self,name):
        """
        Created: 28.03.2005, KP
        Description: Returns a source unit of given name
        """
        return self.sourceunits[self.byName[name]]

        
    def setDataSource(self, dataSource):
        """
        Created: 17.11.2004, JM
        Description: Sets a DataSource for this CombinedDataUnit
        Parameters: dataSource  A DataSource to manage actual
                                image data located on disk
        """
        # A validity check for dataSource
        if not isinstance(dataSource, DataSource.VtiDataSource):
            raise "A CombinedDataUnit can only be loaded from a VtiDataSource"
        # Call to base class, to run common setDataSource
        DataUnit.DataUnit.setDataSource(self,dataSource)
        
    def getDimensions(self):
        """
        Created: 10.11.2004, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        return self.sourceunits[0].getDimensions()
        
    def getDataUnitCount(self):
        """
        Created: 03.11.2004, JM
        Description: Returns the count of DataUnits
        """
        return len(self.sourceunits)

    def getSourceDataUnits(self):
        """
        Created: 03.11.2004, KP
        Description: Returns a list of references to the contained DataUnits
        """
        return self.sourceunits

    def doProcessing(self,duFile,**kws):
        """
        Created: 08.11.2004, JM
        Description: Executes the module's operation using the current settings
        Parameters:
                duFile      The name of the created .DU file
        Keywords:
                settings_only   If this parameter is set, then only the 
                                settings will be written out and not the VTI 
                                files.
                timepoints      The timepoints that should be processed
        """
        callback=None
        
        settings_only = kws.get("settings_only",0)
        callback = kws.get("callback",None)
        timepoints=kws.get("timepoints",range(self.getLength()))
        # We create the vtidatasource with the name of the dataunit file
        # so it knows where to store the vtkImageData objects
        self.dataWriter=DataSource.BXDDataWriter(duFile)

        imageList=[]
        self.n=1
        self.guicallback=callback
        self.module.setControlDataUnit(self)
        if not settings_only:
            for timePoint in timepoints:
                # First we reset the module, so that we can start the operation
                # from clean slate
                bxd.processingTimepoint = timePoint
                self.module.reset()
                # We get the processed timepoint from each of the source data 
                # units
                #self.module.setSettings(self.settings)
                self.module.setTimepoint(timePoint)
                
                for dataunit in self.sourceunits:
                    image=dataunit.getTimePoint(timePoint)
                
                    self.module.addInput(dataunit,image)
                # Get the vtkImageData containing the results of the operation 
                # for this time point
                imageData=self.module.doOperation()
                self.settings.set("Dimensions",str(imageData.GetDimensions()))
                messenger.send(None,"update_processing_progress",timePoint,self.n,len(timepoints))
                self.n+=1
                # Write the image data to disk
                if not settings_only:
                    self.dataWriter.addImageData(imageData)
                    self.dataWriter.sync()
        bxd.processingTimepoint = -1
        if settings_only:
            self.settings.set("SettingsOnly","True")
        self.createDataUnitFile(self.dataWriter)

    def createDataUnitFile(self,writer):
        """
        Created: 1.12.2004, KP, JM
        Description: Writes a du file to disk
        """
        parser=writer.getParser()
        
        # Write out the names of the datasets used for this operation
        for i in range(0,self.getDataUnitCount()):
            key="Source"
            # Use the string representation of the dataunit to get the type 
            # and path of the dataunit
            value=str(self.sourceunits[i])
            self.settings.setCounted(key,i,value)
        
        self.settings.writeTo(parser)
        writer.write()

    def addSourceDataUnit(self, dataUnit,no_init=0):
        """
        Created: 03.11.2004, JM
        Description: Adds 4D data to the unit together with channel-specific
        settings.
        Parameters: dataUnit    The SourceDataUnit to be added
        """
        # If one or more SourceDataUnits have already been added, check that the
        # new SourceDataUnit has the same length as the previously added one(s):
        
        if (self.length != 0) and (self.length != dataUnit.length):
            # XXX: Raise
            print "Given dataunit had wrong length (%d != %d)"%\
            (self.length,dataUnit.length)

        # The DataUnit to be added must have a different name than the
        # previously added, or the dictionary won't work:
        name = dataUnit.getName()
        if name in self.byName:
            raise Logging.GUIError("Datasets have the same name","Cannot load two datasets with the name %s"%name)
        
        count = len(self.sourceunits)
        #count+=1
        self.byName[name]=count
        self.sourceunits.append(dataUnit)

        # Create a settings object of correct type for dataunit
        # using the count as the index
        setting=self.getSettingsClass()(count)
        dataUnit.setSettings(setting)
        # Fetch correct settings for the dataunit from the datasource
        dataUnit.updateSettings()
        # If we just added the first SourceDataUnit, this sets the correct length
        # for the entire CombinedDataUnit. If not, it doesn't change anything.
        self.length = dataUnit.length
        if not no_init:
            for unit in self.sourceunits:
                unit.getSettings().initialize(unit,count+1,unit.getLength())        
            self.settings.initialize(self,count,self.sourceunits[0].getLength())
        
    def switchSourceDataUnits(self,units):
        """
        Created: 11.08.2005, KP
        Description: Switch the source data units used
        """
        if len(units)!=len(self.sourceunits):
            raise Logging.GUIError("Wrong number of dataunits","Cannot switch the processed datasets: you've selected a wrong number of source dataunits.")
        #oldsources=self.sourceunits
        self.sourceunits=[]
        self.byName={}
        for i,unit in enumerate(units):
            #oldunit=oldsources[i]
            self.addSourceDataUnit(unit,no_init=1)
            #unit.getSettings().copySettings(oldunit.getSettings())
            #self.sourceunits.append(unit)
        for i in self.sourceunits:
            i.getSettings().set("ColorTransferFunction",i.getColorTransferFunction())

    def getColorTransferFunction(self):
        return self.sourceunits[0].getColorTransferFunction()

    def doPreview(self, depth,renew,timePoint=0):
        """
        Created: 08.11.2004, JM
        Description: Makes a two-dimensional preview using the class-specific combination function
        Parameters: depth       The preview depth
                    renew       Flag indicating, whether the preview should be 
                                regenerated or if a stored image can be reused
                    timePoint   The timepoint from which to generate the preview
                                Defaults to 0
        """
        
        preview=None
        # If the given timepoint > number of timepoints,
        # it is scaled to be in the range 0-getDataUnitCount()-1
        # with the modulo operator
        timePoint=timePoint%self.getLength()
        
        # If the previously requested preview was a "show original" preview
        # then we can just restore the preview before that without any
        # processing
        showOrig=self.settings.get("ShowOriginal")
        if not showOrig and self.doOrig:
            self.doOrig=0
            Logging.info("Returning saved preview",kw="dataunit")
            return self.origPreview
            
        # If the requested output channels have been specified,
        # then we map those through their corresponding ctf's
        # to be merged to the output
        n=len(self.sourceunits)
        merged=[]
        if self.outputChls:
            merged=[]
            
            for i,unit in enumerate(self.sourceunits):
                if i in self.outputChls and self.outputChls[i]:
                    data=unit.getTimePoint(timePoint)
                    merged.append((data,unit.getColorTransferFunction()))
                    
            if n not in self.outputChls:
                self.outputChls[n]=0
        # If either no output channels have been specified (in which case
        # we return just the normal preview) or the combined result
        # (n = last chl+1) has  been requested
        #print "outputChls=",self.outputChls,"renew=",renew,"n=",n
        if self.merging or not self.outputChls or (n in self.outputChls and self.outputChls[n]):
            #Logging.info("outputChls=",self.outputChls,"n=",n)
            
            # If the renew flag is true, we need to regenerate the preview
            if renew:                
                # We then tell the module to reset itself and
                # initialize it again
                self.module.reset()
                # Go through all the source datasets for the module
                self.module.setSettings(self.settings)
                self.module.setTimepoint(timePoint)
                for dataunit in self.sourceunits:
                    Logging.info("Adding source image data",kw="dataunit")
                    image=dataunit.getTimePoint(timePoint)
                    self.module.addInput(dataunit,image)

            preview=self.module.getPreview(depth)
            # If no output channels were requested, then just return the
            # preview
            
#            if not self.outputChls:
#                print "Returning preview",preview.GetDimensions()
#                return preview
        if not self.merging and self.outputChls:
            if preview:
                merged.append((preview,self.getColorTransferFunction()))
            
            if len(merged)>1:
                #print "Merging..."
                #createalpha=vtk.vtkImageAlphaFilter()
                #createalpha.GetOutput().ReleaseDataFlagOn()                
                #createalpha.MaximumModeOn()
                merge=vtk.vtkImageColorMerge()
                
                for data,ctf in merged:                    
                    merge.AddInput(data)
                    merge.AddLookupTable(ctf)
                    #createalpha.AddInput(data)
                #print "Update..."
                merge.Update()
                preview=merge.GetOutput()
            elif len(merged)==1:
                print merged
                data,ctf = merged[0]
                maptocolor = vtk.vtkImageMapToColors()
                maptocolor.SetInput(data)
                maptocolor.SetLookupTable(ctf)
                maptocolor.Update()
                preview=maptocolor.GetOutput()
        
        if not showOrig and not self.doOrig:
            self.origPreview=preview
        elif showOrig:
            self.doOrig=1            
        return preview
            

    def getBitDepth(self):
        """
        Created: 30.05.2005, KP
        Description: Return the bit depth of the combined dataunit
        """
        return 8

        
    def getSettingsClass(self):
        """
        Created: 02.04.2005, KP
        Description: Return the class that represents settings for this dataunit
        """
        raise "Using bare DataUnitSettings"
 
