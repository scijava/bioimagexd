import sys
import lib
import vtk
import math
import random
class TemperatureDistribution:
      def __init__(self,x,y,z,T_0,D=1/50.0):
          self.xdim,self.ydim,self.zdim=x,y,z
          self.T_0=T_0
          self.D=D
          self.newImage()
          self.scalars={}

      def newImage(self):
          "Allocates a new image structure for filling with data"
          self.data=None
          self.data=vtk.vtkImageData()
#          self.array=vtk.vtkUnsignedCharArray()
#          self.array.Allocate(self.xdim*self.ydim*self.zdim,1000)
#         self.data.GetPointData().SetScalars(self.array)
          self.data.SetDimensions(self.xdim+1,self.ydim+1,self.zdim+1)
          self.data.SetScalarTypeToUnsignedChar()
          self.data.SetSpacing(1,1,1)
          self.data.SetOrigin(0,0,0)
          self.data.AllocateScalars()
          for x in range(0,self.xdim+1):
              for y in range(0,self.ydim+1):
                  for z in range(0,self.zdim+1):
                      self.data.SetScalarComponentFromDouble(x,y,z,0,0)


      def generate(self,npoints,t=1):
          "Generates given amount of points"

          for i in xrange(0,npoints):
              x=random.randint(0,self.xdim)
              y=random.randint(0,self.ydim)
              z=random.randint(0,self.zdim)
#              print "Generating at %d,%d,%d time=%d"%(x,y,z,t)
              self.generatePoint(x,y,z,t)
          for x in range(0,self.xdim+1):
              for y in range(0,self.ydim+1):
                  for z in range(0,self.zdim+1):
                      s=self.data.GetScalarComponentAsDouble(x,y,z,0)
#                      if s:print x,y,z,s


      def GetOutput(self):
          return self.data

      def T(self,x,y,z,t):
          """Temperature distribution function:
Returns temperature of point (x,y,z) at time t:
                              ___________
             A              \/x^2+y^2+z^2
T(x,y,z,t) =----     * e^-  -------------- +  T_0
            t^(3/2)             4Dt^2
"""
          exp=math.exp
          A=255000.0
          D=self.D
          K=math.sqrt(x*x+y*y+z*z)
          L=4.0*D*t*t
          power=K / L
          AperT=A /(t**1.5)
          return AperT*exp(-power) + self.T_0

      def generatePoint(self,x,y,z,t):
          """Generate a scalar value for point (x,y,z) at time t"""
          coord=(x,y,z)
          val=self.T(x,y,z,t)
          print val,
          print " at %d,%d,%d,%d"%(x,y,z,t)
#          self.scalars[coord]=val
          self.data.SetScalarComponentFromDouble(x,y,z,0,int(val))


opacityTF = vtk.vtkPiecewiseFunction()
opacityTF.AddPoint(    0.0,  0.01 )
opacityTF.AddPoint(  100.0,  1.0)
colorTF = vtk.vtkColorTransferFunction()
#colorTF.AddRGBPoint( 0, 1.0,1.0,1.0)
colorTF.AddRGBPoint(240, 0.0, 0.0, 1.0)
colorTF.AddRGBPoint(245,0,1,0)
colorTF.AddRGBPoint(250, 1.0, 0.0, 0.0)

volprop = vtk.vtkVolumeProperty()
volprop.SetColor(colorTF)
volprop.SetScalarOpacity(opacityTF)
volprop.ShadeOff()
volprop.SetInterpolationTypeToNearest()
#volprop.SetInterpolationTypeToLinear()
volprop.SetSpecularPower(10.0)
volprop.SetSpecular(.7)
volprop.SetAmbient(.5)
volprop.SetDiffuse(0.5)


ren=vtk.vtkRenderer()
ren.SetBackground(0,0,0)

dist=TemperatureDistribution(30,30,30,0)
print "Generating data...",
dist.generate(1000,100)
print "done"

def laske_piste(dist,x,y,z,t):
    s=dist.T(x,y,z,t)
    print "(%d,%d,%d) t=%d: "%(x,y,z,t),
    print s
compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
volumeMapper= vtk.vtkVolumeRayCastMapper()
volumeMapper.SetVolumeRayCastFunction( compositeFunction )
volumeMapper.SetInput( dist.GetOutput() )
# sample distance along each ray
volumeMapper.SetSampleDistance(0.2)

# volume is a specialized actor
volume = vtk.vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volprop)

scalarBar=vtk.vtkScalarBarActor()
scalarBar.SetLookupTable(colorTF)
scalarBar.SetTitle("Lämpötila")
scalarBar.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
scalarBar.GetPositionCoordinate().SetValue(0.1,0.01)
scalarBar.SetOrientationToHorizontal()
scalarBar.SetWidth(0.8)
scalarBar.SetHeight(0.17)


ren.AddVolume(volume)
ren.AddProp(scalarBar)

renWin=vtk.vtkRenderWindow()
renWin.SetSize(600,600)
renWin.AddRenderer(ren)

movwriter=lib.MovieWriter(renWin)

def timerEvent(obj,event):
    movwriter.captureFrame()
    print event

print "FOO"
iren= vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
iren.AddObserver("TimerEvent",timerEvent)

#=vtk.vtkCubeAxesActor2D()
#axes.SetInput(dist.GetOutput())
#axes.SetCamera(ren.GetActiveCamera())
#axes.SetLabelFormat("%6.4g")
#axes.ShadowOn()
#axes.SetFlyModeToOuterEdges()
#axes.SetFontFactor(0.8)
#axes.GetProperty().SetColor(1,1,1)
#ren.AddProp(axes)

print "Rendering (press enter)"
sys.stdin.readline()
renWin.Render()
print "Iren"
sys.stdin.readline()
iren.Initialize()
iren.Start()




