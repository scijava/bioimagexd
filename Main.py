#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Main.py
 Project: Selli
 Created: 01.11.2004
 Creator: KP
 Description:

 Main program for the LSM Module

 Modified: 03.11.2004 KP - Added the LSMApplication class to encapsulate Tk root
                           creation
           10.1.2005 KP - Changed class to use wxPython classes

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path
import sys
import Configuration

#sys.path.insert(0,"C:\\Mingw\\lib")
# This will fix the VTK paths using either values from the
# configuration file, or sensible defaults
cfg=Configuration.Configuration("BioImageXD.ini")

import wx
import GUI


class LSMApplication(wx.App):
    """
    Class: LSMApplication
    Created: 03.11.2004, KP
    Description: Encapsulates the wxPython initialization and mainwindow creation
    """

    def OnInit(self):
        """
        Method: OnInit
        Created: 10.1.2005, KP
        Description: Create the application's main window
        """
        self.mainwin=GUI.MainWindow(None,-1,self)
        self.mainwin.Show(True)
        self.SetTopWindow(self.mainwin)
        return True

    def run(self):
        """
        Method: run
        Created: 03.11.2004, KP
        Description: Run the wxPython main loop
        """
        self.MainLoop()

if __name__=='__main__':
    app=LSMApplication(False)

    app.run()



