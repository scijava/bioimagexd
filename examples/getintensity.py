import vtk
from lib import *

for i in range(0,5):
    print "In dataset %d"%i
    green=Data(r"H:\\Konfokaalidataa\\Sample1\\sample1_green%d.vti"%i)
    red=Data(r"H:\\Konfokaalidataa\\Sample1\\sample1_red%d.vti"%i)
    
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
    yellow.calcAvg()
    

