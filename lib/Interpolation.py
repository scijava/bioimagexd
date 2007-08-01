# -*- coding: iso-8859-1 -*-

"""
 Unit: Interpolation
 Project: BioImageXD
 Created: 09.12.2004, KP
 Description:

 A module used to interpolate the intensity transfer functions based on given 
 parameters.


 Copyright (C) 2005  BioImageXD Project
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
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307  USA
"""
__author__ = "BioImageXD Project < http://www.bioimagexd.org/>"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005 / 01 / 13 13:42:03 $"

import bxdexceptions

def linearInterpolation(paramlist1, paramlist2, numberofLists):
	"""
	Function: linearInterpolation(paramlist1, paramlist2, n)
	Created: 09.12.2004, KP
	Description: A function that interpolates n new parameter lists between 
				 two given parameterlists
	Parameters:
		paramlist1		The starting parameters
		paramlist2		The ending parameters
		n				How many parameter lists are interpolated between 
						paramlist1 and paramlist2
	"""
	paramlen = len(paramlist1)
	if len(paramlist1) != len(paramlist2):
		raise bxdexceptions.IncorrectSizeException(("Length of parameter lists do no match: length of first "
		"%d != length of second %d" % (len(paramlist1), len(paramlist2))))
	interpolationStepSizes = []
	results = []
	# Calculate differences of each parameter
	for i in range(paramlen):
		parameterOne, parameterTwo = paramlist1[i], paramlist2[i]
		difference = parameterTwo - parameterOne
		interpolationStepSize = difference / float(numberofLists + 1)
		interpolationStepSizes.append(interpolationStepSize)
	# Create new parameter lists with interpolated parameters
	for interpolationFactor in range(1, numberofLists + 1):
		newlist = []
		for i in range(paramlen):
			parameter = paramlist1[i]
			parameter = parameter + (interpolationFactor) * interpolationStepSizes[i]
			newlist.append(parameter)
		results.append(newlist)
	return results
