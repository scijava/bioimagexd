import vtk

reader_green=vtk.vtkXMLImageDataReader();
reader_green.SetFileName(r"H:\Data\Sample1\sample1_green0.vti");
reader_green.Update()

green=reader_green.GetOutput()

geomfilter=vtk.vtkImageDataGeometryFilter()
geomfilter.SetInput(green)
#geomfilter.SetExtent(0,300,0,300,0,300)

#tri=vtk.vtkTriangleFilter()
#tri.SetInput(geomfilter.GetOutput())

#dela=vtk.vtkDelaunay3D()
#dela.SetInput(geomfilter.GetOutput())

mapper=vtk.vtkPolyDataMapper()
mapper.SetInput(geomfilter.GetOutput())

actor=vtk.vtkActor()
actor.GetProperty().SetColor(1,0,0)
actor.SetMapper(mapper)

ren=vtk.vtkRenderer()
ren.SetBackground(.0,.0,.0)
ren.AddActor(actor)

renWin=vtk.vtkRenderWindow()
renWin.SetSize(600,600)
renWin.AddRenderer(ren)

iren= vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)


renWin.Render()
iren.Initialize()
iren.Start()


