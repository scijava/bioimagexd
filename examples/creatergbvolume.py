import sys
sys.path.remove("C:\\Python23\\lib\\site-packages\\vtk_python")

import vtk
from Numeric import *
import time


print "Reading..."
t1=time.time()
greenreader=vtk.vtkXMLImageDataReader()
greenreader.SetFileName(r"H:\Data\Sample1\sample1_green0.vti")
greenreader.Update()
green=greenreader.GetOutput()

newdata=vtk.vtkImageData()
newdata.SetDimensions(green.GetDimensions())
newdata.SetExtent(green.GetExtent())
newdata.SetScalarTypeToUnsignedChar()
newdata.SetNumberOfScalarComponents(4)
newdata.AllocateScalars()

xd,yd,zd=newdata.GetDimensions()
print "Dims = %d,%d,%d"%(xd,yd,zd)
for x in range(xd):
    for y in range(yd):
        for z in range(zd):
            data=green.GetScalarComponentAsDouble(x,y,z,0)
            newdata.SetScalarComponentFromDouble(x,y,z,0,0)
            newdata.SetScalarComponentFromDouble(x,y,z,1,data)
            newdata.SetScalarComponentFromDouble(x,y,z,2,2)
#            newdata.SetScalarComponentFromDouble(x,y,z,3,data)

writer=vtk.vtkXMLImageDataWriter()
writer.SetFileName("rgbvol.vti")
writer.SetInput(newdata)
writer.Write()


