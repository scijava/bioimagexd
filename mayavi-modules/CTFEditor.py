#!/usr/bin/env python

"""
This module defines a useful Tkinter based GUI editor for color
transfer functions.

Much of the original code was written by Gerard Gorman.  Prabhu
Ramachandran cleaned it up and incorporated it into the MayaVi
sources.

TODO:

  + Create a simple application like the Lut_Editor that can be used
    to edit and create LUTs.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Gerard Gorman and Prabhu Ramachandran"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2003/10/15 22:41:28 $"

import Tkinter
import string
import vtkpython


def save_ctfs(volume_property):
    """Given a vtkVolumeProperty it saves the state of the RGB and
    opacity CTF to a dictionary and returns that."""
    vp = volume_property
    ctf = vp.GetRGBTransferFunction()
    otf = vp.GetScalarOpacity()
    s1, s2 = ctf.GetRange()
    nc = ctf.GetSize()
    ds = float(s2-s1)/(nc - 1)
    rgb, a = [], []
    for i in range(nc):
        rgb.append(ctf.GetColor(s1 + i*ds))
        a.append(otf.GetValue(s1 + i*ds))
    return {'range': (s1, s2), 'rgb':rgb, 'alpha':a}

def load_ctfs(saved_data, volume_property):
    """ Given the saved data produced via save_ctfs(), this member
    sets the state of the passed volume_property appropriately"""
    s1, s2 = saved_data['range']
    rgb = saved_data['rgb']
    a = saved_data['alpha']
    nc = len(a)
    ds = float(s2-s1)/(nc - 1)
    ctf = vtkpython.vtkColorTransferFunction ()
    otf = vtkpython.vtkPiecewiseFunction()
    for i in range(nc):
        v = s1 + i*ds
        ctf.AddRGBPoint(v, *(rgb[i]))
        otf.AddPoint(v, a[i])
    volume_property.SetColor(ctf)
    volume_property.SetScalarOpacity(otf)

def rescale_ctfs(volume_property, new_range):
    """ Given the volume_property with a new_range for the data while
    using the same transfer functions, this function rescales the
    CTF's so that everything work OK. """    
    ctf = volume_property.GetRGBTransferFunction()
    old_range = ctf.GetRange()
    if new_range != old_range:
        s_d = save_ctfs(volume_property)
        s1, s2 = new_range
        if s1 > s2:
            s_d['range'] = (s2, s1)
        else:
            s_d['range'] = (s1, s2)
        load_ctfs(s_d, volume_property)

def set_lut(lut, volume_property):
    """Given a vtkLookupTable and a vtkVolumeProperty it saves the
    state of the RGB and opacity CTF from the volume property to the
    LUT.  The number of colors to use is obtained from the LUT and not
    the CTF."""    
    vp = volume_property
    ctf = vp.GetRGBTransferFunction()
    otf = vp.GetScalarOpacity()
    s1, s2 = ctf.GetRange()
    nc = lut.GetNumberOfColors()
    ds = float(s2-s1)/(nc - 1)
    for i in range(nc):
        r, g, b = ctf.GetColor(s1 + i*ds)
        a = otf.GetValue(s1 + i*ds)
        lut.SetTableValue(i, r, g, b, a)

def set_ctf_from_lut(lut, volume_property):
    """Given a vtkLookupTable and a vtkVolumeProperty it loads the
    state of the RGB and opacity CTF from the lookup table to the CTF.
    The CTF range is obtained from the volume property and the number
    of colors to use is obtained from the LUT."""    
    vp = volume_property
    ctf = vp.GetRGBTransferFunction()
    s1, s2 = ctf.GetRange()
    nc = lut.GetNumberOfColors()
    ds = float(s2-s1)/(nc - 1)
    ctf = vtkpython.vtkColorTransferFunction ()
    otf = vtkpython.vtkPiecewiseFunction()
    for i in range(nc):
        v = s1 + i*ds
        r, g, b, a = lut.GetTableValue(i)
        ctf.AddRGBPoint(v, r, g, b)
        otf.AddPoint(v, a)
    volume_property.SetColor(ctf)
    volume_property.SetScalarOpacity(otf)

    
class PiecewiseFunction:
    def __init__(self, canv, line_color, ctf=None, color=None):
        """ Constructor.

          Input Arguments:

            canv -- The parent Tkinter canvas.
            line_color -- Line color to use for the piecewise function.

            ctf -- A vtkColorTransferFunction or a
            vtkPiecewiseFunction.  Defaults to None where the
            piecewise function is set to a sane default.
            
            color -- The color to be used from the
            vtkColorTransferFunction this has to be one of ['red',
            'green', 'blue'].  If the color is None (default), then
            the ctf is treated as a vtkPiecewiseFunction.
        """
        self.xLast   = -1.0
        self.yLast   = -1.0
        self.npoints = 101
        self.dt = 1.0/(self.npoints - 1)
        self.canv    = canv
        self.line_color   = line_color
        self.line0=None
        self.line1=None
        self.Fxn = vtkpython.vtkCardinalSpline ()
        self.initialize_ctf()
        if ctf:
            if color:
                self.load_vtkColorTransferFunction (ctf, color)
            else:
                self.load_vtkPiecewiseFunction (ctf)

    def initialize_ctf(self):
        # Initalize the piecewise function - 101 points from 0 to 1
        line = []
        for i in range(self.npoints + 1):
            t = self.dt*i
            x = 0.5
            
            line.append (t)
            line.append (x)
            
            self.Fxn.AddPoint (t, x)
        self.lineHandle = self.canv.create_line (line, fill=self.line_color)
    
    def redraw_fxn(self):
        line = []
        for i in range(self.npoints+1):
            t = i*self.dt
            x,y = self.parametric2global (t, self.Fxn.Evaluate(t))
            line.append (x)
            line.append (y)
            
        self.canv.coords(self.lineHandle, *line)
        return

    def global2parametric(self, x, y):
        t = self.dt*int(100.0*x/self.width ())
        f = float(self.height () - y)/self.height ()
        return t,f

    def parametric2global(self, t, f):
        x = t*self.width ()
        y = self.height () - f*self.height ()
        return x,y
    
    def width(self):
        return self.canv.winfo_width ()
    
    def height(self):
        return self.canv.winfo_height ()
    
    def withinCanvas(self, event):
        return (self.withinXBounds (event) & self.withinYBounds (event))
    
    def withinXBounds(self, event):
        return (event.x>=0)&(event.x<=self.width ())

    def withinYBounds(self, event):
        return (event.y>=0)&(event.y<=self.height ())
    
    def resetXYLast(self, event):
	self.xLast = -1
        self.yLast = -1

	
    def setXYLast(self, event):
	if self.xLast < 0:
	    self.sxFirst = event.x
	    self.syFirst = event.y
        self.xLast = event.x
        y = event.y	
        if(y<0):
            y = 0
        elif(y>self.height ()):
            y = self.height ()
        self.yLast = y
        self.sxLast = self.xLast
	self.syLast = self.yLast
            
    def straighten(self):
	print "Line from %d,%d to %d,%d"%(self.sxFirst,self.syFirst,self.sxLast,self.syLast)
	ft,ff = self.global2parametric(self.sxFirst,self.syFirst)
	lt,lf = self.global2parametric(self.sxLast,self.syLast)
	self.Fxn.RemovePoint(ft)
	self.Fxn.AddPoint(ft,ff)
	
	self.Fxn.RemovePoint(lt)
	self.Fxn.AddPoint(lt,lf)

	cnt = abs(self.sxLast-self.sxFirst)
	if (self.sxFirst < self.sxLast):
	    x0=self.sxFirst
	    y0=self.syFirst
	    x1=self.sxLast
	    dy=(self.syLast - self.syFirst)/float(cnt)
	else:
	    x0=self.sxLast
	    y0=self.syLast
	    x1=self.syFirst
	    dy=(self.syFirst - self.syLast)/float(cnt)
	print "dy=",dy,"cnt=",cnt
	for i in range(cnt):
	    t, f = self.global2parametric (x0+i+1, y0+dy*(i+1))
	    self.Fxn.RemovePoint (t)
	    self.Fxn.AddPoint (t, f)
		    
    def onModifyFxn(self, event):
	# Store a variable noting that we're the last modified function
	self.canv.lastFunction = self
        if( self.withinXBounds(event) ):
            y = event.y
            if(y<0):
                y = 0
            elif(y>self.height ()):
                y = self.height ()

            x = float(event.x)
            y = float(event.y)
            
            if(self.xLast<0):
                t, f = self.global2parametric (x, y)
                self.Fxn.RemovePoint (t)
                self.Fxn.AddPoint (t, f)
            else:
                #if(self.xLast<x):
                #    t0, f0 = self.global2parametric (self.xLast, self.yLast)
                #else:
                #    t0, f0 = self.global2parametric (x, y)
                #cnt = int( 0.5+ abs(x - self.xLast)/self.dt)
                cnt = abs(x-self.xLast)
                if(cnt>0):
                    if(self.xLast<x):
                        x0=self.xLast
                        y0=self.yLast
                        x1=x
                        dy=(y - self.yLast)/float(cnt)
                    else:
                        x0=x
                        y0=y
                        x1=self.xLast
                        dy=(self.yLast - y)/float(cnt)
                        
                    for i in range(cnt):
                        t, f = self.global2parametric (x0+i+1, y0+dy*(i+1))
                        self.Fxn.RemovePoint (t)
                        self.Fxn.AddPoint (t, f)

            self.setXYLast(event)
        else:
            self.resetXYLast(event)
        self.Fxn.Compute()
        self.redraw_fxn ()

    def load_vtkPiecewiseFunction(self, vtk_fxn):
        s0, s1 = vtk_fxn.GetRange()
        self.Fxn.RemoveAllPoints ()
        ds = float(s1-s0)/self.npoints
        for i in range(self.npoints+1):
            self.Fxn.AddPoint (i*self.dt, vtk_fxn.GetValue (i*ds))
        self.Fxn.Compute()
        self.redraw_fxn ()

    def load_vtkColorTransferFunction(self, vtk_fxn, color):
        s0, s1 = vtk_fxn.GetRange()
        self.Fxn.RemoveAllPoints ()
        ds = float(s1-s0)/self.npoints
        for i in range(self.npoints+1):
            if string.lower(color) == "red":
                self.Fxn.AddPoint(i*self.dt, vtk_fxn.GetRedValue (i*ds))
            elif string.lower(color) == "green":
                self.Fxn.AddPoint(i*self.dt, vtk_fxn.GetGreenValue (i*ds))
            else:
                self.Fxn.AddPoint(i*self.dt, vtk_fxn.GetBlueValue (i*ds))
        self.Fxn.Compute()
        self.redraw_fxn()
                
    def get_function(self):
        f = vtkpython.vtkPiecewiseFunction ()
        for i in range(self.npoints):
            f.AddPoint(i*self.dt, self.Fxn.Evaluate(i*self.dt))
        return f    

    def get_value(self, t):
        return self.Fxn.Evaluate(t)


class TransferFunctionEditor(Tkinter.Frame):
    
    """ A powerful and easy to use color transfer function editor.
    This is most useful with the volume module and is used to
    edit/create the vtkColorTransferFunction. """
    
    def __init__(self, parent, volume_property, width=250,
                 height=100):
        """Constructor.

        Input Arguments:
          parent -- parent Tk widget.
          volume_property -- a vtkVolumeProperty object that needs to
          be configured.
          width -- default, initial width of editor (250).
          height -- default, initial height of editor (100).
        """          
          
        Tkinter.Frame.__init__(self, parent)
        vp = volume_property
        ctf = vp.GetRGBTransferFunction()
        otf = vp.GetScalarOpacity()
        self.xLast = -1
        self.yLast = -1
	self.alpha_mode=0
        self.min_x, self.max_x = ctf.GetRange()
        self.ds = (self.max_x - self.min_x)/100.0

        self.canv = canv = Tkinter.Canvas(self, width=width,
                                          height=height,
                                          highlightthickness=0, border = 0,
                                          background='black')
        
        # Initalize the opacity/color transfer functions
        self.redFxn = PiecewiseFunction(self.canv, 'red', ctf, 'red')
        self.greenFxn = PiecewiseFunction(self.canv, 'green', ctf, 'green')
        self.blueFxn = PiecewiseFunction(self.canv, 'blue', ctf, 'blue')
        self.alphaFxn = PiecewiseFunction(self.canv, 'white', otf)

      
        canv.bind('<Shift-B1-Motion>',self.alphaFxn.onModifyFxn)
        canv.bind('<B1-Motion>',self.redFxn.onModifyFxn)
        canv.bind('<B2-Motion>',self.greenFxn.onModifyFxn)
        canv.bind('<Control-B1-Motion>',self.greenFxn.onModifyFxn)

	canv.bind('<Double-Button-1>',self.straightenLine)
	
        canv.bind('<Control-B2-Motion>',self.greenFxn.onModifyFxn)
        canv.bind('<Leave>',self.resetXYLast)
        canv.bind('<ButtonRelease>',self.resetXYLast)
        canv.bind('<Motion>',self.UpdateInfo)
        canv.bind('<Configure>', self.redraw)

        canv.pack(side="top", fill="both", expand=1)

        self.color_bar = Tkinter.Canvas(self, width=width, height=10,
                                        highlightthickness=0, border=0,
                                        background='black')
        cb = self.color_bar
        cb.pack(side="top", fill="x", expand=1)
        self.create_color_bar()
        
        l1 = Tkinter.Label(self, text='Scalar:')
        l1.pack(side="left")
        self.s = s = Tkinter.Label(self, text='0.0', relief=Tkinter.RIDGE)
        s.pack(side="left")
        
        self.w = w = Tkinter.Label(self, text='0.0', relief=Tkinter.RIDGE)
        w.pack(side="right")
        l2 = Tkinter.Label(self, text='Weight:')
        l2.pack(side="right")

    def set_alpha_mode(self, mode):
	print "set_alpha_mode(%s)"%mode
	self.alpha_mode = mode
	
    def reset_ctfs(self, volume_property):
        """Updates the CTF's given a vtkVolumeProperty object."""
        vp = volume_property
        ctf = vp.GetRGBTransferFunction()
        otf = vp.GetScalarOpacity()
        self.min_x, self.max_x = ctf.GetRange()
        self.ds = (self.max_x - self.min_x)/100.0

        self.redFxn.load_vtkColorTransferFunction(ctf, 'red')
        self.greenFxn.load_vtkColorTransferFunction(ctf, 'green')
        self.blueFxn.load_vtkColorTransferFunction(ctf, 'blue')
        self.alphaFxn.load_vtkPiecewiseFunction(otf)
        self.redraw()        

    def get_tk_color(self, t):
        r = min(self.redFxn.get_value(t)*255, 255)
        g = min(self.greenFxn.get_value(t)*255, 255)
        b = min(self.blueFxn.get_value(t)*255, 255)
        return "#%02x%02x%02x"%(r, g, b)        

    def create_color_bar(self):
        cb = self.color_bar
        w = 250
        npnt = self.redFxn.npoints
        self.cb_boxes = box = []
        h = 10
        dx = float(w)/(npnt - 1)
        x1 = 0
        dt = 1.0/npnt
        for i in range(npnt):
            col = self.get_tk_color(dt*i)
            box.append(cb.create_rectangle(x1, 0, x1 + dx, h, outline="",
                                           fill=col))
            x1 += dx
        self.update()

    def update_color_bar(self):
        cb = self.color_bar
        w = self.winfo_width()
        npnt = self.redFxn.npoints
        h = cb.winfo_height()
        dx = float(w)/(npnt - 1)
        x1 = 0
        dt = 1.0/npnt
        box = self.cb_boxes
        for i in range(npnt):
            col = self.get_tk_color(dt*i)
            cb.coords(box[i], x1, 0, x1+dx, h)
            cb.itemconfig(box[i], fill=col)
            x1 += dx

    def width(self):
        return self.canv.winfo_width ()
    
    def height(self):
        return self.canv.winfo_height ()
    
    def bind(self,a,b):
        self.canv.bind(a,b)
        
    def UpdateInfo(self, event):
        val = self.min_x + (self.max_x - self.min_x)*float(event.x)/self.width ()
        self.s.config(text='%f'%val)
        
        weight = float (self.height () - event.y)/self.height ()
        self.w.config(text='%f'%weight)
                
    def withinCanvas(self, event):
        return (event.x>=0)&(event.x<=self.width ())&(event.y>=0)&(event.y<=self.height ())
    
    def straightenLine(self,event):
	print "straightenLine()"
	print "lastFunction.straighten()"
	self.canv.lastFunction.straighten()
        self.redraw()
 
    def resetXYLast(self, event):
        self.alphaFxn.resetXYLast(event)
        self.redFxn.resetXYLast(event)
        self.greenFxn.resetXYLast(event)
        self.blueFxn.resetXYLast(event)
        self.redraw ()
        
    def redraw(self, event=None):
        self.alphaFxn.redraw_fxn()
	if self.alpha_mode:
	    return
        self.redFxn.redraw_fxn()
        self.greenFxn.redraw_fxn()
        self.blueFxn.redraw_fxn()
        self.update_color_bar()
        
    def getTFxn(self):
        a = self.alphaFxn.get_function ()
        f = vtkpython.vtkPiecewiseFunction ()
        for i in range(101):
            f.AddPoint (i*self.ds, a.GetValue(i*0.01))
        return f

    def getCTFxn(self):
        ctfun = vtkpython.vtkColorTransferFunction ()
        r = self.redFxn.get_function ()
        g = self.greenFxn.get_function ()
        b = self.blueFxn.get_function ()
        for i in range(101):
            ctfun.AddRGBPoint (i*self.ds, r.GetValue(i*0.01), g.GetValue(i*0.01), b.GetValue(i*0.01))
        return ctfun


