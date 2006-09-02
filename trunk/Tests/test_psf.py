#! /usr/bin/env python
import vtk
psf=vtk.vtkImageDiffractionPSF3D()
psf.SetDimensions(256,256,256)
psf.SetPixelSpacing(1)
psf.SetSliceSpacing(3.1)
psf.SetNormalization(2)
print psf
print psf.GetOutput()
print "Updating..."
psf.Update()
writer=vtk.vtkXMLImageDataWriter()
writer.SetInput(psf.GetOutput())
writer.SetFileName("psf.vti")
writer.Write()

#writer=vtk.vtkXMLImageDataWriter()
#shift=vtk.vtkImageShiftScale()
#shift.SetInput(psf.GetOutput())
#shift.SetOutputScalarTypeToUnsignedChar()
#shift.SetScale(255)
#shift.SetClampOverflow(1)
#writer.SetInput(shift.GetOutput())
#writer.SetFileName("psf2.vti")
#writer.Write()
