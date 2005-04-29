#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: RunTests.py
 Project: Selli
 Created: 23.11.2004, KP
 Description:

 Run all the unittests.

 Modified: 23.11.2004 KP - Created the module

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
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.4 $"
__date__ = "$Date: 2005/01/12 10:07:18 $"

import os,os.path
import sys
import unittest
modulesdir=os.getcwd()
sys.path.append(modulesdir)
lsmdir=os.path.join(os.getcwd(),"LSM")
sys.path.append(lsmdir)

def main():
    """
    Function: main()
    Created: 10.11.2004, KP
    Description: A function that imports all the unittest suites and runs them
    """
    # Import all the test suites
    import Tests
    suite=Tests.getSuites()
    # Load the test runner
    runner=unittest.TextTestRunner()
    # and run the suites
    runner.run(suite)
    # See Tests directory for the actual test suites



if __name__=='__main__':
    import Main
    Main.fixpaths()

    main()
