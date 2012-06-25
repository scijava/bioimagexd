import vtk

itf1=vtk.vtkIntensityTransferFunction()
itf2=vtk.vtkIntensityTransferFunction()

print itf1.IsIdentical()
print itf2.IsIdentical()

