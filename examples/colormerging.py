import vtk
from lib import *

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

# transfer functoin that maps scalar value to color
colorTransfer1 = vtk.vtkColorTransferFunction()
colorTransfer1.AddRGBPoint(1,0,1,0)
colorTransfer1.AddRGBPoint(2,1,0,0)
colorTransfer1.AddRGBPoint(3,1,1,0)
colorTransfer1.SetVectorComponent(2)


v1=Volume(colorTransfer1,opacityTF)

combined=ColorCombination(green.data(),red.data())
combined.start()

ren=Renderer()
ren.addVolume("combined",combined,v1)
ren.setOutline(outline)
ren.start()



