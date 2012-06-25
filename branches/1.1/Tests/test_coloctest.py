#! /usr/bin/env python
import vtk
import sys
#import time
#import threading
#FILE="/home/kalpaha/BioImageXD/Data/sample2B.lsm"
FILE="K:\\Data\\tps.mdb\\coloc1_tp1.lsm"
#FILE="K:\\Data\\tps.mdb\\coloc1_tp9.lsm"
#FILE="K:\\Data\\tps.mdb\\coloc2_tp7.lsm"
#FILE="K:\\Data\\Sample2_b.lsm"
#FILE="C:\\BioImageXD\\Data\\selli_noise1.lsm"
#FILE="C:\\BioImageXD\\Data\\Selli_coloc2_8-bit.lsm"
#FILE="/home/kalpaha/BioImageXD/Data/Selli_coloc2_8-bit.lsm"
#FILE="/home/kalpaha/BioImageXD/Data/selli_noise9.lsm"
sys.path.insert(0,"../lib")
sys.path.insert(0,"..")
#import ImageOperations

reader=vtk.vtkLSMReader()
reader.SetFileName(FILE)
reader.SetUpdateChannel(0)
reader.SetUpdateTimePoint(0)
reader.Update()
ch1=reader.GetOutput()
reader2=vtk.vtkLSMReader()
reader2.SetFileName(FILE)
reader2.SetUpdateChannel(1)
reader2.SetUpdateTimePoint(0)
reader2.Update()
ch2=reader2.GetOutput()

def updateProgress(obj,evt):
    #print "Progress: ",obj.GetProgressText(),obj.GetProgress()
    pass
print "Now calculating P-value..."
coloctest=vtk.vtkImageColocalizationTest()
# Use costes method
coloctest.SetRandomizeZ(0)
coloctest.SetMethod(1);
coloctest.SetManualPSFSize(3);
coloctest.SetNumIterations(10);
coloctest.SetIgnoreZeroPixels(1)

coloctest.AddInput(ch1) 
coloctest.AddInput(ch2)

coloctest.AddObserver("ProgressEvent",updateProgress)
coloctest.Update()

print coloctest
data=coloctest.GetOutput()
writer=vtk.vtkXMLImageDataWriter()
name="random.vti"
print "Writing",name,"..."
writer.SetFileName(name)
writer.SetInput(data)
writer.Write()

