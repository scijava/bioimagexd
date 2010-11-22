# -*- coding: iso-8859-1 -*-

"""
 Unit: AnnotationToolbar
 Project: BioImageXD
 Created: 03.02.2005, KP
 Description:

 A toolbar for the annotations in visualizer

 Copyright (C) 2006	 BioImageXD Project
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#import UIElements

import wx.lib.buttons as buttons
import wx.lib.colourselect as csel
import GUI
import lib.messenger
import Logging
import MaskTray
import MenuManager
import os
import scripting
import vtk
import wx

INCLUDE3D = 1

class AnnotationToolbar(wx.Window):
	"""
	A class representing the vertical annotation toolbar of the visualizer
	"""
	def __init__(self, parent, visualizer):
		wx.Window.__init__(self, parent, -1)
		self.visualizer = visualizer
		self.channelButtons = {}
		self.annotateColor = (0, 255, 0)
		self.interactor = None
		
		self.sizer = wx.GridBagSizer(4, 2)
		self.SetSizer(self.sizer)
		self.eventRecorder = vtk.vtkInteractorEventRecorder()
		self.SetAutoLayout(1)
		#lib.messenger.connect(None, "visualizer_mode_loading", self.onLoadMode)
		
		self.numberOfChannels = 0
		lib.messenger.connect(None, "update_annotations", self.updateAnnotations)
		lib.messenger.connect(None, "tree_selection_changed", self.updateInterpolationGUI)
		self.createAnnotationToolbar()		  
        
	def updateInterpolationGUI(self, *args):
		"""
		"""
		if self.visualizer.dataUnit and INCLUDE3D:
			self.interpolationStart.SetRange(1, self.visualizer.dataUnit.getDimensions()[2])
			self.interpolationEnd.SetRange(1, self.visualizer.dataUnit.getDimensions()[2])

	def onCopyAll(self, event):
		"""
		"""
		shapeAnnotations = filter(lambda x:isinstance(x, GUI.OGLAnnotations.ShapeAnnotation), self.visualizer.getRegionsOfInterest())
		for shapeAnnotation in shapeAnnotations:
			if shapeAnnotation.Selected() and shapeAnnotation.parent != None:
				annotations = shapeAnnotation.parent.GetAnnotations()
				for i in range(len(annotations)):
					if shapeAnnotation != annotations[i]:
						annotations[i].restoreFrom(shapeAnnotation)
				break

	def onInterpolate(self, event):
		"""
		"""
		if self.visualizer.dataUnit:
			start = self.interpolationStart.GetValue() - 1
			end = self.interpolationEnd.GetValue() - 1
			diff = end - start
			if diff < 0:
				raise Exception("The starting point for the ROI interpolation must be greater than its end point.")

			# This is only valid for 3D shape annotations.
			annotations = filter(lambda x:isinstance(x, GUI.OGLAnnotations.ShapeAnnotation), self.visualizer.getRegionsOfInterest())
			# Only one can be selected right? :)
			for annotation in annotations:
				if annotation.Selected() and annotation.parent != None:
					annotations = annotation.parent.GetAnnotations()
					break
						
				startAnnotation = annotations[start]
				endAnnotation = annotations[end]

				for annotation in annotations:
					print annotation.sliceNumber

			crop1 = []
			crop2 = []

			if isinstance(startAnnotation, GUI.OGLAnnotations.MyCircle) or isinstance(startAnnotation, GUI.OGLAnnotations.MyRectangle):
				startW, startH = startAnnotation.GetBoundingBoxMin()
				startX, startY = startAnnotation.GetX(), startAnnotation.GetY()

				endW, endH = endAnnotation.GetBoundingBoxMin()
				endX, endY = endAnnotation.GetX(), endAnnotation.GetY()

				sizes = lib.ImageOperations.InterpolateBetweenCrops([(startW, startH)], [(endW, endH)], diff - 1)
				coordinates = lib.ImageOperations.InterpolateBetweenCrops([(startX, startY)], [(endX, endY)], diff - 1)

				if len(sizes) != len(coordinates):
					errorString = "The number of size dimensions (%d) and coordinates (%d) are different. Cannot proceed with the 3D crop." % (len(sizes), len(coordinates))
					raise Exception(errorString)

				for i in range(0, len(sizes)):
					annotation = annotations[start + i]
					# The difference between handling interpolation with polygons and rectangles/circles,
					# is that polygons can have several points, (x, y)-pairs, that define a single polygon.
					# Rectangles/circles only have one (x, y)-pair per crop (what we define as "crop" in
					# the method at least). These pairs are size (width and height) and coordinates (x and y).
					# And since the "crops" only have one pair, we can safely access the [0] element all the time.
					x, y = coordinates[i][0]
					w, h = sizes[i][0]
					annotation.SetX(x)
					annotation.SetY(y)
					annotation.SetWidth(w)
					annotation.SetHeight(h)

			elif isinstance(startAnnotation, GUI.OGLAnnotations.MyPolygon):
				startPoints = startAnnotation._points
				endPoints = endAnnotation._points

				x1 = startAnnotation.GetX()
				y1 = startAnnotation.GetY()

				x2 = endAnnotation.GetX()
				y2 = endAnnotation.GetY()

				for point in startPoints:
					crop1.append((point[0] + x1, point[1] + y1))

				for point in endPoints:
					crop2.append((point[0] + x2, point[1] + y2))

				# diff - 1, because the InterpolateBetweenCrops function
				# takes as its third parameter a "points inbetween" integer.
				# If we want to interpolate between 1 and 15, then that's 13
				# points inbetween, not 14.
				points = lib.ImageOperations.InterpolateBetweenCrops(crop1, crop2, diff - 1)
				for i in range(0, len(points)):
					point = points[i]
					annotation = annotations[start + i]
					# shape._offset = (self.xoffset, self.yoffset)
					for p in range(len(annotation.GetPoints())):
						annotation.DeletePolygonPoint(p)
					pts = []
					mx, my = annotation.polyCenter(point)
					for x, y in point:
						pts.append((((x - mx)), ((y - my))))
					annotation.Create(pts)
					annotation.SetX(mx)
					annotation.SetY(my)


	def onLoadMode(self, obj, evt, vismode):
		"""
		an event handler for when visualizer is loading a mode
		"""
		renwin = vismode.getRenderWindow()
		if renwin:
			self.interactor = renwin.GetInteractor()
			self.eventRecorder.SetInteractor(self.interactor)
		else:
			self.interactor = None
			
	def createAnnotationToolbar(self):
		"""
		Method to create a toolbar for the annotations
		"""		   
		icondir = scripting.get_icon_dir()
		def createBtn(bid, gifname, tooltip, btnclass = buttons.GenBitmapToggleButton):
			bmp = wx.Image(os.path.join(icondir, gifname), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
			
			btn = btnclass(self, bid, bmp)
			
			btn.SetBestSize((32, 32))
			#btn.SetBitmapLabel()
			btn.SetToolTipString(tooltip)
			return btn
		
		self.circleBtn = createBtn(MenuManager.ID_ROI_CIRCLE, "circle.gif", "Select a circular area of the image")
		self.sizer.Add(self.circleBtn, (0, 0))
		
		self.rectangleBtn = createBtn(MenuManager.ID_ROI_RECTANGLE, "rectangle.gif", \
										"Select a circular area of the image")
		self.sizer.Add(self.rectangleBtn, (0, 1))
		
		self.polygonBtn = createBtn(MenuManager.ID_ROI_POLYGON, "polygon.gif", \
										"Select a polygonal area of the image")
		self.sizer.Add(self.polygonBtn, (1, 0))
		
		self.scaleBtn = createBtn(MenuManager.ID_ADD_SCALE, "scale.gif", "Draw a scale bar on the image")
		self.sizer.Add(self.scaleBtn, (1, 1))

		if INCLUDE3D:
			self.threeDPolygonBtn = createBtn(MenuManager.ID_ROI_THREE_D_POLYGON, "three_d_polygon.gif", "Select one or several polygonal areas of the image in different slices to perform a 3D crop")
			self.sizer.Add(self.threeDPolygonBtn, (2, 0))

			self.threeDCircleBtn = createBtn(MenuManager.ID_ROI_THREE_D_CIRCLE, "three_d_circle.gif", "Select one or several circle areas of the image in different slices to perform a 3D crop")
			self.sizer.Add(self.threeDCircleBtn, (2, 1))

			self.threeDRectangleBtn = createBtn(MenuManager.ID_ROI_THREE_D_RECTANGLE, "three_d_rectangle.gif", "Select one or several rectangle areas of the image in different slices to perform a 3D crop")
			self.sizer.Add(self.threeDRectangleBtn, (3, 0))

		# Interpolation stuff. :)
			self.interpolationStart = wx.SpinCtrl(self, wx.ID_ANY, size = (64, -1), min = 1, max = self.visualizer.dataUnit.getDimensions()[2] if self.visualizer.dataUnit != None else 1)
			self.interpolationStart.SetValue(1)
			self.sizer.Add(self.interpolationStart, (4, 0), span = (1, 2))
			self.interpolationEnd = wx.SpinCtrl(self, wx.ID_ANY, size = (64, -1), min = 1, max = self.visualizer.dataUnit.getDimensions()[2] if self.visualizer.dataUnit != None else 1)
			self.interpolationEnd.SetValue(1)
			self.sizer.Add(self.interpolationEnd, (5, 0), span = (1, 2))
			self.interpolateButton = wx.Button(self, wx.ID_ANY, "Interpolate", size = (64, 24))
			self.sizer.Add(self.interpolateButton, (6, 0), span = (1, 2))
			self.interpolateButton.Bind(wx.EVT_BUTTON, self.onInterpolate)

			self.copyToAllButton = wx.Button(self, wx.ID_ANY, "Copy to all", size = (64, 24))
			self.sizer.Add(self.copyToAllButton, (7, 0), span = (1, 2))
			self.copyToAllButton.Bind(wx.EVT_BUTTON, self.onCopyAll)

		#self.textBtn = createBtn(MenuManager.ID_ANNOTATION_TEXT, "text.gif", "Add a text annotation")
		#self.sizer.Add(self.textBtn, (2, 0))

		icon = wx.Image(os.path.join(icondir, "delete_annotation.gif"), wx.BITMAP_TYPE_GIF).ConvertToBitmap()
		
		self.deleteAnnotationBtn = buttons.GenBitmapButton(self, MenuManager.ID_DEL_ANNOTATION, icon)
		self.deleteAnnotationBtn.SetBestSize((32,32))
		self.deleteAnnotationBtn.SetToolTipString("Delete an annotation")
		
		self.sizer.Add(self.deleteAnnotationBtn, (3, 1))

		#self.roiToMaskBtn = createBtn(MenuManager.ID_ROI_TO_MASK, "roitomask.gif", \
		#								"Convert the selected Region of Interest to a Mask", \
		#								btnclass = buttons.GenBitmapButton)
		#self.sizer.Add(self.roiToMaskBtn, (4, 0))

		#self.fontBtn = createBtn(MenuManager.ID_ANNOTATION_FONT,"fonts.gif",\
		#							"Set the font for annotations", btnclass=buttons.GenBitmapButton)
		#self.sizer.Add(self.fontBtn, (3,1))

		self.colorSelect = csel.ColourSelect(self, -1, "", self.annotateColor, size = (65, -1))
		self.sizer.Add(self.colorSelect, (8, 0), span = (1, 2))
		
		#self.resamplingBtn = createBtn(MenuManager.ID_RESAMPLING, "resample.gif", \
		#								"Enable or disable the resampling of image data")
		#self.resamplingBtn.SetToggle(1)
		
		#self.resampleToFitBtn = createBtn(MenuManager.ID_RESAMPLE_TO_FIT, "resample_tofit.gif", \
		#									"Enable or disable the resampling of image data")
		
		#self.sizer.Add(self.resamplingBtn, (6, 0))
		#self.sizer.Add(self.resampleToFitBtn, (6, 1))
		
#		 self.recordBtn = buttons.GenToggleButton(self, MenuManager.ID_RECORD_EVENTS, "Record", size=(64,-1))
#		 self.sizer.Add(self.recordBtn, (7,0), span=(1,2))
		
#		 self.playBtn = createBtn(MenuManager.ID_PLAY_EVENTS,"player_play.gif", \
#									"Play the recorded events", btnclass=buttons.GenBitmapButton)
#		 self.stopBtn = createBtn(MenuManager.ID_PLAY_EVENTS,"player_pause.gif", \
#									"Stop playing the recorded events", btnclass=buttons.GenBitmapButton)
#		 self.sizer.Add(self.playBtn, (8,0))
#		 self.sizer.Add(self.stopBtn, (8,1))
		
#		 self.playBtn.Bind(wx.EVT_BUTTON, self.onPlayRecording)
#		 self.stopBtn.Bind(wx.EVT_BUTTON, self.onStopPlaying)
#		 self.recordBtn.Bind(wx.EVT_BUTTON, self.onRecord)		  
		
#		bmp = wx.Image(os.path.join(iconpath,"resample.gif")).ConvertToBitmap()
#		tb.DoAddTool(MenuManager.ID_RESAMPLING, "Resampling", bmp, kind = wx.ITEM_CHECK, \
#						shortHelp = "Enable or disable the resampling of image data")
#		wx.EVT_TOOL(self,MenuManager.ID_RESAMPLING,self.onResampleData)
#		tb.EnableTool(MenuManager.ID_RESAMPLING,0)
#		tb.ToggleTool(MenuManager.ID_RESAMPLING,1)
		
#		sbox = wx.StaticBox(self,-1,"Resampling")
#		sboxsizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
#		self.resamplingOff = wx.RadioButton(self,-1,"Disabled", style = wx.RB_GROUP)
#		self.resamplingOn = wx.RadioButton(self,-1,"Enabled")
#		self.resampleToFit = wx.RadioButton(self,-1,"To fit")
		
#		sboxsizer.Add(self.resamplingOn)
#		sboxsizer.Add(self.resamplingOff)
#		sboxsizer.Add(self.resampleToFit)
#		self.sizer.Add(sboxsizer, (6,0),span=(1,2))
#		self.sizer.Add(self.resamplingOn, (7,0),span=(1,2))
#		self.sizer.Add(self.resampleToFit, (8,0),span=(1,2))
		
#		self.dimInfo = UIElements.DimensionInfo(self,-1, size=(120,50))
#		self.sizer.Add(self.dimInfo, (6,0), span=(1,2))
	
		self.sizerCount = 8
		#self.resamplingBtn.Bind(wx.EVT_BUTTON, self.onResampleData)
		#self.resampleToFitBtn.Bind(wx.EVT_BUTTON, self.onResampleToFit)
		self.circleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
		self.rectangleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
		self.polygonBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
		self.scaleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
		if INCLUDE3D:
			self.threeDPolygonBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
			self.threeDCircleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
			self.threeDRectangleBtn.Bind(wx.EVT_BUTTON, self.addAnnotation)
		#self.roiToMaskBtn.Bind(wx.EVT_BUTTON, self.roiToMask)
#		wx.EVT_TOOL(self.parent,MenuManager.ID_ADD_SCALE,self.addAnnotation)
		self.deleteAnnotationBtn.Bind(wx.EVT_BUTTON, self.deleteAnnotation)
		
	def onRecord(self, evt):
		"""
		Start / stop recording events
		"""
		flag = evt.GetIsDown()
		#TODO: playBtn and stopBtn are defined in commented code and therefore not working
		self.playBtn.Enable(not flag)
		self.stopBtn.Enable(not flag)
		if flag:
			self.eventRecorder.SetEnabled(1)
			self.eventRecorder.SetFileName("events.log")
			self.eventRecorder.Record()
		else:
			self.eventRecorder.Stop()
			self.eventRecorder.SetEnabled(0)

			print "Recorded", self.eventRecorder.GetInputString()
			
	def onPlayRecording(self, evt):
		"""
		play a recorded event sequence
		"""
		self.eventRecorder.Play()
		
	def onStopPlaying(self, evt):
		"""
		stop playing a recorded event sequence
		"""
		self.eventRecorder.Stop()

	def onResampleToFit(self, evt):
		"""
		Toggle the resampling on / off
		"""
#		 flag=self.resampleBtn.GetValue()
		
		flag = evt.GetIsDown()
		scripting.resampleToFit = flag
		self.visualizer.updateRendering()		   


#	def onResampleData(self, evt):
#		"""
#		Toggle the resampling on / off
#		"""
#		flag = evt.GetIsDown()
#		scripting.resamplingDisabled = not flag
#
#		lib.messenger.send(None,"data_dimensions_changed")
		
	def clearChannelItems(self):
		"""
		Remove all the channel items
		"""
		for key in self.channelButtons.keys():
			btn = self.channelButtons[key]
			btn.Show(0)
			self.sizer.Detach(btn)
			self.sizer.Remove(btn)
			del btn
		self.numberOfChannels = 0
		
		
	def addChannelItem(self, name, bitmap, toolid, func):
		"""
		Add a channel item
		""" 
		icondir = scripting.get_icon_dir()		   
		btn = buttons.GenBitmapToggleButton(self, toolid, bitmap)
		w, h = bitmap.GetWidth(), bitmap.GetHeight()
		#btn.SetBestSize((w,h))			   
		btn.SetSize((64, 64))
		btn.SetToolTipString(name)
		btn.Bind(wx.EVT_BUTTON, func)
		
		self.numberOfChannels += 1
		self.sizer.Add(btn, (self.sizerCount + self.numberOfChannels, 0), span = (1, 2))
		self.channelButtons[toolid] = btn
		self.Layout()
		
	def toggleChannelItem(self, toolid, flag):
		"""
		Toggle a channel item on or off
		"""
		self.channelButtons[toolid].SetToggle(flag)
		
	def addAnnotation(self, event):
		"""
		Draw a scale to the visualization
		"""
		if not self.visualizer.getCurrentMode():
			return

		annclass = None
		eid = event.GetId()
		multiple = 0
		if eid == MenuManager.ID_ADD_SCALE:
			annclass = "SCALEBAR"
		elif eid == MenuManager.ID_ANNOTATION_TEXT:
			annclass = "TEXT"
		elif eid == MenuManager.ID_ROI_CIRCLE:
			annclass = "CIRCLE"
		elif eid == MenuManager.ID_ROI_RECTANGLE:
			annclass = "RECTANGLE"
		elif eid == MenuManager.ID_ROI_POLYGON:
			annclass = "POLYGON"
			multiple = 1
		elif eid == MenuManager.ID_ROI_THREE_D_POLYGON:
			annclass = "3D_POLYGON"
			multiple = 1
		elif eid == MenuManager.ID_ROI_THREE_D_CIRCLE:
			annclass = "3D_CIRCLE"
		elif eid == MenuManager.ID_ROI_THREE_D_RECTANGLE:
			annclass = "3D_RECTANGLE"
		else:
			Logging.info("BOGUS ANNOTATION SELECTED!", kw = "visualizer")
						
		self.visualizer.getCurrentMode().annotate(annclass, multiple = multiple)
		
		
	def deleteAnnotation(self, event):
		"""
		Delete annotations on the image
		"""
		if self.visualizer.getCurrentMode():
			self.visualizer.getCurrentMode().deleteAnnotation()

	def updateAnnotations(self, *args):
		"""
		Untoggle the annotation buttons because an annotation was added
		"""
		self.scaleBtn.SetToggle(False)
		self.circleBtn.SetToggle(False)
		self.rectangleBtn.SetToggle(False)
		self.polygonBtn.SetToggle(False)
		if INCLUDE3D:
			self.threeDPolygonBtn.SetToggle(False)
			self.threeDCircleBtn.SetToggle(False)
			self.threeDRectangleBtn.SetToggle(False)
				
	def roiToMask(self, evt):
		"""
		Convert the selected ROI to mask
		"""
		if hasattr(self.visualizer.currentWindow, "roiToMask"):
			masks, names = self.visualizer.currentWindow.roiToMask()
                        name = ",".join(names)
			dims = self.visualizer.dataUnit.getDimensions()
			for i in range(len(masks)):
                                masks[i] = MaskTray.Mask(name, dims, masks[i])
			self.visualizer.setMask(masks)
			
