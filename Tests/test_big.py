#! /usr/bin/env python
import vtk
import time

D="<ENTER FILE NAME HERE>"
t=time.time()
def elapsed():
    global t
    return "(%.2fs elapsed)"%(time.time()-t)

r1=vtk.vtkLSMReader()
r1.SetFileName(D)
r2=vtk.vtkLSMReader()
r2.SetFileName(D)
r1.SetUpdateChannel(0)
r2.SetUpdateChannel(1)
d1=r1.GetOutput()
d2=r2.GetOutput()

print "Reading data"
r1.Update()
r2.Update()


itf1=vtk.vtkIntensityTransferFunction()
itf2=vtk.vtkIntensityTransferFunction()

ctf1=vtk.vtkColorTransferFunction()
ctf1.AddRGBPoint(0,0,0,0)
ctf1.AddRGBPoint(255.0,0,1.0,0)


ctf2=vtk.vtkColorTransferFunction()
ctf2.AddRGBPoint(0,0,0,0)
ctf2.AddRGBPoint(255.0,1.0,0,0)


print "Feeding channels to merge ",elapsed()
merge = vtk.vtkImageColorMerge()
#merge.SetNumberOfThreads(5)
merge.AddInput(d1)
merge.AddInput(d2)
merge.AddLookupTable(ctf1)
merge.AddLookupTable(ctf2)
merge.AddIntensityTransferFunction(itf1)
merge.AddIntensityTransferFunction(itf2)

merge.Update()
print "Merging done",elapsed()

mip=vtk.vtkImageSimpleMIP()
#mip.DebugOn()
print "Feeding merge to MIP",elapsed()
mip.SetInput(merge.GetOutput())
mip.Update()

print "Writing MIP out...",elapsed()
writer=vtk.vtkPNGWriter()
writer.SetFileName("Selli_BIG.png")
writer.SetInput(mip.GetOutput())
#writer.SetInput(mip.GetOutput())

writer.Update()
writer.Write()
print "Wrote PNG ",elapsed()
