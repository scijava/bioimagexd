import sys
from lib import *
import vtk

green=Data(DATA_PATH+r"Sample1\\sample1_green0.vti")
red=Data(DATA_PATH+r"Sample1\\sample1_red0.vti")

outline=Outline(green)

# transfer function that maps scalar value to opacity
opacityTF = vtk.vtkPiecewiseFunction()
opacityTF.AddPoint(    0.0,  0.0 )
opacityTF.AddPoint(   20.0,  0.0 )
opacityTF.AddPoint(   80.0,  0.7 )
opacityTF.AddPoint(  200.0,  0.9 )
opacityTF.AddPoint(  255.0,  1.0)




combined=ColorMerge()
combined.addInput(green.data(),128)
combined.addInput(red.data(),128)
combined.start()
colorTransfer1=combined.getColorTransferFunction()

v1=Volume(colorTransfer1,opacityTF)


ren=Renderer()
ren.addVolume("combined",combined,v1)
ren.setOutline(outline)
ren.start()



