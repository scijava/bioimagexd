#! /usr/bin/env python
import vtk
r=vtk.vtkLSMReader()
r.SetFileName("/media/sda12/Data/sample2.lsm")
r.Update()
print r.GetOutput()
