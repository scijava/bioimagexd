# -*- coding: iso-8859-1 -*-
"""
 Unit: Animator.py
 Project: Selli 2
 Created: n/a
 Creator: Heikki Uuksulainen
 Description:

 This module defines the animation making gui for MayaVi

 Bugs:
     Widgets are not deleted in proper order.
     Creating a new spline curve crashes the animator.

 Changes:
            10.02.2005 KP - Started conversion to wxPython
     
 This code is distributed under the conditions of the BSD license.  See
 LICENSE.txt for details.

 Copyright (c) 2004, Heikki Uuksulainen.

 Modified 2005 for Selli 2 Project: Kalle Pahajoki
"""

__author__ = "Heikki Uuksulainen <heuuksul@cc.jyu.fi>"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2004/11/17 13:16:50 $"

import wx
import RenderingInterface

import Common, Base.Objects, Base.ModuleManager, Base.DataVizManager
import Sources.VtkDataReader, Sources.PLOT3DReader, Sources.VRMLImporter
import Sources.VtkXMLDataReader
import vtkpython

from vtk.wx.wxVTKRenderWindowInteractor import *

import SplineEditor
import vtk
import os
from __version__ import version

import Dialogs

math = vtk.vtkMath()

debug = Common.debug
print_err = Common.print_err

class AnimatorPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.sizer=wx.GridBagSizer()
        
        
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.sizer.Fit(self)



class MayaViAnimator:
    """
    This is the main class for handling the animation related stuff.
    """

    def __init__(self, master, mayavi_interface, gui,spline_f):
        debug ("In Animator::__init__ ()")

        self.gui = gui
        self.mayavi_interface = mayavi_interface
        self.splineEditor = SplineEditor.SplineEditor(spline_f)
        self.data_handler = DataHandler(self,mayavi_interface)


    def show_message(self,msg):
        Dialogs.showmessage(self,msg,"MayaVi Animator Message")

    def make_animation(self):
        """
        This method controls the animation. It is very simple at this
        point but some kind of animations can be done. The user has to
        create graphics pipeline to MayaVi before he is able to make
        the animation.
        """
        if not self.splineEditor:
            return 
        renwin = self.mayavi_interface.get_render_window() 
        ren = renwin.get_renderer()
        if self.data_handler.dvm:
            module_mgr = self.data_handler.get_current_module_manager()
            if not module_mgr.get_module(0):
                Dialogs.showwarning(self,"You must specify some module to MayaVi first!","Oops!")
                return

        if self.gui.get_frames_per_timepoint() == 0:
            Dialogs.showwarning(self,"Frames per time point must be posivive integer!","Oops!")
            return
                
        if not ren:
            Dialogs.showwarning(self,"No renderer in main render window!! This should not be possible!","Oops!")
            return
                
        numFrames = self.gui.get_frames()
                
        self.set_rendering_status("Starting rendering")
        points = self.splineEditor.get_points() # vtkPolyData
        cam = ren.GetActiveCamera()
        step_size = points.GetNumberOfPoints()/numFrames
        self.change_data(0)
        for i in range(0,numFrames):
            if (i != 0 and i % self.gui.frames_per_timepoint.get() == 0 and self.gui.time.get() > 1):
                self.change_next_data() 
            curr_file_name = self.data_handler.get_absolut_out_file_name(i)
            self.set_camera_params(ren,cam,i,points,step_size)
            self.render_frame(cam,ren,i+1)
            self.save_frame(curr_file_name,self.gui.out_file_type.get())
            
        self.set_rendering_status("Completed")
        self.data_handler.next_file_name_index = 0
            
    def set_camera_params(self,ren,cam,i,points,step_size):
        """
        Camera location must be set for each rendered frame. If the
        spline curve in the spline editor is active, then the
        position will be calculated related to the step
        size. Otherwise the position is the position of the camera
        in the spline editor window.
        """
        # Focal point is allways the centre of the data.
        focal = self.get_focal_point()
        cam.SetFocalPoint(focal)
        position = points.GetPoint(i*step_size)
        if not self.splineEditor.is_active():
            position = self.splineEditor.get_camera().GetPosition()
        cam.SetPosition(position)
        #cam.SetViewUp(self.splineEditor.get_camera().GetViewUp())
        cam.SetViewUp((0,0,1))
        cam.ComputeViewPlaneNormal()
        cam.OrthogonalizeViewUp()
        # With this we can be sure that all of the props will be visible.
        ren.ResetCameraClippingRange()

    def set_rendering_status(self,status):
        self.gui.set_rendering_status(status)

    def set_time_dimension(self,dim):
        self.gui.set_timepoints(dim)

    def save_frame(self,file,type):
        """
        Save the rendered frame. We use MayaVis operations for the
        actual saving. The type of the saved files will be defined in
        the GUI.
        """
        if len(file) == 0:
            return 
        self.set_rendering_status("Saving "+file)
        renwin = self.mayavi_interface.get_render_window()
        comm = "renwin.save_%s(file)"
        eval(eval("comm%type"))        

    def render_frame(self,cam,ren,i):
        self.set_rendering_status("Rendering frame "+str(i))
        ren.SetActiveCamera(cam)
        self.mayavi_interface.Render()         


    def change_next_data(self):
        self.data_handler.set_next_data_set()

    def change_data(self,key):
        self.data_handler.change_data(key)

    def open_many_vtk_xml(self):
        self.data_handler.input_dir = self.gui.input_dir
        self.data_handler.input_pattern = self.gui.input_filename_pattern
        self.data_handler.time_dimension = self.gui.get_timepoints_num()
        self.data_handler.open_many_vtk_xml()
        self.init_data()
        
    def init_data(self):
        data_src = self.data_handler.get_data_src(0)
        if not data_src:
            return
        
        self.gui.x.set(self.data_handler.data_width())
        self.gui.y.set(self.data_handler.data_height())
        self.gui.z.set(self.data_handler.data_depth())
        self.gui.time.set(self.data_handler.time_dimension)
            
        self.splineEditor.update_data(data_src)
        self.init_spline(self.gui.control_points.get())
        self.init_spline_camera()
            
        self.gui.make_animation.config(state=Tkinter.NORMAL)
        self.gui.make_new_rand_spline.config(state=Tkinter.NORMAL)
        self.splineEditor.render()

    def init_spline(self,control_points):
        self.splineEditor.init_spline(control_points)

    def init_spline_camera(self):
        self.splineEditor.init_camera()

    def get_timepoints_num(self):
        return self.gui.time.get()

    def set_output_dir(self,out_dir):
        if not out_dir:
            return
        self.data_handler.output_dir = out_dir
        
    def set_output_pattern(self,out_pattern):
        if not out_pattern:
            return
        self.data_handler.output_pattern = out_pattern
        
    def set_output_file_type(self,out_type):
        if not out_type:
            return
        self.data_handler.output_type = out_type
        
    def get_frames(self):
        ret = 0
        try:
            ret = self.get_frames_per_timepoint() * self.get_timepoints_num()
        except:
            pass
        return ret

    def get_frames_per_timepoint(self):
        ret = 0
        try:
            ret = self.gui.frames_per_timepoint.get()
        except:
            pass
        return ret
    
    def get_curr_time_point(self):
        return self.gui.data_set_scale.get()
        
    def get_focal_point(self):
        return self.data_handler.get_center()


    def __del__(self):
        debug ("In Animator::__del__ ()")
        print "Animator.__del__()"
        self.quit()
        
    def quit (self, event=None):
        print "Animator.guit()"
        debug ("In Animator::quit ()")
        del self.splineEditor
        #self.splineEditor = None
        #self.splineEditor.quit()


