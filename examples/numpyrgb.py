import sys
sys.path.remove("C:\\Python23\\lib\\site-packages\\vtk_python")

import vtk
from Numeric import *
import time

def VTKtoNumpy(vol,multicompo=0):
    exporter = vtk.vtkImageExport()
    exporter.SetInput(vol)
#    if multicompo:
#        exporter.SetDataNumberOfScalarComponents(multicompo)
    print "Number of components: ",exporter.GetDataNumberOfScalarComponents()
    print "Datatype=",exporter.GetDataScalarTypeAsString()
    dims = exporter.GetDataDimensions()
    if multicompo:
        dims=(dims[0],dims[1],dims[2],multicompo)
    print "Dimensions of vtk data:",dims
    print "datatype=",exporter.GetDataScalarType()
    if (exporter.GetDataScalarType() == 3):
        type = UnsignedInt8
    if (exporter.GetDataScalarType() == 5):
        type = Int16
    origin=vol.GetOrigin()
    extent=vol.GetExtent()
    spacing=vol.GetSpacing()
#    print "origin,",vol.GetOrigin()
#    print "extetn",vol.GetExtent()
#    print "spacing",vol.GetSpacing()
    a = zeros(reduce(multiply,dims),type)
    s = a.tostring()
    print "Converting..."
    exporter.SetExportVoidPointer(s)
    print "exporter.Export()"
    exporter.Export()
    print "done, reshaping"
    if multicompo:
        # Why z,x,y not z,y,x
        a = reshape(fromstring(s,type),(dims[2],dims[0],dims[1],dims[3]))
    else:
        a = reshape(fromstring(s,type),(dims[2],dims[0],dims[1]))
    return a,(origin,extent,spacing)

def NumpyToVTK(imArray,info):
    #    imString=imArray.tostring()
    if imArray.typecode()!='b':
        arr = imArray.astype(UnsignedInt8)
    else:
        arr=imArray
    print "Type of array now:",arr.typecode()
    imString=arr.tostring()
    dim=arr.shape

    importer=vtk.vtkImageImport()
    importer.CopyImportVoidPointer(imString,len(imString))
    importer.SetDataScalarTypeToUnsignedChar()
    importer.SetNumberOfScalarComponents(1)
    extent = importer.GetDataExtent()
    importer.SetWholeExtent(info[1])
    importer.SetDataExtent(info[1])
    importer.SetDataSpacing(info[2])
    importer.SetDataOrigin(info[0])

    return importer.GetOutput()

def NumpyToVTK24bit(imArray,info):
    #    imString=imArray.tostring()
    if imArray.typecode()!='b':
        arr = imArray.astype(UnsignedInt8)
    else:
        arr=imArray
    print "Type of array now:",arr.typecode()
    imString=arr.tostring()
    dim=arr.shape

    importer=vtk.vtkImageImport()
    #importer.CopyImportVoidPointer(imString,len(imString))
    importer.SetImportVoidPointer(imString,len(imString))
    importer.SetDataScalarTypeToUnsignedChar()
    importer.SetNumberOfScalarComponents(3)   #4
    extent = importer.GetDataExtent()
    importer.SetWholeExtent(info[1])
    importer.SetDataExtent(info[1])
    importer.SetDataSpacing(info[2])
    importer.SetDataOrigin(info[0])

    return importer.GetOutput()

print "Reading..."
t1=time.time()
reader=vtk.vtkXMLImageDataReader()
reader.SetFileName("rgbvol.vti")
reader.Update()
rgb=reader.GetOutput()

print "Converting newdata"
newn,newinfo=VTKtoNumpy(rgb,3)
print "Done"


print newn.shape


