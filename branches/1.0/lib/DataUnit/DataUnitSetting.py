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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import vtk
import ImageOperations
import pickle
import Logging
import zlib
import Modules
import ConfigParser

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
        self.modules=Modules.DynamicLoader.getTaskModules()
        self.dataunit = None
        self.channels = 0
        self.timepoints = 0
        if kws.has_key("type"):
            self.setType(kws["type"])
        self.n=n
        self.serialized={}
        self.register("SettingsOnly",serialize=1)
        self.registerPrivate("ColorTransferFunction",serialize=1)
        self.register("PreviewedDataset")
        self.set("PreviewedDataset",-1)
        self.register("Annotations",serialize=1)
#        self.register("SourceCount")
        self.registerCounted("Source")
        self.register("VoxelSize")
        self.register("Spacing")
        #self.register("Origin")
        self.register("Dimensions")
        self.register("ShowOriginal",serialize=1)
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
            settingsclass=self.modules[type][2].getSettingsClass()
            Logging.info("Settings class=",settingsclass,kw="processing")
            #obj=eval(type)(self.n)
            obj=settingsclass(self.n)
            obj.setType(type)
            return obj.readFrom(parser)
        
        for key in self.registered.keys():
            ser=self.serialized[key]
            if ser:
                Logging.info("is %s serialized: %s"%(key,ser),kw="dataunit")
            if key in self.counted:
                try:
                    n=parser.get("Count",key)
                except:
                    Logging.info("Got no key count for %s"%key,kw="dataunit")
                    continue
                n=int(n)
                Logging.info("Got %d keys for %s"%(n,key),kw="dataunit")
                
                for i in range(n):
                    ckey="%s[%d]"%(key,i)
                    #try:
                    try:
                        value=parser.get(key,ckey)
                        if ser:
                            value=self.deserialize(key,value)
                            #Logging.info("Deserialized ",key,"=",value,kw="dataunit")
                        self.setCounted(key,i,value)
                        self.counted[key]=i
                    except ConfigParser.NoSectionError:
                        Logging.info("Got no keys for section %s"%key,kw="dataunit")
            else:
                #value=parser.get("ColorTransferFunction","ColorTransferFunction")
                try:
                    value=parser.get(key,key)
                    
                    if ser:
                        #Logging.info("Trying to deserialize ",key,value,kw="dataunit")
                        value=self.deserialize(key,value)
                        #Logging.info("Deserialized ",key,"=",value,kw="dataunit")
                    self.set(key,value)
                except ConfigParser.NoSectionError:
                    Logging.info("Got no keys for section %s"%key,kw="dataunit")
        return self
                
    def writeKey(self,key,parser,n=-1):
        """
        Method: writeKey(key,parser)
        Created: 27.03.2005
        Description: Write a key and it's value to parser
        """    
        nkey="%s[%d]"%(key,n)
        if not (key in self.settings or nkey in self.settings) and not (key in self.private or nkey in self.private):
            Logging.info("neither ",key,"nor",nkey,"in ",self.settings.keys(),kw="dataunit")
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
                #print "Writing key %s with count %d"%(key,self.counted[key])
                for i in range(self.counted[key]+1):
                    self.writeKey(key,parser,i)
            else:
                #print "Writing key ",key
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
        Logging.info("Serializing name ",name,kw="dataunit")
        if "ColorTransferFunction" in name:
            s=ImageOperations.lutToString(value)
            s2=""
            for i in s:
                s2+=repr(i)
            return s2
        # Annotations is a list of classes that can easily be
        # pickled / unpickled
        if "Annotations" in name:
            Logging.info("Pickling %d annotations"%len(value),kw="dataunit")
            s=pickle.dumps(value,protocol=pickle.HIGHEST_PROTOCOL)
            s=zlib.compress(s)
            return s
            
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
        #print "deserialize",name
        if "ColorTransferFunction" in name:
            data=eval(value)            
            ctf=vtk.vtkColorTransferFunction()
            ImageOperations.loadLUTFromString(data,ctf)
            return ctf
        # Annotations is a list of classes that can easily be
        # pickled / unpickled
        if "Annotations" in name:
            Logging.info("deserializing Annotations",kw="dataunit")
            val=zlib.decompress(value)
            val=pickle.loads(val)
            Logging.info("unpickled %d annotations"%len(val),kw="dataunit")
            return val
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
        return "%s ( %s )"%(str(self.__class__),str(self.settings))

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