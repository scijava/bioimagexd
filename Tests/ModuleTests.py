# -*- coding: iso-8859-1 -*-
"""
 Unit: ModuleTests.py
 Project: Selli
 Created: 23.11.2004, KP
 Description:

 Test cases for the operation of the various modules

 Modified: 23.11.2004 KP - Created the test cases
 
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

import Colocalization
import vtk
import Module
import random

class ColocalizationTestCase(unittest.TestCase):
    """
    --------------------------------------------------------------
    Class: ColocalizationTestCase
    Created: 23.11.2004
    Creator: KP
    Description: A class for testing the colocalization module
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
        self.module=Colocalization.Colocalization()
        self.reader=vtk.vtkXMLImageDataReader()
        self.reader.SetFileName("H:\\Data\\Sample1\sample1_green0.vti")
        self.reader.Update()
        self.green=self.reader.GetOutput()
        self.reader.SetFileName("H:\\Data\\Sample1\sample1_red0.vti")
        self.reader.Update()
        self.red=self.reader.GetOutput()

        self.data1=self.module.allocateImageData(5,5,5)
        self.data2=self.module.allocateImageData(5,5,5)

    def tearDown(self):
        """
        --------------------------------------------------------------
        Method: tearDown()
        Created: 23.11.2004
        Creator: KP
        Description: Cleans things up
        -------------------------------------------------------------
        """
        del self.module
        del self.reader

    def testThreshold(self):
        """
        --------------------------------------------------------------
        Method: testThreshold()
        Created: 23.11.2004
        Creator: KP
        Description: Test for threshold in Colocalization
        -------------------------------------------------------------
        """

        # place 10 random points in the new data
        colopoints=[]
        noncolopoints=[]
        
        for i in range(10):
            x=random.randrange(5)
            y=random.randrange(5)
            z=random.randrange(5)
            colopoints.append((x,y,z))
            self.data1.SetScalarComponentFromDouble(x,y,z,0,255)
            self.data2.SetScalarComponentFromDouble(x,y,z,0,255)

        for i in range(10):
            x=random.randrange(5)
            y=random.randrange(5)
            z=random.randrange(5)
            colopoints.append((x,y,z))
            self.data1.SetScalarComponentFromDouble(x,y,z,0,70)
            self.data2.SetScalarComponentFromDouble(x,y,z,0,70)
        
        # do the colocalization
        self.module.reset()
        self.module.addInput(self.data1,threshold=80)
        self.module.addInput(self.data2,threshold=80)
        colo=self.module.doColocalization()

        # results
        for point in colopoints:
            x,y,z=point
            assert(colo.GetScalarComponentAsDouble(x,y,z,0)!=0),\
                "Colocalization point is non-zero"

        for point in noncolopoints:
            assert(colo.GetScalarComponentAsDouble(x,y,z,0)==0),\
            "Point with no colocalization is zero"




def suite():
    """
    --------------------------------------------------------------
    Function: suite()
    Created: 23.11.2004
    Creator: KP
    Description: Runs test in this file
    -------------------------------------------------------------
    """
#    colosuite=unittest.makeSuite(ColocalizationTestCase,'test')
#    mergingsuite=unittest.makeSuite(ColorMergingTestCase,'test')

#    allsuites=unittest.TestSuite((colosuite,mergingsuite))
#    return allsuites
#    return colosuite
    return None
