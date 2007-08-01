#! /usr/bin/env python
import vtk
import sys
sys.path.insert(0,"../lib")
sys.path.insert(0,"..")
import ImageOperations

reader=vtk.vtkLSMReader()
reader.SetFileName("/home/kalpaha/BioImageXD/Data/sample2.lsm")
reader.SetUpdateChannel(0)
reader.SetUpdateTimePoint(5)
reader.Update()
ch1=reader.GetOutput()
reader2=vtk.vtkLSMReader()
reader2.SetFileName("/home/kalpaha/BioImageXD/Data/sample2.lsm")
reader2.SetUpdateChannel(1)
reader2.SetUpdateTimePoint(5)
reader2.Update()
ch2=reader2.GetOutput()



#w1=vtk.vtkXMLImageDataWriter()
#w1.SetFileName("Ch1.vti")
#w1.SetInput(ch1)
#w1.Write()
#w2=vtk.vtkXMLImageDataWriter()
#w2.SetFileName("Ch2.vti")
#w2.SetInput(ch2)
#w2.Write()

coloc=vtk.vtkImageAutoThresholdColocalization()
coloc.AddInput(ch1)
coloc.AddInput(ch2)
coloc.Update()

print coloc

data=coloc.GetOutput(0)
plotdata=coloc.GetOutput(1)
print "Plot data=",plotdata
i=0
writer=vtk.vtkXMLImageDataWriter()
pdata=data.GetPointData()
name=None
if pdata:
    name=pdata.GetScalars().GetName()
    if name:
	name+=".vti"
if not name:
    name="unnamed.vti"%i

print "Writing",name,"..."
writer.SetFileName(name)
writer.SetInput(data)
writer.Write()

writer=vtk.vtkXMLImageDataWriter()
writer.SetInput(plotdata)
writer.SetFileName("scatterplot.vti")
writer.Write()

lut=ImageOperations.loadLUT("../LUT/Amber.lut")

maptocol=vtk.vtkImageMapToColors()
maptocol.SetLookupTable(lut)
maptocol.SetInput(plotdata)
maptocol.Update()

pngwriter=vtk.vtkPNGWriter()
#pngwriter.SetInput(maptocol.GetOutput())
pngwriter.SetInput(plotdata)
pngwriter.SetFileName("scatterplot.png")
pngwriter.Write()
