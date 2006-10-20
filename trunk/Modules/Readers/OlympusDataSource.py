# -*- coding: iso-8859-1 -*-
"""
 Unit: OlympusDataSource
 Project: BioImageXD
 Created: 16.02.2006, KP
 Description: A datasource for reading Olympus OIF files

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
__version__ = "$Revision: 1.37 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import ConfigParser
import struct

import codecs

import math
    
from DataSource import *
import DataUnit
        
def getExtensions(): return ["oif"]
def getFileType(): return "Olympus Image Format datasets (*.oif)"        
def getClass(): return OlympusDataSource
    
class OlympusDataSource(DataSource):
    """
    Created: 12.04.2005, KP
    Description: Olympus OIF files datasource
    """
    def __init__(self,filename="",channel=-1,basename="", lutname="",name="",dims=(0,0,0),t=0,voxelsize=(1,1,1),reverse=0, emission = 0, excitation = 0):
        """
        Created: 12.04.2005, KP
        Description: Constructor
        """    
        DataSource.__init__(self)
        if not name:name="Ch%d"%channel
        self.name= name
        self.basename = basename
        self.lutname = lutname
        self.tps = t
        self.filename=filename
        self.parser = RawConfigParser()
        self.reader = None
        self.originalScalarRange = (0,4095)
        self.channel = channel
        self.dimensions = dims
        self.voxelsize = voxelsize
        self.spacing = None
        self.emission = emission
        self.excitation = excitation
        self.color = None
        self.shift = None
        self.noZ=0
        self.reverseSlices=reverse
        if filename:
            self.path=os.path.dirname(filename)
        if channel>=0:
            self.ctf = self.readLUT()
        self.setPath(filename)
        
        self.unit_coeffs={"nm":1e-9,"um":1e-6,"mm":0.001}
        
        
    def getDataSetCount(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        """
        if not self.tps:return 1
        return self.tps
        
    def getEmissionWavelength(self):
        """
        Created: 07.04.2006, KP
        Description: Returns the emission wavelength used to image this channel
        managed by this DataSource
        """
        return self.emission
            
    def getExcitationWavelength(self):
        """
        Created: 07.04.2006, KP
        Description: Returns the excitation wavelength used to image the channel
        managed by this DataSource
        """
        return self.excitation

        
     
        
    def getFileName(self):
        """
        Created: 21.07.2005
        Description: Return the file name
        """    
        return self.filename
        

    
    def getDataSet(self, i,raw=0):
        """
        Created: 12.04.2005, KP
        Description: Returns the image data for timepoint i
        """
        data=self.getTimepoint(i)        
        if raw:
            return data
            
        
        self.originalScalarRange=data.GetScalarRange()
        
        data=self.getResampledData(data,i)
        
        
        data=self.getIntensityScaledData(data)
        
        
        data.ReleaseDataFlagOff()
        return data
        
    def getTimepoint(self,n):
        """
        Created: 16.02.2006, KP
        Description: Return the nth timepoint
        """        
        path=os.path.join(self.path,"%s.oif.files"%self.basename)
        if not self.reader:
            self.reader = vtk.vtkExtTIFFReader()
            #self.reader.RawModeOn()
            #self.reader=vtk.vtkImageReader()
            #self.reader.SetDataScalarTypeToUnsignedShort()
            x,y,z=self.dimensions
            self.reader.SetDataExtent(0,x-1,0,y-1,0,z-1)
        
        zpat=""
        tpat=""
        cpat=os.path.sep+"%s_C%.3d"%(self.lutname,self.channel)
        path+=cpat
        #self.reader.SetFilePrefix(path)
        if self.dimensions[2]>1:
            zpat="Z%.3d"
        if self.tps > 0:
            tpat="T%.3d"
        pat=path+zpat+tpat+".tif"
        
        self.reader.SetFilePattern(pat)
        if self.reverseSlices and 0:
            #print "offset=",self.dimensions[2]
            self.reader.SetFileNameSliceOffset(self.dimensions[2])
            self.reader.SetFileNameSliceSpacing(-1)
        else:
            self.reader.SetFileNameSliceOffset(1)

#        print "pattern='"+self.reader.GetFilePattern()+"'"
        self.reader.Update()
        #print self.reader
#        print vtk,self.reader
#        print "Scalar range for data=",self.reader.GetOutput().GetScalarRange()
        return self.reader.GetOutput()
        
        
    def getDimensions(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if self.resampleDims:
            
            return self.resampleDims
        if not self.dimensions:
            raise "No dimensions given for ",str(self)
            #print "Got dimensions=",self.dimensions
        return self.dimensions

    def readLUT(self): 
        """
        Created: 16.02.2006, KP
        Description: Read the LUT for this dataset
        """
        lutpath = os.path.join(self.path,"%s.oif.files"%self.basename,"%s_LUT%d.lut"%(self.lutname,self.channel))
        f=codecs.open(lutpath,"r","utf-16")
        #print "Reading lut from %s..."%lutpath
        while 1:
            line=f.readline()
            if "ColorLUTData" in line:
                break
        
        
        pos=f.tell()
        f.close()
        f=open(lutpath,"rb")
        f.seek(-4*65536,2)
        data=f.read()
        #print "Got ",len(data),"bytes"
        
        format="i"*65536
        values=struct.unpack(format,data)
        ctf=vtk.vtkColorTransferFunction()
        #print values
        vals=[( ((x>>16)&0xff)/255.0,((x>>8)&0xff)/255.0,(x&0xff)/255.0) for x in values]
        
        #def f(x):( (x>>16)&0xff
        i=0
        r2,g2,b2=-1,-1,-1
        coeff = 16.0
        minval,maxval = self.getScalarRange()
        
        if self.explicitScale:
            shift = self.intensityShift
            if self.intensityShift:
                maxval+=self.intensityShift
                #print "Maximum value after being shifted=",maxval
            scale = self.intensityScale
            if not scale:
                scale = 255.0 / maxval
            maxval*=scale
            
            self.scalarRange = (0,maxval)
            self.bitdepth = int(math.log(maxval+1,2))
            #print "Maximum value after being scaled=",maxval
            
        coeff = 65536.0 / (maxval+1)
        #coeff=int(coeff)
#        print "coeff=",coeff
#        print "Largest value=",len(vals)/coeff
        
        for i in range(0, maxval+1):
            r,g,b = vals[int(i*coeff)]
            ctf.AddRGBPoint(i, r,g,b)
            
        return ctf
        
        
    def getSpacing(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the spacing of the datasets this 
                     dataunit contains
        """
        if not self.spacing:
            a,b,c = self.getVoxelSize()
            self.spacing=[1,b/a,c/a]
        return self.spacing
        
    def getVoxelSize(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the voxel size of the datasets this 
                     dataunit contains
        """
        if not self.voxelsize:
            x,y,z,tp,ch,vx,vy,vz=self.getAllDimensions(self.parser)
                         
            self.voxelsize=(vx,vy,vz)

            #print "Got voxel size=",self.voxelsize
        return self.voxelsize
    
    def getAllDimensions(self,parser):
        """
        Created: 16.02.2006, KP
        Description: Read the number of timepoints, channels and XYZ from the OIF file
        """    
        timepoints = 0
        channels = 0
        x = 0
        y = 0
        z = 1
        for i in range(0,7):
            sect="Axis %d Parameters Common"%i
            key = "AxisCode"
            data = parser.get(sect,key)
            # If Axis i is the time axis
            n = timepoints = int(parser.get(sect,"MaxSize"))
            unit = parser.get(sect,"UnitName")
            unit=unit.replace('"',"")
            sp = parser.get(sect,"StartPosition")
            ep = parser.get(sect,"EndPosition")
            sp = sp.replace('"','')
            ep = ep.replace('"','')
            
            startpos=float(sp)
            endpos = float(ep)
            
            
            if endpos<startpos:
                self.reverseSlices=1
            
            diff=abs(endpos-startpos)
            if unit in self.unit_coeffs:
                coeff=self.unit_coeffs[unit]
            
            diff*=coeff
            if data == '"T"':
                timepoints = n
            elif data == '"C"':
                channels = n
            elif data == '"X"':
                x = n
                vx=diff
            elif data == '"Y"':
                y = n
                vy=diff
            elif data == '"Z"':
                z = n
                vz=diff
        
        if z==0:
            z=1
            self.noZ=1
        vx/=float(x)
        vy/=float(y)
        if z>1:
            vz/=float(z-1)
        self.originalDimensions = (x,y,z)
        return x,y,z,timepoints,channels,vx,vy,vz
                
                
    def getLUTPath(self, parser):
        """
        Created: 05.09.2006, KP
        Description: Read the base name for the LUT file which can also be used
                     for the paths of the TIFF files
        """
        path = parser.get("ProfileSaveInfo","LutFileName0")
        path = os.path.basename(path)
        path = path.split("\\")[-1]
        parts = path.split("_")
        path = "_".join(parts[:-1])
        return path
                
    def getDyes(self,parser,n):
        """
        Created: 16.02.2006, KP
        Description: Read the dye names for n channels
        """ 
        names=[]
        exs=[]
        ems=[]
        for i in range(1,n+1):
            sect="Channel %d Parameters"%i
            data = parser.get(sect,"DyeName")
            data=data.replace('"',"")
            emission = int(parser.get(sect,"EmissionWavelength"))
            excitation = int(parser.get(sect,"ExcitationWavelength"))
            names.append(data)
            exs.append(excitation)
            ems.append(emission)
        return names,(exs,ems)
            
            
    def loadFromFile(self, filename):
        """
        Created: 12.04.2005, KP
        Description: Loads the specified .oif-file and imports data from it.
        Parameters:   filename  The .oif-file to be loaded
        """
        self.filename=filename
        self.path=os.path.dirname(filename)
        
        basefile=os.path.basename(filename)
        basefile=basefile.replace(".oif","")
        
        try:
            f=open(filename)
            f.close()
        except IOError, ex:
            Logging.error("Failed to open Olympus OIF File",
            "Failed to open file %s for reading: %s"%(filename,str(ex)))        

        fp = codecs.open(filename,"r","utf-16")
        self.parser.readfp(fp)
        x,y,z,tps,chs,vx,vy,vz = self.getAllDimensions(self.parser)
        
        voxsiz=(vx,vy,vz)
        names,(excitations,emissions)=self.getDyes(self.parser,chs)
        
        lutpath = self.getLUTPath(self.parser)
        
        dataunits=[]
        for ch in range(1,chs+1):
            name=names[ch-1]    
            excitation = excitations[ch-1]
            emission = emissions[ch-1]
            datasource=OlympusDataSource(filename,ch,name=name,basename=basefile,
                                        lutname = lutpath,
                                        dims=(x,y,z),t=tps,voxelsize=voxsiz,
                                        reverse=self.reverseSlices,
                                        emission = emission,
                                        excitation = excitation)
            dataunit=DataUnit.DataUnit()
            dataunit.setDataSource(datasource)
            dataunits.append(dataunit)
            
        return dataunits


    def getName(self):
        """
        Created: 18.11.2005, KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        return self.name

    def resetColorTransferFunction(self):
        """
        Created: 12.10.2006, KP
        Description: A method that will reset the CTF from the datasource.
                     This is useful e.g. when scaling the intensities of the    
                     dataset
        """
        self.ctf = None
        return self.getColorTransferFunction()
    
    def getColorTransferFunction(self):
        """
        Created: 26.04.2005, KP
        Description: Returns the ctf of the dataset series which this datasource
                     operates on
        """
        if not self.ctf:
            self.ctf = self.readLUT()
        return self.ctf        
