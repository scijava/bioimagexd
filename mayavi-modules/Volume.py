"""
This Volume module allows one to view a structured points dataset with
either unsigned char or short data as a volume.  The module also
provides a powerful GUI to edit the Color Transfer Function (CTF).
You can drag the mouse with different buttons to change the colors.
The following are the mouse buttons and key combinations that can be
used to edit the CTF -- red curve: Button-1, green curve:
Button-2/Control-Button-1, blue curve: Button-3/Control-Button-2,
alpha/opacity: Shift-Button-1.

It is possible to use either the vtkVolumeRayCastMapper or the
vtkVolumeTextureMapper2D.  It is also possible to choose among various
ray cast functions.

This code is distributed under the conditions of the BSD license.  See
LICENSE.txt for details.

Copyright (c) 2003, Prabhu Ramachandran.
"""

__author__ = "Gerard Gorman and Prabhu Ramachandran"
__version__ = "$Revision: 1.6 $"
__date__ = "$Date: 2003/11/06 07:19:27 $"

import Base.Objects, Common
import Tkinter
import tkFileDialog
import vtkpython
import vtkPipeline.vtkMethodParser
import vtkPipeline.ConfigVtkObj
try:
    import Misc.CTFEditor as CTFEditor
except ImportError:
    import mayavi.Misc.CTFEditor as CTFEditor

try:
    import Misc.Lut_Editor as Lut_Editor
except ImportError:
    import mayavi.Misc.Lut_Editor as Lut_Editor

debug = Common.debug


def default_opacity_transfer_function(x1, x2):
    maxs = max(x1, x2)
    mins = min(x1, x2)
    opacityTransferFunction = vtkpython.vtkPiecewiseFunction()
    opacityTransferFunction.AddPoint(mins, 0.0)
    opacityTransferFunction.AddPoint(maxs, 0.2)
    return opacityTransferFunction

def default_color_transfer_function(x1, x2):
    maxs = max(x1, x2)
    mins = min(x1, x2)
    ds=(maxs - mins)/4.0
    colorTransferFunction = vtkpython.vtkColorTransferFunction()
    colorTransferFunction.AddRGBPoint(mins,      1.00, 0.0, 0.00)
    colorTransferFunction.AddRGBPoint(mins+ds,   0.75, 0.5, 0.25)
    colorTransferFunction.AddRGBPoint(mins+2*ds, 0.50, 1.0, 0.50)
    colorTransferFunction.AddRGBPoint(mins+3*ds, 0.25, 0.5, 0.75)
    colorTransferFunction.AddRGBPoint(maxs,      0.00, 0.0, 1.00)
    return colorTransferFunction


def write_lut_to_file (file_name, lut):
    """Given a filename and a vtkLookupTable this writes the lut the
    file."""
    output = open (file_name, "w")
    n_col = lut.GetNumberOfColors()
    output.write ("LOOKUP_TABLE some_name %d\n"%(n_col))
    for i in range (n_col):
        c = lut.GetTableValue(i)
        str = "%f %f %f %f\n"%(c)
        output.write (str)
    output.close ()


class Volume (Base.Objects.Module):
    
    """ This Volume module allows one to view a structured points
    dataset with either unsigned char or short data as a volume.  The
    module also provides a powerful GUI to edit the Color Transfer
    Function (CTF).  You can drag the mouse with different buttons to
    change the colors.  The following are the mouse buttons and key
    combinations that can be used to edit the CTF -- red curve:
    Button-1, green curve: Button-2/Control-Button-1, blue curve:
    Button-3/Control-Button-2, alpha/opacity: Shift-Button-1.

    It is possible to use either the vtkVolumeRayCastMapper or the
    vtkVolumeTextureMapper2D.  It is also possible to choose among
    various ray cast functions.  """

    def __init__ (self, mod_m): 
        debug ("In Volume::__init__ ()")
        Common.state.busy ()
        Base.Objects.Module.__init__ (self, mod_m)
        self.actor = self.act = vtkpython.vtkVolume ()
        self.data_out = self.mod_m.GetOutput ()
        self._initialize ()
        self._gui_init ()
        self.legend = VolumeLegend(self.renwin, mod_m)
        self.legend.update_lut(self.actor.GetProperty())
        self.renwin.add_actors(self.legend.get_scalar_bar())
        self.renwin.Render ()
        Common.state.idle ()

    def __del__ (self): 
        debug ("In Volume::__del__ ()")
        if self.act:
            self.renwin.remove_actors (self.act)
            self.renwin.remove_actors (self.legend.get_scalar_bar())
        self.renwin.Render ()

    def _initialize (self):
        debug ("In Volume::_initialize ()")
        self.data_range = dr = self.mod_m.get_scalar_data_range ()
        
        ctf = default_color_transfer_function(dr[0], dr[1])
        otf = default_opacity_transfer_function(dr[0], dr[1])

        self.map_type = 0 # 0 - Ray cast, 1 - TextureMapper, 2 - TextureMapper3D
        self.rc_func = 0 # 0 - composite, 1 - MIP, 2 - Isosurface
        if self.map_type == 0:
            self.map = vtkpython.vtkVolumeRayCastMapper ()
            self.ray_cast_func = self.get_ray_cast_function()
            self.map.SetVolumeRayCastFunction (self.ray_cast_func)
        elif self.map_type == 1:
            self.map = vtkpython.vtkVolumeTextureMapper2D ()
	elif self.map_type == 2:
	    self.map = vtkpython.vtkVolumeTextureMapper3D ()
            
        self.map.SetInput (self.mod_m.GetOutput ())
        
        # The property describes how the data will look
        volumeProperty = vtkpython.vtkVolumeProperty()
        volumeProperty.SetColor(ctf)
        volumeProperty.SetScalarOpacity(otf)
        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.ShadeOn()
                
        self.act.SetMapper (self.map)
        self.act.SetProperty (volumeProperty)
        
        self.renwin.add_actors (self.act)
        # used for the pipeline browser
        self.pipe_objs = self.act
        
    def _gui_init (self): 
        debug ("In Volume::_gui_init ()")
        self.transfer_fxn = None
        self.map_type_var = Tkinter.IntVar()
        self.map_type_var.set(self.map_type)
        self.map_gui = None
        self.rc_func_var = Tkinter.IntVar()
        self.rc_func_var.set(self.rc_func)
        self.rcf_gui = None

    def SetInput (self, source): 
        debug ("In Volume::SetInput ()")
        Common.state.busy ()
        self.data_out = source
        self.map.SetInput (self.data_out)
        dr = self.mod_m.get_scalar_data_range ()
        if (dr[0] != self.data_range[0]) or (dr[1] != self.data_range[1]):
            self.data_range = dr
            vp = self.actor.GetProperty()
            CTFEditor.rescale_ctfs(vp, dr)
            if self.root and self.transfer_fxn and self.root.winfo_exists():
                self.transfer_fxn.reset_ctfs (vp)
            self.legend.update()
        Common.state.idle ()

    def save_config (self, file): 
        debug ("In Volume::save_config ()")
        s = {}
        s['map_type'] = self.map_type
        s['rc_func'] = self.rc_func
        cfg = {}
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.dump(self.map, cfg)
        s['map_config'] = cfg
        cfg = {}
        p.dump(self.ray_cast_func, cfg)
        s['rcf_config'] = cfg
        vol_prop = self.actor.GetProperty()
        cfg = {}
        p.dump(vol_prop, cfg)
        s['vol_prop_config'] = cfg
        s['ctfs'] = CTFEditor.save_ctfs(vol_prop)
        cfg = {}
        self.legend.save_config(cfg)
        s['legend_config'] = cfg
        # note that you have to write this as one single line!
        file.write("%s\n"%s)

    def load_config (self, file): 
        debug ("In Volume::load_config ()")
        s = eval(file.readline())        
        self.set_map_type(s['map_type'])
        self.map_type_var.set(s['map_type'])
        self.set_ray_cast_function(s['rc_func'])
        self.rc_func_var.set(s['rc_func'])
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.load(self.map, s['map_config'])
        p.load(self.ray_cast_func, s['rcf_config'])
        vol_prop = self.actor.GetProperty()
        p.load(vol_prop, s['vol_prop_config'])
        CTFEditor.load_ctfs(s['ctfs'], vol_prop)
        legend_config = s.get('legend_config')
        if legend_config:
            self.legend.load_config(legend_config)
        self.legend.update_lut(vol_prop)
        self.renwin.Render()

    def config_changed (self): 
        debug ("In Volume::config_changed ()")
        self.legend.config_changed()

    def make_main_gui (self): 
        debug ("In Volume::make_main_gui ()")
        frame = Tkinter.Frame (self.root, relief='ridge', bd=2)
        frame.pack (side='top', fill='both', expand=1)
        rw = 0
        tf = CTFEditor.TransferFunctionEditor(frame,
                                              self.actor.GetProperty())
        self.transfer_fxn = tf
        tf.pack (side='top', fill='both', expand=1)
        #self.transfer_fxn.bind ("<ButtonRelease>", self.change_transferfunction)
        rw = rw + 1

        f = Tkinter.Frame(frame)
        f.pack (side='top', fill='both', expand=1)        
        rw = 0
        but = Tkinter.Button(f, text = "Update", underline=0,
                             command=self.change_transferfunction)
        but.grid (row=rw, column=0, columnspan=2, sticky='wens')
        self.root.bind('<Alt-u>', self.change_transferfunction)
        rw = rw + 1
        
        but = Tkinter.Button(f, text = "Reset transfer functions",
                             command=self.reset_ctf_defaults)
        but.grid (row=rw, column=0, columnspan=2, sticky='wens')
        rw = rw + 1

        but = Tkinter.Button(f, text = "Save CTF", underline=0,
                             command=self.save_ctf_gui)
        but.grid (row=rw, column=0, sticky='wens')
        but = Tkinter.Button(f, text = "Load CTF", underline=1,
                             command=self.load_ctf_gui)
        but.grid (row=rw, column=1, sticky='wens')
        self.root.bind("<Alt-s>", self.save_ctf_gui)
        self.root.bind("<Alt-o>", self.load_ctf_gui)
        rw = rw + 1

        but = Tkinter.Button(f, text = "Configure volume property",
                             underline=10,
                             command=self.config_vol_prop_gui)
        but.grid (row=rw, column=0, columnspan=2, sticky='wens')
        self.root.bind('<Alt-v>', self.config_vol_prop_gui)
        rw = rw + 1

        # Choice for the Mapper.
        b = Tkinter.Radiobutton(f, text="Use RayCastMapper",
                                variable=self.map_type_var, value=0,
                                command=self.change_map_type_gui)
        b.grid (row=rw, column=0, columnspan=2, sticky='w')
        rw = rw + 1
        b = Tkinter.Radiobutton(f, text="Use TextureMapper",
                                variable=self.map_type_var, value=1,
                                command=self.change_map_type_gui)
        b.grid (row=rw, column=0, columnspan=2, sticky='w')
        rw = rw + 1
        b = Tkinter.Radiobutton(f, text="Use TextureMapper3D",
                                variable=self.map_type_var, value=2,
                                command=self.change_map_type_gui)
        b.grid (row=rw, column=0, columnspan=2, sticky='w')
        rw = rw + 1	
        
        # Create GUI for the Mapper
        self.map_gui_frame = Tkinter.Frame(f)
        self.map_gui_frame.grid(row=rw, column=0, columnspan=2,
                                sticky='wens')
        self.make_map_gui()
        rw = rw + 1

        # Create a GUI for the RayCastFunction
        self.rcf_gui_frame = Tkinter.Frame(f)
        self.rcf_gui_frame.grid(row=rw, column=0, columnspan=2,
                                sticky='wens')
        self.make_rcf_gui()
        rw = rw + 1
        but = Tkinter.Button(f, text = "Configure Legend",
                             underline=10,
                             command=self.config_legend_gui)
        but.grid (row=rw, column=0, columnspan=2, sticky='wens')
        self.root.bind('<Alt-l>', self.config_legend_gui)
        rw = rw + 1

    def make_map_gui(self):
        if self.map_gui:
            for i in self.map_gui_frame.children.values():
                i.destroy()

        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        self.map_gui = CVOF(self.map_gui_frame, self.renwin)
        if self.map_type == 0:            
            t_m = ["AutoAdjustSampleDistancesOn", "CroppingOn",
                   "IntermixIntersectingGeometryOn", "UseImageClipperOn"]
            gs_m = ['CroppingRegionPlanes', 'ImageSampleDistance',
                    'SampleDistance']
        elif self.map_type == 1:
            t_m = ['CroppingOn', 'UseImageClipperOn']
            gs_m = ['CroppingRegionPlanes', 'MaximumNumberOfPlanes',
                    'MaximumStorageSize', 'TargetTextureSize']
        self.map_gui.configure(self.map, get=[], toggle=t_m, get_set=gs_m,
                               state=[], auto_update=1, one_frame=1)
        self.map_gui.pack(side='top', fill='both', expand=1)
        but = Tkinter.Button(self.map_gui_frame,
                             text = "More volume mapper options",
                             underline=0,
                             command=self.config_vol_map_gui)
        but.pack(side='top', fill='both', expand=1)
        self.root.bind('<Alt-m>', self.config_vol_map_gui)

    def make_rcf_gui(self):
        if self.rcf_gui:
            self.rcf_gui.destroy()        

        if self.map_type != 0:
            return
        
        f = Tkinter.Frame(self.rcf_gui_frame)
        self.rcf_gui = f
        f.pack(side='top', fill='both', expand=1)

        # Choice for the RayCastFunction.
        rw = 0
        b = Tkinter.Radiobutton(f, text="Use RayCastCompositeFunction",
                                variable=self.rc_func_var, value=0,
                                command=self.change_ray_cast_func_gui)
        b.grid (row=rw, column=0, sticky='w')
        rw = rw + 1
        b = Tkinter.Radiobutton(f, text="Use RayCastCompositeRGBFunction",
                                variable=self.rc_func_var, value=1,
                                command=self.change_ray_cast_func_gui)
        b.grid (row=rw, column=0, sticky='w')
        rw = rw + 1	
        b = Tkinter.Radiobutton(f, text="Use RayCastMIPFunction",
                                variable=self.rc_func_var, value=2,
                                command=self.change_ray_cast_func_gui)
        b.grid (row=rw, column=0, sticky='w')
        rw = rw + 1        
        b = Tkinter.Radiobutton(f, text="Use RayCastIsosurfaceFunction",
                                variable=self.rc_func_var, value=3,
                                command=self.change_ray_cast_func_gui)
        b.grid (row=rw, column=0, sticky='w')
        rw = rw + 1

        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        gui = CVOF(self.rcf_gui, self.renwin)
        gui.configure(self.ray_cast_func, get=[], toggle=[], auto_update=1)
        gui.grid (row=rw, column=0, sticky='wens')
        rw = rw + 1        

    def change_transferfunction(self, event=None):
        ctf = self.transfer_fxn.getCTFxn()
        otf = self.transfer_fxn.getTFxn()
        Common.state.busy ()
        prop = self.actor.GetProperty()
        prop.SetColor( ctf )
        prop.SetScalarOpacity(otf)
        self.legend.update_lut(prop)
        self.renwin.Render ()
        Common.state.idle ()

    def reset_ctf_defaults(self):
        Common.state.busy ()
        dr = self.data_range
        vp = self.actor.GetProperty ()
        vp.SetColor(default_color_transfer_function(dr[0], dr[1]))
        vp.SetScalarOpacity(default_opacity_transfer_function(dr[0],
                                                              dr[1]))
        self.transfer_fxn.reset_ctfs (vp)
        self.legend.update_lut(vp)
        self.renwin.Render ()
        Common.state.idle ()

    def set_map_type(self, map_type):
        if map_type == self.map_type:
            return
        Common.state.busy ()
        if map_type == 0:
            self.map = vtkpython.vtkVolumeRayCastMapper ()
            self.map.SetVolumeRayCastFunction (self.ray_cast_func)
        elif map_type == 1:
            self.map = vtkpython.vtkVolumeTextureMapper2D()
	elif map_type == 2:
	    self.map = vtkpython.vtkVolumeTextureMapper3D()
	else:
	    raise "Unrecognized mapper type"
        self.map_type = map_type
        self.map.SetInput (self.mod_m.GetOutput ())
        self.act.SetMapper (self.map)
        if self.root and self.root.winfo_exists():
            self.make_map_gui()
            self.make_rcf_gui()
        self.renwin.Render ()     
        Common.state.idle ()            

    def change_map_type_gui(self, event=None):
        val = self.map_type_var.get()
        self.set_map_type(val)
        
    def get_ray_cast_function(self):
        return [vtkpython.vtkVolumeRayCastCompositeFunction,vtkpython.vtkVolumeRayCastRGBCompositeFunction,
    vtkpython.vtkVolumeRayCastMIPFunction,
                vtkpython.vtkVolumeRayCastIsosurfaceFunction,
		
		][self.rc_func]()
    
    def set_ray_cast_function(self, rc_func):
        if rc_func == self.rc_func:
            return
        Common.state.busy()
        self.rc_func = rc_func
        if self.map_type == 0:
            self.ray_cast_func = self.get_ray_cast_function()
	    if isinstance(self.ray_cast_func,vtkpython.vtkVolumeRayCastRGBCompositeFunction):
		self.transfer_fxn.set_alpha_mode(1)
	    else:
		self.transfer_fxn.set_alpha_mode(0)	    
            self.map.SetVolumeRayCastFunction (self.ray_cast_func)
        self.renwin.Render()
        Common.state.idle()
            
    def change_ray_cast_func_gui(self, event=None):
        val = self.rc_func_var.get()
        if val != self.rc_func:	    
            self.set_ray_cast_function(val)
            self.make_rcf_gui()
        
    def config_vol_prop_gui(self, event=None):
        debug("In Volume::config_vol_prop_gui()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        conf.configure (None, self.actor.GetProperty())

    def config_vol_map_gui(self, event=None):
        debug("In Volume::config_vol_map_gui()")
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        conf.configure (None, self.map)

    def config_legend_gui(self, event=None):
        debug("In Volume::config_legend_gui()")
        self.legend.configure(self.root)

    def save_ctf_gui(self, event=None):
        debug("In Volume::save_ctf_gui()")
        d = tkFileDialog.asksaveasfilename
        f_name = d (title="Save CTF to file", 
                    defaultextension=".lut",
                    filetypes=[("Lookup table files", "*.lut"), 
                               ("All files", "*")])
        if len (f_name) != 0:
            self.legend.save_lut_to_file(f_name)
        
    def load_ctf_gui(self, event=None):
        debug("In Volume::save_ctf_gui()")
        d = tkFileDialog.askopenfilename
        f_name = d (title="Open CTF file", 
                    filetypes=[("Lookup table files",
                                "*.lut"), 
                               ("All files", "*")])
        if len (f_name) != 0:
            self.load_ctf(f_name)
    
    def load_ctf(self, filename):
        self.legend.load_lut_from_file(filename)
        vp = self.actor.GetProperty()
        Common.state.busy ()
        CTFEditor.set_ctf_from_lut(self.legend.get_lut(), vp)
        if self.root and self.transfer_fxn and self.root.winfo_exists():
            self.transfer_fxn.reset_ctfs (vp)
        self.renwin.Render ()
        Common.state.idle ()        
        

class VolumeLegend:
    def __init__(self, renwin, mod_m):
        self.renwin = renwin
        self.mod_m = mod_m
        self.sc_bar = sb = vtkpython.vtkScalarBarActor()
        self.lut = vtkpython.vtkLookupTable()
        self.lut.SetNumberOfColors(101)
        self.lut.Build()
        self.lut.SetRange(self.mod_m.get_scalar_data_range())
        name = self.mod_m.get_scalar_data_name()
        if not name:
            name = " "
        self.sc_bar.SetTitle(name)
        sb.SetLookupTable(self.lut)
        sb.SetVisibility(0)
        sb.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.set_horizontal ()
        sb.SetNumberOfLabels (8)
        sb.GetProperty ().SetColor(*Common.config.fg_color)
        self.root = None
        self.legend_orient = Tkinter.IntVar()
        self.legend_orient.set(0)

    def get_lut(self):
        return self.lut

    def get_scalar_bar(self):
        return self.sc_bar

    def update(self):
        self.lut.SetRange(self.mod_m.get_scalar_data_range())
        name = self.mod_m.get_scalar_data_name()
        if not name:
            name = " "
        self.sc_bar.SetTitle(name)

    def save_config (self, dict_obj): 
        debug ("In VolumeLegend::save_config ()")
        cfg = {}
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.dump(self.sc_bar, cfg)
        dict_obj['sc_bar_config'] = cfg

    def load_config(self, dict_obj):
        debug ("In VolumeLegend::save_config ()")
        p = vtkPipeline.vtkMethodParser.VtkPickler ()
        p.load(self.sc_bar, dict_obj['sc_bar_config'])
        l_o = self.sc_bar.GetOrientation()
        if l_o == 0:
            self.set_horizontal()
        else:
            self.set_vertical()
        # reseting the config because the user might have changed numbers.
        p.load(self.sc_bar, dict_obj['sc_bar_config'])
            
    def configure(self, master):
        self.root = Tkinter.Toplevel (master)
        self.root.title ("Configure Volume Legend")
        self.root.protocol ("WM_DELETE_WINDOW", self.close)
        f = Tkinter.Frame(self.root, relief='ridge', bd=2)
        f.pack()

        self.legend_orient.set(self.sc_bar.GetOrientation())
        rw = 0
        rb = Tkinter.Radiobutton (f, text='Horizontal Legend',
                                  value=0, variable=self.legend_orient,
                                  command=self.change_legend_orient)
        rb.grid(row=rw, column=0, sticky="we")
        rw += 1         
        rb = Tkinter.Radiobutton (f, text='Vertical Legend',
                                  value=1, variable=self.legend_orient,
                                  command=self.change_legend_orient)
        rb.grid(row=rw, column=0, sticky="we")
        rw += 1

        CVOF = vtkPipeline.ConfigVtkObj.ConfigVtkObjFrame
        gui = CVOF(f, self.renwin)
        t_m = ['BoldOn', 'ItalicOn', 'ShadowOn', 'VisibilityOn']
        gs_m = ['LabelFormat', 'MaximumNumberOfColors',
                'NumberOfLabels', 'Title']
        s_m = [['SetFontFamilyToArial', 'SetFontFamilyToCourier',
                'SetFontFamilyToTimes']]
        gui.configure(self.sc_bar, get=[], toggle=t_m, state=s_m,
                      get_set=gs_m, one_frame=1, auto_update=1)
        gui.grid(row=rw, column=0, sticky="ew")
        rw += 1 
        
        b = Tkinter.Button(f, text="More options",
                           command=self.config_sc_bar_gui)
        b.grid(row=rw, column=0, sticky="ew")
        rw += 1 

        f1 = Tkinter.Frame(self.root)
        f1.pack()
        b = Tkinter.Button(f1, text="Close", underline=0,
                           command=self.close)
        b.grid(row=0, column=0, sticky='ew')
        self.root.bind("<Alt-c>", self.close)

    def config_changed (self): 
        debug ("In VolumeLegend::config_changed ()")
        self.sc_bar.GetProperty ().SetColor(*Common.config.fg_color)

    def change_legend_orient (self): 
        "Changes orientation of the legend."
        val = self.legend_orient.get ()
        if val == 0:
            self.set_horizontal ()
        elif val == 1:
            self.set_vertical ()
        self.renwin.Render ()

    def set_horizontal (self): 
        "Makes the legend horizontal with default values."
        self.sc_bar.GetPositionCoordinate().SetValue (0.1,0.01)
        self.sc_bar.SetOrientationToHorizontal ()
        self.sc_bar.SetWidth (0.8)
        self.sc_bar.SetHeight (0.14)

    def set_vertical (self): 
        "Makes the legend horizontal with default values."
        self.sc_bar.GetPositionCoordinate().SetValue (0.01,0.15)
        self.sc_bar.SetOrientationToVertical ()
        self.sc_bar.SetWidth (0.14)
        self.sc_bar.SetHeight (0.85)

    def update_lut(self, volume_prop):
        CTFEditor.set_lut(self.lut, volume_prop)
        self.sc_bar.Modified ()
        self.renwin.Render ()        

    def close(self, event=None):
        self.root.destroy()

    def config_sc_bar_gui(self, event=None):
        conf = vtkPipeline.ConfigVtkObj.ConfigVtkObj (self.renwin)
        conf.configure (self.root, self.sc_bar)

    def save_lut_to_file(self, filename):
        write_lut_to_file(filename, self.lut)

    def load_lut_from_file(self, filename):
        lut_lst = Lut_Editor.parse_lut_file(filename)
        Lut_Editor.set_lut(self.lut, lut_lst)
