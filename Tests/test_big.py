#! /usr/bin/env python
import vtk
import time
#D="/media/sda12/Data/selli/Selli_BIG.lsm"
D="/home/heuuksul/data/Selli_BIG.lsm"
#D="/media/sda12/Data/selli/selli_coloc1_8-bit.lsm"
#D="/media/sda12/Data/sample2.lsm"
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


mip=vtk.vtkImageSimpleMIP()
#mip.DebugOn()
print "Feeding merge to MIP",elapsed()
mip.SetInput(merge.GetOutput())

streamer  = vtk.vtkMemoryLimitImageDataStreamer()
streamer.SetMemoryLimit(300*1024)
streamer.SetInput(mip.GetOutput())

writer=vtk.vtkPNGWriter()
writer.SetFileName("Selli_BIG.png")
writer.SetInput(streamer.GetOutput())
#writer.SetInput(mip.GetOutput())
print "Feeding MIP to writer ",elapsed()
writer.Update()
writer.Write()
print "Wrote PNG ",elapsed()
