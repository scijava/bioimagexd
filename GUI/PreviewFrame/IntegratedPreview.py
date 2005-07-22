# -*- coding: iso-8859-1 -*-

"""
 Unit: IntegratedPreview
 Project: BioImageXD
 Created: 03.04.2005, KP
 Description:

 A widget that can be used to Preview any operations done by a subclass of Module.
 The type of preview can be selected and depends on the type of data that is input.
 
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
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import os.path

from PreviewFrame import *
import wx
from DataUnit import CombinedDataUnit

import ColorTransferEditor

import Modules
import Logging
import vtk
import wx.lib.scrolledpanel as scrolled

class IntegratedPreview(PreviewFrame):
    """
    Class: IntegratedPreview
    Created: 03.04.2005, KP
    Description: A widget that previews data output by wide variety
                 of processing modules
    """
    def __init__(self,master,parentwin=None,**kws):
        PreviewFrame.__init__(self,master,parentwin,**kws)
                
        

        

        
