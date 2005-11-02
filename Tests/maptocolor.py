import vtk
reader=vtk.vtkXMLImageDataReader()
reader.SetFileName("sample2_1tp_0.vti")
reader.Update()
data=reader.GetOutput()
writer=vtk.vtkPNGWriter()

voi=vtk.vtkExtractVOI()
voi.SetInput(data)
voi.SetVOI(0,511,0,511,12,12)
voi.Update()
data=voi.GetOutput()
writer.SetInput(data)
writer.SetFileDimensionality(2)
writer.SetFileName("before.png")
writer.Write()


#mapToColors.RemoveAllInputs()
mapToColors=vtk.vtkImageMapToColors()
mapToColors.SetInput(data)
#updateColor()
ctf=vtk.vtkColorTransferFunction()
ctf.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
ctf.AddRGBPoint(255.0, 0.0, 1.0, 0.0)
#print ctf.GetTable(0,255,256)
print data.GetScalarRange(),data.GetScalarTypeAsString(),ctf
val=[0,0,0]
#for i in range(0,256,1):
#    ctf.GetColor(float(i),val)
#    r,g,b=val
#    print "%d maps to %f,%f,%f"%(i,r,g,b)
mapToColors.SetLookupTable(ctf)
mapToColors.SetOutputFormatToRGB()

mapToColors.Update()

data=mapToColors.GetOutput()
print data.GetScalarRange(),data.GetScalarTypeAsString()

#voi=vtk.vtkExtractVOI()
#voi.SetInput(data)
#voi.SetVOI(0,511,0,511,12,12)
#voi.Update()
#data=voi.GetOutput()
writer.SetInput(data)
writer.SetFileDimensionality(2)
writer.SetFileName("after.png")
writer.Write()
