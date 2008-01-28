# -*- coding: iso-8859-1 -*-
"""
 Unit: Manipulation
 Project: BioImageXD
 Created: 04.04.2006, KP
 
 Description:
 A module for various data manipulation purposes

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

__author__ = "BioImageXD Project <http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.13 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import lib.FilterBasedModule

class Manipulation(lib.FilterBasedModule.FilterBasedModule):
	"""
	Created: 04.04.2006, KP
	Description: Manipulationes a single dataunit in specified ways
	"""

	def __init__(self, **kws):
		"""
		Initialization
		"""
		lib.FilterBasedModule.FilterBasedModule.__init__(self, **kws)
