#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: BioImageXD
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
import imp
import platform
import scripting

try:
    import profile
except:
    profile=None

if "check" in sys.argv:
    import pychecker.checker
    import Logging
    Logging.HIDE_DEBUG=Logging.KWS

    

todir=scripting.get_main_dir()

#todir=os.path.dirname(__file__)
#todir=os.path.join(os.getcwd(),todir)
if todir:
    os.chdir(todir)
        

import csv

import Configuration
#sys.path.insert(0,"C:\\Mingw\\lib")
# This will fix the VTK paths using either values from the
# configuration file, or sensible defaults

conffile = os.path.join(scripting.get_config_dir(),"BioImageXD.ini")
cfg=Configuration.Configuration(conffile)

# We need to import VTK here so that it is imported before wxpython.
# if wxpython gets imported before vtk, the vtkExtTIFFReader will not read the olympus files
# DO NOT ask me why that is!
import vtk

import Logging
import scripting


import glob

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
        iconpath = scripting.get_icon_dir()
        bmp = wx.Image(os.path.join(iconpath,"splash2.jpg"),wx.BITMAP_TYPE_JPEG).ConvertToBitmap()

        splash=wx.SplashScreen(bmp,
                                 wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                                 3000, None, -1)
        splash.Show()
         # Import Psyco if available
        try:
            pass
            #import psyco

            #psyco.log()
            #psyco.profile()
            #psyco.full()
        except ImportError:
            pass        
        provider = wx.SimpleHelpProvider()
        wx.HelpProvider_Set(provider)
        
        self.mainwin=GUI.MainWindow.MainWindow(None,-1,self,splash)
        self.mainwin.config=wx.Config("BioImageXD", style=wx.CONFIG_USE_LOCAL_FILE)        
        
        scripting.app = self
        scripting.mainwin = self.mainwin
        
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
    if "py2exe" in sys.argv or "py2app" in sys.argv:
        from build_app import *
        build()
    else:


        # If the main application is frozen, then we redirect logging
        # to  a log file
        if "tofile" in sys.argv or scripting.main_is_frozen():
            import time
            logfile="output_%s.log"%(time.strftime("%d.%m.%y@:%H:%M"))
            logdir=get_log_dir()
            if not os.path.exists(logdir):
                os.mkdir(logdir)
	    logfile=os.path.join(logdir,logfile)
            f1=open(logfile,"w")
	    logfile2=os.path.join(logdir,"latest.log")
	    f2=open(logfile2,"w")
	    f = Logging.Tee(f1,f2)
	    import atexit
	    atexit.register(f.flush)
            sys.stdout = f 
            sys.stderr = f
            Logging.outfile = f
            Logging.enableFull()
        
        if "profint" in sys.argv:
            import pstats
            p = pstats.Stats('prof.log')
            p.sort_stats('time', 'cum').print_stats(.5, 'init')
            sys.exit(0)
        
        app=LSMApplication(0)    
        if "profile" in sys.argv and profile:
            profile.run('app.run()', 'prof.log')
        else:
            app.run()
