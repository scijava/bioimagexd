# -*- coding: iso-8859-1 -*-

"""
 Unit: Animator
 Project: BioImageXD
 Created: 19.06.2005, KP
 Description:

 An animator mode for Visualizer
          
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
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


from Visualizer.VisualizationMode import VisualizationMode
from GUI import MenuManager

def getName():return "animator"
def getClass():return AnimatorMode
def getConfigPanel(): return None
def getImmediateRendering(): return False
def getRenderingDelay(): return 10000
def showZoomToolbar(): return False


from GUI import Urmas
import Logging
import wx
        
class AnimatorMode(VisualizationMode):
    def __init__(self,parent,visualizer):
        """
        Method: __init__
        Created: 24.05.2005, KP
        Description: Initialization
        """
        VisualizationMode.__init__(self,parent,visualizer)
        self.parent=parent
        self.menuManager=visualizer.menuManager
        self.visualizer=visualizer
        
        self.dataUnit=None
        
        self.urmaswin=None
        self.doLockSliderPanel=0
        
    def layoutTwice(self):
        """
        Method: layoutTwice()
        Created: 20.12.2005, KP
        Description: Method that is queried for whether the mode needs to
                     be laid out twice
        """
        return True
        #return False
        
    def closeOnReload(self):
        return True
        
    def showSideBar(self):
        """
        Method: showSideBar()
        Created: 24.05.2005, KP
        Description: Method that is queried to determine whether
                     to show the sidebar
        """
        return False
        
    def relayout(self):
        """
        Method: relayout()
        Created: 07.08.2005, KP
        Description: Method called when the size of the window changes
        """    
        #self.urmaswin.Layout()
        #wx.CallAfter(self.urmaswin.Layout)
        #wx.CallAfter(self.visualizer.OnSize)
        
        

        
    def activate(self,sidebarwin):
        """
        Method: activate()
        Created: 24.05.2005, KP
        Description: Set the mode of visualization
        """
        self.sidebarWin=sidebarwin
        Logging.info("Disabling tasks in menu",kw="visualizer")
        self.menuManager.mainToolbar.EnableTool(MenuManager.ID_ADJUST,0)
        self.menuManager.mainToolbar.EnableTool(MenuManager.ID_RESTORE,0)
        self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLOCALIZATION,0)
        self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLORMERGING,0)
        self.visualizer.sliderPanel.Show(0)
        if not self.urmaswin:
            # Ugly hack
            self.urmaswin=Urmas.UrmasWindow(self.parent,self.visualizer.menuManager,self.visualizer.mainwin.taskWin,self.visualizer)
        else:
            self.urmaswin.enableRendering(1)
            self.urmaswin.Show()
            wx.CallAfter(self.urmaswin.updateRenderWindow)
            
        return self.urmaswin
        
    def Render(self):
        """
        Method: Render()
        Created: 24.05.2005, KP
        Description: Update the rendering
        """      
        pass        
        
    def setBackground(self,r,g,b):
        """
        Method: setBackground(r,g,b)
        Created: 24.05.2005, KP
        Description: Set the background color
        """        
        pass
        
    def updateRendering(self):
        """
        Method: updateRendering
        Created: 26.05.2005, KP
        Description: Update the rendering
        """      
        pass
        
    def lockSliderPanel(self,flag):
        """
        Method: lockSliderPanel
        Created: 30.01.2006, KP
        Description: Set a flag indicating whether the sliderpanel 
                     should be switched back to normal when switching
                     from animator
        """     
        self.doLockSliderPanel=flag
        
    def deactivate(self,newmode=None):
        """
        Method: deactivate()
        Created: 24.05.2005, KP
        Description: Unset the mode of visualization
        """
        self.urmaswin.Show(0) 
        self.urmaswin.enableRendering(0)   
        
        if not self.doLockSliderPanel:
            self.visualizer.setCurrentSliderPanel(self.visualizer.sliderPanel)        
            self.visualizer.sliderPanel.Show(1)
        if newmode!="3d":
            self.menuManager.mainToolbar.EnableTool(MenuManager.ID_ADJUST,1)
            self.menuManager.mainToolbar.EnableTool(MenuManager.ID_RESTORE,1)
            self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLOCALIZATION,1)
            self.menuManager.mainToolbar.EnableTool(MenuManager.ID_COLORMERGING,1)        
        
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit
        Created: 25.05.2005, KP
        Description: Set the dataunit to be visualized
        """
        self.urmaswin.setDataUnit(dataUnit)
        
    def setTimepoint(self,tp):
        """
        Method: setTimepoint
        Created: 25.05.2005, KP
        Description: Set the timepoint to be visualized
        """
        pass

    def saveSnapshot(self,filename):
        """
        Method: saveSnapshot(filename)
        Created: 05.06.2005, KP
        Description: Save a snapshot of the scene
        """      
        pass
        
    def reloadMode(self):
        """
        Method: reloadMode()
        Created: 1.09.2005, KP
        Description: Method called when the user tries to reload the mode
        """    
        pass
#        self.menuManager.enable(MenuManager.ID_ADJUST)
#        self.menuManager.enable(MenuManager.ID_RESTORE)
#        self.menuManager.enable(MenuManager.ID_COLOCALIZATION)


        # safeguard

    def __del_(self):
        print "Deleting urmaswin"
        del self.urmaswin