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
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


def linearInterpolation(paramlist1, paramlist2, n):
		"""
		Function: linearInterpolation(paramlist1,paramlist2,n)
		Created: 09.12.2004, KP
		Description: A function that interpolates n new parameter lists between 
					 two given parameterlists
		Parameters:
			paramlist1      The starting parameters
			paramlist2      The ending parameters
			n               How many parameter lists are interpolated between 
							paramlist1 and paramlist2
		"""
		paramlen = len(paramlist1)
		if len(paramlist1) != len(paramlist2):
			raise ("Length of parameter lists do no match: length of first "
			"%d != length of second %d" % (len(paramlist1), len(paramlist2)))
		diffs = []
		results = []
		# Calculate differences of each parameter
		for i in range(paramlen):
			p1, p2 = paramlist1[i], paramlist2[i]
			diff = p2 - p1
			diff /= float(n + 1)
			diffs.append(diff)
		# Create new parameter lists with interpolated parameters
		for newnumber in range(n):
			newlist = []
			for i in range(paramlen):
				p = paramlist1[i]
				p = p + (newnumber + 1) * diffs[i]
				newlist.append(p)
			results.append(newlist)
		return results

interpolate = linearInterpolation


