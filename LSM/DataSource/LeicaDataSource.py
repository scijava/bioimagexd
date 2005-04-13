# -*- coding: iso-8859-1 -*-
"""
 Unit: LeicaDataSource
 Project: BioImageXD
 Created: 12.04.2005, KP
 Description: 

 A module for reading data produced by Leica microscopes. 
 
 Intial code by Karl Garsha <garsha@itg.uiuc.edu>. 
 Modified by Kalle Pahajoki for BioImageXD use.
 
 Modified: 12.04.2005 - Created module with Karl's code as a base

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 Karl Garsha, BioImageXD Project.
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
import Image
        
from DataSource import *
        
class LeicaDataSource(DataSource):
    """
    Class: LeicaDataSource
    Created: 12.04.2005, KP
    Description: Leica format datasource
    """
    def __init__(self,filename="",experiment="",channel=-1):
        """
        Method: __init__
        Created: 12.04.2005, KP
        Description: Constructor
        """    
        self.reader = LeicaExperiment(filename)
        self.experiment = experiment
        self.channel = channel
        self.dimensions = None
        self.voxelsize = None
        self.spacing = None
        self.color = None
        
    def getDataSetCount(self):
        """
        Method: getDataSetCount
        Created: 12.04.2005, KP
        Description: Returns the number of individual DataSets (=time points)
        managed by this DataSource
        """
        return self.reader.GetNumberOfTimepoints(self.experiment)
        
    def getDataSet(self, i):
        """
        Method: getDataSet
        Created: 12.04.2005, KP
        Description: Returns the DataSet at the specified index
        Parameters:   i       The index
        """
        return self.reader.GetTimepoint(self.experiment,self.channel,i)
        
    def getDimensions(self):
        """
        Method: getDimensions()
        Created: 12.04.2005, KP
        Description: Returns the (x,y,z) dimensions of the datasets this 
                     dataunit contains
        """
        if not self.dimensions:
            self.dimensions=self.reader.GetDimensions(self.experiment)
            print "Got dimensions=",self.dimensions
        return self.dimensions
        
    def getSpacing(self):
        """
        Method: getSpacing()
        Created: 12.04.2005, KP
        Description: Returns the spacing of the datasets this 
                     dataunit contains
        """
        if not self.spacing:
            # TODO: Is this ok
            self.spacing = self.getVoxelSize()
            #data=self.getDataSet(0)
            #self.spacing=data.GetSpacing()
        return self.spacing
        
    def getVoxelSize(self):
        """
        Method: getVoxelSize()
        Created: 12.04.2005, KP
        Description: Returns the voxel size of the datasets this 
                     dataunit contains
        """
        if not self.voxelsize:
            self.voxelsize = self.reader.GetVoxelSize(self.experiment)
            print "Got voxel size=",self.voxelsize
        return self.voxelsize
    
    def loadFromFile(self, filename):
        """
        Method: loadFromFile
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
            print "There are %d channels in %s"%(channelNum,filename)
            for i in range(channelNum):
                # We create a datasource with specific channel number that
                #  we can associate with the dataunit
                
                datasource=LeicaDataSource(filename,experiment,i)
                dataunit=DataUnit.DataUnit.DataUnit()
                dataunit.setDataSource(datasource)
                dataunits.append((experiment,dataunit))
            
        return dataunits


    def getName(self):
        """
        Method: getName
        Created: 18.11.2005, KP
        Description: Returns the name of the dataset series which this datasource
                     operates on
        """
        return "Ch%.2d"%self.channel

    def getColor(self):
        """
        Method: getColor()
        Created: 27.03.2005, KP
        Description: Returns the color of the dataset series which this datasource
                     operates on
        """
        if not self.color:
            self.color=self.reader.GetColor(self.experiment,self.channel)
        return self.color

        
class LeicaExperiment:
    def __init__ (self, ExpPathTxt):
        self.SeriesDict={}
        self.path=""
        self.setFileName(ExpPathTxt)
        self.TP_CH_VolDataList=[]
        
    def setFileName(self,filename):
        """
        Method: setFileName()
        Created: 12.04.2005, KP
        Description: Sets the file name to be opened
        """
        self.filename=filename
        if filename:
            self.path=os.path.dirname(filename)
            self.Read()
    
    def Read(self):
        """
        Method: Read()
        Created: 12.04.2005, KP
        Description: Read the given file
        """    
        self.CreateExpDataStruct(self.filename)
        
    def GetExperiments(self):
        """
        Method: Get_Experiments()
        Created: 12.04.2005, KP
        Description: Return the number of channels this dataset contains
        """    
        return self.SeriesDict.keys()

    def GetNumberOfChannels(self,experiment):
        """
        Method: GetNumberOfChannels(experiment)
        Created: 12.04.2005, KP
        Description: Return the number of channels an experiment contains
        """    
        return self.SeriesDict[experiment]["NumChan"]

    def GetNumberOfTimepoints(self,experiment):
        """
        Method: GetNumberOfTimepoints(experiment)
        Created: 12.04.2005, KP
        Description: Return the number of channels an experiment contains
        """
        print self.SeriesDict.keys()
        return self.SeriesDict[experiment]["Num_T"]
        
    def GetDimensions(self,experiment):
        """
        Method: GetDimensions(experiment)
        Created: 12.04.2005, KP
        Description: Return dimensions of an experiment
        """    
        x=self.SeriesDict[experiment]["Resolution_X"]   
        y=self.SeriesDict[experiment]["Resolution_Y"]   
        z=self.SeriesDict[experiment]["Number_Sections"]   
        return (x,y,z)
        
    def GetColor(self,experiment,channel):
        """
        Method: GetColor(experiment,channel)
        Created: 12.04.2005, KP
        Description: Return the data for a given timepoint
        """    
        if len(self.TP_CH_VolDataList) == 0:
            self.ReadLeicaVolData(experiment)

        channels=self.TP_CH_VolDataList[0]
        rdr=channels[channel]
        rdr.ComputeInternalFileName(0)
        filename=rdr.GetInternalFileName()
        img=Image.open(filename)
        palette=img.palette.getdata()[1]
        r=palette[255]
        g=palette[2*256-1]
        b=palette[3*256-1]
        return ord(r),ord(g),ord(b)

    def GetTimepoint(self,experiment,channel,timepoint):
        """
        Method: GetTimepoint(experiment,channel,timepoint)
        Created: 12.04.2005, KP
        Description: Return the data for a given timepoint
        """    
        if len(self.TP_CH_VolDataList) == 0:
            self.ReadLeicaVolData(experiment)

        channels=self.TP_CH_VolDataList[timepoint]
        rdr=channels[channel]
        rdr.Update()
        return rdr.GetOutput()
        
    def GetVoxelSize(self,experiment):
        """
        Method: GetVoxelSize(experiment)
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

    def Extract_Series_Info(self):
        self.SeriesDict={}
        RE_ScanMode=re.compile(r'ScanMode.*',re.I)
        RE_X=re.compile(r'Format-Width.+\d+',re.I)
        RE_Y=re.compile(r'Format-Height.+\d+',re.I)
        RE_NumChan=re.compile(r'Dimension_2.*',re.I)
        RE_LogicalSize=re.compile(r'Logical\sSize.+\d+',re.I)
        RE_NumSect=re.compile(r'Dimension_3.*',re.I)
        RE_T=re.compile(r'Dimension_4.*',re.I)
        RE_SeriesName=re.compile(r'Series\sName:.*',re.I)
        RE_Width=re.compile(r'Size-Width.+\d+',re.I)
        RE_Height=re.compile(r'Size-Height.+\d+',re.I)
        RE_Depth=re.compile(r'Size-Depth.+\d+',re.I)
        RE_VoxelWidth=re.compile(r'Voxel-Width.+\d+',re.I)
        RE_VoxelHeight=re.compile(r'Voxel-Height.+\d+',re.I)
        RE_VoxelDepth=re.compile(r'Voxel-Depth.+\d+',re.I)
        RE_Bit_Depth=re.compile(r'Resolution.+\d+',re.I)
        RE_NonWhitespace=re.compile(r'\w+',re.I)
        
        for string in self.Series_Data_List:
            Series_Data=string
            Series_Info={}
            #Now we get the scan mode (eg. xyz)
            SeriesScanModeLine=RE_ScanMode.search(Series_Data)
            SeriesScanModeSplit=SeriesScanModeLine.group(0).split()
            SeriesScanMode=SeriesScanModeSplit[1].strip()
            Series_Info['Scan_Mode']=SeriesScanMode
            if SeriesScanMode=='xyz' or SeriesScanMode=='xyzt':
                #Get the numchan-dimension value
                SeriesDataSplit=RE_NumChan.split(Series_Data)
                NumChan_String=SeriesDataSplit[1]
                NumChanMatch=RE_LogicalSize.search(NumChan_String)
                NumChanLine=NumChanMatch.group(0)
                WordsNumChan=NumChanLine.split()
                WordsNumChan.reverse()
                NumChan=int(WordsNumChan[0].strip())
                Series_Info['NumChan']=NumChan
                Series_Data=SeriesDataSplit[1] #Breaks data text into progressively smaller pieces
                #Get the z-dimension value
                SeriesDataSplit=RE_NumSect.split(Series_Data)
                NumSect_String=SeriesDataSplit[1]
                NumSectMatch=RE_LogicalSize.search(NumSect_String)
                NumSectLine=NumSectMatch.group(0)
                WordsZ_Res=NumSectLine.split()
                WordsZ_Res.reverse()
                Z_Res=int(WordsZ_Res[0].strip())
                Series_Info['Number_Sections']=Z_Res
                Series_Data=SeriesDataSplit[1] #Breaks data text into progressively smaller pieces
                #Check for Time dimension--if so, get time data
                if RE_T.match(Series_Data):
                    SeriesDataSplit=RE_T.split(Series_Data)
                    T_String=SeriesDataSplit[1]
                    T_Match=RE_LogicalSize.search(NumSect_String)
                    T_Line=T_Match.group(0)
                    WordsNumT=T_Line.split()
                    WordsNumT.reverse()
                    NumT=int(WordsNumT[0].strip())
                    Series_Info['Num_T']=NumT
                    Series_Data=SeriesDataSplit[1]
                else:
                    Series_Info['Num_T']=1
                #Now we get the series name
                SeriesNameString=RE_SeriesName.search(Series_Data)
                SeriesNameLine=SeriesNameString.group(0)
                SeriesNameSplit=SeriesNameLine.split()
                SeriesNameSplit.reverse()
                SeriesNameTxtString=RE_NonWhitespace.search(SeriesNameSplit[0].strip())#this is intended to get the alpha-num. char values and drop the newlines
                SeriesName=SeriesNameTxtString.group(0)# should return the series name w/o newline
                Series_Info['Series_Name']=SeriesName #It works! Holy toledo-what a pain in butt.
                
                #Now we get the series width_x
                SeriesWidthString=RE_Width.search(Series_Data)
                SeriesWidthLine=SeriesWidthString.group(0)
                SeriesWidthSplit=SeriesWidthLine.split()
                SeriesWidthSplit.reverse()
                SeriesWidth=float(SeriesWidthSplit[0])
                Series_Info['Width_X']=SeriesWidth
                #Now we get the series height_y
                SeriesHeightString=RE_Height.search(Series_Data)
                SeriesHeightLine=SeriesHeightString.group(0)
                SeriesHeightSplit=SeriesHeightLine.split()
                SeriesHeightSplit.reverse()
                SeriesHeight=float(SeriesHeightSplit[0].strip())
                Series_Info['Height_Y']=SeriesHeight
                #Now we get the series depth_z
                SeriesDepthString=RE_Depth.search(Series_Data)
                SeriesDepthLine=SeriesDepthString.group(0)
                SeriesDepthSplit=SeriesDepthLine.split()
                SeriesDepthSplit.reverse()
                SeriesDepth=float(SeriesDepthSplit[0].strip())
                Series_Info['Depth_Z']=SeriesDepth
                #Now we get the series voxel_width
                SeriesVoxelWidthString=RE_VoxelWidth.search(Series_Data)
                SeriesVoxelWidthLine=SeriesVoxelWidthString.group(0)
                SeriesVoxelWidthSplit=SeriesVoxelWidthLine.split()
                SeriesVoxelWidthSplit.reverse()
                SeriesVoxelWidth=float(SeriesVoxelWidthSplit[0].strip())
                Series_Info['Voxel_Width_X']=SeriesVoxelWidth
                #Now we get the series voxel_height
                SeriesVoxelHeightString=RE_VoxelHeight.search(Series_Data)
                SeriesVoxelHeightLine=SeriesVoxelHeightString.group(0)
                SeriesVoxelHeightSplit=SeriesVoxelHeightLine.split()
                SeriesVoxelHeightSplit.reverse()
                SeriesVoxelHeight=float(SeriesVoxelHeightSplit[0].strip())
                Series_Info['Voxel_Height_Y']=SeriesVoxelHeight
                #Now we get the series voxel_depth
                SeriesVoxelDepthString=RE_VoxelDepth.search(Series_Data)
                SeriesVoxelDepthLine=SeriesVoxelDepthString.group(0)
                SeriesVoxelDepthSplit=SeriesVoxelDepthLine.split()
                SeriesVoxelDepthSplit.reverse()
                SeriesVoxelDepth=float(SeriesVoxelDepthSplit[0].strip())
                Series_Info['Voxel_Depth_Z']=SeriesVoxelDepth
                #Now we get the series bit_depth
                SeriesBitDepthString=RE_Bit_Depth.search(Series_Data)
                SeriesBitDepthLine=SeriesBitDepthString.group(0)
                SeriesBitDepthSplit=SeriesBitDepthLine.split()
                SeriesBitDepthSplit.reverse()
                SeriesBitDepth=float(SeriesBitDepthSplit[0].strip())
                Series_Info['Bit_Depth']=SeriesBitDepth	
                #Now we get the series res_x
                SeriesResXString=RE_X.search(Series_Data)
                SeriesResXLine=SeriesResXString.group(0)
                SeriesResXSplit=SeriesResXLine.split()
                SeriesResXSplit.reverse()
                SeriesResX=int(SeriesResXSplit[0].strip())
                Series_Info['Resolution_X']=SeriesResX
                #Now we get the series res_y
                SeriesResYString=RE_Y.search(Series_Data)
                SeriesResYLine=SeriesResYString.group(0)
                SeriesResYSplit=SeriesResYLine.split()
                SeriesResYSplit.reverse()
                SeriesResY=int(SeriesResYSplit[0].strip())
                Series_Info['Resolution_Y']=SeriesResY
                
                #make a dictionary containing each series info dictionary (dictionary of dictionaries)
                SeriesName=Series_Info['Series_Name']
                self.SeriesDict[SeriesName]=Series_Info

    def Create_Tiff_Lists(self):
        for key, value in self.SeriesDict.items():
            Series_Info=value
            Series_Name=key
            Num_T_Points=(Series_Info['Num_T'])
            TimePoints=[]
            for a in xrange(Num_T_Points): #starts at 0 and counts up to (but not including) Num_T_Points.
                TP_Name='_t'+str((a%10000)//1000)+str((a%1000)//100)+str((a%100)//10)+str((a%10)//1)
                Num_Chan=Series_Info['NumChan']
                Channels=[]
                for b in xrange(Num_Chan):
                    File_List=[]
                    CH_Name=('_ch'+str((b%100)//10)+str((b%10)//1))
                    Num_Z_Sec=Series_Info['Number_Sections']
                    for c in xrange(Num_Z_Sec):
                        Z_Name=str('_z'+str((c%1000)//100)+str((c%100)//10)+str((c%10)//1))
                        if Num_T_Points > 1:
                            Slice_Name = self.ExpName + '_' + Series_Name + TP_Name + Z_Name + CH_Name + '.tif'
                        else:
                            Slice_Name = self.ExpName + '_' + Series_Name + Z_Name + CH_Name + '.tif'
                        File_List.append(Slice_Name)
                    Channels.append(File_List)
                TimePoints.append(Channels)
            Series_Info['TiffList']=TimePoints
            self.SeriesDict[Series_Name]=Series_Info #puts modified Series_Info dictionary back into SeriesDict

    def CreateExpDataStruct(self,ExpPathTxt):
        self.Sep_Series(ExpPathTxt)
        self.Extract_Series_Info()
        self.Create_Tiff_Lists()

    #this is a work in progress and hasn't been tested
    def ExportVTKVol_VTK(self,Series_Name):
        VTK_Writer=vtk.vtkStructuredPointsWriter()
        if len(self.TP_CH_VolDataList) == 0:
            self.ReadLeicaVolData(Series_Name)
        for TimePoint in self.TP_CH_VolDataList:
            for Channel in Timepoint:
                VTK_Writer.SetInput(Channel.GetOutput())
                VTK_Writer.SetFileName(Series_Name +'_t_'+str(self.TP_CH_VolDataList.index(TimePoint)%100//10)+str(self.TP_CH_VolDataList.index(TimePoint)%10//1)+'_ch_'+str(TimePoint.index(Channel)%100//10)+str(TimePoint.index(Channel)%10//1))
                VTK_Writer.SetFileTypeToBinary()
                VTK_Writer.Update()
                VTK_Writer.Write()
            
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
                ImageReader=vtk.vtkImageReader()
                TIFFReader=vtk.vtkTIFFReader()
                #First read the images for a particular channel
                ImageName=Channel[0] #Take the first tif name
                #RE_zsplit=re.compile(r'.+_z000.+',re.I)  #split the filename at the z position, exising the z-pos variable
                RE_FilePrefix=re.compile(r'.+_z',re.I) #match for the file prefix
                RE_FilePostfix=re.compile(r'_ch\d+.tif',re.I) #search for the end part of the file name
                FilePrefixMatch=re.match(RE_FilePrefix,ImageName)
                ImagePrefix=string.strip(FilePrefixMatch.group(0))#we match the first part of the filename (above), then get the matched string
                FilePostfixSearch=re.search(RE_FilePostfix,ImageName)
                FilePostfixGroup=FilePostfixSearch.group(0)#this gives us the string found by the search
                ImagePattern='%s%03i'+str(FilePostfixGroup) #fsprint stuff--string+3 int spaces padded w/ zeros+last part of name eg. "_ch00.tif"
                if FilePrefixMatch != None:
                    #print "self.path=",self.path
                    ImagePrefix=os.path.join(self.path,ImagePrefix)
                    #print "Using image prefix=",ImagePrefix
                    ImageReader.SetFilePrefix(ImagePrefix)
                    TIFFReader.SetFilePrefix(ImagePrefix) 
                if FilePostfixSearch != None:
                    ImageReader.SetFilePattern(ImagePattern)
                    TIFFReader.SetFilePattern(ImagePattern)
                if Series_Info['Bit_Depth']==8:
                    ImageReader.SetDataScalarTypeToUnsignedChar()
                    TIFFReader.SetDataScalarTypeToUnsignedChar()
                else:
                    raise "Only 8-bit data supported"
                #print ImageReader
                #ImageReader.SetDataByteOrderToLittleEndian()
                ImageReader.FileLowerLeftOff()
                ImageReader.SetDataOrigin(0.0,0.0,0.0)
                ImageReader.SetNumberOfScalarComponents(1)
                TIFFReader.SetNumberOfScalarComponents(1)
                #ImageReader.SetDataScalarTypeToUnsignedChar()
                ImageReader.SetDataExtent(0,XYDim,0,XYDim,0,NumSect)
                TIFFReader.SetDataExtent(0,XYDim,0,XYDim,0,NumSect)
                ImageReader.SetDataSpacing(XSpace,YSpace,ZSpace)
                TIFFReader.SetDataSpacing(XSpace,YSpace,ZSpace)
                TIFFReader.Update()
                ImageReader.Update()
                
                
                hsiz=TIFFReader.GetHeaderSize()
                if hsiz>0:
                    ImageReader.SetHeaderSize(hsiz)
                ImageReader.Update() #necessary--used when incremental changes are made to ImageReader properties
                #print "Output=",TIFFReader.GetOutput()
                #print "Output=",ImageReader.GetOutput()
                ChnlVolDataLst.append(ImageReader)#now we have a list with the imported volume data for each channel
            self.TP_CH_VolDataList.append(ChnlVolDataLst)	
            
        #used for testing image reader behavior on different platforms
        #def ViewSampleImage(self,Series_Name):
        #Series_Info=self.SeriesDict[Series_Name]
        #TiffList=Series_Info['TiffList']
        #XYDim=Series_Info['Resolution_X']-1
        #XSpace=Series_Info['Voxel_Width_X']
        #YSpace=Series_Info['Voxel_Height_Y']
        #ZSpace=Series_Info['Voxel_Depth_Z']
        #ImageReader.SetDataSpacing(XSpace,YSpace,ZSpace)
        #self.TP_CH_VolDataList=[] #contains the vol data for each timepoint, each channel
        #TimePoint = TiffList[0]
        #Channel = TimePoint[1]
        #ImageReader=vtk.vtkImageReader()
        #if Series_Info['Bit_Depth']==8:
            #ImageReader.SetDataScalarTypeToUnsignedChar()
        #else:
            #pass
        #ImageReader.SetDataByteOrderToLittleEndian()
        #ImageReader.SetNumberOfScalarComponents(1)
        #ImageReader.SetDataExtent(0,XYDim,0,XYDim,0,0)
        #ImageReader.SetDataSpacing(XSpace,YSpace,ZSpace)
        #First read the images for a particular channel
        #ImageName=Channel[4] #Take the first tif name
        #ImageReader.SetFileName(ImageName)
        #ImageReader.Update() 
        #Viewer=vtk.vtkImageViewer()
        #Viewer.SetInput(ImageReader.GetOutput())
        #Viewer.Render()
