
""" 
    Kolokalisaatiodemo v.0

    Karkea, toimii jotenkin, kommentointi puuttuu etc.
"""

import vtk

reader_red=vtk.vtkXMLImageDataReader();
reader_red.SetFileName(r"H:\Konfokaalidataa\Sample1\sample1_red0.vti");
reader_red.Update()

reader_green=vtk.vtkXMLImageDataReader();
reader_green.SetFileName(r"H:\Konfokaalidataa\Sample1\sample1_green0.vti");
reader_green.Update()

outline=vtk.vtkOutlineFilter()
outline.SetInput(reader_red.GetOutput())
outlineMapper=vtk.vtkPolyDataMapper()
outlineMapper.SetInput(outline.GetOutput())
outlineActor=vtk.vtkActor()
outlineActor.SetMapper(outlineMapper)
outlineActor.GetProperty().SetColor(1,1,1)


image_kolo = vtk.vtkImageData()
image_kolo.CopyStructure(reader_red.GetOutput())
#image_kolo.

image_red=reader_red.GetOutput()
lkmp = image_kolo.GetNumberOfPoints()
lkmc = image_kolo.GetNumberOfCells()
dims = image_red.GetDimensions()

image_green=reader_green.GetOutput()

print lkmp
print lkmc
#print dims

#print image.GetScalarTypeAsString()
#print image.GetNumberOfScalarComponents()

# And the magic...
for x in range(0,dims[0]):
    for y in range(0,dims[1]):
        for z in range(0,dims[2]):
            scal_red=image_red.GetScalarComponentAsFloat(x,y,z,0)
            scal_green=image_green.GetScalarComponentAsFloat(x,y,z,0)
            if scal_red>4 and scal_green>4:
               image_kolo.SetScalarComponentFromFloat(x,y,z,0,255)
               #print "At %d,%d,%d scalar = %f"%(x,y,z,scal)


#isosurface=vtkContourFilter()
#isosurface.SetInput(reader_red.GetOutput())
#isosurface.SetValue(0,.2)
#isosurfaceMapper=vtkPolyDataMapper()
#isosurfaceMapper.SetInput(isosurface.GetOutput())
#isosurfaceMapper.SetColorModeToMapScalars()
#isosurfaceActor = vtkActor()
#isosurfaceActor.SetMapper(isosurfaceMapper)

# transfer function that maps scalar value to opacity
opacityTF = vtk.vtkPiecewiseFunction()
opacityTF.AddPoint(    0.0,  0.0 )
#opacityTF.AddPoint(   20.0,  0.0 )
#opacityTF.AddPoint(   80.0,  0.7 )
#opacityTF.AddPoint(  200.0,  0.9 )
opacityTF.AddPoint(  255.0,  0.7)

# transfer functoin that maps scalar value to color
colorTF_red = vtk.vtkColorTransferFunction()
colorTF_red.AddRGBPoint( 0.0, 0.2, 0.0, 0.0)
colorTF_red.AddRGBPoint(255.0, 1.0, 0.0, 0.0)

# transfer functoin that maps scalar value to color
colorTF_green = vtk.vtkColorTransferFunction()
colorTF_green.AddRGBPoint( 0.0, 0.0, 0.2, 0.0)
colorTF_green.AddRGBPoint(255.0, 0.0, 1.0, 0.0)

# transfer functoin that maps scalar value to color
colorTF_kolo = vtk.vtkColorTransferFunction()
colorTF_kolo.AddRGBPoint( 0.0, 0.2, 0.2, 0.2)
colorTF_kolo.AddRGBPoint(255.0, 1.0, 1.0, 1.0)


# property of the volume (lighting, transfer functions)
volprop_red = vtk.vtkVolumeProperty()
volprop_red.SetColor(colorTF_red)
volprop_red.SetScalarOpacity(opacityTF)
volprop_red.ShadeOn()
volprop_red.SetInterpolationTypeToLinear()
volprop_red.SetSpecularPower(10.0)
volprop_red.SetSpecular(.7)
volprop_red.SetAmbient(.5)
volprop_red.SetDiffuse(.5)

# property of the volume (lighting, transfer functions)
volprop_green = vtk.vtkVolumeProperty()
volprop_green.SetColor(colorTF_green)
volprop_green.SetScalarOpacity(opacityTF)
volprop_green.ShadeOn()
volprop_green.SetInterpolationTypeToLinear()
volprop_green.SetSpecularPower(10.0)
volprop_green.SetSpecular(.7)
volprop_green.SetAmbient(.5)
volprop_green.SetDiffuse(.5)

# property of the volume (lighting, transfer functions)
volprop_kolo = vtk.vtkVolumeProperty()
volprop_kolo.SetColor(colorTF_kolo)
volprop_kolo.SetScalarOpacity(opacityTF)
volprop_kolo.ShadeOn()
volprop_kolo.SetInterpolationTypeToLinear()
volprop_kolo.SetSpecularPower(10.0)
volprop_kolo.SetSpecular(.7)
volprop_kolo.SetAmbient(.5)
volprop_kolo.SetDiffuse(.5)


ren=vtk.vtkRenderer()
ren.SetBackground(.0,.0,.0)

# mapper
# the composite function is the line integrator
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
volumeMapper_red = vtk.vtkVolumeRayCastMapper()
volumeMapper_red.SetVolumeRayCastFunction( compositeFunction )
volumeMapper_red.SetInput( reader_red.GetOutput() )
# sample distance along each ray
volumeMapper_red.SetSampleDistance(.2)

# volume is a specialized actor
volume_red = vtk.vtkVolume()
volume_red.SetMapper(volumeMapper_red)
volume_red.SetProperty(volprop_red)


# mapper
# the composite function is the line integrator
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
volumeMapper_green = vtk.vtkVolumeRayCastMapper()
volumeMapper_green.SetVolumeRayCastFunction( compositeFunction )
volumeMapper_green.SetInput( reader_red.GetOutput() )
# sample distance along each ray
volumeMapper_green.SetSampleDistance(.2)

# volume is a specialized actor
volume_green = vtk.vtkVolume()
volume_green.SetMapper(volumeMapper_green)
volume_green.SetProperty(volprop_green)


# mapper
# the composite function is the line integrator
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
volumeMapper_kolo = vtk.vtkVolumeRayCastMapper()
volumeMapper_kolo.SetVolumeRayCastFunction( compositeFunction )
volumeMapper_kolo.SetInput( image_kolo )
# sample distance along each ray
volumeMapper_kolo.SetSampleDistance(.2)

# volume is a specialized actor
volume_kolo = vtk.vtkVolume()
volume_kolo.SetMapper(volumeMapper_kolo)
volume_kolo.SetProperty(volprop_kolo)

# add the actors, vain kolokalisaatio p‰‰ll‰, hidastui liikaa
#ren.AddVolume( volume_red )
#ren.AddVolume( volume_green )
ren.AddVolume( volume_kolo )

scalarBar=vtk.vtkScalarBarActor()
scalarBar.SetTitle("Iso value")

renWin=vtk.vtkRenderWindow()
renWin.SetSize(600,600)
renWin.AddRenderer(ren)

iren= vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

ren.AddActor(outlineActor)
#ren.AddActor(scalarBar)

renWin.Render()
iren.Initialize()
iren.Start()


