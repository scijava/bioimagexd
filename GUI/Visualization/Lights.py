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
#from tkColorChooser import askcolor
from math import pi, sin, cos, atan2, sqrt
import vtkpython
#import vtkPipeline.vtkMethodParser
import string
import sys
import Dialogs

def colorBitmap(bmp,color):
    img=bmp.ConvertToImage()
    w,h=bmp.GetSize()
    bmp2=wx.EmptyBitmap(w,h)
    dc = wx.MemoryDC()
    dc.SelectObject(bmp2)
    dc.BeginDrawing()
    dc.SetBackground(wx.Brush(color))
    dc.DrawRectangle(0,0,w,h)
    dc.DrawBitmap(bmp,0,0)
    dc.EndDrawing()
    dc.SelectObject(wx.NullBitmap)
    dc = None    
    return bmp2


class Light:
    def __init__(self):
        self.source = vtkpython.vtkLight()
        self.glyph = LightGlyph()
        self.el = 0
        self.az = 0

    def switchon(self):
        self.source.SwitchOn()
        self.glyph.show()

    def switchoff(self):
        self.source.SwitchOff()
        self.glyph.hide()
        
    def getstate(self):
        return ['off','on'][self.source.GetSwitch()]

    def addglyph(self, ren):
        self.glyph.add(ren)

    def moveto(self, el, az):
        self.el = el
        self.az = az
        self.glyph.moveto(el, az)
        self.source.SetPosition(self.topos(el, az))

    def setelevation(self, el):
        self.moveto(el, self.az)

    def getelevation(self):
        return self.el

    def setazmuth(self, az):
        self.moveto(self.el, az)

    def getazmuth(self):
        return self.az

    def topos(self, el, az):
        theta = az*pi/180.0
        phi = (90.0-el)*pi/180.0
        x = sin(theta)*sin(phi)
        y = cos(phi)
        z = cos(theta)*sin(phi)
        return x, y, z

    def frompos(self, (x, y, z) ):
        theta = atan2(x, z)
        phi = atan2(sqrt(x**2+z**2), y)
        az = theta*180.0/pi
        el = 90.0 - phi*180.0/pi
        return el, az

    def getcolor(self):
        rgb = self.source.GetColor()
        r = int(rgb[0]*255); g = int(rgb[1]*255); b = int(rgb[2]*255);
        return (r, g, b)

    def setcolor(self, rgb):
        r = rgb[0] / 255.0; g = rgb[1] / 255.0; b = rgb[2] / 255.0
        self.source.SetColor((r, g, b))

    def getintensity(self):
        return self.source.GetIntensity()

    def setintensity(self, i):
        self.source.SetIntensity(i)

    def sync(self):
        self.el, self.az = self.frompos(self.source.GetPosition())
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
        self.source.SetSwitch(self.saved[0])
        self.source.SetPosition(self.saved[1])
        self.source.SetColor(self.saved[2])
        self.source.SetIntensity(self.saved[3])
        del(self.saved)

    def update(self):
        self.sync()
        self.moveto(self.el, self.az)

class LightGlyph:

    def __init__(self):
        nverts = 10
            
        # First build the cone portion
        cone = vtkpython.vtkConeSource()
        cone.SetResolution(nverts)
        cone.SetRadius(.08)
        cone.SetHeight(.2)
        cone.CappingOff()
    
        coneMapper = vtkpython.vtkPolyDataMapper()
        coneMapper.SetInput(cone.GetOutput())

        # Now take care of the capping polygon
        pts = vtkpython.vtkPoints()
        pts.SetNumberOfPoints(nverts)
    
        for i in range(0, nverts):
            theta = 2*i*pi/nverts + pi/2
            pts.InsertPoint(i,0.8,.08*sin(theta),.08*cos(theta))
        
        poly = vtkpython.vtkPolygon()
        poly.GetPointIds().SetNumberOfIds(nverts)
        for i in range(0, nverts):
            poly.GetPointIds().SetId(i, i)
        
        pdata = vtkpython.vtkPolyData()
        pdata.Allocate(1, 1)
        pdata.InsertNextCell(poly.GetCellType(), poly.GetPointIds())
        pdata.SetPoints(pts)
        capmapper = vtkpython.vtkPolyDataMapper()
        capmapper.SetInput(pdata)

        self.el = 0.0
        self.az = 0.0

        self.coneActor = vtkpython.vtkActor()
        self.coneActor.SetMapper(coneMapper)
        self.coneActor.SetPosition(0.9,0,0)
        self.coneActor.SetOrigin(-0.9,0,0)
        self.coneActor.GetProperty().SetColor(0, 1, 1)
        self.coneActor.GetProperty().SetAmbient(.1)
        self.coneActor.RotateY(-90)

        self.capActor = vtkpython.vtkActor()
        self.capActor.SetMapper(capmapper)
        self.capActor.GetProperty().SetAmbientColor(1, 1,0)
        self.capActor.GetProperty().SetAmbient(1)
        self.capActor.GetProperty().SetDiffuse(0)
        self.capActor.RotateY(-90)

    def add(self, ren):
        ren.AddActor(self.coneActor)
        ren.AddActor(self.capActor)

    def moveto(self, el=None, az = None):
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


def ArcActor(from_, to, rad=1.0, axis='z', n=20):
    from_ = from_*pi/180
    to = to*pi/180
    angle = to - from_
    
    ppnts = vtkpython.vtkPoints()
    ppnts.SetNumberOfPoints(n)
    
    for i in range(0, n):
        theta = from_+i*angle/(n-1)
        if axis == 'x':
            ppnts.InsertPoint(i,0.0, cos(theta), sin(theta))
        elif axis == 'y':
            ppnts.InsertPoint(i, sin(theta),0.0, cos(theta))
        elif axis == 'z':
            ppnts.InsertPoint(i, cos(theta), sin(theta),0.0)
            
    pline = vtkpython.vtkPolyLine()
    pline.GetPointIds().SetNumberOfIds(n)
    for i in range(0, n):
        pline.GetPointIds().SetId(i, i)

    pdata = vtkpython.vtkPolyData()
    pdata.Allocate(1, 1)
    pdata.InsertNextCell(pline.GetCellType(), pline.GetPointIds())
    pdata.SetPoints(ppnts)
    
    mapper = vtkpython.vtkPolyDataMapper()
    mapper.SetInput(pdata)
    
    actor = vtkpython.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(1,0,0)
    return actor


class LightSwitch(wx.Panel):
    led_data = "\
    #define small_led_width 9\
    #define small_led_height 5\
    static unsigned char small_led_bits[] = {\
    0x00, 0x00, 0x7c, 0x00, 0x7c, 0x00, 0x7c, 0x00, 0x00, 0x00 };"

    def __init__(self, master, id, command=None):
        wx.Panel.__init__(self,master,-1)
        self.sizer=wx.GridBagSizer()
        #Tkinter.Frame.__init__(self, master, borderwidth=2, relief='groove')
        self.id = id
        self.command = command
        self.light = None
        #self.button = Tkinter.Button(self, borderwidth=2)
        
        #self.led = Tkinter.BitmapImage(data=self.led_data)
        self.led = wx.Bitmap(self.led_data)
        self.button = wx.BitmapButton(self,-1,self.led)
        #self.led = wx.Image()
        #self.pad = Tkinter.Frame(self, height=5)
        self.pad = wx.Panel(self,-1,size=(-1,5))

        #self.button.configure(image=self.led, command=self.flip)
        #self.button.configure(padx=0, pady=0)
        #self.pad.grid(row=0)
        #self.button.grid(row=1)
        #self.disable()
        self.sizer.Add(self.pad,(0,0))
        self.sizer.Add(self.button,(1,0))
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.Enable(0)

    def attach(self, light):
        self.light = light
        self.setposition(light.getstate())
        self.enable()

    def flip(self):
        if self.light.getstate() == 'off':
            self.setposition('on')
            self.light.switchon()
            if self.command != None:
                self.command(self.id,'on')
        else:
            self.setposition('off')
            self.light.switchoff()
            if self.command != None:
                self.command(self.id,'off')

    def setposition(self, pos):
        self.sizer.Detach(self.button)
        self.sizer.Detach(self.pad)
        if pos == 'on' :
            self.sw_state = 1
            self.sizer.Add(self.button,(0,0))
            self.sizer.Add(self.pad,(1,0))
            #self.button.grid(row=0)
            #self.pad.grid(row=1)
        else:
            self.sw_state = 0
            self.sizer.Add(self.button,(1,0))
            self.sizer.Add(self.pad,(0,0))
            #self.pad.grid(row=0)
            #self.button.grid(row=1)

    def ledon(self):
        print "ledon"
        self.led = colorBitmap(self.led,(255,0,0))
        self.button.SetBitmapLabel(self.led)
        #self.led.configure(foreground='red')

    def ledoff(self):
        print "ledoff"
        self.led = colorBitmap(self.led,(0,0,0))
        self.button.SetBitmapLabel(self.led)
        #self.led.configure(foreground='black')

    def enable(self):
        self.button.Enable(1)
#        self.button.configure(state='normal')

    def disable(self):
        self.button.Enable(0)
        #self.button.configure(state='disabled')

    def update(self):
        self.setposition(self.light.getstate())


class ScrollScale(wx.ScrollBar):
    def __init__(self, master, from_=0.0, to=1.0, size=0.1, command=None,
                  **kw):
        #Tkinter.Scrollbar.__init__(self, master, kw)
        #Tkinter.Scrollbar.configure(self, command=self.handle, repeatinterval=20)
        #wx.ScrollBar.__init__(self,master,-1,minValue = from_, maxValue = to)
        wx.ScrollBar.__init__(self,master,-1)
        self.SetScrollbar(from_,1,to,1,1)
        self.Bind(wx.EVT_SCROLL,self.handle)
        self.from_ = from_
        self.to = to
        self.size = size
        self.rendercmd=None
        self.hsize = size/2
        if to > from_:
            self.unit = 1.0
            self.page = 15.0
        else:
            self.unit = -1.0
            self.page = -15.0
        self.val = 0.5*(from_+to)
        self.command = command
        #self.event_add("<<Update>>","<ButtonRelease>")
        self.redraw()

    def mapv(self, val):
        val = (val - self.from_)/(self.to - self.from_)
        return (val*(1.0-self.size) + self.hsize)

    def imapv(self, val):
        val = (val-self.hsize)/(1.0-self.size)
        return (val*(self.to-self.from_)+self.from_)

    def set(self, val):
        changed = 0
        if val < min(self.from_, self.to):
            val = min(self.from_, self.to)
        elif val > max(self.from_, self.to):
            val = max(self.from_, self.to)
        if val != self.val:
            changed = 1
            self.val = val
            self.redraw()
        return changed

    def handle(self, event):
        b=self.GetThumbPosition()
        print "Handle, b=",b
        newval = self.imapv(float(b)+self.hsize)
##        if a == "moveto":
##            newval = self.imapv(float(b)+self.hsize)
##        elif c == "units":
##            newval = self.val+float(b)*self.unit
##            self.event_generate("<<Update>>")
##        else:
##            newval = self.val+float(b)*self.page
##            self.event_generate("<<Update>>")
        if self.command != None and self.set(newval) == 1:
            self.command(self.val)

    def redraw(self):
        val = self.mapv(self.val)
        #Tkinter.Scrollbar.set(self, val-self.hsize, val+self.hsize)
        #self.SetValue(val)
        self.SetThumbPosition(val)
        if self.rendercmd:
            self.rendercmd('world')    

class ElTool(ScrollScale):
    def __init__(self, master, ren, rendercmd):
        ScrollScale.__init__(self, master, size=.1, from_=90, to=-90,
                            orient='vertical', width=12,
                            command = self.apply)
        self.rendercmd = rendercmd
        self.light = None
        self.axis = ArcActor(0.0, 360.0, axis='y', n = 61)
        self.axis.GetProperty().SetColor(0.0, 1.0,0.0)
        ren.AddActor(self.axis)
        #self.bind("<<Update>>", lambda e, s=self, w='world': s.rendercmd(w))
        

    def apply(self, el, norender=0):
        offset = sin(el/180.0*pi)
        scale = cos(el/180.0*pi)
        self.axis.SetScale(scale, 1.0, scale)
        self.axis.SetPosition(0.0, offset,0.0)
        if self.light != None:
            self.light.setelevation(el)
        if norender == 0:
            self.rendercmd('lights')
        
    def setel(self, el, norender=0):
        if self.set(el) == 1:
            self.apply(el, norender=norender)

    def attach(self, light):
        self.light = light
        self.setel(light.getelevation(), norender=1)

    def update(self):
        self.setel(self.light.getelevation())


class AzTool(ScrollScale):
    def __init__(self, master, ren, rendercmd):
        ScrollScale.__init__(self, master, size=.1, from_=-180, to=180,
                            orient='horizontal', width=12,
                            command = self.apply)
        self.rendercmd = rendercmd
        self.light = None
        self.axis = ArcActor(0.0, 180.0, axis='x', n = 31)
        self.axis.GetProperty().SetColor(1.0,0.0,0.0)
        ren.AddActor(self.axis)
        #self.bind("<<Update>>", lambda e, s=self, w='world': s.rendercmd(w))

    def apply(self, az, norender=0):
        self.axis.SetOrientation(0.0, az,0.0)
        if self.light != None:
            self.light.setazmuth(az)
        if norender == 0:
            self.rendercmd('lights')

    def setaz(self, az, norender=0):
        if self.set(az) == 1:
            self.apply(az, norender=norender)

    def attach(self, light):
        self.light = light
        self.setaz(light.getazmuth(), norender=1)

    def update(self):
        self.setaz(self.light.getazmuth())
        

class IntensityTool(wx.Slider):
    def __init__(self, master, rendercmd):
        #Tkinter.Scale.__init__(self, master, orient='vertical',
        #                       width=10, showvalue=0,
        #                       sliderlength=15, from_=1.0, to=0.0,
        #                       resolution=.01, sliderrelief='ridge')
        #self.bind("<ButtonRelease>", self.handler)
        wx.Slider.__init__(self,master,-1,size=(10,-1),minValue=0,maxValue=15,style=wx.SL_VERTICAL)
        self.Bind(wx.EVT_SCROLL,self.handler)
        light =  None
        self.rendercmd = rendercmd

    def handler(self, event):
        
        val=self.GetValue()
        print "handler! val=",val,val/15.0
        val/=15.0
        if self.light != None:
            self.light.setintensity(val)
            self.rendercmd('world')

    def attach(self, light):
        self.light = light
        self.SetValue(light.getintensity()*15.0)

    def update(self):
        val=self.light.getintensity()*15.0
        self.SetValue(val)


class ColorTool(wx.BitmapButton):
    swatch_data = '#define solid_width 14\
    #define solid_height 14\
    static unsigned char solid_bits[] = {\
    0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f,\
    0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f, 0xff, 0x3f,\
    0xff, 0x3f, 0xff, 0x3f };'

    def __init__(self, master, rendercmd):
        #self.swatch = Tkinter.BitmapImage(data=self.swatch_data)
        self.swatch = wx.Bitmap(self.swatch_data)
#        Tkinter.Button.__init__(self, master, image=self.swatch,
#                                relief='raised',
#                                command=self.handler, width=12, height=12)
        wx.BitmapButton.__init__(self,master,-1,self.swatch,size=(32,32))
        self.Bind(wx.EVT_BUTTON,self.handler)

        self.light=None
        self.rendercmd = rendercmd
        #self.configure(state='disabled')
        self.Enable(0)
    
    def handler(self,event):
        r, g, b = self.light.getcolor()
        color = Dialogs.askcolor((r, g, b))
        if color != (None, None) :
            self.swatch = colorBitmap(self.swatch,color[0])
            self.SetBitmapLabel(self.swatch)
            #self.swatch.configure(foreground="#%02x%02x%02x" % color[0])
            self.light.setcolor(color[0])
            self.rendercmd('world')
            
    def attach(self, light):
        self.light = light
        self.Enable(1)
        #self.configure(state='normal')
        r, g, b = self.light.getcolor()
        self.swatch = colorBitmap(self.swatch,(r,g,b))
        self.SetBitmapLabel(self.swatch)
        #self.swatch.configure(foreground="#%02x%02x%02x" % (r, g, b))

    def update(self):
        r, g, b = self.light.getcolor()
        self.swatch = colorBitmap(self.swatch,(r,g,b))
        self.SetBitmapLabel(self.swatch)
        #self.swatch.configure(foreground="#%02x%02x%02x" % (r, g, b))


class LightTool(wx.Frame):
    left_data = "\
    #define small_left_width 11\
    #define small_left_height 11\
    static unsigned char small_left_bits[] = {\
    0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x60, 0x00, 0x70, 0x00, 0x78, 0x00,\
    0x70, 0x00, 0x60, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00 };"

    right_data = "\
    #define small_right_width 11\
    #define small_right_height 11\
    static unsigned char small_right_bits[] = {\
    0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x30, 0x00, 0x70, 0x00, 0xf0, 0x00,\
    0x70, 0x00, 0x30, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00 };"

    headlight_data = "\
    #define headlight_width 10\
    #define headlight_height 10\
    static unsigned char headlight_bits[] = {\
    0x00, 0x00, 0x3e, 0x00, 0x1e, 0x00, 0x2e, 0x00, 0x36, 0x00, 0x5a, 0x00,\
    0x60, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00 };"


    def __init__(self, master, lights, renwidget ):
        #Tkinter.Toplevel.__init__(self, master)
        print "master=",master
        wx.Frame.__init__(self,master,-1)
        self.connected = None
        self.num_lights_on = 0
        self.lights = lights
        self.renwidget = renwidget

        for l in lights:
            l.sync()
            l.save()
        self.sizer = wx.GridBagSizer()
        
        self.gfxwin = wxVTKRenderWindowInteractor(self,-1,size=(220,200))
        self.ren = vtkpython.vtkRenderer()

        self.switchbank = wx.Panel(self,-1,style=wx.RAISED_BORDER)
        self.switchsizer=wx.GridBagSizer()
        
        self.leftarrow = wx.Bitmap(self.left_data)
        
        self.bprev = wx.BitmapButton(self.switchbank,-1,self.leftarrow)
        self.bprev.Bind(wx.EVT_BUTTON,lambda s=self,w='prev':s.connect(w))
        self.switchsizer.Add(self.bprev,(0,0))
        self.sw=[]
        for i in range(0, 8):
            self.sw.insert(i, LightSwitch(self.switchbank, i,
                                          command=self.switchhandler))
            self.switchsizer.Add(self.sw[i],(0,i+1))
            self.sw[i].attach(lights[i])
            if lights[i].getstate() == 'on':
                self.num_lights_on += 1
                

        if self.num_lights_on == 1:
            for i in range(0, 8):
                if lights[i].getstate() == 'on':
                    self.sw[i].disable()
       
        self.rightarrow = wx.Bitmap(self.right_data)
        self.bnext = wx.BitmapButton(self.switchbank,-1,self.rightarrow)
        self.bnext.Bind(wx.EVT_BUTTON,lambda s=self,w='next':s.connect(w))
        self.switchsizer.Add(self.bnext,(0,9))

        self.switchbank.SetSizer(self.switchsizer)
        self.switchbank.SetAutoLayout(1)
        self.switchsizer.Fit(self.switchbank)


        self.azbar = AzTool(self, self.ren, self.redraw)
        self.elbar = ElTool(self, self.ren, self.redraw)
        self.headlight = wx.Bitmap(self.headlight_data)

        self.resetelaz = wx.BitmapButton(self,-1,self.headlight,size=(32,32))
        self.resetelaz.Bind(wx.EVT_BUTTON,self.elazreset_handler)

        self.intscale = IntensityTool(self, self.redraw)
        self.colorbtn = ColorTool(self, self.redraw)

        #self.f1 = Tkinter.Frame(self, relief='ridge', bd=2)
        self.f1 = wx.Panel(self,-1,style=wx.RAISED_BORDER)
        self.f1sizer=wx.GridBagSizer()
        
        #l = Tkinter.Label(self.f1, text="Default lighting:")
        #l.grid(row=0, column=0, sticky='w')              
        l = wx.StaticText(self.f1,-1,"Default lighting:")
        self.f1sizer.Add(l,(0,0))
        
        #b = Tkinter.Button(self.f1, text="VTK", width=6, 
        #                   command=lambda e=None: self.reset_handler('vtk'))        
        b = wx.Button(self.f1,-1,"VTK")
        b.Bind(wx.EVT_BUTTON,lambda e=None:self.reset_handler('vtk'))
            
        #b.grid(row=0, column=1, sticky='e')
        self.f1sizer.Add(b,(0,1))
        
        #b = Tkinter.Button(self.f1, text="Raymond", 
        #                   command=lambda e=None:
        #                   self.reset_handler('raymond'))
        #b.grid(row=0, column=2, sticky='w', padx=5)
        b = wx.Button(self.f1,-1,"Raymond")
        b.Bind(wx.EVT_BUTTON,lambda e=None:self.reset_handler('raymond'))
        self.f1sizer.Add(b,(0,2))
        
        self.f1.SetSizer(self.f1sizer)
        self.f1.SetAutoLayout(1)
        self.f1sizer.Fit(self.f1)
        
        self.f2 = wx.Panel(self)
        self.f2sizer=wx.GridBagSizer()
        #b = Tkinter.Button(self.f2, text="OK", underline=0, width=6,
        #                   command=self.ok_handler)
        #b.grid(row=0, column=0, sticky='e', padx=5)
        
        b = wx.Button(self.f2,-1,"OK")
        b.Bind(wx.EVT_BUTTON,self.ok_handler)
        self.f2sizer.Add(b,(0,0))
                
#        Tkinter.Frame(self.f2, width=30).grid(row=0, column=1)
        #b = Tkinter.Button(self.f2, text="Cancel", underline=0,
        #                   command=self.cancel_handler)
        #b.grid(row=0, column=2, sticky='w', padx=5)
        b = wx.Button(self.f2,-1,"Cancel")
        b.Bind(wx.EVT_BUTTON,self.cancel_handler)
        self.f2sizer.Add(b,(0,2))
                
        self.f2.SetSizer(self.f2sizer)
        self.f2.SetAutoLayout(1)
        self.f2sizer.Fit(self.f2)
        #self.bind('<KeyPress-c>', self.cancel_handler)
        #self.bind('<KeyPress-C>', self.cancel_handler)

        #self.gfxwin.grid(row=0, column=0)
        self.sizer.Add(self.gfxwin,(0,0))
        #self.elbar.grid(row=0, column=1, sticky='ns', padx=2)
        #self.azbar.grid(row=1, column=0, sticky='ew', pady=2)
        self.sizer.Add(self.elbar,(0,1),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)
        self.sizer.Add(self.azbar,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)

        #self.resetelaz.grid(row=1, column=1)
        #self.switchbank.grid(row=2, column=0, sticky='ew')
        self.sizer.Add(self.resetelaz,(1,1))
        self.sizer.Add(self.switchbank,(2,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        #self.intscale.grid(row=0, column=2, padx=5, sticky='ns')
        #self.colorbtn.grid(row=1, column=2, padx=2, pady=2)
        self.sizer.Add(self.intscale,(0,2),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)
        self.sizer.Add(self.colorbtn,(1,2))
        
        #self.f1.grid(row=3, column=0, columnspan=3, sticky='ew', pady=3)
        #self.f2.grid(row=4, column=0, columnspan=3, sticky='ew', pady=3)
        self.sizer.Add(self.f1,(3,0),span=(1,3),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.sizer.Add(self.f2,(4,0),span=(1,3),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        
        self.gfxwin.Bind(wx.EVT_LEFT_UP,lambda e,s=self,w='picked':s.connect(w,event=e))
        self.gfxwin.Bind(wx.EVT_LEFT_DOWN,lambda e:None)
        self.gfxwin.Bind(wx.EVT_MOTION,lambda e:None)
        #self.gfxwin.bind("<ButtonRelease>",
        #                 lambda e, s=self, w='picked': s.connect(w, event=e))
        #self.gfxwin.bind("<ButtonPress>", lambda e:None)
        #self.gfxwin.bind("<B1-Motion>", lambda e:None)
        #self.gfxwin.bind("<B2-Motion>", lambda e:None)
        #self.gfxwin.bind("<B3-Motion>", lambda e:None)

        #self.protocol("WM_DELETE_WINDOW", self.cancel_handler)
        self.Bind(wx.EVT_CLOSE,self.cancel_handler)

        self.gfxwin.GetRenderWindow().AddRenderer(self.ren)
        self.ren.SetBackground(0.0,0.0,0.0)
        self.picker = vtkpython.vtkCellPicker()
        self.picker.SetTolerance(0.0005)

        for l in lights:
            l.addglyph(self.ren)

        self.ren.GetActiveCamera().Zoom(1.6)
        self.connect('first')
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    def switchhandler(self, which, state):
        if state == 'on':
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
        for i in (self.azbar, self.elbar, self.intscale, self.colorbtn):
            i.update()

    def elazreset_handler(self,event):
        self.elbar.setel(0.0, norender=1)
        self.azbar.setaz(0.0, norender=1)
        self.redraw('all')
    
    def ok_handler(self, event=None):
        self.redraw('world')
        #self.destroy()
        self.Close()
        #self.quit()

    def cancel_handler(self, event=None):
        for l in self.lights:
            l.restore()
        self.redraw('world')
        #self.destroy()
        #self.quit()
        self.Close()

    def reset_handler(self, mode):
        init_lights(self.lights, mode)
        self.update()
        self.connect('first')
        self.redraw('all')
        
    def connect(self, which, event=None):
        if which == 'first':
            nn = -1
            for n in range(1, 9):
                if self.lights[(nn+n)%8].getstate() == 'on':
                    lnum = (nn+n)%8
                    break
        elif which == 'prev':
            nn = self.connected
            for n in range(1, 9):
                if self.lights[(nn-n)%8].getstate() == 'on':
                    lnum = (nn-n)%8
                    break
        elif which == 'next':
            nn = self.connected
            for n in range(1, 9):
                if self.lights[(nn+n)%8].getstate() == 'on':
                    lnum = (nn+n)%8
                    break
        elif which == 'picked':
            w, h = self.gfxwin.GetRenderWindow().GetSize()
            x,y=event.GetPosition()
            self.picker.Pick(x, h-y,0, self.ren)
            actor= self.picker.GetActor()
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
            self.elbar.attach(self.lights[lnum])
            self.azbar.attach(self.lights[lnum])
            self.intscale.attach(self.lights[lnum])
            self.colorbtn.attach(self.lights[lnum])
            self.redraw('lights')

    def redraw(self, what):
        if what == 'lights':
            self.gfxwin.GetRenderWindow().Render()
        elif what == 'world':
            self.renwidget.Render()
        elif what == 'all':
            self.gfxwin.GetRenderWindow().Render()
            self.renwidget.Render()


def init_lights(lights, mode='vtk'):
    """Given a set of 8 lights and a mode, initializes the lights
    appropriately.  Valid modes currently are 'vtk' and 'raymond'.
    'vtk' is the default VTK light setup with only one light on in
    headlight mode.e 'raymond' is Raymond Maple's default
    configuration with three active lights."""
    if mode == 'raymond':
        for i in range(8):
            if i < 3 :
                lights[i].switchon()
                lights[i].setintensity(1.0)
                lights[i].setcolor((255, 255, 255))
            else:
                lights[i].switchoff()
                lights[i].moveto(0.0, 0.0)
                lights[i].setintensity(1.0)
                lights[i].setcolor((255, 255, 255))
                
        lights[0].moveto(45.0, 45.0)
        lights[1].moveto(-30.0,-60.0)
        lights[1].setintensity(0.6)
        lights[2].moveto(-30.0, 60.0)
        lights[2].setintensity(0.5)
    else:
        for i in range(8):
            if i == 0 :
                lights[i].switchon()
                lights[i].moveto(0.0, 0.0)
                lights[i].setintensity(1.0)
                lights[i].setcolor((255, 255, 255))
            else:
                lights[i].switchoff()
    

class LightManager:
    """Creates and manages 8 different lights."""
    
    def __init__(self, master, renwin, renderer, mode='vtk'):
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

        dumblight = vtkpython.vtkLight()
        dumblight.SwitchOff()
        ren.AddLight(dumblight)
        for l in lights:
            ren.AddLight(l.source)

        return lights
        
    def init_lights(self, mode='vtk'):
        init_lights(self.lights, mode)

    def config(self, event=None):
        """Shows the light configuration dialog."""
        if (not self.cfg_widget):
            self.cfg_widget = LightTool(self.master, self.lights,
                                        self.renwin)
            self.cfg_widget.Show()
            #self.cfg_widget.focus_set()
            #self.cfg_widget.transient(self.master)
            #self.cfg_widget.mainloop()
        #elif (self.cfg_widget and self.cfg_widget.winfo_exists()):
        #    self.cfg_widget.deiconify()
        #    self.cfg_widget.lift()
        #    self.cfg_widget.focus_set()


def main():
    
    """A simple example illustrating the use of the Light manipulation
    code in a simple VTK application."""
    
    root = Tkinter.Tk()
    renwidget = vtkTkRenderWidget(root,width=300,height=300)
    renwidget.pack()
    renWin = renwidget.GetRenderWindow()
    ren1 = vtkpython.vtkRenderer()
    renWin.AddRenderer( ren1 )

    def halt(event=None):
        event.widget.winfo_toplevel().destroy()

    # Call to define the lights and initialize them in the "raymond"
    # configuration.  This is all you need to do to use the light
    # manipulator!    
    ################################################
    lm = LightManager(root, renwidget, ren1, mode='raymond')
    renwidget.bind("<l>", lm.config)
    ################################################

    renwidget.bind("<e>", halt)
    root.protocol("WM_DELETE_WINDOW", halt)

    sphere = vtkpython.vtkSphereSource()
    sphereMapper = vtkpython.vtkPolyDataMapper()
    sphereMapper.SetInput( sphere.GetOutput() )
    sphereActor = vtkpython.vtkLODActor()
    sphereActor.SetMapper( sphereMapper )

    cone = vtkpython.vtkConeSource()
    glyph = vtkpython.vtkGlyph3D()
    glyph.SetInput( sphere.GetOutput() )
    glyph.SetSource(cone.GetOutput())
    glyph.SetVectorModeToUseNormal()
    glyph.SetScaleModeToScaleByVector()
    glyph.SetScaleFactor( 0.25 )
    glyph.ReleaseDataFlagOn()

    spikeMapper = vtkpython.vtkPolyDataMapper()
    spikeMapper.SetInput( glyph.GetOutput() )
    spikeActor = vtkpython.vtkLODActor()
    spikeActor.SetMapper( spikeMapper )

    ren1.AddActor( sphereActor )
    ren1.AddActor( spikeActor )
    ren1.SetBackground( 0.1, 0.2, 0.4 )
    renWin.SetSize( 300, 300 )
    del renWin

    root.mainloop()

if __name__ == "__main__":
    main()
