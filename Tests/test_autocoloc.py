#! /usr/bin/env python
import vtk
import vtkbxd
import sys
sys.path.insert(0,"../lib")
sys.path.insert(0,"..")
import ImageOperations
LSMFILE="/Users/kallepahajoki/BioImageXD/Data/sample1_single.lsm"
reader=vtk.vtkLSMReader()
reader.SetFileName(LSMFILE)
reader.SetUpdateChannel(0)
reader.Update()
ch1=reader.GetOutput()
reader2=vtk.vtkLSMReader()
reader2.SetFileName(LSMFILE)
reader2.SetUpdateChannel(1)
reader2.Update()
ch2=reader2.GetOutput()

coloc=vtk.vtkImageAutoThresholdColocalization()
coloc.AddInput(ch1)
coloc.AddInput(ch2)
coloc.Update()

print coloc

#data=coloc.GetOutput(0)
#plotdata=coloc.GetOutput(1)
#print "Plot data=",plotdata
#i=0
#writer=vtk.vtkXMLImageDataWriter()
#pdata=data.GetPointData()
#name=None
#if pdata:
#    name=pdata.GetScalars().GetName()
#    if name:#
#	name+=".vti"
#if not name:
#    name="unnamed.vti"%i
#
#print "Writing",name,"..."
#writer.SetFileName(name)
#writer.SetInput(data)
#writer.Write()

#writer=vtk.vtkXMLImageDataWriter()
#writer.SetInput(plotdata)
#writer.SetFileName("scatterplot.vti")
#writer.Write()

#lut=ImageOperations.loadLUT("../LUT/Amber.lut")

#maptocol=vtk.vtkImageMapToColors()
#maptocol.SetLookupTable(lut)
#maptocol.SetInput(plotdata)
#maptocol.Update()

#pngwriter=vtk.vtkPNGWriter()
#pngwriter.SetInput(plotdata)
#pngwriter.SetFileName("scatterplot.png")
#pngwriter.Write()
