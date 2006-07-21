#! /usr/bin/env python
import vtk
import time
PATH="/media/sda12/Data/Olympus/silicone/su8onsilicone3.oif.files/su8onsilicone3_C001Z%.3d.tif"
t=time.time()
written=1
TIMES=40
for i in range(0,TIMES):
    rdr = vtk.vtkExtTIFFReader()
    rdr.SetDataExtent(0,1023,0,1023,0,42)
    rdr.SetFilePattern(PATH)
    rdr.SetFileNameSliceOffset(1)
    rdr.Update()
    data = rdr.GetOutput()
    if not written:
	writer = vtk.vtkXMLImageDataWriter()
	writer.SetFileName("koe.vti")
	writer.SetInput(data)
	writer.Write()	
	del writer
	written=1
    del data
    del rdr
    
    
t2=time.time()
print "Time it took to read OIF %d times="%TIMES,t2-t
print "Average: ",(t2-t)/float(TIMES)
t=time.time()
written=1
for i in range(0,TIMES):
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName("/media/sda12/Data/Olympus/silicone/silicone.vti")
    reader.Update()
    data = reader.GetOutput()
    if not written:
	written=1
	writer = vtk.vtkXMLImageDataWriter()
	writer.SetFileName("koe2.vti")
	writer.SetInput(data)
	writer.Write()
	del writer
    del data
    del reader
t2=time.time()    
print "Time it took to read VTI %d times="%TIMES,t2-t
print "Average: ",(t2-t)/float(TIMES)
