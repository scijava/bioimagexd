#! /usr/bin/env python
import vtk
import sys

output=vtk.vtkFileOutputWindow()
output.SetFileName("log.txt")
output.SetInstance(output)
r = vtk.vtkLSMReader()
r.DebugOn()
r.SetFileName("K:\\Data\\Selli\\selli_fading1.lsm")
#r.SetFileName("K:\\Data\\sample2.lsm")

voi=vtk.vtkExtractVOI()
voi.SetInput(r.GetOutput())
voi.SetVOI(0,511,0,511,11,11)

writer=vtk.vtkPNGWriter()
writer.SetInput(voi.GetOutput())
writer.SetFileName("fading.png")
writer.Update()
writer.Write()
print "Done, press enter!"
sys.stdin.readline()
