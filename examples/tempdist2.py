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


ren=vtk.vtkRenderer()
ren.SetBackground(0,0,0)

xdim,ydim,zdim=30,30,30
dist=TemperatureDistribution(xdim,ydim,zdim,0)
print "Generating data...",
dist.generate(10,100)
print "done"


geomfilter=vtk.vtkGeometryFilter()
geomfilter.SetExtent(0,xdim,0,ydim,0,zdim)
geomfilter.SetInput(dist.GetOutput())

#delau=vtk.vtkDelaunay3D()
#delau.SetOffset(100)
#delau.SetInput(geomfilter.GetOutput())

#cont=vtk.vtkContourGrid()
#cont.SetInput(delau.GetOutput())
#cont.GenerateValues(50,0,255)
#cont.ComputeNormalsOn()

surf=vtk.vtkSurfaceReconstructionFilter()
surf.SetInput(geomfilter.GetOutput())

cf = vtk.vtkContourFilter()
cf.SetInput(surf.GetOutput())
cf.SetValue(0, 0.0)

mapper=vtk.vtkPolyDataMapper()
mapper.SetInput(cf.GetOutput())
#mapper.SetScalarRange(0,255)
actor=vtk.vtkActor()
actor.SetMapper(mapper);

ren.AddActor(actor)

#ren.AddVolume(volume)
#ren.AddProp(scalarBar)

renWin=vtk.vtkRenderWindow()
renWin.SetSize(600,600)
renWin.AddRenderer(ren)

movwriter=lib.MovieWriter(renWin)

def timerEvent(obj,event):
    movwriter.captureFrame()
    print event

iren= vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
#iren.AddObserver("TimerEvent",timerEvent)

#axes=vtk.vtkCubeAxesActor2D()
#axes.SetInput(dist.GetOutput())
#axes.SetCamera(ren.GetActiveCamera())
#axes.SetLabelFormat("%6.4g")
#axes.ShadowOn()
#axes.SetFlyModeToOuterEdges()
#axes.SetFontFactor(0.8)
#axes.GetProperty().SetColor(1,1,1)
#ren.AddProp(axes)

print "Rendering"
renWin.Render()
iren.Initialize()
iren.Start()




