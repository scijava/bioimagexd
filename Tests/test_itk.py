import vtk
import itk
import time
FILE="/media/sda12/Data/selli/selli_coloc1_8-bit.lsm"

t=time.time()
reader=vtk.vtkLSMReader()
reader.SetFileName(FILE)
reader.SetUpdateChannel(0)
reader.SetUpdateTimePoint(0)
medfilter = vtk.vtkImageHybridMedian2D()
medfilter.SetInput(reader.GetOutput())
print "Doing median filtering",time.time()-t
medfilter.Update()
print "done",time.time()-t
cast = vtk.vtkImageCast()
cast.SetOutputScalarTypeToFloat()
cast.SetInput(medfilter.GetOutput())

f3 = itk.Image.F3
vtktoitk=itk.VTKImageToImageFilter[f3].New()
vtktoitk.SetInput(cast.GetOutput())

print "Moving data over to ITK side",time.time()-t
vtktoitk.Update()
print "done.",time.time()-t
print "Doing gradient magnitude",time.time()-t
gradmag = itk.GradientMagnitudeImageFilter[f3,f3].New()
gradmag.SetInput(vtktoitk.GetOutput())
gradmag.Update()
print "done",time.time()-t
print "Doing watershed segmentation",time.time()-t
watershed = itk.WatershedImageFilter[f3].New()
watershed.SetInput(gradmag.GetOutput())
watershed.SetThreshold(0.01)
watershed.SetLevel(0.2)

watershed.Update()
print "done",time.time()-t
print "Moving to VTK side",time.time()-t
itktovtk=itk.ImageToVTKImageFilter[f3,f3]
itktovtk.SetInput(watershed.GetOutput())
print "done"
print "Writing data out",time.time()-t
writer = vtk.vtkXMLImageDataWriter()
writer.SetFileName("output.vti")
writer.SetInput(itktovtk.GetOutput())
writer.Write()
print "done",time.time()-t
