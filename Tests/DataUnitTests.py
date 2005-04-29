# -*- coding: iso-8859-1 -*-
"""
 Unit: DataUnitTests.py
 Project: Selli
 Created: 24.11.2004, JM
 Description:

 Test cases for DataUnits

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
import DataUnit
import CombinedDataUnit

class DataUnitTestCase(unittest.TestCase):
    """
    --------------------------------------------------------------
    Class: DataUnitTestCase
    Created: 24.11.2004
    Creator: KP
    Description: A class for testing the DataUnit's functions
    -------------------------------------------------------------
    """
    def setUp(self):
        """
        --------------------------------------------------------------
        Method: setUp()
        Created: 24.11.2004
        Creator: KP
        Description: Sets up the test data
        -------------------------------------------------------------
        """
        self.name="test"
        self.dataunit=DataUnit.DataUnit(self.name)

    def tearDown(self):
        """
        --------------------------------------------------------------
        Method: tearDown()
        Created: 24.11.2004
        Creator: KP
        Description: Cleans things up
        -------------------------------------------------------------
        """

        del self.dataunit

    def testDataUnit(self):
        """
        --------------------------------------------------------------
        Method: testDataUnit()
        Created: 24.11.2004
        Creator: KP
        Description: Test getName method in DataUnit
        -------------------------------------------------------------
        """

        assert(self.dataunit.getName() == self.name),\
        "DataUnit did not get the right name"

class SourceDataUnitTestCase(unittest.TestCase):
    """
    --------------------------------------------------------------
    Class: SourceDataUnitTestCase
    Created: 24.11.2004
    Creator: KP
    Description: A class for testing the SourceDataUnit's functions
    -------------------------------------------------------------
    """

    def setUp(self):
        """
        --------------------------------------------------------------
        Method: setUp()
        Created: 24.11.2004
        Creator: KP
        Description: Sets up the test data
        -------------------------------------------------------------
        """

        self.name="test"
        self.color=[10,20,30]
        self.dataunit=DataUnit.SourceDataUnit(self.name)
        self.dataunit.setColor(*color)
    def tearDown(self):
        """
        --------------------------------------------------------------
        Method: tearDown()
        Created: 24.11.2004
        Creator: KP
        Description: Cleans things up
        -------------------------------------------------------------
        """

        del self.dataunit

    def testDataUnit(self):
        """
        --------------------------------------------------------------
        Method: testDataUnit()
        Created: 24.11.2004
        Creator: KP
        Description: Tests methods in SourceDataUnit
        -------------------------------------------------------------
        """

        assert(self.dataunit.getName() == self.name),\
        "SourceDataUnit did not get the right name"
        assert(self.dataunit.red == color[1] and \
        self.dataunit.green == color[2] and \
        self.dataunit.blue == color[3]),\
        "SourceDataUnit did not get the right color"

class CombinedDataUnitTestCase(unittest.TestCase):
    """
    --------------------------------------------------------------
    Class: CombinedDataUnitTestCase
    Created: 24.11.2004
    Creator: KP
    Description: A class for testing the CombinedDataUnit's functions
    -------------------------------------------------------------
    """

    def setUp(self):
        """
        --------------------------------------------------------------
        Method: setUp()
        Created: 24.11.2004
        Creator: KP
        Description: Sets up the test data
        -------------------------------------------------------------
        """

        self.name="test"
        self.dataunit=DataUnit.CombinedDataUnit(self.name)

    def tearDown(self):
        """
        --------------------------------------------------------------
        Method: tearDown()
        Created: 24.11.2004
        Creator: KP
        Description: Cleans things up
        -------------------------------------------------------------
        """

        del self.dataunit

    def testDataUnit(self):
        """
        --------------------------------------------------------------
        Method: testDataUnit()
        Created: 24.11.2004
        Creator: KP
        Description: Test methods in CombinedDataUnit
        -------------------------------------------------------------
        """

        assert(self.dataunit.getName() == self.name),\
        "CombinedDataUnit did not get the right name"

def suite():
    """
    --------------------------------------------------------------
    Function: suite()
    Created: 24.11.2004
    Creator: KP
    Description: Runs test in this file
    -------------------------------------------------------------
    """

    DataUnitSuite=unittest.makeSuite(DataUnitTestCase,'test')
    SourceDataUnitSuite=unittest.makeSuite(SourceDataUnitTestCase,'test')

    allsuites=unittest.TestSuite((...))
    return allsuites
