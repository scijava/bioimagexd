#! /usr/bin/env python
import vtk
import time
D="/media/sda12/Data/sample2.lsm"
t=time.time()
def elapsed():
    global t
    return "(%.2fs elapsed)"%(time.time()-t)

r1=vtk.vtkLSMReader()
r1.SetFileName(D)
r1.SetUpdateChannel(0)

d1=r1.GetOutput()


itf1=vtk.vtkIntensityTransferFunction()
itf1.SetBrightness(50.0)

ctf1=vtk.vtkColorTransferFunction()
ctf1.AddRGBPoint(0,0,0,0)
ctf1.AddRGBPoint(255.0,0,1.0,0)


print "Feeding channels to merge ",elapsed()
merge = vtk.vtkImageColorMerge()
#merge.SetNumberOfThreads(5)
merge.AddInput(d1)
merge.AddLookupTable(ctf1)
merge.AddIntensityTransferFunction(itf1)

itfmap = vtk.vtkImageMapToIntensities()
itfmap.SetInput(d1)
itfmap.SetIntensityTransferFunction(itf1)

maptocolor=vtk.vtkImageMapToColors()
maptocolor.SetOutputFormatToRGB()
maptocolor.SetInput(itfmap.GetOutput())
maptocolor.SetLookupTable(ctf1)


mip=vtk.vtkImageSimpleMIP()

print "Feeding merge to MIP",elapsed()
mip.SetInput(merge.GetOutput())

#flip =vtk.vtkImageFlip()
#flip.SetFilteredAxis(1)

#flip.SetInput(mip.GetOutput())
writer=vtk.vtkPNGWriter()
writer.SetFileName("ITFmapped.png")
writer.SetInput(mip.GetOutput())
print "Feeding MIP to writer ",elapsed()
writer.Update()
writer.Write()
print "Wrote PNG ",elapsed()


mip2=vtk.vtkImageSimpleMIP()
mip2.SetInput(maptocolor.GetOutput())
writer2=vtk.vtkPNGWriter()
writer2.SetFileName("ITFmapped2.png")
writer2.SetInput(mip2.GetOutput())
writer2.Update()
writer2.Write()
mip.Update()
mip2.Update()
i1=mip.GetOutput()
i2=mip2.GetOutput()

m1=0
m2=0

for x in range(0,512):
    for y in range(0,512):
	c1 = i1.GetScalarComponentAsDouble(x,y,0,1)
	c2 = i2.GetScalarComponentAsDouble(x,y,0,1)
	if c1>m1:m1=c1
	if c2>m2:m2=c2
	if c1 != c2 and (c1>=251 or c2>=251):
	    print "Images differ at ",x,y,"values =",c1,"and",c2

print "Largest in 1",m1
print "Largest in 2",m2
