#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: XMLGUIBuilder
 Project: BioImageXD
 Created: 25.01.2008, KP
 Description:

 A class for building a GUI for a processing filter using an XML description

 Copyright (C) 2005	 BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and / or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307	 USA

"""
__author__ = "BioImageXD Project < http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005 / 01 / 13 14:52:39 $"

import xml.sax
import wx
import cStringIO

class XMLGUIHandler(xml.sax.handler.ContentHandler):
	"""
	Created: 26.01.2008, KP
	Description: the SAX parser for XMLGUI definitions
	"""
	def __init__(self):
		pass
		
	def startElement(self, name, attrs):
		"""
		handle the starting on an element
		"""
		print "startElement",name,attrs
		
	def endElement(self, name):
		"""
		handle the ending of an element
		"""
		print "endElement",name

	def endDocument(self):
		pass
		
	


class XMLGUIElement:
	"""
	a base class for all user interface elements available to XMLGUIBuilder
	"""
	inputTypes = []
	def __init__(self, builder, parent, *args, **kws):
		self.id = kws.get("id","")
		self.currentFilter = builder.getFilter()
		self.parent = parent
		self.builder = builder
		self.uiElement = None
		
	def getUI(self):
		"""
		return the actual UI element
		"""
		return self.uiElement
		
class XMLGUIContainer:
	"""
	Created: 26.01.2008, KP
	Description: a base class for all container elements in the XMLGUIBuilder
	"""
	def __init__(self, parent, *args, **kws):
		pass
		
	
class XMLGUIBuilder(wx.Panel):
	"""
	An XML based GUI builder for the manipulation filters
	""" 
	def __init__(self, parent, myfilter):
		"""
		Initialization
		""" 
		wx.Panel.__init__(self, parent, -1)

		self.filter = myfilter
		self.sizer = wx.GridBagSizer()
		
		self.elementsForParameters = {}
		

		self.items = {}
		self.buildGUI(myfilter)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		
	def getFilter(self):
		"""
		Creted: 26.01.2008, KP
		return the current filter
		"""
		return self.filter
		
	def getElementForParameter(self, parameter):
		"""
		return the user interafece element for reading the given parameter
		"""
		return self.elementsForParameter.get(parameter,None)
		
	def buildGUI(self, filter):
		"""
		create the GUI for the filter
		"""
		xmlstring = filter.getXMLDescription()
		parser = xml.sax.make_parser()
		parser.setContentHandler(XMLGUIHandler())
		parser.parse(cStringIO.StringIO(xmlstring))
		
