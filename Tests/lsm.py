#! /usr/bin/env python
import vtk
r=vtk.vtkLSMReader()
r.DebugOn()
r.SetFileName("/home/kalpaha/BioImageXD/Data/selli_noise6.lsm")
r.Update()
print r.GetOutput()
