# -*- coding: iso-8859-1 -*-

"""
 Unit: InfoWidget.py
 Project: Selli
 Created: 03.11.2004
 Creator: KP
 Description:

 A widget that displays information about channels/dataset series selected in 
 the tree view.

 Modified 03.11.2004 KP - Created the class
          15.12.2004 JV - Fixed: handles ColorCombinationDataUnit properly

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"
import os.path

from Logging import *

from CombinedDataUnit import *


class InfoWidget(wxPanel):
    """
    --------------------------------------------------------------
    Class: InfoWidget
    Created: 03.11.2004
    Creator: KP
    Description: A class for displaying information about selected datasets
                 of given type
    -------------------------------------------------------------
    """
    def __init__(self,master):
        """
        --------------------------------------------------------------
        Method: __init__
        Created: 03.11.2004
        Creator: KP
        Description: Initialization for the Info node
        -------------------------------------------------------------
        """
        wxPanel.__init__(self,master)
        
