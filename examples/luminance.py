import sys
sys.path=sys.path[:-1]
from vtk import *

r=vtkXMLImageDataReader()
r.SetFileName("rgbvol.vti")
r.Update()

lumi=vtkImageLuminance()
data=r.GetOutput()
lumi.SetInput(data)
lumi.Update()


output=lumi.GetOutput()
print output

rgb=[]
for i in range(0,3):
    rgb.append(data.GetScalarComponentAsDouble(0,0,0,i))
print rgb
print output.GetScalarComponentAsDouble(0,0,0,0)
rgb=[]
for i in range(0,3):
    rgb.append(data.GetScalarComponentAsDouble(0,0,0,i))
print rgb
print output.GetScalarComponentAsDouble(5,5,5,0)
sys.stdin.readline()
