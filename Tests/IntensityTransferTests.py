# -*- coding: iso-8859-1 -*-
"""
 Unit: IntensityTransferTests.py
 Project: Selli
 Created: 23.11.2004, KP
 Description:

 Test cases for the operation of intensity transfer function

 Modified: 24.11.2004 KP - Created the test cases

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

import unittest

import IntensityTransferFunction
import vtk
import Module
import random

class IntensityTransferTestCase(unittest.TestCase):
    """
    --------------------------------------------------------------
    Class: IntensityTransferTestCase
    Created: 24.11.2004
    Creator: KP
    Description: A class for testing the IntensityTransferFunction's functions
    -------------------------------------------------------------
    """
    def setUp(self):
        """
        --------------------------------------------------------------
        Method: setUp()
        Created: 23.11.2004
        Creator: KP
        Description: Sets up the test data
        -------------------------------------------------------------
        """
        tf=IntensityTransferFunction.IntensityTransferFunction()
        pass
    
    def tearDown(self):
        """
        --------------------------------------------------------------
        Method: tearDown()
        Created: 23.11.2004
        Creator: KP
        Description: Cleans things up
        -------------------------------------------------------------
        """
        pass
    
    def testIdentMapping(self):
        """
        --------------------------------------------------------------
        Method: testIdentMapping()
        Created: 23.11.2004
        Creator: KP
        Description: Test for mapping through intensity transfer function
        -------------------------------------------------------------
        """
        tf2=IntensityTransferFunction.IntensityTransferFunction()
        lst=tf2.getAsList()
        for i in range(256):
            assert lst[i]==i,"IntensityTransferFunction by default identical"


def suite():
    """
    --------------------------------------------------------------
    Function: suite()
    Created: 23.11.2004
    Creator: KP
    Description: Runs test in this file
    -------------------------------------------------------------
    """
    tfsuite=unittest.makeSuite(IntensityTransferTestCase,'test')
    return tfsuite
