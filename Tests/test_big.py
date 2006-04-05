#! /usr/bin/env python
import vtk
import time
t=time.time()
def elapsed():
    global t
    return "(%.2fs elapsed)"%(time.time()-t)

r1=vtk.vtkLSMReader()
r1.SetFileName("/media/sda12/Data/selli/Selli_BIG.lsm")
r2=vtk.vtkLSMReader()
r2.SetFileName("/media/sda12/Data/selli/Selli_BIG.lsm")
r1.SetUpdateChannel(0)
r2.SetUpdateChannel(1)
d1=r1.GetOutput()
d2=r2.GetOutput()

merge = vtk.vtkImageMerge()


ctf1=vtk.vtkColorTransferFunction()
ctf1.AddRGBPoint(0,0,0,0)
ctf1.AddRGBPoint(1.0,0,255,0)

ctf2=vtk.vtkColorTransferFunction()
ctf2.AddRGBPoint(0,0,0,0)
ctf2.AddRGBPoint(1.0,255,0,0)

m1=vtk.vtkImageMapToColors()
m2=vtk.vtkImageMapToColors()
m1.SetOutputFormatToRGB()
m2.SetOutputFormatToRGB()
m1.SetLookupTable(ctf1)
m2.SetLookupTable(ctf2)
print "Feeding channels to coloring ",elapsed()
m1.SetInput(d1)
m2.SetInput(d2)
cd1=m1.GetOutput()
cd2=m2.GetOutput()
print "Feeding channels to merge ",elapsed()
merge.AddInput(cd1)
merge.AddInput(cd2)

mip=vtk.vtkImageSimpleMIP()
print "Feeding merge to MIP",elapsed()
mip.SetInput(merge.GetOutput())

writer=vtk.vtkPNGWriter()
writer.SetFileName("Selli_BIG.png")
writer.SetInput(mip.GetOutput())
print "Feeding MIP to writer ",elapsed()
writer.Update()
writer.Write()
print "Wrote PNG ",elapsed()
