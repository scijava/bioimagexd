# -*- coding: iso-8859-1 -*-
"""
 Unit: Animator.py
 Project: BioImageXD
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

 Modified 2005 for BioImageXD Project: Kalle Pahajoki
"""

__author__ = "Heikki Uuksulainen <heuuksul@cc.jyu.fi>"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2004/11/17 13:16:50 $"

import wx
import RenderingInterface

from mayavi import Common, Base, Sources
from mayavi.Base import Objects, ModuleManager, DataVizManager
from mayavi.Sources import VtkDataReader, PLOT3DReader, VRMLImporter, VtkXMLDataReader
import vtkpython

from vtk.wx.wxVTKRenderWindowInteractor import *

import SplineEditor
import vtk
import os
#from __version__ import version

import Logging
import Dialogs

math = vtk.vtkMath()

debug = Common.debug
print_err = Common.print_err

class AnimatorPanel(wx.Panel):
    """
    Class: AnimatorPanel
    Created: 10.2.2005, KP
    Description: A class that contains the spline editor and configuration
                 controls related to it.
    """
    def __init__(self,parent):
        """
        Method: __init__
        Created: 10.2.2005, KP
        Description: Initialize the config panel
        """        
        wx.Panel.__init__(self,parent)
        print "AnimatorPanel(...)"
        self.sizer=wx.GridBagSizer()
        self.splineEditor=SplineEditor.SplineEditor(self)
        self.animator=MayaViAnimator(self,self.splineEditor)        
        
        self.sizer.Add(self.splineEditor,(0,0))
        
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.sizer.Fit(self)
        



class MayaViAnimator:
    """
    Class: MayaViAnimator
    Created: n/a, HU
    Description: This is the main class for handling the animation related stuff.
    """

    def __init__(self, parent,splineEditor):
        """
        Method: __init__
        Created: n/a, HU
        Description: Initialize the mayavi animator
        """            
        self.gui = parent
        self.renderingInterface = RenderingInterface.getRenderingInterface()
        self.splineEditor = splineEditor
        # XXX: this should be configurable
        self.type="png"
        
        
    def show_message(self,msg):
        """
        Method: __init__
        Created: 10.2.2005, KP
        Description: Show a message using the BioImageXD dialogs
        """                
        Dialogs.showmessage(self,msg,"MayaVi Animator Message")

    def make_animation(self):
        """
        Method: make_animation()
        Created: n/a, HU
        Description:  This method controls the animation. It is very simple at this
                      point but some kind of animations can be done. The user has to
                      create graphics pipeline to MayaVi before he is able to make
                      the animation.
        """
        if not self.splineEditor:
            return 
        self.renderingInterface.setCurrentTimepoint(0)
        self.animator.initData()
        renwin = self.renderingInterface.getRenderWindow() 
        ren = renwin.get_renderer()
        if self.renderingInterface.isMayaViModuleLoaded() == False:
            Dialogs.showwarning(self,"You must specify some module to MayaVi first!","Oops!")
            return

 #       if self.gui.get_frames_per_timepoint() == 0:
 #           Dialogs.showwarning(self,"Frames per time point must be posivive integer!","Oops!")
 #           return
                
        if not ren:
            Dialogs.showwarning(self,"No renderer in main render window!! This should not be possible!","Oops!")
            return
                
        # XXX: Fix this
        numFrames = 30
        framesPerTimepoint=numFrames/self.renderingInterface.getNumberOfTimepoints()
        
                
        self.setRenderingStatus("Starting rendering")
        points = self.splineEditor.get_points() # vtkPolyData
        cam = ren.GetActiveCamera()
        step_size = points.GetNumberOfPoints()/numFrames
        t=0
        for i in range(0,numFrames):
            if (i != 0 and i % framesPerTimepoint == 0):
                t+=1
                self.renderingInterace.setCurrentTimepoint(t)
            curr_file_name = self.renderingInterface.getFilename(i)
            self.setCameraParams(ren,cam,i,points,step_size)
            self.renderFrame(cam,ren,i+1)
            self.renderingInterface.saveFrame(curr_file_name)
            
        self.setRenderingStatus("Completed")
        #self.data_handler.next_file_name_index = 0
            
    def setCameraParams(self,ren,cam,i,points,step_size):
        """
        Method: setCameraParams(renderer, camera, frameNumber, numberOfPoints, stepSize)
        Created: n/a, HU
        Description:  Camera location must be set for each rendered frame. If the
                      spline curve in the spline editor is active, then the
                      position will be calculated related to the step
                      size. Otherwise the position is the position of the camera
                      in the spline editor window.
        Parameters:
                renderer    The renderer we're using
                camera      The camera we're using
                frameNumber Number of the rendered frame
                numerOfPoints How many points there are in the spline
                stepSize    Size of one step
        """
        # Focal point is allways the centre of the data.
        focal = self.renderingInterace.getCenter()
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

    def setRenderingStatus(self,status):
        Logging.info("Rendering status:",status)

    def renderFrame(self,cam,ren,i):
        self.setRenderingStatus("Rendering frame "+str(i))
        ren.SetActiveCamera(cam)
        self.renderingInterface.render()         
        
    def initData(self):          
        self.splineEditor.update_data(self.renderingInterface.getCurrentData())
        self.splineEditor.init_spline(control_points)
        self.init_spline_camera()
        self.splineEditor.init_camera()
            
        self.splineEditor.render()

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


