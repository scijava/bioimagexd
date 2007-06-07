import vtkbxd
import vtk

for key,val in vtkbxd.__dict__.items():
    if key not in vtk.__dict__:
        vtk.__dict__[key]=vtkbxd.__dict__[key]
