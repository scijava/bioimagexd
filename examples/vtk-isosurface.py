import vtk
reader=vtk.vtkXMLImageDataReader();
reader.SetFileName(r"H:\Konfokaalidataa\Sample1\sample1_green0.vti");
reader.Update()
outline=vtk.vtkOutlineFilter()
outline.SetInput(reader.GetOutput())
outlineMapper=vtk.vtkPolyDataMapper()
outlineMapper.SetInput(outline.GetOutput())
outlineActor=vtk.vtkActor()
outlineActor.SetMapper(outlineMapper)
outlineActor.GetProperty().SetColor(1,0,0)

#isosurface=vtkContourFilter()
#isosurface.SetInput(reader.GetOutput())
#isosurface.SetValue(0,.2)
#isosurfaceMapper=vtkPolyDataMapper()
#isosurfaceMapper.SetInput(isosurface.GetOutput())
#isosurfaceMapper.SetColorModeToMapScalars()
#isosurfaceActor = vtkActor()
#isosurfaceActor.SetMapper(isosurfaceMapper)

# transfer function that maps scalar value to opacity
opacityTF = vtk.vtkPiecewiseFunction()
opacityTF.AddPoint(    0.0,  0.0 )
opacityTF.AddPoint(   20.0,  0.0 )
opacityTF.AddPoint(   80.0,  0.7 )
opacityTF.AddPoint(  200.0,  0.9 )
opacityTF.AddPoint(  250.0,  0.95)
opacityTF.AddPoint(  300.0,  1.0 )

# transfer functoin that maps scalar value to color
colorTF = vtk.vtkColorTransferFunction()
colorTF.AddRGBPoint( 20.0, 0.15, 0.4, 0.3)
colorTF.AddRGBPoint( 80.0, 0.15, 0.4, 0.3)
colorTF.AddRGBPoint(100.0, 0.3, 0.8, 0.0)
colorTF.AddRGBPoint(500.0, 0.3, 0.8, 0.0)

# property of the volume (lighting, transfer functions)
volprop = vtk.vtkVolumeProperty()
volprop.SetColor(colorTF)
volprop.SetScalarOpacity(opacityTF)
volprop.ShadeOn()
volprop.SetInterpolationTypeToLinear()
volprop.SetSpecularPower(10.0)
volprop.SetSpecular(.7)
volprop.SetAmbient(.5)
volprop.SetDiffuse(.5)

ren=vtk.vtkRenderer()
ren.SetBackground(.8,.8,.8)

# mapper
# the composite function is the line integrator
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
volumeMapper = vtk.vtkVolumeRayCastMapper()
volumeMapper.SetVolumeRayCastFunction( compositeFunction )
volumeMapper.SetInput( reader.GetOutput() )
# sample distance along each ray
volumeMapper.SetSampleDistance(.2)

# volume is a specialized actor
volume = vtk.vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volprop)

# add the actors
ren.AddVolume( volume )

scalarBar=vtk.vtkScalarBarActor()
scalarBar.SetTitle("Iso value")

renWin=vtk.vtkRenderWindow()
renWin.SetSize(400,400)
renWin.AddRenderer(ren)

iren= vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

ren.AddActor(outlineActor)
#ren.AddActor(scalarBar)

renWin.Render()
iren.Initialize()
iren.Start()


