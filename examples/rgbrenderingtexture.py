import sys
sys.path=sys.path[:-1]
import time
import vtk

reader=vtk.vtkXMLImageDataReader();
#reader.SetFileName(r"H:\Data\merge\merge_0.vti");
reader.SetFileName(r"H:\Data\Sample1\sample1_green0.vti")
reader.Update()

# property of the volume (lighting, transfer functions)
volprop = vtk.vtkVolumeProperty()
volprop.ShadeOn()
volprop.SetInterpolationTypeToLinear()
volprop.SetSpecularPower(10.0)
volprop.SetSpecular(.7)
volprop.SetAmbient(.5)
volprop.SetDiffuse(.5)

opacity=vtk.vtkPiecewiseFunction()
opacity.AddPoint(0.0,0.0)
opacity.AddPoint(255.0,0.95)
volprop.SetScalarOpacity(opacity)

color=vtk.vtkColorTransferFunction()
color.AddRGBPoint(0.0,0,0,0)
color.AddRGBPoint(255,0,1.0,0)
volprop.SetColor(color)


ren=vtk.vtkRenderer()
ren.SetBackground(0,0,0)

volumeMapper = vtk.vtkVolumeTextureMapper2D()
#volumeMapper.DirectRGBOn()
volumeMapper.SetInput( reader.GetOutput() )

# volume is a specialized actor
volume = vtk.vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volprop)

ren.AddVolume( volume )

renWin=vtk.vtkRenderWindow()
renWin.SetSize(600,600)
renWin.AddRenderer(ren)

iren= vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)


renWin.Render()
iren.Initialize()
iren.Start()


