#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: UrmasPersist
 Project: BioImageXD
 Created: 11.04.2005, KP
 Description:

 URPO - The URMAS Persistent Objects
 
 This is a module for writing out / reading in an URMAS timeline
 that uses the python ConfigParser. Urpo utilizes the __getstate__ / 
 __setstate__ methods for pickling. A __getstate__ is required, but
 if no __setstate__ is present, Urpo will update target dictionary
 with the depersisted items.
 
 
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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#from ConfigParser import *

from lib.persistence import state_pickler

def getVTKState(obj):
	"""
	Created: 02.08.2005, KP
	Description: Get state of vtk object
	"""     
	state = {}
	blocked = ["GetOutput", "GetReleaseDataFlag", "GetOutputPort", "GetViewPlaneNormal"]
	dirlist = dir(obj)
	for i in dirlist:
		if i not in blocked:                
			if i[0:3] == "Get":
				setter = i.replace("Get", "Set")
				if setter in dirlist:
					try:
						state[i] = eval("obj.%s()" % i)
					except:
						pass
	return state
	
def setVTKState(obj, state):
	"""
	Created: 02.08.2005, KP
	Description: Set state of vtk object
	"""     
	for key in state.keys():
		setfunc = key.replace("Get", "Set")
#            Logging.info("Setting %s of %s"%(setfunc,obj),kw="rendering")
		try:
			eval("obj.%s(state[\"%s\"])" % (setfunc, key))
		except:
			pass
	

class UrmasPersist:
	"""
	Created: 11.04.2005, KP
	Description: A class that persists / depersists an Urmas timeline
	"""    
	def __init__(self, control):
		"""
		Created: 11.04.2005, KP
		Description: Initialize
		"""           
		self.control = control
	
	def persist(self, filename):
		"""
		Created: 11.04.2005, KP
		Description: Write the given control object out to the given file
		"""    
		state_pickler.dump(self.control, open(filename, "w"))
		
	def depersist(self, filename):
		"""
		Created: 11.04.2005, KP
		Description: Read the given control object from a given file
		"""               
		state = state_pickler.load_state(open(filename, "r"))
		state_pickler.set_state(self.control, state)
