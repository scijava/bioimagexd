import vtk
from lib import *


green=Data(r"H:\\Konfokaalidataa\\Sample1\\sample1_green0.vti")
red=Data(r"H:\\Konfokaalidataa\\Sample1\\sample1_red0.vti")

gsurf=Surface(green)
gsurf.setColor(0,1,0)
rsurf=Surface(red)
rsurf.setColor(1,0,0)

estimate=EstimatePolyData([rsurf,gsurf])
ren=Renderer()

ren.addSurface("green_surf",gsurf)
ren.addSurface("red_surf",rsurf)

app=Append([gsurf,rsurf])
#tri=Triangulate(app)

rec=vtk.vtkSurfaceReconstructionFilter()
rec.SetInput(rsurf.getPolyData())

cont=vtk.vtkContourFilter()
cont.SetInput(rec.GetOutput())

cont.SetValue(0,0)
print cont.GetOutput()
ren.addPolyData("rec",cont.GetOutput())
#print "Contoured"
#ren.addPolyData("reconstructed_surface",cont.GetOutput())

#estimate2=EstimatePolyData([cont])
#estimate2.move(0.1,0.8)
#estimate2.setColor(1,1,0)

#ren.addUnstructuredGrid("triangulated",tri.GetOutput())

#ren.addActor(estimate2.getTextActor())
ren.addActor(estimate.getTextActor())
print "start"
ren.start()































































































































































