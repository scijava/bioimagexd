#! /usr/bin/env python
import vtk
import time

import sys
sys.path.insert(0,"H:\\vtkBXD\\bin")
sys.path.insert(0,"..\\vtkBXD\\Wrapping\\Python")

#import vtkbxd

#D="/Users/dan/Documents/volumerender/colocsample/colocsample1b.lsm"
D="H:\\Data\\LSM\\Selli_noise2.lsm"
#D="H:\\Data\\LSM\\sample1_series12.lsm"
t=time.time()
def elapsed():
    global t
    return "(%.2fs elapsed)"%(time.time()-t)

r1=vtk.vtkLSMReader()
r1.SetFileName(D)
r1.SetUpdateChannel(0)
d1=r1.GetOutput()

r2=vtk.vtkLSMReader()
r2.SetFileName(D)
r2.SetUpdateChannel(1)
d2=r2.GetOutput()

print "Reading data"

ctf1=vtk.vtkColorTransferFunction()
ctf1.AddRGBPoint(0,0,0,0)
ctf1.AddRGBPoint(255.0,0,1.0,0)

ctf2=vtk.vtkColorTransferFunction()
ctf2.AddRGBPoint(0,0,0,0)
ctf2.AddRGBPoint(255.0,1.0,0,0)

#mip1 = vtk.vtkImageSimpleMIP()
#mip1.SetInput(d1)
#mip2 = vtk.vtkImageSimpleMIP()
#mip2.SetInput(d2)

#mip1.Update()
#mip2.Update()

print "Feeding channels to merge ",elapsed()
merge = vtk.vtkImageColorMerge()
#merge.AddInput(mip1.GetOutput())
#merge.AddInput(mip2.GetOutput())
merge.AddInput(d1)
merge.AddInput(d2)

merge.AddLookupTable(ctf1)
merge.AddLookupTable(ctf2)
#merge.DebugOn()
#merge.AddIntensityTransferFunction(itf1)
#merge.AddIntensityTransferFunction(itf2)
#merge.GetOutput().ReleaseDataFlagOn()

#merge.Update()

streamer = vtk.vtkImageDataStreamer()
streamer.SetNumberOfStreamDivisions(1)
streamer.SetInput(merge.GetOutput())
streamer.GetExtentTranslator().SetSplitModeToZSlab()
streamer.Update()
data = streamer.GetOutput()

mip = vtk.vtkImageSimpleMIP()
mip.SetInput(data)


writer=vtk.vtkPNGWriter()
writer.SetFileName("Selli_BIG.png")
writer.SetInput(mip.GetOutput())
writer.Write()
print "Wrote PNG ",elapsed()
