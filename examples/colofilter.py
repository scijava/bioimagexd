from lib import *

import vtk
import sys
green=Data(r"H:\\Data\\Sample1\\sample1_green0.vti")
red=Data(r"H:\\Data\\Sample1\\sample1_red0.vti")

outline=Outline(green)

# transfer function that maps scalar value to opacity
opacityTF = vtk.vtkPiecewiseFunction()
opacityTF.AddPoint(    0.0,  0.0 )
opacityTF.AddPoint(   20.0,  0.0 )
opacityTF.AddPoint(   80.0,  0.7 )
opacityTF.AddPoint(  200.0,  0.9 )
opacityTF.AddPoint(  255.0,  1.0)

# transfer functoin that maps scalar value to color
colorTransfer1 = generateColorTransferFunction(GREEN)
colorTransfer2 = generateColorTransferFunction(RED)
colorTransfer3 = generateColorTransferFunction(YELLOW)

v1=Volume(colorTransfer1,opacityTF)
v2=Volume(colorTransfer2,opacityTF)
v3=Volume(colorTransfer3,opacityTF)

yellow=Colocalization(green.data(),red.data())
yellow.start()

ren=Renderer()
ren.addVolume("green",green,v1)
ren.addVolume("red",red,v2)
ren.addVolume("yellow",yellow,v3)
#ren.setOutline(outline)
print "Rendering..."
sys.stdin.readline()
ren.start()



