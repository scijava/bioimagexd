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

def getpath(path):
    return os.path.normpath(os.path.join(os.getcwd(),reduce(os.path.join,path)))

def fixpaths():    
    sys.path.insert(0,getpath(["Modules"]))
    
    removethese=[]
    for i in sys.path:
        if i.find("vtk_python")!=-1:
            removethese.append(i)
        if i.find("VTK")!=-1:
            removethese.append(i)
    for i in removethese:
        sys.path.remove(i)
        print "Removed old vtk %s from search path"%i

    sys.path.append(getpath(["LSM"]))
    sys.path.append(getpath(["GUI"]))
    vtkdir=getpath(["Libraries","VTK"])
    sys.path.append(getpath(["Libraries"]))
    

    sys.path.append("/usr/lib/python2.4/config")
    if os.path.isdir(vtkdir):
        print "Added ..\\VTK as VTK"
        sys.path.insert(0,getpath([vtkdir,"bin"]))
        sys.path.insert(0,getpath([vtkdir,"Wrapping","Python"]))
    else:
        sys.path.insert(0,"C:\\MYTEMP\\VTK\\BIN")
        sys.path.insert(0,"C:\\MYTEMP\\VTK\\Wrapping\\Python")
        print "Added C:\\Mytemp\VTK as VTK"
    print sys.path

fixpaths()
import wx

import GUI


class LSMApplication(wx.App):
    """
    Class: LSMApplication
    Created: 03.11.2004, KP
    Description: Encapsulates the wxPython initialization and mainwindow creation
    """

        
    def OnInit(self):
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
    # We add the Module directory to search path so that
    # all classes have access to them despite their location in
    # the filesystem hierarchy


    app=LSMApplication(False)

    app.run()



