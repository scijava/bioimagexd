# -*- coding: iso-8859-1 -*-

"""
 Unit: DataUnitSetting
 Project: BioImageXD
 Created: 26.03.2005, KP
 Description:

 This is a class that holds all settings of a dataunit. A dataunit's 
 setting object is the only thing differentiating it from another
 dataunit.
 
 This code was re-written for clarity. The code produced by the
 Selli-project was used as a starting point for producing this code.
 http://sovellusprojektit.it.jyu.fi/selli/
 
 Modified: 26.03.2005 - Started complete re-write.

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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import ImageOperations
import pickle

class DataUnitSettings:
    """
    Class: DataUnitSetting
    Created: 26.03.2005, KP
    Description: This is a class that holds all settings of a dataunit
    """    
    # Global settings, shared by all instances
    # The different source units differentiate by having a number
    # and using the counted keys
    settings={}
    
    def __init__(self,n=-1,**kws):
        """
        Method: __init__
        Created: 26.03.2005
        Description: Constructor
        Parameters:
            n   Number of the dataset this is associated to
                Reflects in that set() and get() of counted variables
                will set only the nth variable
        """
        self.counted={}
        self.registered={}
        self.private={}
        self.isPrivate={}
        self.type=None
        self.dataunit = None
        self.channels = 0
        self.timepoints = 0
        if kws.has_key("type"):
            self.setType(kws["type"])
        self.n=n
        self.serialized={}
        self.registerPrivate("ColorTransferFunction",1)        
        self.register("PreviewedDataset")
        self.set("PreviewedDataset",-1)
        self.register("SourceCount")
        self.registerCounted("Source")
        self.register("VoxelSize")
        self.register("Spacing")
        #self.register("Origin")
        self.register("Dimensions")
        self.register("Type")
        self.register("Name")
        self.register("BitDepth")
        
        
    def asType(self,newtype):
        """
        Method: asType(type)
        Created: 3.04.2005
        Description: Return this setting as given type
        """
        newclass=eval(newtype)

        settings=newclass(self.n)
        settings.initialize(self.dataunit,self.channels,self.timepoints)
        return settings
        
    def setType(self,newtype):
        """
        Method: setType(type)
        Created: 2.04.2005
        Description: Set the type of this dataunit
        """
        self.type=newtype
        self.set("Type",newtype)
        
    def getType(self):
        """
        Method: getType()
        Created: 2.04.2005
        Description: Set the type of this dataunit
        """
        return self.type
        
        
        
    def register(self,name,serialize=0):
        """
        Method: register
        Created: 26.03.2005
        Description: Register a name as valid key. 
        Parameters:
            serialize   The value will be written out/read through
                        the serialize/deserialize methods
        """    
        
        self.registered[name]=1
        self.serialized[name]=serialize
        self.isPrivate[name]=0

    def registerPrivate(self,name,serialize=0):
        """
        Method: register
        Created: 26.03.2005
        Description: Register a name as valid key. 
        Parameters:
            serialize   The value will be written out/read through
                        the serialize/deserialize methods
        """    
        self.registered[name]=1
        self.isPrivate[name]=1
        self.serialized[name]=serialize
        
    def registerCounted(self,name,serialize=0):
        """
        Method: registerCounted(name)
        Created: 26.03.2005
        Description: Register a name as valid key that is counted
        Parameters:
            serialize   The value will be written out/read through
                        the serialize/deserialize methods
        """    
        self.registered[name]=1
        self.counted[name]=1
        self.serialized[name]=serialize
        self.isPrivate[name]=0
    
        
    def readFrom(self,parser):
        """
        Method: readFrom(parser)
        Created: 26.03.2005
        Description: Attempt to read all registered keys from a parser
        """    
        if not self.get("Type"):
            type=parser.get("Type","Type")
            obj=eval(type)(self.n)
            obj.setType(type)
            return obj.readFrom(parser)
        
        for key in self.registered.keys():
            ser=self.serialized[key]
            if ser:print "is %s serialized: %s"%(key,ser)
            if key in self.counted:
                try:
                    n=parser.get("Count",key)
                except:
                    print "Got no count for %s"%key
                    continue
                n=int(n)
                print "Got %d keys for %s"%(n,key)
                
                for i in range(n):
                    ckey="%s[%d]"%(key,i)
                    try:
                        value=parser.get(key,ckey)
                        if ser:
                            value=self.deserialize(okey,value)
                        self.set(ckey,value)
                        self.counted[key]=i
                    except:
                        pass
            else:
                #value=parser.get("ColorTransferFunction","ColorTransferFunction")
                try:
                    #print "Trying to read %s"%key
                    #print "has section:%s"%parser.has_section(key)
                    value=parser.get(key,key)
                    #print "Got ",value
                    
                    if ser:
                        value=self.deserialize(key,value)
                    self.set(key,value)
                except:
                    pass
        return self
                
    def writeKey(self,key,parser,n=-1):
        """
        Method: writeKey(key,parser)
        Created: 27.03.2005
        Description: Write a key and it's value to parser
        """    
        nkey="%s[%d]"%(key,n)
        if not (key in self.settings or nkey in self.settings):
            return
        okey=key
        if n!=-1:
            key=nkey
        if self.isPrivate[okey]:
            value=self.private[okey]
        else:
            value=self.settings[key]
        if self.serialized[okey]:
            value=self.serialize(okey,value)
        if not parser.has_section(okey):
            parser.add_section(okey)
        parser.set(okey,key,value)
        
                
    def writeTo(self,parser):
        """
        Method: writeTo(parser)
        Created: 26.03.2005
        Description: Attempt to write all keys to a parser
        """    
        keys=[]
        if not parser.has_section("Settings"):
            parser.add_section("Settings")
        for key in self.registered.keys():
            if key in self.counted:
                print "Writing key %s with count %d"%(key,self.counted[key])
                for i in range(self.counted[key]+1):
                    self.writeKey(key,parser,i)
            else:
                self.writeKey(key,parser)                
               
        if len(self.counted.keys()):
            if not parser.has_section("Count"):
                parser.add_section("Count")
        for key in self.counted.keys():
            value=self.counted[key]
            parser.set("Count",key,value)
            
    def set(self,name,value,overwrite=1):
        """
        Method: set(name,value)
        Created: 26.03.2005
        Description: Sets the value of a key
        """
        if not overwrite and self.settings.has_key(name):
            print "Will not overwrite %s"%name
            return
        if self.n != -1 and name in self.counted:
            #print "Setting counted %d,%s,%s"%(self.n,name,value)
            return self.setCounted(name,self.n,value,overwrite)
        if name not in self.registered:
            raise "No key %s registered"%name
        if self.isPrivate[name]:
#            print "Setting private %s"%name
            self.private[name]=value
        else:
            self.settings[name]=value
        
    def setCounted(self,name,count,value,overwrite=1):
        """
        Method: setCounted(name,count,value)
        Created: 26.03.2005
        Description: If there are more than one setting associated,
                     for example, with different channels, then this
                     can be used to set the value of that variable
                     properly.
        """
        if not name in self.registered:
            raise "No key %s registered"%name
        keyval="%s[%d]"%(name,count)
        if not overwrite and (keyval in self.settings):
            #print "Will not overwrite %s"%keyval
            return
        self.settings[keyval]=value
        if self.counted[name]<count:
            self.counted[name]=count
        
    def get(self,name):
        """
        Method: get(name)
        Created: 26.03.2005
        Description: Return the value of a key
        """
        if self.n != -1 and name in self.counted:
            name="%s[%d]"%(name,self.n)
        if name in self.private:
            return self.private[name]
        if name in self.settings:
            return self.settings[name]
        return None
    
    def getCounted(self,name,count):
        """
        Method: getCounted(name,count)
        Created: 26.03.2005
        Description: Return the value of a key
        """
        #print "in self.settings: %s"%self.settings.has_key("%s[%d]"%(name,count))
        #if self.n != -1:
        #    return self.get(name)
        key="%s[%d]"%(name,count)
        return self.get(key)
        
        
    def serialize(self,name,value):
        """
        Method: serialize(name,value)
        Created: 27.03.2005
        Description: Returns the value of a given key in a format
                     that can be written to disk.
        """
        print "serializing name=",name
        if "ColorTransferFunction" in name:
            s=ImageOperations.lutToString(value)
            s2=""
            for i in s:
                s2+=repr(i)
            return s2

        if name not in ["IntensityTransferFunction","IntensityTransferFunctions","AlphaTransferFunction"]:
            return str(value)
            
            
            
        val=ImageOperations.getAsParameterList(value)
        return str(val)
        
    def deserialize(self,name,value):
        """
        Method: deserialize(name,value)
        Created: 27.03.2005
        Description: Returns the value of a given key
        """
        #print "deserialize(%s,...)"%name    
        if "ColorTransferFunction" in name:
            data=eval(value)   
            
            ctf=vtk.vtkColorTransferFunction()
            ImageOperations.loadLUTFromString(data,ctf)
            return ctf
        if name not in ["IntensityTransferFunction","IntensityTransferFunctions","AlphaTransferFunction"]:
            return eval(value)
        tf=vtk.vtkIntensityTransferFunction()
        lst=eval(value)
        ImageOperations.setFromParameterList(tf,lst)
        return tf
        
    def __str__(self):
        """
        Method: __str__
        Created: 30.03.2005
        Description: Returns the string representation of this class
        """
        return "DataUnitSettings( %s )"%str(self.settings)

    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 03.04.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        self.channels = channels
        self.timepoints = timepoints
        self.dataunit = dataunit
    
        
class ColocalizationSettings(DataUnitSettings):
    """
    Class: ColocalizationSettings
    Created: 26.03.2005, KP
    Description: Registers keys related to colocalization in a dataunitsetting
    """
    def __init__(self,n=-1):
        """
        Method: __init__
        Created: 26.03.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
        self.registerCounted("Color")       
        
        self.set("Type","ColocalizationSettings")
        self.registerCounted("ColocalizationLowerThreshold")
        self.registerCounted("ColocalizationUpperThreshold")

        self.register("PearsonsCorrelation")
        self.register("OverlapCoefficient")
        self.register("OverlapCoefficientK1")
        self.register("OverlapCoefficientK2")
        self.register("ColocalizationCoefficientM1")
        self.register("ColocalizationCoefficientM2")
        
        self.set("PearsonsCorrelation",0)
        self.set("OverlapCoefficient",0)
        self.set("OverlapCoefficientK1",0)
        self.set("OverlapCoefficientK2",0)
        self.set("ColocalizationCoefficientM1",0)
        self.set("ColocalizationCoefficientM2",0)        
        
        self.register("ColocalizationColorTransferFunction",1)
        ctf = vtk.vtkColorTransferFunction()
        ctf.AddRGBPoint(0,0,0,0)
        ctf.AddRGBPoint(255, 1.0, 1.0, 1.0)
        self.set("ColocalizationColorTransferFunction",ctf)
        self.register("ColocalizationDepth")
        self.set("ColocalizationDepth",8)
        self.register("ColocalizationAmount")
        self.register("ColocalizationLeastVoxelsOverThreshold")

    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)
        print "Initializing colocaliztion for %d channels"%channels
        for i in range(channels):
            self.setCounted("ColocalizationLowerThreshold",i,128,0)
            self.setCounted("ColocalizationUpperThreshold",i,255,0)

        
class ColorMergingSettings(DataUnitSettings):
    """
    Class: ColorMergingSettings
    Created: 27.03.2005, KP
    Description: Stores color merging related settings
    """
    def __init__(self,n=-1):
        """
        Method: __init__
        Created: 27.03.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
        self.registerCounted("MergingColorTransferFunction",1)       
        self.set("Type","ColorMergingSettings") 
        self.registerCounted("IntensityTransferFunction",1)
        self.register("AlphaTransferFunction",1)
        self.register("AlphaMode")
        
        tf=vtk.vtkIntensityTransferFunction()
        self.set("AlphaTransferFunction",tf)
        self.set("AlphaMode",[0,0])

    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)
#        print "Initializing for %d channels"%channels
        for i in range(channels):
            #ctf = vtk.vtkColorTransferFunction()
            #ctf.AddRGBPoint(0,0,0,0)
            #ctf.AddRGBPoint(255, 1.0, 1.0, 1.0)
            #self.setCounted("MergingColorTransferFunction",i,ctf,0)
            tf=vtk.vtkIntensityTransferFunction()
            self.setCounted("IntensityTransferFunction",i,tf,0)
            
class SingleUnitProcessingSettings(DataUnitSettings):
    """
    Class: SingleUnitProcessingSettings
    Created: 27.03.2005, KP
    Description: Stores settings related to single unit processing
    """
    def __init__(self,n=-1):
        """
        Method: __init__
        Created: 27.03.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
#        self.register("ColorTransferFunction")        
        self.registerCounted("IntensityTransferFunctions",1)
        self.register("MedianFiltering")
        self.register("MedianNeighborhood")
        self.register("SolitaryFiltering")
        self.register("SolitaryHorizontalThreshold")
        self.register("SolitaryVerticalThreshold")
        self.register("SolitaryProcessingThreshold")
        self.register("InterpolationTimepoints")
        self.set("Type","SingleUnitProcessingSettings")
        #ctf = vtk.vtkColorTransferFunction()
        #ctf.AddRGBPoint(0,0,0,0)
        #ctf.AddRGBPoint(255, 0.7, 0.7, 0.7)
 
        #self.set("ColorTransferFunction",ctf,0)
        self.set("InterpolationTimepoints",[])
        self.set("MedianFiltering",0)
        self.set("MedianNeighborhood",[0,0,0])
        self.set("SolitaryFiltering",0)
        self.set("SolitaryHorizontalThreshold",0)
        self.set("SolitaryVerticalThreshold",0)
        self.set("SolitaryProcessingThreshold",0)

            
        
    def initialize(self,dataunit,channels, timepoints):
        """
        Method: initialize(dataunit,channels, timepoints)
        Created: 27.03.2005
        Description: Set initial values for settings based on 
                     number of channels and timepoints
        """
        DataUnitSettings.initialize(self,dataunit,channels,timepoints)
        ctf = self.get("ColorTransferFunction")
        if 0 and not ctf:
#            print "Initializing to color",dataunit.getColor()
            ctf = vtk.vtkColorTransferFunction()
            r,g,b=dataunit.getColor()
            r/=255.0
            g/=255.0
            b/=255.0
            r,g,b=int(r),int(g),int(b)
            ctf.AddRGBPoint(0,0,0,0)
            ctf.AddRGBPoint(255, r,g,b)
            self.set("ColorTransferFunction",ctf)
        
#        print "Initializing %d timepoints"%timepoints
        for i in range(timepoints):
            tf=vtk.vtkIntensityTransferFunction()
            self.setCounted("IntensityTransferFunctions",i,tf,0)
 
class ResliceSettings(DataUnitSettings):
    """
    Class: ResliceSettings
    Created: 04.04.2005, KP
    Description: Stores settings related to reslice
    """
    def __init__(self,n=-1):
        """
        Method: __init__
        Created: 04.04.2005, KP
        Description: Constructor
        """
        DataUnitSettings.__init__(self,n)
        self.register("ResliceXAngle")        
        self.register("ResliceYAngle")        
        self.register("ResliceZAngle") 
        self.set("ResliceXAngle",0.0)
        self.set("ResliceYAngle",0.0)
        self.set("ResliceZAngle",90.0)
        self.register("Color")   
        
