import sys
sys.path=sys.path[:-1]
sys.path.insert(0,r"C:\mytemp\vtk\bin")
sys.path.insert(0,r"C:\mytemp\vtk\Wrapping\Python")
import time
import vtk



reader=vtk.vtkXMLImageDataReader();
reader.SetFileName(r"C:\Mytemp\merging_0.vti");



# property of the volume (lighting, transfer functions)
volprop = vtk.vtkVolumeProperty()
volprop.ShadeOn()
volprop.SetInterpolationTypeToLinear()
volprop.SetSpecularPower(10.0)
volprop.SetSpecular(.7)
volprop.SetAmbient(.5)
volprop.SetDiffuse(.5)


ren=vtk.vtkRenderer()
ren.SetBackground(1,1,1)

# mapper
# the composite function is the line integrator
compositeFunction = vtk.vtkVolumeRayCastRGBCompositeFunction()
volumeMapper = vtk.vtkVolumeRayCastMapper()
volumeMapper.SetVolumeRayCastFunction( compositeFunction )
volumeMapper.SetInput( reader.GetOutput() )
# sample distance along each ray
volumeMapper.SetSampleDistance(.2)

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


