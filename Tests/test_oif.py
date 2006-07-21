#! /usr/bin/env python
import vtk
PATH="/media/sda12/Data/Olympus/silicone/su8onsilicone3.oif.files/su8onsilicone3_C001Z%.3d.tif"
rdr = vtk.vtkExtTIFFReader()
rdr.SetDataExtent(0,1023,0,1023,0,42)
rdr.SetFilePattern(PATH)
rdr.SetFileNameSliceOffset(1)
rdr.Update()
data = rdr.GetOutput()

a,b = data.GetScalarRange()
scale = vtk.vtkImageShiftScale()
scale.SetShift(-a)
scale.SetScale(255.0/b)
scale.SetOutputScalarTypeToUnsignedChar()
scale.SetInput(data)

data=scale.GetOutput()

writer = vtk.vtkXMLImageDataWriter()
writer.SetFileName("/media/sda12/Data/Olympus/silicone/silicone.vti")
writer.SetInput(data)
writer.Update()
