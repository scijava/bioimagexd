#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: Main
 Project: BioImageXD
 Created: 01.11.2004, KP
 Description:

 BioImageXD main program

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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import os.path
import os
import sys
import csv


import Logging

import glob
import Configuration

#sys.path.insert(0,"C:\\Mingw\\lib")
# This will fix the VTK paths using either values from the
# configuration file, or sensible defaults
cfg=Configuration.Configuration("BioImageXD.ini")

import imp

def main_is_frozen():
   return (hasattr(sys, "frozen") or # new py2exe
           hasattr(sys, "importers") # old py2exe
           or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
   if main_is_frozen():
       return os.path.dirname(sys.executable)
   return os.path.dirname(sys.argv[0])

import lib
import GUI
import Visualizer
import wx

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
        bmp = wx.Image(os.path.join("Icons","splash2.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()

        splash=wx.SplashScreen(bmp,
                                 wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                                 3000, None, -1)
        splash.Show()
        self.mainwin=GUI.MainWindow.MainWindow(None,-1,self,splash)
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
    if "tofile" in sys.argv:
        fp=open("log.txt","w")
        Logging.outfile=fp

    if "py2exe" in sys.argv:
        from build_app import *
        build()
    else:
        # Import Psyco if available
        #try:
        #    import psyco
        #    psyco.full()
        #except ImportError:
        #    pass
        # If the main application is frozen, then we redirect logging
        # to  a log file
        if main_is_frozen():
            import time
            logfile="%s.log"%(time.strftime("%d.%m.%y"))
            f=open(logfile,"w")
            sys.stdout = f 
            sys.stderr = f
            Logging.outfile = f
            Logging.enableFull()
        app=LSMApplication(0)
        app.run()



