import sys
sys.path.remove("C:\\Python23\\lib\\site-packages\\vtk_python")

import vtk
import threading


DATA_PATH=r"H:\\Konfokaalidataa\\"

RED,GREEN,BLUE,YELLOW=1,2,3,4

class MovieWriter:
    def __init__(self,renWin,framename=r"Z:\\Sovellusprojekti\\CVS\\source\\demot\\frame_%.3d.png"):
        self.renWin=renWin
        self.frame=0
        self.framename=framename
        self.windowtoimage=vtk.vtkWindowToImageFilter()
        self.windowtoimage.SetInput(renWin)
        self.pngwriter=vtk.vtkPNGWriter()
        self.pngwriter.SetInput(self.windowtoimage.GetOutput())
    
    def captureFrame(self):
        print "Writing %s"%(self.framename%self.frame)
        self.pngwriter.SetFileName(self.framename%self.frame)
        self.frame+=1
        self.windowtoimage.Modified()
        self.pngwriter.Write()
        
        

class Data:
    def __init__(self,file):
	self.filename=file
	self._reader=vtk.vtkXMLImageDataReader()
	self._reader.SetFileName(file)
    	self._reader.Update()
    def data(self):
    	return self._reader
    def GetOutput(self):
    	return self._reader.GetOutput()

def generateColorTransferFunction(color):
    colorTF = vtk.vtkColorTransferFunction()
    if color==RED:
	colorTF.AddRGBPoint( 20.0, 1,0,0)
    elif color==GREEN:
	colorTF.AddRGBPoint( 20.0, 0,1.0,0)
    elif color==BLUE:
    	colorTF.AddRGBPoint( 20.0, 0,0.0,1.0)
    elif color==YELLOW:
	colorTF.AddRGBPoint(20.0,1,1,0)
    else:
    	colorTF.AddRGBPoint( 20.0, 0.5,0.5,0.5)
    return colorTF

class Outline:
    def __init__(self,data):
    	self.outline=vtk.vtkOutlineFilter()
    	self.outline.SetInput(data.data().GetOutput())
    	self.mapper=vtk.vtkPolyDataMapper()
    	self.mapper.SetInput(self.outline.GetOutput())
    	self.outlineActor=vtk.vtkActor()
    	self.outlineActor.SetMapper(self.mapper)
    	self.outlineActor.GetProperty().SetColor(1,0,0)
    def actor(self):
	    return self.outlineActor

class Volume:
    def __init__(self,colorTF,opacityTF):
    	# property of the volume (lighting, transfer functions)
    	self.volprop = vtk.vtkVolumeProperty()
    	self.volprop.SetColor(colorTF)
    	self.volprop.SetScalarOpacity(opacityTF)
    	self.volprop.ShadeOn()
    	self.volprop.SetInterpolationTypeToLinear()
    	self.volprop.SetSpecularPower(10.0)
    	self.volprop.SetSpecular(.7)
    	self.volprop.SetAmbient(.5)
    	self.volprop.SetDiffuse(.5)

    def property(self):
    	return self.volprop

class Renderer:
    def __init__(self):
    	self.props={}
    	self.actors={}
    	self.mappers={}
    	self.ren=vtk.vtkRenderer()
#    	self.ren.SetBackground(.8,.8,.8)
        self.ren.SetBackground(0,0,0)
    	# mapper
    	# the composite function is the line integrator
    	self.compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
    	self.renWin=vtk.vtkRenderWindow()
    	self.renWin.SetSize(640,480)
    	self.renWin.AddRenderer(self.ren)
    	self.iren= vtk.vtkRenderWindowInteractor()
    	self.iren.SetRenderWindow(self.renWin)

    def addUnstructuredGrid(self,name,data):
        mapper=vtk.vtkDataSetMapper()
        self.mappers[name]=mapper
        mapper.SetInput(data)
        act=vtk.vtkActor()
        act.SetMapper(mapper)
        self.actors[name]=act
        self.ren.AddActor(act)

    def addPolyData(self,name,data):
        mapper=vtk.vtkPolyDataMapper()
        self.mappers[name]=mapper
        mapper.SetInput(data)
        act=vtk.vtkActor()
        act.SetMapper(mapper)
        self.actors[name]=act
        self.ren.AddActor(act)

    def addSurface(self,name,data):
        mapper=data.getMapper()
        self.mappers[name]=mapper
        mapper.SetInput(data.GetOutput())
        act=vtk.vtkActor()
        act.SetMapper(mapper)
        self.actors[name]=act
        self.ren.AddActor(act)

    def addActor(self,act):
        self.ren.AddActor(act)

    def addVolume(self,name,data,prop):
    	# volume is a specialized actor
	mapper=vtk.vtkVolumeRayCastMapper()
#        mapper=vtk.vtkVolumeTextureMapper2D()
#	mapper.IndependentComponentsOff()
#	print "Independent components: %d"%(mapper.GetIndependentComponents())
    	self.mappers[name] = mapper
    	mapper.SetVolumeRayCastFunction(self.compositeFunction )
    	mapper.SetInput( data.GetOutput() )
    	# sample distance along each ray
    	mapper.SetSampleDistance(.2)
    
    	volume = vtk.vtkVolume()
    	self.actors[name]=volume
    	volume.SetMapper(mapper)
    	self.props[name]=prop
    	volume.SetProperty(prop.property())
    	self.ren.AddVolume(volume)

    def getSurface(self,name):
        return self.vols[name]

    def getVolume(self,name):
    	return self.vols[name]
    def getProperty(self,name):
    	return self.props[name]
    def getMapper(self,name):
    	return self.mappers[name]
    def setOutline(self,ol):
    	self.ren.AddActor(ol.actor())
    def start(self):
    	self.renWin.Render()
    	self.iren.Initialize()
    	self.iren.Start()


class Colocalization:
    def __init__(self,d1,d2):
    	self.green=d1.GetOutput()
    	self.red=d2.GetOutput()
    	self.green.SetScalarTypeToUnsignedChar()
    	self.red.SetScalarTypeToUnsignedChar()
    	self.x1,self.y1,self.z1=self.green.GetDimensions()
    	self.x2,self.y2,self.z2=self.green.GetDimensions()
    
    	print "Green data dimensions %d,%d,%d"%(self.x1,self.y1,self.z1)
    	print "Red data dimensions %d,%d,%d"%(self.x2,self.y2,self.z2)
    	print self.green.GetScalarTypeAsString()
    	self.new=vtk.vtkImageData()
    	self.new.SetScalarTypeToUnsignedChar()
    	self.new.SetExtent(self.green.GetExtent())
    	self.new.SetDimensions(self.x1+1,self.y1+1,self.z1+1)
    	self.new.AllocateScalars()
        self.getgreen=self.green.GetScalarComponentAsDouble
        self.getred=self.red.GetScalarComponentAsDouble

    def start(self):
#    	self.calcAvg()
    	self.generateColocalizationMap()

    def calcAvg(self):
    	totred=0
    	totgreen=0
    	maxred=0
    	maxgreen=0
    	ng=0
    	nr=0
    	getred=self.getred
    	getgreen=self.getgreen
    	for x in range(0,self.x1):
    	    for y in range(0,self.y1):
    		for z in range(0,self.z1):
    		    ag=getgreen(x,y,z,0)
    		    ar=getred(x,y,z,0)
    		    if ag>maxgreen:maxgreen=ag
    		    if ar>maxred:maxred=ar
    		    totred+=ar
    		    totgreen+=ag
    		    if ag:ng+=1
    		    if ar:nr+=1
    	self.avgred=totred/(1.0*nr)
    	self.avggreen=totgreen/(1.0*ng)
    	self.maxred=maxred
    	self.maxgreen=maxgreen
    	print "Average / Maximum for green channel: %f / %d"%(self.avggreen,maxgreen)
    	print "Average / Maximum for red channel: %f / %d"%(self.avgred,maxgreen)

    def generateColocalizationMap(self):
    	getred=self.getred
    	getgreen=self.getgreen
        setfunc=self.new.SetScalarComponentFromDouble
    	for x in range(0,self.x1):
    	    for y in range(0,self.y1):
    		    for z in range(0,self.z1):
    			s1=getgreen(x,y,z,0)
    			s2=getred(x,y,z,0)
    			if s1>100 and s2>100:
    			    setfunc(x,y,z,0,0.5*(s1+s2));
    			else:
    			    setfunc(x,y,z,0,0.0)
    def data(self):
    	return self.new
    def GetOutput(self):
	    return self.new

class ColorCombination:
    def __init__(self,d1,d2):
        print "ColorCombination"
        self.green=d1.GetOutput()
    	self.red=d2.GetOutput()
    	self.green.SetScalarTypeToUnsignedChar()
    	self.red.SetScalarTypeToUnsignedChar()
    	self.x1,self.y1,self.z1=self.green.GetDimensions()
    	self.x2,self.y2,self.z2=self.green.GetDimensions()
    
    	print "Green data dimensions %d,%d,%d"%(self.x1,self.y1,self.z1)
    	print "Red data dimensions %d,%d,%d"%(self.x2,self.y2,self.z2)
    	print self.green.GetScalarTypeAsString()
    	self.new=vtk.vtkImageData()
    	self.new.SetScalarTypeToUnsignedChar()
    	self.new.SetNumberOfScalarComponents(2)
    	self.new.SetExtent(self.green.GetExtent())
    	self.new.SetDimensions(self.x1+1,self.y1+1,self.z1+1)
    	self.new.AllocateScalars()
        self.getgreen=self.green.GetScalarComponentAsDouble
        self.getred=self.red.GetScalarComponentAsDouble

    def start(self):
        self.generateColorCombination()

    def generateColorCombination(self):
	getred=self.getred
    	getgreen=self.getgreen
        setfunc=self.new.SetScalarComponentFromDouble
        for x in range(0,self.x1):
	    for y in range(0,self.y1):
		for z in range(0,self.z1):
		    greenScalar=getgreen(x,y,z,0)
		    redScalar=getred(x,y,z,0)
		    combScalar=0
		    colorComp=0
		    if greenScalar>redScalar:
			colorComponent=1
			combScalar=greenScalar
		    elif redScalar>greenScalar:
			colorComponent=2
			combScalar=redScalar
		    # Kun vtkVolumeMapper:ille annetaan kaksikomponenttista skalaaridataa
		    # ja sanotaan IndependentComponentsOff(), se tulkitsee ensimmäisen
		    # komponentin värinä
		    # Asetetaan ensimmäinen skalaarikomponentti, joka ilmoittaa värin		    
		    setfunc(x,y,z,0,0)
		    setfunc(x,y,z,1,combScalar)



    def data(self):
    	return self.new
    def GetOutput(self):
	return self.new

class EstimatePolyData:
    def __init__(self,surflist):
        self.data=surflist
        self.vols=[]
        self.areas=[]
        self.trisurfs=[]
        for i in surflist:
            self.estimate(i)
            
        self.textProp = vtk.vtkTextProperty()
        self.textProp.SetFontSize(16)
        self.textProp.SetFontFamilyToArial()
        self.textProp.BoldOn()
        self.textProp.ItalicOff()
        self.textProp.ShadowOn()

        self.textMapper = vtk.vtkTextMapper()
        self.textMapper.SetInput("%d pintaa, Pinta-ala: %f  Tilavuus: %f"%(len(self.vols),self.getVolume(),self.getArea()))

        self.textActor=vtk.vtkActor2D()
        self.setColor(1,1,1)
        self.textActor.SetMapper(self.textMapper)
        self.textActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        self.move(0.05,0.85)

    def estimate(self,surface):
        trifilter=vtk.vtkTriangleFilter()
        trifilter.SetInput(surface.GetOutput())
        self.trisurfs.append(trifilter.GetOutput())
        massprop=vtk.vtkMassProperties()
        massprop.SetInput(trifilter.GetOutput())
        self.vols.append(massprop.GetVolume())
        self.areas.append(massprop.GetSurfaceArea())

    def setColor(self,r,g,b):
        self.textActor.GetProperty().SetColor(r,g,b)


    def move(self,x,y):
        self.textActor.GetPositionCoordinate().SetValue(x,y)

    def getTriangleSurface(self,n):
        return self.trisurfs[n]

    def getTextActor(self):
        return self.textActor

    def getVolume(self):
        tot=0
        for i in self.vols:
            tot+=i
        return tot

    def getArea(self):
        tot=0
        for i in self.areas:
            tot+=i
        return tot

class Append:
    def __init__(self,list):
        self.append=vtk.vtkAppendPolyData()
        for i in list:
            self.append.AddInput(i.GetOutput())
    def GetOutput(self):
        return self.append.GetOutput()


class Triangulate:
    def __init__(self,polydata):
        self.data=polydata.GetOutput()
        self.tri=vtk.vtkDelaunay3D()
        self.tri.SetTolerance(0.1)
        self.tri.SetInput(self.data)
    def GetOutput(self):
        return self.tri.GetOutput()
        
class ReconstructSurface:
    def __init__(self,polydata):
        self.data=polydata.GetOutput()
        self.surfrec=vtk.vtkSurfaceReconstructionFilter()
        self.surfrec.SetInput(self.data)
    def GetOutput(self):
        return self.surfrec.GetOutput()

class Surface:
    def __init__(self,d):
        self.data=d
        # Create the contour bands.
        self.cont_filter = vtk.vtkContourFilter()
        self.cont_filter.SetInput(d.GetOutput())
        self.cont_filter.SetValue(0,128)
#        self.cont_filter.GenerateValues(15, 0, 255)
        # Compute normals to give a better look.
        self.normals = vtk.vtkPolyDataNormals()
        self.normals.SetInput(self.cont_filter.GetOutput())
        self.normals.SetFeatureAngle(60)
        self.normals.ConsistencyOff()
        self.normals.SplittingOff()

        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInput(self.normals.GetOutput())
        self.mapper.SetColorModeToMapScalars()
#        self.mapper.SetScalarRange(0, 255)
        self.setColor(0,0,1)

    def setColor(self,r,g,b):
        self.lut = vtk.vtkColorTransferFunction()
        self.lut.AddRGBPoint(10,r,g,b)
        self.mapper.SetLookupTable(self.lut)


    def getPolyData(self):
        return self.cont_filter.GetOutput()

    def getMapper(self):
        return self.mapper

    def GetOutput(self):
        return self.normals.GetOutput()

class ColorMerge:
    def __init__(self):
        self.n=0
        self.channels=[]
        self.ncols=[]
        self.new=None

    def addInput(self,data,ncols):
        chl=data.GetOutput()
        self.channels.append(chl)
        self.ncols.append(ncols)
        chl.SetScalarTypeToUnsignedChar()
        self.xdim,self.ydim,self.zdim=chl.GetDimensions()
    	print "Data dimensions %d,%d,%d"%(self.xdim,self.ydim,self.zdim)

        if not self.new:
       	    self.new=vtk.vtkImageData()
            self.new.SetScalarTypeToUnsignedChar()
#    	    self.new.SetNumberOfScalarComponents(2)
    	    self.new.SetExtent(chl.GetExtent())
    	    self.new.SetDimensions(self.x1+1,self.y1+1,self.z1+1)
    	    self.new.AllocateScalars()

    def start(self):
        dc=self.doCoordinate
        self.r=range(0,len(self.channels))
        self.getters=[]
        self.setter=self.new.SetScalarComponentFromDouble
        for i in self.r:
            self.getters.append(self.channels[i].GetScalarComponentAsDouble)

        for x in range(0,self.x1):
            for y in range(0,self.y1):
                for z in range(0,self.z1):
                    dc(x,y,z)
                    
    def scaleScalar(self,scalar,n):
        pass       

    def doCoordinate(self,x,y,z):
        maxscal=0
        nchl=-1
        for i in self.r:
            scalar=self.getters[i](x,y,z)
            if scalar>maxscal:maxscal=scalar
            nchl=i
        self.setter(x,y,z,0,maxscal)


    def data(self):
    	return self.new
    def GetOutput(self):
        return self.new

