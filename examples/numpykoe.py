import sys        
sys.path.remove("C:\\Python23\\lib\\site-packages\\vtk_python")

from vtk import *
from Numeric import *
import time

def VTKtoNumpy(vol):
    exporter = vtkImageExport()
    exporter.SetInput(vol)
    dims = exporter.GetDataDimensions()
    if (exporter.GetDataScalarType() == 3):
        type = UnsignedInt8
    if (exporter.GetDataScalarType() == 5):
        type = Int16
    print "Type=",type
    a = zeros(reduce(multiply,dims),type)
    s = a.tostring()
    exporter.SetExportVoidPointer(s)
    exporter.Export()
    a = reshape(fromstring(s,type),(dims[2],dims[0],dims[1]))
    return a

def NumpyToVTK(imArray):
#    imString=imArray.tostring()
    imString = imArray.astype(Int8).tostring()
    dim=imArray.shape
    print imArray.typecode()
    importer=vtkImageImport()
    importer.CopyImportVoidPointer(imString,len(imString))
    importer.SetDataScalarTypeToUnsignedChar()
    importer.SetNumberOfScalarComponents(1)

    extent = importer.GetDataExtent()
    importer.SetDataExtent(extent[0],extent[0]+dim[2]-1,
                         extent[2],extent[2]+dim[1]-1,
                         extent[4],extent[4]+dim[0]-1)
    importer.SetWholeExtent(extent[0],extent[0]+dim[2]-1,
                          extent[2],extent[2]+dim[1]-1,
                          extent[4],extent[4]+dim[0]-1)

    return importer.GetOutput()

def docolo(x,y,z):
    if greenn[x,y,z] > 80 and redn[x,y,z] > 80:
        return 255
    return 0

print "Reading..."
t1=time.time()
redreader=vtkXMLImageDataReader()
redreader.SetFileName(r"H:\Data\Sample2\sample2_red0.vti")
redreader.Update()
red=redreader.GetOutput()
greenreader=vtkXMLImageDataReader()
greenreader.SetFileName(r"H:\Data\Sample2\sample2_green0.vti")
greenreader.Update()
green=greenreader.GetOutput()
t2=time.time()
print "Reading took %f seconds"%(t2-t1)
redn=VTKtoNumpy(red)
greenn=VTKtoNumpy(green)
t1=time.time()
print "Conversion took %f seconds"%(t1-t2)

t1=time.time()

redmask=greater_equal(redn,81)
greenmask=greater_equal(greenn,81)

result=logical_and(redmask,greenmask)
result*=255

data=NumpyToVTK(result)
t2=time.time()
print "Processing took %f seconds"%(t2-t1)
writer=vtkXMLImageDataWriter()
writer.SetFileName("result.vti")
writer.SetInput(data)
writer.Write()

t1=time.time()
print "Writing took %f seconds"%(t1-t2)
sys.stdin.readline()
