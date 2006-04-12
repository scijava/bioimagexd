# -*- coding: iso-8859-1 -*-

"""
 Unit: scripting
 Project: BioImageXD
 Created: 13.02.2006, KP
 Description:

 A module containing various shortcuts for ease of scripting the app
 
 Copyright (C) 2006  BioImageXD Project
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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import sys,os
import imp
import platform

record = 0

app = None
mainwin = None

def main_is_frozen():
   return (hasattr(sys, "frozen") or # new py2exe
           hasattr(sys, "importers") # old py2exe
           or imp.is_frozen("__main__")) # tools/freeze



def get_main_dir():
    if "checker.py" in sys.argv[0]:
        return "."
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])
    
   
def get_log_dir():
    if platform.system()=="Darwin":
        return os.path.expanduser("~/Library/Logs/BioImageXD")
    else:
        return "logs"
    
def get_config_dir():
    if platform.system()=="Darwin":
        return os.path.expanduser("~/Library/Preferences")
    else:
        return get_main_dir() 
        
def get_icon_dir():
    if platform.system()=="Darwin" and main_is_frozen():
        dir=os.environ['RESOURCEPATH']
        path=os.path.join(dir,"Icons")
        return path
    else:
        return os.path.join(".","Icons")
        
        
def get_module_dir():
    if platform.system()=="Darwin" and main_is_frozen():
        dir=os.environ['RESOURCEPATH']
        path=os.path.join(dir,"Modules")
        return path
    else:
        return "Modules"
