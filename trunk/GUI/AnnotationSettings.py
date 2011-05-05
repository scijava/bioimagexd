# -*- coding: iso-8859-1 -*-

"""
 Unit: AnnotationSettings
 Project: BioImageXD
 Description:

 This is a singleton class that stores annotation settings.

 Copyright (C) 2005	 BioImageXD Project
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
__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx

class AnnotationSettings:
	instance = None
	class AnnotationSettingsHelper:
		def __call__(self, *args, **kwargs):
			if AnnotationSettings.instance is None:
				object = AnnotationSettings()
				AnnotationSettings.instance = object
			return AnnotationSettings.instance
	getInstance = AnnotationSettingsHelper()
	
	def __init__(self):
		if not AnnotationSettings.instance == None:
			raise RuntimeError, 'Only one instance of SettingsAnnotations is allowed!'
		AnnotationSettings.instance = self
		
		self.annotations = {}
		self.textColors = {}
		self.colorDatabase = wx.TheColourDatabase

	def getAnnotations(self):
		return self.annotations

	def setAnnotations(self, annotations):
		self.annotations = annotations

	def addAnnotation(self, annotation):
		if annotation not in self.annotations:
			self.annotations[annotation.getName()] = annotation

	def removeAnnotation(self, annotation):
		self.annotations.pop(annotation.getName())

	def addColor(self, id, color):
		if not self.textColors.has_key(id):
			self.textColors[id] = color
			colordb = wx.TheColourDatabase
			colordb.AddColour(id, color)

	def getColor(self, id):
		return self.textColors.get(id)
		
	def updateAnnotation(self, annotation, newAnnotation):
		self.annotations[annotation.getName()] = newAnnotation
