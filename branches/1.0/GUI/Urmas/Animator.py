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
     
 This code is distributed under the conditions of the BSD license.  See
 LICENSE.txt for details.
 
 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

__author__ = "Heikki Uuksulainen <heuuksul@cc.jyu.fi>"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2004/11/17 13:16:50 $"

raise "NEVER IMPORT ME AGAIN"
import wx
import RenderingInterface

import vtkpython

from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

import PreviewFrame
import SplineEditor
import vtk
import os
#from __version__ import version

import Logging
import Dialogs

math = vtk.vtkMath()

class AnimatorPanel:
    """
    Class: AnimatorPanel
    Created: 10.2.2005, KP
    Description: A class that contains the spline editor and configuration
                 controls related to it.
    """
    def __init__(self,parent,control,renwin):
        """
        Method: __init__
        Created: 10.2.2005, KP
        Description: Initialize the config panel
        """        
        #wx.Panel.__init__(self,parent)
        self.splineEditor=None
        self.control = control
        
        print "AnimatorPanel(...)"
        #self.sizer=wx.GridBagSizer()

        #self.animator=MayaViAnimator(self,self.splineEditor)

        #self.sizer.Add(self.splineEditor,(0,0))

        #self.SetSizer(self.sizer)
        #self.SetAutoLayout(True)
        #self.sizer.Fit(self)
        



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
        self.controlPoints=0
        self.type="png"
        
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
        
        renwin = self.renderingInterface.getRenderWindow() 
        ren = renwin.get_renderer()
        if self.renderingInterface.isMayaViModuleLoaded() == False:
            Dialogs.showwarning(self,"You must specify some module to MayaVi first!","Oops!")
            return
            
        if not ren:
            Dialogs.showwarning(self,"No renderer in main render window!! This should not be possible!","Oops!")
            return
                
        # XXX: Fix this
        numFrames = 30
        framesPerTimepoint=numFrames/self.renderingInterface.getNumberOfTimepoints()
        
                
        self.setRenderingStatus("Starting rendering")
        points = self.splineEditor.getPoints() # vtkPolyData
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
        Created: Heikki Uuksulainen
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
        if not self.splineEditor.isActive():
            position = self.splineEditor.getCamera().GetPosition()
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
        self.splineEditor.updateData(self.renderingInterface.getCurrentData(),self.renderingInterface.getColorTransferFunction())
        #self.splineEditor.initSpline(self.controlPoints)
        self.splineEditor.initCamera()
            
        self.splineEditor.render()

    #def __del__(self):
    #    del self.splineEditor


