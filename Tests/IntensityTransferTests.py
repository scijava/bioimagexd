# -*- coding: iso-8859-1 -*-
"""
 Unit: IntensityTransferTests.py
 Project: Selli
 Created: 23.11.2004
 Creator: KP
 Description:

 Test cases for the operation of intensity transfer function

 Modified: 24.11.2004 KP - Created the test cases


 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
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
