"""
A VTK light manipulation tool for wxPython.  This is sufficiently
general that it can be used by non-BioImageXD applications.  It basically
creates 8 different lights which can be configured using a GUI. 

This module was entirely written by Raymond Maple.  It was later
modified by Prabhu and made suitable for inclusion in MayaVi. Later
still it was modified by Kalle Pahajoki and made suitable for inclusion
in BioImageXD

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2002, Raymond C. Maple and Prabhu Ramachandran.
Copyright (c) 2005, Kalle Pahajoki. Modified for wxPython
"""

__author__ = "Raymond C. Maple <mapler@erinet.com>"
__version__ = "$Revision: 1.5 $"
__date__ = "$Date: 2003/10/22 20:23:55 $"
__credits__ = """This module was entirely written by Raymond Maple.
It was later modified by Prabhu Ramachandran and made suitable for
inclusion in MayaVi."""


#import Tkinter
#from vtkRenderWidget import vtkTkRenderWidget
import wx
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
#from vtk.wx.wxVTKRenderWindow import wxVTKRenderWindow
from math import pi, sin, cos, atan2, sqrt
import vtk
#import string
import sys
#import GUI.Dialogs
from GUI.RangedSlider import RangedSlider
import wx.lib.colourselect as csel


class Light:
	def __init__(self):
		self.source = vtk.vtkLight()
		self.glyph = LightGlyph()
		self.el = 0
		self.az = 0
		self.saved = []
		
	def __getState__(self):
		"""
		Created: 02.08.2005, KP
		Description: A getState method that saves the lights
		"""            
		self.save()
		odict = {"saved":self.saved}
		return odict
		
	def __set_pure_state__(self, state):
		"""
		Created: 02.08.2005, KP
		Description: Set the state of the light
		"""
		self.saved = state.saved
		self.restore()
		
	def switchOn(self):
		self.source.SwitchOn()
		self.glyph.show()

	def switchOff(self):
		self.source.SwitchOff()
		self.glyph.hide()
		
	def getState(self):
		return self.source.GetSwitch()

	def addGlyph(self, ren):
		self.glyph.add(ren)

	def moveTo(self, el, az):
		self.el = el
		self.az = az
		self.glyph.moveTo(el, az)
		self.source.SetPosition(self.toPos(el, az))

	def setElevation(self, el):
		self.moveTo(el, self.az)

	def getElevation(self):
		return self.el

	def setAzimuth(self, az):
		self.moveTo(self.el, az)

	def getAzimuth(self):
		return self.az

	def toPos(self, el, az):
		theta = az * pi / 180.0
		phi = (90.0 - el) * pi / 180.0
		x = sin(theta) * sin(phi)
		y = cos(phi)
		z = cos(theta) * sin(phi)
		return x, y, z

	def fromPos(self, (x, y, z) ):
		theta = atan2(x, z)
		phi = atan2(sqrt(x ** 2 + z ** 2), y)
		az = theta * 180.0 / pi
		el = 90.0 - phi * 180.0 / pi
		return el, az

	def getColor(self):
		rgb = self.source.GetColor()
		r = int(rgb[0] * 255); g = int(rgb[1] * 255); b = int(rgb[2] * 255)
		return (r, g, b)

	def setColor(self, rgb):
		r = rgb[0] / 255.0; g = rgb[1] / 255.0; b = rgb[2] / 255.0
		self.source.SetColor((r, g, b))

	def getIntensity(self):
		return self.source.GetIntensity()

	def setIntensity(self, i):
		self.source.SetIntensity(i)

	def sync(self):
		self.el, self.az = self.fromPos(self.source.GetPosition())
		if self.source.GetSwitch() == 1:
			self.glyph.show()
		else:
			self.glyph.hide()

	def save(self):
		self.saved = []
		self.saved.insert(0, self.source.GetSwitch())
		self.saved.insert(1, self.source.GetPosition())
		self.saved.insert(2, self.source.GetColor())
		self.saved.insert(3, self.source.GetIntensity())

	def restore(self):
		if len(self.saved):
			self.source.SetSwitch(self.saved[0])
			self.source.SetPosition(self.saved[1])
			self.source.SetColor(self.saved[2])
			self.source.SetIntensity(self.saved[3])
			del(self.saved)
			self.saved = []

	def update(self):
		self.sync()
		self.moveTo(self.el, self.az)

class LightGlyph:

	def __init__(self):
		nverts = 10
			
		# First build the cone portion
		cone = vtk.vtkConeSource()
		cone.SetResolution(nverts)
		cone.SetRadius(.08)
		cone.SetHeight(.2)
		cone.CappingOff()
	
		coneMapper = vtk.vtkPolyDataMapper()
		coneMapper.SetInput(cone.GetOutput())

		# Now take care of the capping polygon
		pts = vtk.vtkPoints()
		pts.SetNumberOfPoints(nverts)
	
		for i in range(0, nverts):
			theta = 2 * i * pi / nverts + pi / 2
			pts.InsertPoint(i, 0.8, .08 * sin(theta), .08 * cos(theta))
		
		poly = vtk.vtkPolygon()
		poly.GetPointIds().SetNumberOfIds(nverts)
		for i in range(0, nverts):
			poly.GetPointIds().SetId(i, i)
		
		pdata = vtk.vtkPolyData()
		pdata.Allocate(1, 1)
		pdata.InsertNextCell(poly.GetCellType(), poly.GetPointIds())
		pdata.SetPoints(pts)
		capmapper = vtk.vtkPolyDataMapper()
		capmapper.SetInput(pdata)

		self.el = 0.0
		self.az = 0.0

		self.coneActor = vtk.vtkActor()
		self.coneActor.SetMapper(coneMapper)
		self.coneActor.SetPosition(0.9, 0, 0)
		self.coneActor.SetOrigin(-0.9, 0, 0)
		self.coneActor.GetProperty().SetColor(0, 1, 1)
		self.coneActor.GetProperty().SetAmbient(.1)
		self.coneActor.RotateY(-90)

		self.capActor = vtk.vtkActor()
		self.capActor.SetMapper(capmapper)
		self.capActor.GetProperty().SetAmbientColor(1, 1, 0)
		self.capActor.GetProperty().SetAmbient(1)
		self.capActor.GetProperty().SetDiffuse(0)
		self.capActor.RotateY(-90)

	def add(self, ren):
		ren.AddActor(self.coneActor)
		ren.AddActor(self.capActor)

	def moveTo(self, el = None, az = None):
		self.coneActor.RotateZ(-self.el)
		self.coneActor.RotateY(-self.az)
		self.capActor.RotateZ(-self.el)
		self.capActor.RotateY(-self.az)
		if el != None: self.el = el
		if az != None: self.az = az
		self.coneActor.RotateY(self.az)
		self.coneActor.RotateZ(self.el)
		self.capActor.RotateY(self.az)
		self.capActor.RotateZ(self.el)

	def show(self):
		self.coneActor.VisibilityOn()
		self.capActor.VisibilityOn()

	def hide(self):
		self.coneActor.VisibilityOff()
		self.capActor.VisibilityOff()


def ArcActor(fromValue, to, rad = 1.0, axis = 'z', n = 20):
	fromValue = fromValue * pi / 180
	to = to * pi / 180
	angle = to - fromValue
	
	ppnts = vtk.vtkPoints()
	ppnts.SetNumberOfPoints(n)
	
	for i in range(0, n):
		theta = fromValue + i * angle / (n - 1)
		if axis == 'x':
			ppnts.InsertPoint(i, 0.0, cos(theta), sin(theta))
		elif axis == 'y':
			ppnts.InsertPoint(i, sin(theta), 0.0, cos(theta))
		elif axis == 'z':
			ppnts.InsertPoint(i, cos(theta), sin(theta), 0.0)
			
	pline = vtk.vtkPolyLine()
	pline.GetPointIds().SetNumberOfIds(n)
	for i in range(0, n):
		pline.GetPointIds().SetId(i, i)

	pdata = vtk.vtkPolyData()
	pdata.Allocate(1, 1)
	pdata.InsertNextCell(pline.GetCellType(), pline.GetPointIds())
	pdata.SetPoints(ppnts)
	
	mapper = vtk.vtkPolyDataMapper()
	mapper.SetInput(pdata)
	
	actor = vtk.vtkActor()
	actor.SetMapper(mapper)
	actor.GetProperty().SetColor(1, 0, 0)
	return actor

		
class LightSwitch(wx.CheckBox):
	def __init__(self, master, id, command = None):
		wx.CheckBox.__init__(self, master, -1)
		self.id = id
		self.Bind(wx.EVT_CHECKBOX, self.flip)
		self.command = command
		self.light = None
		self.Enable(0)

	def attach(self, light):
		self.light = light
		self.setState(light.getState())
		self.enable()

	def flip(self, event = None):
		if self.light.getState() == 0:
			self.setState(1)
			self.light.switchOn()
			if self.command != None:
				self.command(self.id, 1)
		else:
			self.setState(0)
			self.light.switchOff()
			if self.command != None:
				self.command(self.id, 0)

	def setState(self, pos):
		self.sw_state = pos
		self.SetValue(pos)

	def ledon(self):
		pass
	def ledoff(self):
		pass
		
	def enable(self):
		self.Enable(1)

	def disable(self):
		self.Enable(0)

	def update(self):
		self.setState(self.light.getState())


class ScrollScale(RangedSlider):
	def __init__(self, master, fromValue = 0.0, to = 1.0, command = None,
				  **kw):
		if kw.has_key("orient"):
			if kw["orient"] == "vertical":
				stl = wx.SB_VERTICAL
			else:
				stl = wx.SB_HORIZONTAL
		RangedSlider.__init__(self, master, -1, 1024, style = stl)
		self.setRange(0, 100, fromValue, to)
		self.Bind(wx.EVT_SCROLL, self.handle)
		self.oldval = -0xdeadbeef
		self.set((fromValue + to) * 0.5)
		self.command = command
		#self.event_add("<<Update>>","<ButtonRelease>")
		self.redraw()


	def set(self, val):
		changed = 0
		if val != self.oldval:
			changed = 1
			self.setScaledValue(val)
			self.redraw()
			self.oldval = val
		return changed

	def handle(self, event):
		newval = self.getScaledValue()
		#print "Handle, newval=",newval
		if self.command != None and self.set(newval) == 1:
			self.command(newval)
		self.update_event()

	def redraw(self):
		pass
		
class ElevationTool(ScrollScale):
	def __init__(self, master, ren, updateCallback):
		ScrollScale.__init__(self, master, fromValue = 90 , to = -90,
							orient = 'vertical', width = 12,
							command = self.apply)
		self.updateCallback = updateCallback
		self.light = None
		self.axis = ArcActor(0.0, 360.0, axis = 'y', n = 61)
		self.axis.GetProperty().SetColor(0.0, 1.0, 0.0)
		ren.AddActor(self.axis)
		#self.bind("<<Update>>", lambda e, s=self, w='world': s.updateCallback(w))
		
	def update_event(self):
		self.updateCallback('world')

	def apply(self, el, norender = 0):
		offset = sin(el / 180.0 * pi)
		scale = cos(el / 180.0 * pi)
		self.axis.SetScale(scale, 1.0, scale)
		self.axis.SetPosition(0.0, offset, 0.0)
		if self.light != None:
			self.light.setElevation(el)
		if norender == 0:
			self.updateCallback('lights')
		
	def setElevation(self, el, norender = 0):
		if self.set(el) == 1:
			self.apply(el, norender = norender)

	def attach(self, light):
		self.light = light
		self.setElevation(light.getElevation(), norender = 1)

	def update(self):
		self.setElevation(self.light.getElevation())


class AzimuthTool(ScrollScale):
	def __init__(self, master, ren, updateCallback):
		ScrollScale.__init__(self, master, fromValue = -180, to = 180,
							orient = 'horizontal', width = 12,
							command = self.apply)
		self.updateCallback = updateCallback
		self.light = None
		self.axis = ArcActor(0.0, 180.0, axis = 'x', n = 31)
		self.axis.GetProperty().SetColor(1.0, 0.0, 0.0)
		ren.AddActor(self.axis)
		#self.bind("<<Update>>", lambda e, s=self, w='world': s.updateCallback(w))

	def update_event(self):
		self.updateCallback('world')

	def apply(self, az, norender = 0):
		self.axis.SetOrientation(0.0, az, 0.0)
		if self.light != None:
			self.light.setAzimuth(az)
		if norender == 0:
			self.updateCallback('lights')

	def setAzimuth(self, az, norender = 0):
		if self.set(az) == 1:
			self.apply(az, norender = norender)

	def attach(self, light):
		self.light = light
		self.setAzimuth(light.getAzimuth(), norender = 1)

	def update(self):
		self.setAzimuth(self.light.getAzimuth())
		

class IntensityTool(RangedSlider):
	def __init__(self, master, updateCallback):
		RangedSlider.__init__(self, master, -1, 200, size = (300, -1))
		self.setRange(0, 100, 0.0, 2.0)
		self.Bind(wx.EVT_SCROLL, self.handler)
		light =  None
		self.updateCallback = updateCallback

	def handler(self, event):
		val = self.getScaledValue()
		if self.light != None:
			self.light.setIntensity(val)
			self.updateCallback('world')

	def attach(self, light):
		self.light = light
		self.setScaledValue(light.getIntensity())

	def update(self):
		val = self.light.getIntensity()
		self.setScaledValue(val)


class ColorTool(csel.ColourSelect):

	def __init__(self, master, updateCallback):
		#wx.BitmapButton.__init__(self,master,-1,self.swatch,size=(32,32))
		csel.ColourSelect.__init__(self, master, -1, "", size = (32, 32))
		#self.Bind(wx.EVT_COLOURSELECT,self.handler)

		self.light = None
		self.updateCallback = updateCallback
		#self.configure(state='disabled')
		self.Enable(0)
	
	def OnChange(self):
		color = self.GetValue()
		r, g, b = color.Red(), color.Green(), color.Blue()
		print "Setting light color to ", (r, g, b)
		self.light.setColor((r, g, b))
		self.updateCallback('world')
			
	def attach(self, light):
		self.light = light
		self.Enable(1)
		r, g, b = self.light.getColor()
		self.SetColour((r, g, b))

	def update(self):
		r, g, b = self.light.getColor()
		self.SetColour((r, g, b))


class LightTool(wx.Dialog):
	def __init__(self, master, lights, renwidget ):
		
		wx.Dialog.__init__(self, master, -1, "Lights configuration")
		#wx.Frame.__init__(self,master,-1)
		self.s = wx.BoxSizer(wx.VERTICAL)
		
		#self.panel=wx.Panel(self,-1)
		#self.s.Add(self.panel,1)
		self.panel = self
		
		
		self.connected = None
		self.num_lights_on = 0
		self.lights = lights
		self.renwidget = renwidget

		for l in lights:
			l.sync()
			print "Saving light ", l
			l.save()
		self.sizer = wx.GridBagSizer()
		
		self.ren = vtk.vtkRenderer()

		self.switchbank = wx.Panel(self.panel, -1, style = wx.RAISED_BORDER)
		self.switchsizer = wx.GridBagSizer()
		
		self.sw = []
		for i in range(0, 8):
			self.sw.insert(i, LightSwitch(self.switchbank, i,
										  command = self.switchhandler))
			self.switchsizer.Add(self.sw[i], (0, i + 1))
			self.sw[i].attach(lights[i])
			if lights[i].getState():
				self.num_lights_on += 1
				

		if self.num_lights_on == 1:
			for i in range(0, 8):
				if lights[i].getState():
					self.sw[i].disable()
	   
		self.switchbank.SetSizer(self.switchsizer)
		self.switchbank.SetAutoLayout(1)
		self.switchsizer.Fit(self.switchbank)


		self.azimuthBar = AzimuthTool(self.panel, self.ren, self.redraw)
		self.elevationBar = ElevationTool(self.panel, self.ren, self.redraw)
		
		self.f1 = wx.Panel(self.panel, -1)#,style=wx.RAISED_BORDER)
		self.f1sizer = wx.GridBagSizer()
		
		l = wx.StaticText(self.f1, -1, "Default lighting:")
		self.f1sizer.Add(l, (0, 0))
		
		b = wx.Button(self.f1, -1, "VTK")
		b.Bind(wx.EVT_BUTTON, lambda e = None:self.reset_handler('vtk'))
		self.f1sizer.Add(b, (0, 1))
		
		b = wx.Button(self.f1, -1, "Raymond")
		b.Bind(wx.EVT_BUTTON, lambda e = None:self.reset_handler('raymond'))
		self.f1sizer.Add(b, (0, 2))
		
		self.f1.SetSizer(self.f1sizer)
		self.f1.SetAutoLayout(1)
		self.f1sizer.Fit(self.f1)

		self.btnPanel = wx.Panel(self.panel, -1)
		self.btnsizer = wx.GridBagSizer()
		
		self.resetelaz = wx.Button(self.btnPanel, -1, "Set to headlight")
		self.resetelaz.Bind(wx.EVT_BUTTON, self.elazreset_handler)
		self.colorbtn = ColorTool(self.btnPanel, self.redraw)
		self.intensityLbl = wx.StaticText(self.btnPanel, -1, "Intensity:")
		self.intscale = IntensityTool(self.btnPanel, self.redraw)

		self.btnsizer.Add(self.resetelaz, (0, 0))
		self.btnsizer.Add(self.colorbtn, (0, 1))
		self.btnsizer.Add(self.intensityLbl, (1, 0))
		self.btnsizer.Add(self.intscale, (2, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		
		self.btnPanel.SetSizer(self.btnsizer)
		self.btnPanel.SetAutoLayout(1)
		
		self.btnsizer.Fit(self.btnPanel)

		self.f2 = wx.Panel(self.panel)
		self.f2sizer = wx.GridBagSizer()
		
		b = wx.Button(self.f2, -1, "OK")
		b.Bind(wx.EVT_BUTTON, self.onOkBtn)
		self.f2sizer.Add(b, (0, 0))

		b = wx.Button(self.f2, -1, "Apply")
		b.Bind(wx.EVT_BUTTON, self.apply_handler)
		self.f2sizer.Add(b, (0, 1))


		b = wx.Button(self.f2, -1, "Cancel")
		b.Bind(wx.EVT_BUTTON, self.onCancelBtn)
		self.f2sizer.Add(b, (0, 2))
				
		self.f2.SetSizer(self.f2sizer)
		self.f2.SetAutoLayout(1)
		self.f2sizer.Fit(self.f2)

		
		self.gfxwin = wxVTKRenderWindowInteractor(self.panel, -1, size = wx.Size(220, 200))
		#self.gfxwin.Initialize()
		self.gfxwin.Render()
		#self.gfxwin.Initialize()
		#self.gfxwin.Start()
		
		self.sizer.Add(self.gfxwin, (0, 0))
		self.sizer.Add(self.elevationBar, (0, 1), flag = wx.EXPAND | wx.TOP | wx.BOTTOM)
		self.sizer.Add(self.azimuthBar, (1, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
#        self.sizer.Add(self.resetelaz,(1,1))
		
		self.sizer.Add(self.switchbank, (2, 0), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		
		#self.sizer.Add(self.intscale,(0,2),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)
 #       self.sizer.Add(self.colorbtn,(1,2))
		
		self.sizer.Add(self.f1, (3, 0), span = (1, 3), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sizer.Add(self.btnPanel, (4, 0), span = (1, 3), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		self.sizer.Add(self.f2, (5, 0), span = (1, 3), flag = wx.EXPAND | wx.LEFT | wx.RIGHT)
		
		self.gfxwin.Bind(wx.EVT_LEFT_UP, lambda e, s = self, w = 'picked':s.connect(w, event = e))
		self.gfxwin.Bind(wx.EVT_LEFT_DOWN, lambda e:None)
		self.gfxwin.Bind(wx.EVT_MOTION, lambda e:None)

		self.gfxwin.Bind(wx.EVT_LEFT_UP, lambda e, s = self, w = 'picked':s.connect(w, event = e))
  

		#self.protocol("WM_DELETE_WINDOW", self.onCancelBtn)
		self.Bind(wx.EVT_CLOSE, self.onCancelBtn)

		self.gfxwin.GetRenderWindow().AddRenderer(self.ren)

		cam = self.ren.GetActiveCamera()
		x, y, z, a, b, c = (0, 0, 1, 0, 1, 0)
		cam.SetFocalPoint(0, 0, 0)
		cam.SetPosition(x, y, z)
		cam.SetViewUp(a, b, c)
		self.ren.ResetCamera()
		
		self.gfxwin.Render()
		self.ren.SetBackground(0.0, 0.0, 0.0)
		self.picker = vtk.vtkCellPicker()
		self.picker.SetTolerance(0.0005)

		for l in lights:
			l.addGlyph(self.ren)

		self.ren.GetActiveCamera().Zoom(1.6)
		self.connect('first')

		self.panel.SetSizer(self.sizer)
		self.panel.SetAutoLayout(1)
		self.sizer.Fit(self.panel)
		
		#self.SetSizer(self.s)
		#self.s.Fit(self)
		#self.SetAutoLayout(1)        

	def switchhandler(self, which, state):
		if state:
			if self.num_lights_on == 1: self.sw[self.connected].enable()
			self.num_lights_on += 1
			self.connect(which)
		else:
			if which == self.connected: self.connect('prev')
			self.num_lights_on -= 1
			if self.num_lights_on == 1: self.sw[self.connected].disable()
		self.redraw('all')

	def update(self):
		for i in self.sw:
			i.update()
		for i in (self.azimuthBar, self.elevationBar, self.intscale, self.colorbtn):
			i.update()

	def elazreset_handler(self, event):
		self.elevationBar.setElevation(0.0, norender = 1)
		self.azimuthBar.setAzimuth(0.0, norender = 1)
		self.redraw('all')

	def apply_handler(self, event = None):
		self.redraw('all')
	
	def onOkBtn(self, event = None):
		self.redraw('world')
		self.gfxwin.Destroy()
		self.Destroy()

	def onCancelBtn(self, event = None):
		for l in self.lights:
			l.restore()
		self.redraw('world')
		self.gfxwin.Destroy()
		self.Destroy()

	def reset_handler(self, mode):
		init_lights(self.lights, mode)
		self.update()
		self.connect('first')
		self.redraw('all')
		
	def connect(self, which, event = None):
		if which == 'first':
			nn = -1
			for n in range(1, 9):
				if self.lights[(nn + n) % 8].getState():
					lnum = (nn + n) % 8
					break
		elif which == 'prev':
			nn = self.connected
			for n in range(1, 9):
				if self.lights[(nn - n) % 8].getState() :
					lnum = (nn - n) % 8
					break
		elif which == 'next':
			nn = self.connected
			for n in range(1, 9):
				if self.lights[(nn + n) % 8].getState():
					lnum = (nn + n) % 8
					break
		elif which == 'picked':
			w, h = self.gfxwin.GetRenderWindow().GetSize()
			x, y = event.GetPosition()
			self.picker.Pick(x, h - y, 0, self.ren)
			actor = self.picker.GetActor()
			lnum = self.connected
			for i in range(0, 8):
				if actor == self.lights[i].glyph.coneActor or \
				   actor == self.lights[i].glyph.capActor:
					lnum = i
					break
		else:
			lnum = which

		if lnum != self.connected:
			if self.connected != None: self.sw[self.connected].ledoff()
			self.connected = lnum
			self.sw[lnum].ledon()
			self.elevationBar.attach(self.lights[lnum])
			self.azimuthBar.attach(self.lights[lnum])
			self.intscale.attach(self.lights[lnum])
			self.colorbtn.attach(self.lights[lnum])
			self.redraw('lights')

	def redraw(self, what):
		if what == 'lights':
			self.gfxwin.GetRenderWindow().Render()
		elif what == 'world':
			#self.renwidget.Render()
			self.gfxwin.GetRenderWindow().Render()
		elif what == 'all':
			self.gfxwin.GetRenderWindow().Render()
			self.renwidget.Render()


def init_lights(lights, mode = 'vtk'):
	"""Given a set of 8 lights and a mode, initializes the lights
	appropriately.  Valid modes currently are 'vtk' and 'raymond'.
	'vtk' is the default VTK light setup with only one light on in
	headlight mode.e 'raymond' is Raymond Maple's default
	configuration with three active lights."""
	if mode == 'raymond':
		for i in range(8):
			if i < 3 :
				lights[i].switchOn()
				lights[i].setIntensity(1.0)
				lights[i].setColor((255, 255, 255))
			else:
				lights[i].switchOff()
				lights[i].moveTo(0.0, 0.0)
				lights[i].setIntensity(1.0)
				lights[i].setColor((255, 255, 255))
				
		lights[0].moveTo(45.0, 45.0)
		lights[1].moveTo(-30.0, -60.0)
		lights[1].setIntensity(0.6)
		lights[2].moveTo(-30.0, 60.0)
		lights[2].setIntensity(0.5)
	else:
		for i in range(8):
			if i == 0 :
				lights[i].switchOn()
				lights[i].moveTo(0.0, 0.0)
				lights[i].setIntensity(1.0)
				lights[i].setColor((255, 255, 255))
			else:
				lights[i].switchOff()
	

class LightManager:
	"""Creates and manages 8 different lights."""
	
	def __init__(self, master, renwin, renderer, mode = 'vtk'):
		self.master = master
		self.renwin = renwin
		self.renderer = renderer
		self.cfg_widget = None
		self.lights = self._create_lights()
		self.init_lights(mode)

	def _create_lights(self):
		"""Creates the lights and adds them to the renderer."""
		ren = self.renderer
		lights = []
		for i in range(0, 8):
			lights.insert(i, Light())
			lights[i].source.SetLightTypeToCameraLight()

		if sys.platform != 'darwin':
			ren.ClearLights()

		# In vtk 3.2, the first light is always a headlight, and at
		# least as implemented in vtkRenderWidget, cannot be made
		# otherwise.  To avoid this behavior, an initial light is
		# added and switched off, never to be messed with again! Thus
		# the active lights are actually lights 1-9 in the renderer.

		# this hack seems to be necessary under VTK 4.x too.

		dumblight = vtk.vtkLight()
		dumblight.SwitchOff()
		ren.AddLight(dumblight)
		for l in lights:
			ren.AddLight(l.source)

		return lights
		
	def init_lights(self, mode = 'vtk'):
		init_lights(self.lights, mode)
		
	def __getState__(self):
		"""
		Created: 02.08.2005, KP
		Description: A getState method that saves the lights
		"""            
		odict = {"lights":self.lights}
		return odict

	def __set_pure_state__(self, state):
		"""
		Created: 11.04.2005, KP
		Description: Set the state of the light
		"""
		for i, light in enumerate(state.lights):
			self.lights[i].__set_pure_state__(light)
		
	def config(self, event = None):
		"""Shows the light configuration dialog."""
		if (not self.cfg_widget):
			self.cfg_widget = LightTool(self.master, self.lights,
										self.renwin)
			self.cfg_widget.Show()
