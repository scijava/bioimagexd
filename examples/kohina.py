
"""
    Kohinanpoistodemo v.0

    Karkea, toimii jotenkin, kommentointi puuttuu etc.
    Muokattu tˆrke‰sti kolokalisaatiodemosta
"""
import time
import vtk

#asetukset
#threshold
usethreshold = True
threshold = 20
#mediaanisuodatus
usemedian = False
neighborhood = 2
#yksin‰isten poisto
removesolitary = True


reader_red=vtk.vtkXMLImageDataReader();
reader_red.SetFileName(r"H:\Konfokaalidataa\Sample1\sample1_red0.vti");
reader_red.Update()

#reader_green=vtk.vtkXMLImageDataReader();
#reader_green.SetFileName(r"H:\Konfokaalidataa\Sample1\sample1_green0.vti");
#reader_green.Update()

outline=vtk.vtkOutlineFilter()
outline.SetInput(reader_red.GetOutput())
outlineMapper=vtk.vtkPolyDataMapper()
outlineMapper.SetInput(outline.GetOutput())
outlineActor=vtk.vtkActor()
outlineActor.SetMapper(outlineMapper)
outlineActor.GetProperty().SetColor(1,1,1)


image_kohi = vtk.vtkImageData()
image_kohi.CopyStructure(reader_red.GetOutput())
#image_kolo.

image_red=reader_red.GetOutput()
lkmp = image_kohi.GetNumberOfPoints()
lkmc = image_kohi.GetNumberOfCells()
dims = image_red.GetDimensions()

#image_green=reader_green.GetOutput()

print lkmp
print lkmc
#print dims

#print image.GetScalarTypeAsString()
#print image.GetNumberOfScalarComponents()

# And the magic...
#print dims[0]*dims[1]*dims[2]

rx=range(0,dims[0])
ry=range(0,dims[1])
rz=range(0,dims[2])
xd,yd,zd=dims

#print image_red.

red_get=image_red.GetScalarComponentAsFloat
#green_get=image_green.GetScalarComponentAsFloat
kohi_set=image_kohi.SetScalarComponentFromFloat

if usethreshold :
   print "joojoo"
else:
   threshold=0

print "Aloitetaan datan k‰sittely (threshold)"
t=time.time()
for x in rx:
    for y in ry:
        for z in rz:
            scal_red=red_get(x,y,z,0)
            #scal_green=green_get(x,y,z,0)

            # no onhan se ruma

            if scal_red>threshold :
              # Oikeasti pit‰is teh‰ oma silmukka sun muuta niin s‰‰t‰is t‰m‰nkin iffin
              if removesolitary :
               if x>0 and red_get(x-1,y,z,0)>threshold:
                 scal=scal_red
               else:
                 if x<dims[0]-1 and red_get(x+1,y,z,0)>threshold:
                   scal=scal_red
                 else:
                   if y>0 and red_get(x,y-1,z,0)>threshold:
                     scal=scal_red
                   else:
                     if y<dims[1]-1 and red_get(x,y+1,z,0)>threshold:
                       scal=scal_red
                     else:scal=0
              else:scal=scal_red
            else:scal=0

            kohi_set(x,y,z,0,scal)
            #print "At %d,%d,%d scalar = %f"%(x,y,z,scal)
t2=time.time()
print "aikaa meni",t2-t

# mediaanisuodatus
#print "Aloitetaan datan k‰sittely (median3d)"
#t=time.time()
#t2=time.time()
#print "aikaa meni",t2-t

if usemedian:
   median = vtk.vtkImageMedian3D()
   median.SetInput(image_kohi)
   median.SetKernelSize(neighborhood,neighborhood,neighborhood)  #huomaa ett‰ kaikkiin k‰ytetty nyt samaa
   median.ReleaseDataFlagOff()

# transfer function that maps scalar value to opacity
opacityTF = vtk.vtkPiecewiseFunction()
opacityTF.AddPoint(    0.0,  0.0 )
#opacityTF.AddPoint(   20.0,  0.0 )
#opacityTF.AddPoint(   80.0,  0.7 )
#opacityTF.AddPoint(  200.0,  0.9 )
opacityTF.AddPoint(  255.0,  0.7)

# transfer functoin that maps scalar value to color
colorTF_red = vtk.vtkColorTransferFunction()
colorTF_red.AddRGBPoint( 0.0, 0.0, 0.0, 0.0)
colorTF_red.AddRGBPoint(5.0, 1.0, 0.0, 0.0)

# transfer functoin that maps scalar value to color
#colorTF_green = vtk.vtkColorTransferFunction()
#colorTF_green.AddRGBPoint( 0.0, 0.0, 0.2, 0.0)
#colorTF_green.AddRGBPoint(5.0, 0.0, 1.0, 0.0)

# transfer functoin that maps scalar value to color
colorTF_kohi = vtk.vtkColorTransferFunction()
colorTF_kohi.AddRGBPoint( 0.0, 0.0, 0.0, 0.0)
colorTF_kohi.AddRGBPoint(5.0, 1.0, 0.0, 0.0)


# property of the volume (lighting, transfer functions)
volprop_red = vtk.vtkVolumeProperty()
volprop_red.SetColor(colorTF_red)
volprop_red.SetScalarOpacity(opacityTF)
volprop_red.ShadeOff()
volprop_red.SetInterpolationTypeToNearest()
volprop_red.SetSpecularPower(10.0)
volprop_red.SetSpecular(.7)
volprop_red.SetAmbient(.5)
volprop_red.SetDiffuse(.5)

# property of the volume (lighting, transfer functions)
#volprop_green = vtk.vtkVolumeProperty()
#volprop_green.SetColor(colorTF_green)
#volprop_green.SetScalarOpacity(opacityTF)
#volprop_green.ShadeOn()
#volprop_green.SetInterpolationTypeToLinear()
#volprop_green.SetSpecularPower(10.0)
#volprop_green.SetSpecular(.7)
#volprop_green.SetAmbient(.5)
#volprop_green.SetDiffuse(.5)

# property of the volume (lighting, transfer functions)
volprop_kohi = vtk.vtkVolumeProperty()
volprop_kohi.SetColor(colorTF_kohi)
volprop_kohi.SetScalarOpacity(opacityTF)
volprop_kohi.ShadeOff()
volprop_kohi.SetInterpolationTypeToNearest()
volprop_kohi.SetSpecularPower(10.0)
volprop_kohi.SetSpecular(.7)
volprop_kohi.SetAmbient(.5)
volprop_kohi.SetDiffuse(.5)


ren=vtk.vtkRenderer()
ren.SetBackground(.9,.9,.9)

# mapper
# the composite function is the line integrator
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
volumeMapper_red = vtk.vtkVolumeRayCastMapper()
volumeMapper_red.SetVolumeRayCastFunction( compositeFunction )
volumeMapper_red.SetInput( reader_red.GetOutput() )
# sample distance along each ray
volumeMapper_red.SetSampleDistance(.2)

# volume is a specialized actor
volume_red = vtk.vtkVolume()
volume_red.SetMapper(volumeMapper_red)
volume_red.SetProperty(volprop_red)


# mapper
# the composite function is the line integrator
#compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
#volumeMapper_green = vtk.vtkVolumeRayCastMapper()
#volumeMapper_green.SetVolumeRayCastFunction( compositeFunction )
#volumeMapper_green.SetInput( reader_green.GetOutput() )
# sample distance along each ray
#volumeMapper_green.SetSampleDistance(.2)

# volume is a specialized actor
#volume_green = vtk.vtkVolume()
#volume_green.SetMapper(volumeMapper_green)
#volume_green.SetProperty(volprop_green)


# mapper
# the composite function is the line integrator
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
volumeMapper_kohi = vtk.vtkVolumeRayCastMapper()
volumeMapper_kohi.SetVolumeRayCastFunction( compositeFunction )

if usemedian:
  volumeMapper_kohi.SetInput( median.GetOutput() )
else:
  volumeMapper_kohi.SetInput( image_kohi )

# sample distance along each ray
volumeMapper_kohi.SetSampleDistance(.2)

# volume is a specialized actor
volume_kohi = vtk.vtkVolume()
volume_kohi.SetMapper(volumeMapper_kohi)
volume_kohi.SetProperty(volprop_kohi)

# add the actors, vain kolokalisaatio p‰‰ll‰, hidastui liikaa
#ren.AddVolume( volume_green )
#ren.AddVolume( volume_red )
ren.AddVolume( volume_kohi )

scalarBar=vtk.vtkScalarBarActor()
scalarBar.SetTitle("Iso value")

renWin=vtk.vtkRenderWindow()
renWin.SetSize(600,600)
renWin.AddRenderer(ren)

iren= vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

ren.AddActor(outlineActor)
#ren.AddActor(scalarBar)

renWin.Render()
iren.Initialize()
iren.Start()


