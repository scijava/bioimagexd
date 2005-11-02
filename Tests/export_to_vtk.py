#! /usr/bin/env python
import vtk
import sys
reader=vtk.vtkLSMReader()
reader.SetFileName("/Users/bioimagexd/Desktop/lsm_samples/selli_coloc1_8-bit.lsm")
reader.SetUpdateChannel(1)
reader.Update()

writer=vtk.vtkStructuredPointsWriter()
writer.SetInput(reader.GetOutput())
writer.SetFileName("coloc1.vtk")
writer.Write()
