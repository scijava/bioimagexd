#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: RunTests.py
 Project: Selli
 Created: 23.11.2004
 Creator: KP
 Description:

 Run all the unittests.

 Modified: 23.11.2004 KP - Created the module

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
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
    --------------------------------------------------------------
    Function: main()
    Created: 10.11.2004
    Creator: KP
    Description: A function that imports all the unittest suites and runs them
    -------------------------------------------------------------
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
