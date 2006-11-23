# -*- coding: iso-8859-1 -*-
"""
 Unit: LeicaDataSource
 Project: BioImageXD
 Created: 12.04.2005, KP
 Description: 

 A module for reading data produced by Leica microscopes. 
 
 Intial code by Karl Garsha <garsha@itg.uiuc.edu>. 
 Modified by Kalle Pahajoki for BioImageXD use.
 
 Copyright (C) 2005  Karl Garsha, BioImageXD Project
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
__author__ = "Karl Garsha, BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"
import wx
import os
import sys
import re
import string
import vtk
import math
try:
    import Image
except:
    Image=None
from DataSource import *
import DataUnit

def getExtensions(): return ["txt"]
def getFileType(): return "Leica TCS-NT datasets (*.txt)"
def getClass(): return LeicaDataSource
        
class LeicaDataSource(DataSource):
    """
    Class: LeicaDataSource
    Created: 12.04.2005, KP
    Description: Leica format datasource
    """
    def __init__(self,filename="",experiment="",channel=-1):
        """
        Created: 12.04.2005, KP
        Description: Constructor
        """    
        DataSource.__init__(self)
        self.filename=filename
        self.reader = LeicaExperiment(filename)
        self.experiment = experiment
        if experiment:
            self.originalDimensions=self.reader.GetDimensions(self.experiment)
        self.channel = channel
        self.dimensions = None
        self.voxelsize = None
        self.spacing = None
        self.color = None
        self.ctf = None
        self.setPath(filename)
        
    def getDataSetCount(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        """
        return self.reader.GetNumberOfTimepoints(self.experiment)
    def getFileName(self):
        """
        Created: 21.07.2005
        Description: Return the file name
        """    
        return self.filename
        

    
    def getDataSet(self, i,raw=0):
        """
        Created: 12.04.2005, KP
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        """
        data=self.reader.GetTimepoint(self.experiment,self.channel,i)
        return self.getResampledData(data,i)
        
    def getDimensions(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if self.resampleDims:
            return self.resampleDims
        if not self.dimensions:
            self.dimensions=self.reader.GetDimensions(self.experiment)            
            #print "Got dimensions=",self.dimensions
        return self.dimensions

    
        
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

            #data=self.getDataSet(0)
            #self.spacing=data.GetSpacing()
        return self.spacing
        
    def getVoxelSize(self):
        """
        Created: 12.04.2005, KP
        Description: Returns the voxel size of the datasets this 
                     dataunit contains
        """
        if not self.voxelsize:
            self.voxelsize = self.reader.GetVoxelSize(self.experiment)

            
            #print "Got voxel size=",self.voxelsize
        return self.voxelsize
    
    def loadFromFile(self, filename):
        """
        Created: 12.04.2005, KP
        Description: Loads the specified .txt-file and imports data from it.
        Parameters:   filename  The .txt-file to be loaded
        """
        self.filename=filename
        self.path=os.path.dirname(filename)
        self.reader.setFileName(filename)
        try:
            f=open(filename)
            f.close()
        except IOError, ex:
            Logging.error("Failed to open Leica File",
            "Failed to open file %s for reading: %s"%(filename,str(ex)))

        self.reader.Read()
        dataunits=[]
        experiments = self.reader.GetExperiments()
        for experiment in experiments:
            channelNum=self.reader.GetNumberOfChannels(experiment)
            #print "There are %d channels in %s"%(channelNum,filename)
            for i in range(channelNum):
                # We create a datasource with specific channel number that
                #  we can associate with the dataunit
                
                datasource=LeicaDataSource(filename,experiment,i)
                dataunit=DataUnit.DataUnit()
                dataunit.setDataSource(datasource)
                dataunits.append((experiment,dataunit))
            
        return dataunits


    def getName(self):
        """
        Created: 18.11.2005, KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        return "Ch%.2d"%self.channel

        
    def getColorTransferFunction(self):
        """
        Created: 26.04.2005, KP
        Description: Returns the ctf of the dataset series which this datasource
                     operates on
        """
        bd=self.getBitDepth()
        print "Bit depth=",bd
        if bd==32:
            return None
        if not self.ctf:
            print "Using ctf based on TIFF Color"
            ctf = vtk.vtkColorTransferFunction()            
            r,g,b=self.reader.GetColor(self.experiment,self.channel)
            r/=255.0
            g/=255.0
            b/=255.0
            ctf.AddRGBPoint(0,0,0,0)
            ctf.AddRGBPoint(255,r,g,b)
            self.ctf = ctf
        return self.ctf        

        
class LeicaExperiment:
    def __init__ (self, ExpPathTxt):
        self.SeriesDict={}
        # Store snapshots in a dict of it's own, so we can give them separately 
        # if requested
        self.SnapshotDict={}
        self.path=""

        self.RE_ScanMode=re.compile(r'ScanMode.*',re.I)
        self.RE_X=re.compile(r'Format-Width.+\d+',re.I)
        self.RE_Y=re.compile(r'Format-Height.+\d+',re.I)
        self.RE_NumChan=re.compile(r'Dimension_2.*',re.I)
        self.RE_LogicalSize=re.compile(r'Logical\sSize.+\d+',re.I)
        self.RE_NumSect=re.compile(r'Dimension_3.*',re.I)
        self.RE_T=re.compile(r'Dimension_4.*',re.I)
        self.RE_SeriesName=re.compile(r'Series\sName:(.*)',re.I)
        self.RE_Width=re.compile(r'Size-Width.+\d+',re.I)
        self.RE_Height=re.compile(r'Size-Height.+\d+',re.I)
        self.RE_Depth=re.compile(r'Size-Depth.+\d+',re.I)
        self.RE_VoxelWidth=re.compile(r'Voxel-Width.+\d+',re.I)
        self.RE_VoxelHeight=re.compile(r'Voxel-Height.+\d+',re.I)
        self.RE_VoxelDepth=re.compile(r'Voxel-Depth.+\d+',re.I)
        self.RE_Bit_Depth=re.compile(r'Resolution.+\d+',re.I)
        self.RE_PixelSize=re.compile(r'Pixel Size in Byte.+\d+',re.I)
        self.RE_NonWhitespace=re.compile(r'\w+',re.I)
        
        
        self.setFileName(ExpPathTxt)
        self.TP_CH_VolDataList=[]
        

        
    def setFileName(self,filename):
        """
        Created: 12.04.2005, KP
        Description: Sets the file name to be opened
        """
        print "File name = ",filename
        self.filename=filename
        if filename:
            self.path=os.path.dirname(filename)
            self.Read()
    
    def Read(self):
        """
        Created: 12.04.2005, KP
        Description: Read the given file
        """    
        print "Trying to read ",self.filename
        self.CreateExpDataStruct(self.filename)
        
    def GetExperiments(self):
        """
        Created: 12.04.2005, KP
        Description: Return the number of channels this dataset contains
        """    
        return self.SeriesDict.keys()

    def GetNumberOfChannels(self,experiment):
        """
        Created: 12.04.2005, KP
        Description: Return the number of channels an experiment contains
        """    
        return self.SeriesDict[experiment]["NumChan"]

    def GetNumberOfTimepoints(self,experiment):
        """
        Created: 12.04.2005, KP
        Description: Return the number of channels an experiment contains
        """        
        #print self.SeriesDict.keys()
        return self.SeriesDict[experiment]["Num_T"]
        
    def GetDimensions(self,experiment):
        """
        Created: 12.04.2005, KP
        Description: Return dimensions of an experiment
        """    
        x=self.SeriesDict[experiment]["Resolution_X"]   
        y=self.SeriesDict[experiment]["Resolution_Y"]   
        z=self.SeriesDict[experiment]["Number_Sections"]   
        return (x,y,z)
        
    def GetColor(self,experiment,channel):
        """
        Created: 12.04.2005, KP
        Description: Return the data for a given timepoint
        """    
        if len(self.TP_CH_VolDataList) == 0:
            self.ReadLeicaVolData(experiment)

        channels=self.TP_CH_VolDataList[0]
        rdr=channels[channel]
        rdr.ComputeInternalFileName(0)
        #filename = self.SeriesDict[experiment]["TiffList"][0][0][0]
#        print filename

        #filename=rdr.GetInternalFileName()
        fn=rdr.GetInternalFileName()
        #fn=os.path.join(self.path,filename)
        #print fn##
        #f=open(fn)
        if not Image:return 0,0,0
        img=Image.open(fn)
        if not img.palette:
            return 255,255,255
        
        palette=img.palette.getdata()[1]
        r=palette[255]
        g=palette[2*256-1]
        b=palette[3*256-1]
        return ord(r),ord(g),ord(b)

    def GetTimepoint(self,experiment,channel,timepoint):
        """
        Created: 12.04.2005, KP
        Description: Return the data for a given timepoint
        """    
        if len(self.TP_CH_VolDataList) == 0:
            self.ReadLeicaVolData(experiment)

        channels=self.TP_CH_VolDataList[timepoint]
        rdr=channels[channel]
        #rdr.Update()
        return rdr.GetOutput()
        
    def GetVoxelSize(self,experiment):
        """
        Created: 12.04.2005, KP
        Description: Return voxel size of an experiment
        """    
        x=self.SeriesDict[experiment]["Voxel_Width_X"]   
        y=self.SeriesDict[experiment]["Voxel_Height_Y"]   
        z=self.SeriesDict[experiment]["Voxel_Depth_Z"]   
        # They are now in microm, scale to meters as LSM reader does
        x/=1000000.0
        y/=1000000.0
        z/=1000000.0
        return (x,y,z)
        
        

    def Sep_Series(self, ExpPathTxt):
        InfoFile=open(ExpPathTxt)#If the actual file is returned with the open dialog, we can skip this.
        InfoFile_AsString=InfoFile.read()
        SplitString = re.compile(r'\*+\sNEXT\sIMAGE\s\*+',re.I) 
        ImageList=SplitString.split(InfoFile_AsString)
        self.Series_Data_List=[]
        for stringa in ImageList:
            #self.Series_Data_List.append=cStringIO(ImageList[stringCounter])
            self.Series_Data_List.append(stringa)
            ExpPathPair=os.path.split(ExpPathTxt)
            self.ExpPath=ExpPathPair[0]
            
            PreExpName=ExpPathPair[1]
            PreExpNameLst=string.split(PreExpName,'.')
            self.ExpName=PreExpNameLst[0] #this gets rid of the file extension
            
    def GetScanMode(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the scan mode from given data
        """        
        SeriesScanModeLine=self.RE_ScanMode.search(Series_Data)
        if not SeriesScanModeLine:
            return None
        SeriesScanModeSplit=SeriesScanModeLine.group(0).split()
        SeriesScanMode=SeriesScanModeSplit[1].strip()
        return SeriesScanMode

    def GetSeriesName(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the series name from given data
        """               
        SeriesNameString=self.RE_SeriesName.search(Series_Data)
        SeriesNameLine=SeriesNameString.group(1)
        SeriesNameLine=SeriesNameLine.strip()
        SeriesNameLine=SeriesNameLine.replace(chr(0),"")
        return SeriesNameLine
        SeriesNameSplit=SeriesNameLine.split()
        SeriesNameSplit.reverse()
        SeriesNameTxtString=self.RE_NonWhitespace.search(SeriesNameSplit[0].strip())#this is intended to get the alpha-num. char values and drop the newlines
        SeriesName=SeriesNameTxtString.group(0)
        # should return the series name w/o newline
        return SeriesName
        #It works! Holy toledo-what a pain in butt.
        
    def GetNumChan(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the number of channels from given data
        """              
        SeriesDataSplit=self.RE_NumChan.split(Series_Data)
        NumChan_String=SeriesDataSplit[1]
        NumChanMatch=self.RE_LogicalSize.search(NumChan_String)
        NumChanLine=NumChanMatch.group(0)
        WordsNumChan=NumChanLine.split()
        WordsNumChan.reverse()
        NumChan=int(WordsNumChan[0].strip())
        return NumChan        
        
    def GetZDimension(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the z dimension from given data
        """              
        #Get the z-dimension value
        if not self.RE_NumSect.search(Series_Data):
            return 1
        SeriesDataSplit=self.RE_NumSect.split(Series_Data)
        
        
        NumSect_String=SeriesDataSplit[1]
        NumSectMatch=self.RE_LogicalSize.search(NumSect_String)
        NumSectLine=NumSectMatch.group(0)
        WordsZ_Res=NumSectLine.split()
        WordsZ_Res.reverse()
        Z_Res=int(WordsZ_Res[0].strip())
        return Z_Res
        
    def GetTimeDimension(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the time dimension from given data
        """          
        SeriesDataSplit=self.RE_T.split(Series_Data)
        T_String=SeriesDataSplit[1]
        T_Match=self.RE_LogicalSize.search(T_String)
        T_Line=T_Match.group(0)
        T_Line=T_Line.replace(chr(0)," ")
        WordsNumT=T_Line.split()
        #WordsNumT.reverse()
        NumT=int(WordsNumT[-1].strip())
        return NumT
        
    def GetWidth(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the width from given data
        """                  
        SeriesWidthString=self.RE_Width.search(Series_Data)
        SeriesWidthLine=SeriesWidthString.group(0)
        SeriesWidthSplit=SeriesWidthLine.split()
        SeriesWidthSplit.reverse()
        SeriesWidth=float(SeriesWidthSplit[0])
        return SeriesWidth
        
    def GetHeight(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the height from given data
        """                   
        SeriesHeightString=self.RE_Height.search(Series_Data)
        SeriesHeightLine=SeriesHeightString.group(0)
        SeriesHeightSplit=SeriesHeightLine.split()
        SeriesHeightSplit.reverse()
        SeriesHeight=float(SeriesHeightSplit[0].strip())
        return SeriesHeight
        
    def GetDepth(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the depth from given data
        """ 
        print "Searching from",Series_Data
        SeriesDepthString=self.RE_Depth.search(Series_Data)
        SeriesDepthLine=SeriesDepthString.group(0)
        
        SeriesDepthSplit=SeriesDepthLine.split()
        SeriesDepthSplit.reverse()
        
        SeriesDepth=float(SeriesDepthSplit[0].strip())
        print "Returning depth",SeriesDepth
        return SeriesDepth
        
    def GetVoxelWidth(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the voxel width from given data
        """ 
        SeriesVoxelWidthString=self.RE_VoxelWidth.search(Series_Data)
        SeriesVoxelWidthLine=SeriesVoxelWidthString.group(0)
        SeriesVoxelWidthSplit=SeriesVoxelWidthLine.split()
        SeriesVoxelWidthSplit.reverse()
        SeriesVoxelWidth=float(SeriesVoxelWidthSplit[0].strip())
        return SeriesVoxelWidth
        
    def GetVoxelHeight(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the voxel height from given data
        """             
        SeriesVoxelHeightString=self.RE_VoxelHeight.search(Series_Data)
        SeriesVoxelHeightLine=SeriesVoxelHeightString.group(0)
        SeriesVoxelHeightSplit=SeriesVoxelHeightLine.split()
        SeriesVoxelHeightSplit.reverse()
        SeriesVoxelHeight=float(SeriesVoxelHeightSplit[0].strip())
        return SeriesVoxelHeight
        
    def GetVoxelDepth(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the voxel depth from given data
        """                
        SeriesVoxelDepthString=self.RE_VoxelDepth.search(Series_Data)
        SeriesVoxelDepthLine=SeriesVoxelDepthString.group(0)
        SeriesVoxelDepthSplit=SeriesVoxelDepthLine.split()
        SeriesVoxelDepthSplit.reverse()
        SeriesVoxelDepth=float(SeriesVoxelDepthSplit[0].strip())
        return SeriesVoxelDepth
        
    def GetBitDepth(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the bit depth from given data
        """             
        SeriesBitDepthString=self.RE_Bit_Depth.search(Series_Data)
        SeriesBitDepthLine=SeriesBitDepthString.group(0)
        SeriesBitDepthSplit=SeriesBitDepthLine.split()
        SeriesBitDepthSplit.reverse()
        SeriesBitDepth=float(SeriesBitDepthSplit[0].strip())
        return SeriesBitDepth

    def GetNumberOfComponents(self,Series_Data):
        """
        Created: 20.02.2006, KP
        Description: Return the number of components per pixel
        """             
        SeriesPixelSizeString=self.RE_PixelSize.search(Series_Data)
        if not SeriesPixelSizeString:
            return 1
        SeriesPixelSizeLine=SeriesPixelSizeString.group(0)
        SeriesPixelSizeSplit=SeriesPixelSizeLine.split()
        SeriesPixelSizeSplit.reverse()
        SeriesPixelSize=float(SeriesPixelSizeSplit[0].strip())
        return SeriesPixelSize
        
        
    def GetResolutionX(self,Series_Data):
        """
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the x resolution from given data
        """                                    
        SeriesResXString=self.RE_X.search(Series_Data)
        SeriesResXLine=SeriesResXString.group(0)
        SeriesResXSplit=SeriesResXLine.split()
        SeriesResXSplit.reverse()
        SeriesResX=int(SeriesResXSplit[0].strip())
        return SeriesResX
                
    def GetResolutionY(self,Series_Data):
        """
        Method: GetResolutionY(data)
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Return the x resolution from given data
        """                                            
        SeriesResYString=self.RE_Y.search(Series_Data)
        SeriesResYLine=SeriesResYString.group(0)
        SeriesResYSplit=SeriesResYLine.split()
        SeriesResYSplit.reverse()
        SeriesResY=int(SeriesResYSplit[0].strip())
        return SeriesResY
                        
                        
    def Extract_Series_Info(self):
        """
        Method: Extract_Series_Info
        Created: 15.04.2005, KP, based on Karl Garsha's code
        Description: Extract the info about the series
        """        
        self.SeriesDict={}
        
        #print "Series_Data_List=",self.Series_Data_List
        for string in self.Series_Data_List:
            Series_Data=string
            Series_Info={}
 
            seriesname = self.GetSeriesName(Series_Data)
            SeriesScanMode=self.GetScanMode(Series_Data)
            Series_Info['Pixel_Size']=self.GetNumberOfComponents(Series_Data)                
            
            
            Series_Info['Series_Name'] = seriesname
            #print "\n\nSeries name=",seriesname,"\nScanMode=",SeriesScanMode,"\n"
            if not SeriesScanMode:
                if "snapshot" in seriesname.lower():
                    # TODO: This is a snapshot, handle it as such
                    print "Do not know how to handle snapshot %s, continuing"%seriesname
                    continue
                else:
                    print "Unrecognized entity without scanmode:",seriesname
            else:
                Series_Info['Scan_Mode']=SeriesScanMode
            
            if SeriesScanMode in ['xyz','xyzt']:
                Logging.info("Scan mode is ",SeriesScanMode,kw="io")
                #print Series_Data
                Series_Info['NumChan']=self.GetNumChan(Series_Data)
                #print "Number of channels=",Series_Info['NumChan']
                SeriesDataSplit=self.RE_NumChan.split(Series_Data)
                Series_Data=SeriesDataSplit[1] #Breaks data text into progressively smaller pieces
          
                z=self.GetZDimension(Series_Data)
                Series_Info['Number_Sections']=z
                if z !=1:
                    SeriesDataSplit=self.RE_NumSect.split(Series_Data)
                    Series_Data=SeriesDataSplit[1] #Breaks data text into progressively smaller pieces
                
                #Check for Time dimension--if so, get time data
                if self.RE_T.search(Series_Data):
                    t=self.GetTimeDimension(Series_Data)
                    
                    Series_Info['Num_T']=t
                    SeriesDataSplit=self.RE_T.split(Series_Data)
                    Series_Data=SeriesDataSplit[1]
                else:
                    #raise "No timepoints found"
                    Series_Info['Num_T']=1
                Series_Info['Width_X']=self.GetWidth(Series_Data)
                Series_Info['Height_Y']=self.GetHeight(Series_Data)
                Series_Info['Depth_Z']=self.GetDepth(Series_Data)
                Series_Info['Voxel_Width_X']=self.GetVoxelWidth(Series_Data)
                Series_Info['Voxel_Height_Y']=self.GetVoxelHeight(Series_Data)
                Series_Info['Voxel_Depth_Z']=self.GetVoxelDepth(Series_Data)

                Series_Info['Bit_Depth']=self.GetBitDepth(Series_Data)

                print "Pixel size of dataset=",Series_Info['Pixel_Size']
                Series_Info['Resolution_X']=self.GetResolutionX(Series_Data)
                Series_Info['Resolution_Y']=self.GetResolutionY(Series_Data)
                
                #make a dictionary containing each series info dictionary (dictionary of dictionaries)
                SeriesName=Series_Info['Series_Name']
                self.SeriesDict[SeriesName]=Series_Info

    def Create_Tiff_Lists(self):
        for key, value in self.SeriesDict.items():
            Series_Info=value
            Series_Name=key
            Num_T_Points=(Series_Info['Num_T'])
            print "Creating TIFF list"
            print "Num_T_Points=",Num_T_Points
            
            
            TimePoints=[]
            for a in xrange(Num_T_Points): #starts at 0 and counts up to (but not including) Num_T_Points.
                n=int(math.log(Num_T_Points))
                if n==1:n=2
                TP_pat="_t%%.%dd"%n
                #print "TP_Pattern=",TP_pat
                #raise "foo"
                TP_Name=TP_pat%a
                #TP_Name='_t'+str((a%10000)//1000)+str((a%1000)//100)+str((a%100)//10)+str((a%10)//1)
                
                Num_Chan=Series_Info['NumChan']
                print "Num_Chan=",Num_Chan
                Channels=[]
                for b in xrange(Num_Chan):
                    File_List=[]
                    if 1 or Num_Chan>1:
                        CH_Name=('_ch'+str((b%100)//10)+str((b%10)//1))
                    else:
                        print "Since only one channel, no _chXXX"
                        CH_Name=("")
                    Num_Z_Sec=Series_Info['Number_Sections']
                    for c in xrange(Num_Z_Sec):
                        #if Num_Z_Sec!=1:
                        Z_Name=str('_z'+str((c%1000)//100)+str((c%100)//10)+str((c%10)//1))
                        #Z_Name="_z%.3d"%c
                        #print "ZName=",Z_Name
                        #else:
                        #    print "NO Z since only one section"
                        #    Z_Name=""
                        
                        if Num_T_Points > 1:
                            Slice_Name_With_Z = self.ExpName + '_' + Series_Name + TP_Name + Z_Name + CH_Name + '.tif'
                            Slice_Name_No_Z = self.ExpName + '_' + Series_Name + TP_Name + CH_Name + '.tif'
                        else:
                            Slice_Name_With_Z = self.ExpName + '_' + Series_Name + Z_Name + CH_Name + '.tif'
                            Slice_Name_No_Z = self.ExpName + '_' + Series_Name  + CH_Name + '.tif'
                        if os.path.exists(os.path.join(self.path,Slice_Name_With_Z)):
                            File_List.append(Slice_Name_With_Z)
                            print "Using with Z"
                        elif os.path.exists(os.path.join(self.path,Slice_Name_No_Z)):
                            print "Using no z"
                            File_List.append(Slice_Name_No_Z)
                        
                    Channels.append(File_List)
                TimePoints.append(Channels)
            Series_Info['TiffList']=TimePoints
            self.SeriesDict[Series_Name]=Series_Info #puts modified Series_Info dictionary back into SeriesDict

    def CreateExpDataStruct(self,ExpPathTxt):
        self.Sep_Series(ExpPathTxt)
        self.Extract_Series_Info()
        self.Create_Tiff_Lists()
            
    def ReadLeicaVolDataOld(self,Series_Name):
        #os.chdir(self.ExpPath)#needed for Tkinter file select
        global TP_CH_VolDataList
        Series_Info=self.SeriesDict[Series_Name]
        TiffList=Series_Info['TiffList']
        XYDim=Series_Info['Resolution_X']-1
        NumSect=Series_Info['Number_Sections']-1
        XSpace=Series_Info['Voxel_Width_X']
        YSpace=Series_Info['Voxel_Height_Y']
        ZSpace=Series_Info['Voxel_Depth_Z']
        self.TP_CH_VolDataList=[] #contains the vol data for each timepoint, each channel
        for TimePoint in TiffList:
            ChnlVolDataLst=[] #contains the volumetric datasets for each channel w/in each timepoint
            for Channel in TimePoint:
                
                TIFFReader=vtk.vtkExtTIFFReader()
                if Series_Info['Pixel_Size'] !=3:
                    TIFFReader.RawModeOn()
                #First read the images for a particular channel
                print "Image list=",Channel
                ImageName=Channel[0] #Take the first tif name
                print "Image name='%s'"%ImageName
                # Check to see whether the image name contains either
                # channels or z slices at all. If not, then we can just you
                # the filename and skip a whole bunch of processing
                if ("_ch" in ImageName) or ("_z" in ImageName):
                    print "Has channels or is z stack"
                    #RE_zsplit=re.compile(r'.+_z000.+',re.I)  #split the filename at the z position, exising the z-pos variable
                    #match for the file prefix
                    RE_FilePrefix=re.compile(r'.+_z',re.I) 
                    # match for files that only have _chXXX
                    RE_FileChPrefix=re.compile(r'(.+)_ch',re.I)
                    #search for the end part of the file name
                    RE_FilePostfix=re.compile(r'_ch\d+.tif',re.I) 
                    FilePrefixMatch=re.match(RE_FilePrefix,ImageName)
                    
                    # Match the part before _z
                    if FilePrefixMatch:
                        ImagePrefix=string.strip(FilePrefixMatch.group(0))#we match the first part of the filename (above), then get the matched string
                        print "ImagePrefix=",ImagePrefix
                    else:
                        print "No Z, Matching ch only"
                        FilePrefixMatch=re.match(RE_FileChPrefix,ImageName)
                        #raise "Got no ImagePrefix for ",ImageName
                        #we match the first part of the filename (above), then get the matched string
                        if FilePrefixMatch:
                            ImagePrefix=string.strip(FilePrefixMatch.group(1))
                        
                            print FilePrefixMatch.groups()
                            print "ImagePrefix (ch only)=",ImagePrefix                    
                        else:
                            print "No file prefix"
                            ImagePrefix=""
                    print "Image prefix=",ImagePrefix
                    FilePostfixSearch=re.search(RE_FilePostfix,ImageName)
                    if FilePostfixSearch:
                        #this gives us the string found by the search
                        FilePostfixGroup=FilePostfixSearch.group(0)                        
                        print "FilePostfixGroup=",FilePostfixGroup
                    else:
                        print "No file postfix group"
                        FilePostfixGroup=".tif"
                    if Series_Info["Number_Sections"]>1:                
                        #fsprint stuff--string+3 int spaces padded w/ zeros+last part of name eg. "_ch00.tif"
                        print "Has z slices"
                        z=Series_Info['Number_Sections']
                        
                        nzslices=int(math.ceil(math.log(z,10)))
                        print "z=%d, log z=%d"%(z,nzslices)
                        pat='%%s%%0%di'%nzslices
                        ImagePattern=pat+str(FilePostfixGroup) 
                    else:
                        ImagePattern='%s'+str(FilePostfixGroup)
                    print "ImagePattern=",ImagePattern
                    if FilePrefixMatch != None:
                        print "self.path=",self.path
                        
                        ImagePrefix=os.path.join(self.path,ImagePrefix)
                        ImagePrefix.encode("latin-1")
                        #print "Using image# prefix='%s'"%ImagePrefix
    
                        
                        TIFFReader.SetFilePrefix(ImagePrefix) 
                    #if FilePostfixSearch != None:
                    if ImagePattern:
                        ImagePattern.encode("latin-1")
                        #ImageReader.SetFilePattern(ImagePattern)
                        TIFFReader.SetFilePattern(ImagePattern)
                else:
                    print "Using simply the ImageName",ImageName
                    name=os.path.join(self.path,ImageName)
                    #ImageReader.SetFileName(name)
                    TIFFReader.SetFileName(name)
                
                print "Bit depth of image=",Series_Info["Bit_Depth"]
                    
                if Series_Info['Bit_Depth']==8:
                    #ImageReader.SetDataScalarTypeToUnsignedChar()
                    TIFFReader.SetDataScalarTypeToUnsignedChar()
                else:
                    raise "Only 8-bit data supported"
                TIFFReader.FileLowerLeftOff()
                TIFFReader.SetDataExtent(0,XYDim,0,XYDim,0,NumSect)
                TIFFReader.SetDataSpacing(XSpace,YSpace,ZSpace)
                
                TIFFReader.Update()
                
                
                
                ChnlVolDataLst.append(TIFFReader)#now we have a list with the imported volume data for each channel
            self.TP_CH_VolDataList.append(ChnlVolDataLst)   
            
 
    def ReadLeicaVolData(self,Series_Name):
        #os.chdir(self.ExpPath)#needed for Tkinter file select
        global TP_CH_VolDataList
        Series_Info=self.SeriesDict[Series_Name]
        TiffList=Series_Info['TiffList']
        XYDim=Series_Info['Resolution_X']-1
        NumSect=Series_Info['Number_Sections']-1
        XSpace=Series_Info['Voxel_Width_X']
        YSpace=Series_Info['Voxel_Height_Y']
        ZSpace=Series_Info['Voxel_Depth_Z']
        self.TP_CH_VolDataList=[] #contains the vol data for each timepoint, each channel
        for TimePoint in TiffList:
            ChnlVolDataLst=[] #contains the volumetric datasets for each channel w/in each timepoint
            for Channel in TimePoint:
                
                TIFFReader=vtk.vtkExtTIFFReader()
                if Series_Info['Pixel_Size'] !=3:
                    TIFFReader.RawModeOn()
                    
                arr = vtk.vtkStringArray()
                for i in Channel:
                    arr.InsertNextValue(os.path.join(self.path,i))
                TIFFReader.SetFileNames(arr)
                #First read the images for a particular channel
                #print "Image list=",Channel
                #ImageName=Channel[0] #Take the first tif name
                #print "Image name='%s'"%ImageName
                # Check to see whether the image name contains either
                # channels or z slices at all. If not, then we can just you
                # the filename and skip a whole bunch of processing
                
                print "Bit depth of image=",Series_Info["Bit_Depth"]
                    
                if Series_Info['Bit_Depth']==8:
                    #ImageReader.SetDataScalarTypeToUnsignedChar()
                    TIFFReader.SetDataScalarTypeToUnsignedChar()
                else:
                    raise "Only 8-bit data supported"
                TIFFReader.FileLowerLeftOff()
                TIFFReader.SetDataExtent(0,XYDim,0,XYDim,0,NumSect)
                TIFFReader.SetDataSpacing(XSpace,YSpace,ZSpace)
                
                TIFFReader.Update()
                
                
                
                ChnlVolDataLst.append(TIFFReader)#now we have a list with the imported volume data for each channel
            self.TP_CH_VolDataList.append(ChnlVolDataLst)   
            

