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

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD Project.
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import ImageOperations

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
        self.type=None
        if kws.has_key("type"):
            self.setType(kws["type"])
        self.n=n
        self.serialized={}
        self.register("SourceCount")
        self.registerCounted("Source")
        self.register("VoxelSize")
        self.register("Spacing")
        #self.register("Origin")
        self.register("Dimensions")
        self.register("Type")
        self.register("Name")
        
    def setType(self,type):
        """
        Method: setType(type)
        Created: 2.04.2005
        Description: Set the type of this dataunit
        """
        self.type=type
        self.set("Type",type)
        
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
            if key in self.counted:
                ser=self.serialized[key]
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
                try:
                    value=parser.get(key,key)
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
                for i in range(self.counted[key]):
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
            #print "Will not overwrite %s"%name
            return
        if self.n != -1 and name in self.counted:
            print "Setting counted %d,%s,%s"%(self.n,name,value)
            return self.setCounted(name,self.n,value,overwrite)
        if name not in self.registered:
            raise "No key %s registered"%name
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
            print "Will not overwrite %s"%keyval
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
        if name in self.settings:
            return self.settings[name]
        return None
    
    def getCounted(self,name,count):
        """
        Method: getCounted(name,count)
        Created: 26.03.2005
        Description: Return the value of a key
        """
        print "in self.settings: %s"%self.settings.has_key("%s[%d]"%(name,count))
        if self.n != -1:
            return self.get(name)
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
        
        self.register("ColocalizationColor")
        self.set("ColocalizationColor",(255,255,255))
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
        self.registerCounted("Color")       
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
        print "Initializing for %d channels"%channels
        for i in range(channels):
            self.setCounted("Color",i,(255,255,255),0)
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
        self.register("Color")        
        self.registerCounted("IntensityTransferFunctions",1)
        self.register("MedianFiltering")
        self.register("MedianNeighborhood")
        self.register("SolitaryFiltering")
        self.register("SolitaryHorizontalThreshold")
        self.register("SolitaryVerticalThreshold")
        self.register("SolitaryProcessingThreshold")
        self.register("InterpolationTimepoints")
        self.set("Type","SingleUnitProcessingSettings")
        self.set("Color",(123,123,123))
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
        print "Initializing to color",dataunit.getColor()
        self.set("Color",dataunit.getColor(),0)
        print "Initializing %d timepoints"%timepoints
        for i in range(timepoints):
            tf=vtk.vtkIntensityTransferFunction()
            self.setCounted("IntensityTransferFunctions",i,tf,0)
 
