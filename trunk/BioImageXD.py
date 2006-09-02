#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: BioImageXD
 Project: BioImageXD
 Created: 01.11.2004, KP
 Description:

 BioImageXD main program

 Copyright (C) 2005, 2006  BioImageXD Project
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
import scripting as bxd
import getopt

try:
    import profile
except:
    profile=None

if "check" in sys.argv:
    import pychecker.checker
    import Logging
    Logging.HIDE_DEBUG=Logging.KWS

    

todir=bxd.get_main_dir()

#todir=os.path.dirname(__file__)
#todir=os.path.join(os.getcwd(),todir)
if todir:
    os.chdir(todir)
        

# Insert the path for the ITK libraries
if not todir:
    todir=os.getcwd()
itklibdir=os.path.join(todir,os.path.join("ITK-pkg","lib"))
itkbindir=os.path.join(todir,os.path.join("ITK-pkg","bin"))
itkpythondir=os.path.join(todir,os.path.join("ITK-pkg","Python"))
sys.path.insert(0,itklibdir)
sys.path.insert(0,itkbindir)
sys.path.insert(0,itkpythondir)
PATH=os.getenv("PATH")
PATH=PATH+os.path.pathsep+itklibdir+os.path.pathsep+itkbindir+os.path.pathsep+itkpythondir
os.putenv("PATH",PATH)
print PATH
print itklibdir,itkbindir,itkpythondir
    
        
import csv

import Configuration
# This will fix the VTK paths using either values from the
# configuration file, or sensible defaults

conffile = os.path.join(bxd.get_config_dir(),"BioImageXD.ini")
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
    Created: 03.11.2004, KP
    Description: Encapsulates the wxPython initialization and mainwindow creation
    """

    def OnInit(self):
        """
        Created: 10.1.2005, KP
        Description: Create the application's main window
        """
        iconpath = bxd.get_icon_dir()
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
        
        bxd.app = self
        bxd.mainWindow = self.mainwin
        
        self.mainwin.Show(True)
        self.SetTopWindow(self.mainwin)
        
    
        return True

    def run(self, files, scriptfile):
        """
        Created: 03.11.2004, KP
        Description: Run the wxPython main loop
        """
        if files:
            self.mainwin.loadFiles(files)
        
        if scriptfile:
            self.mainwin.loadScript(scriptfile)
        self.MainLoop()


def usage():
    print "Usage: BioImageXD [-h|--help] | [-x script.bxs|--execute=script.bxs] [-i file|--input=file] [-d directory|--directory=directory]"
    print ""
    print "-x | --execute\tExecute the given script file"
    print "-i | --input\tLoad the given file as default input"
    print "-d | --directory\tLoad all files from given directory"
    print "-t | --tofile\tLog all messages to a log file"
    print "-l | --logfile\tLog all messages to given file"
    print "-p | --profile\tProfile the execution of the program"
    print "-P | --interpret\tInterpret the results of the profiling"
    
    sys.exit(2)
    

if __name__=='__main__':
    if "py2exe" in sys.argv or "py2app" in sys.argv:
        from build_app import *
        build()
    else:
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'hx:i:d:tpPl', ["help","execute=","input=","directory=","tofile","profile","interpret","logfile"])
        except getopt.GetoptError:
            usage()
        
        toFile = 0
        doProfile = 0
        doInterpret=0
        scriptFile = ""
        logfile=""
        logdir=""
        dataFiles=[]
        for opt,arg in opts:
            if opt in ["-h","--help"]:
                usage()
            elif opt in ["-x","--execute"]:
                scriptFile = arg
            elif opt in ["-d","--directory"]:
                dataFiles = glob.glob(os.path.join(arg,"*"))
            elif opt in ["-i","--input"]:
                dataFiles = [arg]
            elif opt in ["-t","--tofile"]:
                toFile = 1
            elif opt in ["-p","--profile"]:
                doProfile = 1
            elif opt in ["-P","--interpret"]:
                doInterpret=1
            elif opt in ["-l","--logfile"]:
                logfile=arg
        # If the main application is frozen, then we redirect logging
        # to  a log file
        if toFile or bxd.main_is_frozen():
            import time
            if not logfile:
                logfile=time.strftime("output_%d.%m.%y@%H%M.log")
                
                logdir=bxd.get_log_dir()
                if not os.path.exists(logdir):
                    os.mkdir(logdir)
                logfile=os.path.join(logdir,logfile)
            f1=open(logfile,"w")
            if logdir:
                logfile2=os.path.join(logdir,"latest.log")
                f2=open(logfile2,"w")
                f = Logging.Tee(f1,f2)
            import atexit
            atexit.register(f.flush)
            sys.stdout = f 
            sys.stderr = f
            Logging.outfile = f
            Logging.enableFull()
        
        if doInterpret:
            import pstats
            p = pstats.Stats('prof.log')
            p.sort_stats('time', 'cum').print_stats(.5, 'init')
            sys.exit(0)
        
        app=LSMApplication(0)    
        
        if doProfile and profile:
            profile.run('app.run(dataFiles, scriptFile)', 'prof.log')
        else:
            app.run(dataFiles, scriptFile)
