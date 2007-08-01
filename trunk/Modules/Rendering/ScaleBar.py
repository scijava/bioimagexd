# -*- coding: iso-8859-1 -*-

"""
 Unit: ScaleBar
 Project: BioImageXD
 Created: 05.06.2005, KP
 Description:

 A module containing a scale bar for visualization
 
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#import wx

from Visualizer.VisualizationModules import VisualizationModule
from Visualizer.ModuleConfiguration import ModuleConfigurationPanel
import vtk

def getClass():
	return ScaleBarModule

def getConfigPanel():
	return ScaleBarConfigurationPanel

def getName():
	return "Scale bar"

class ScaleBarModule(VisualizationModule):
	"""
	Created: 05.06.2005, KP
	Description: A module for showing a scale bar
	"""    
	def __init__(self, parent, visualizer, **kws):
		"""
		Created: 03.05.2005, KP
		Description: Initialization
		"""     
		self.x, self.y, self.z = -1, -1, -1
		VisualizationModule.__init__(self, parent, visualizer, **kws)   
		#self.name = "Scale bar"
		self.renew = 1
		self.mapper = vtk.vtkDataSetMapper()
		
		self.actor = vtk.vtkActor()
		self.actor.SetMapper(self.mapper)
		self.width = 10
		self.widthPx = 100
		self.voxelSize = (1, 1, 1)
		
		self.renderer = self.parent.getRenderer()
		self.renderer.AddActor(self.actor)
		

		self.polyLine = vtk.vtkPolyLine()
		#self.mapper.SetInput(self.polyLine.GetOutput())
		self.actor.GetProperty().SetColor(1, 1, 1)
			   
		self.textActor = vtk.vtkTextActor()
		#self.textActor.ScaledTextOn()
		self.renderer.AddActor2D(self.textActor)
		
		iactor = self.wxrenwin.GetRenderWindow().GetInteractor()
		style = iactor.GetInteractorStyle()
#        style.AddObserver("StartInteractionEvent",self.updateLine)
		style.AddObserver("EndInteractionEvent", self.updateRendering)
		#self.updateRendering()
		
		
	def setDataUnit(self, dataunit):
		"""
		Created: 28.04.2005, KP
		Description: Sets the dataunit this module uses for visualization
		"""       
		VisualizationModule.setDataUnit(self, dataunit)
		
		if self.visualizer.getProcessedMode():
			self.voxelSize = dataunit.getSourceDataUnits()[0].getVoxelSize()
		else:
			self.voxelSize = dataunit.getVoxelSize()  
		self.updateLine()
	  
	def pointsToPolyline(self, pts, rawmode = 0):
		"""
		Created: 06.05.2005, KP
		Description: Make a set of 2D points into a 3D polyline
		"""      
		renderer = self.renderer
		n = 0
		points = vtk.vtkPoints()
		lst = []
		for point in pts:
			x, y, z = point
			renderer.SetDisplayPoint(x, y, z)
			renderer.DisplayToWorld()
			pt = renderer.GetWorldPoint()
			pt = pt[0:3]
			if rawmode:
				lst.append(pt)
			else:
				points.InsertPoint(n, pt)
			n += 1
		if rawmode:
			points = lst
		return n, points

	def updateLine(self):
		"""
		Created: 06.05.2005, KP
		Description: Update the line to be near the selected point
		"""          
		
		self.polyGrid = vtk.vtkUnstructuredGrid()
		self.mapper.SetInput(self.polyGrid)

		
		pts = []
		pts.append((10, 105, 0))
		pts.append((10, 95, 0))
		pts.append((10, 100, 0))
		pts.append((10 + self.widthPx, 100, 0))
		pts.append((10 + self.widthPx, 105, 0))
		pts.append((10 + self.widthPx, 95, 0))
		n, points = self.pointsToPolyline(pts)
		print "widthPx=", 100
		pts2 = [(0, 0, 0), (self.widthPx, 0, 0)]
		n, points2 = self.pointsToPolyline(pts2, 1)
		p1, p2 = points2
		m = vtk.vtkMath()
		x, y, z = p1
		x *= self.voxelSize[0] * 1000000
		y *= self.voxelSize[1] * 1000000
		z *= self.voxelSize[2] * 1000000
		p1 = (x, y, z)
		x, y, z = p2
		x *= self.voxelSize[0] * 1000000
		y *= self.voxelSize[1] * 1000000
		z *= self.voxelSize[2] * 1000000
		p2 = (x, y, z)
		diff = m.Distance2BetweenPoints(p2, p1)

		
		print "got diff=", diff
		self.width = diff

		self.textActor.SetDisplayPosition(-40 + self.widthPx / 2, 80)
		self.textActor.SetInput("%.2fum" % self.width)

		
		self.polyLine.GetPointIds().SetNumberOfIds(n)
		for i in range(n):
			self.polyLine.GetPointIds().SetId(i, i)
		
		self.polyGrid.InsertNextCell(self.polyLine.GetCellType(),
									 self.polyLine.GetPointIds())
		self.polyGrid.SetPoints(points)


	def showTimepoint(self, value):
		"""
		Created: 28.04.2005, KP
		Description: Set the timepoint to be displayed
		"""          
		pass
		
	def updateRendering(self, e1 = None, e2 = None):
		"""
		Created: 03.05.2005, KP
		Description: Update the Rendering of this module
		"""             
		self.updateLine()
		self.mapper.Update()
		self.wxrenwin.Render()    

	def disableRendering(self):
		"""
		Created: 15.05.2005, KP
		Description: Disable the Rendering of this module
		"""          
		self.renderer.RemoveActor(self.actor)
		self.renderer.RemoveActor2D(self.textActor)
		self.wxrenwin.Render()
		
	def enableRendering(self):
		"""
		Created: 15.05.2005, KP
		Description: Enable the Rendering of this module
		"""          
		self.renderer.AddActor(self.actor)
		self.renderer.AddActor2D(self.textActor)
		self.wxrenwin.Render()

class ScaleBarConfigurationPanel(ModuleConfigurationPanel):
		
	def __init__(self, parent, visualizer, name = "Scale bar", **kws):
		"""
		Created: 04.05.2005, KP
		Description: Initialization
		"""     
		ModuleConfigurationPanel.__init__(self, parent, visualizer, name, **kws)
	
	def initializeGUI(self):
		"""
		Created: 28.04.2005, KP
		Description: Initialization
		"""  
#        self.addButton=wx.Button(self,-1,"Add plane")
#        self.addButton.Bind(wx.EVT_BUTTON,self.onAddPlane)
#        self.contentSizer.Add(self.addButton,(0,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)

	def setModule(self, module):
		"""
		Created: 28.04.2005, KP
		Description: Set the module to be configured
		"""  
		ModuleConfigurationPanel.setModule(self, module)
