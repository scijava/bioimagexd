# -*- coding: iso-8859-1 -*-

"""
 Unit: TimepointSelection.py
 Project: Selli 2
 Created: 03.02.2005
 Creator: KP
 Description:

 This is a base widget for all operations that need to let the user select
 the timepoints that are operated upon. Used by rendering and various 
 operation windows 
 
 Modified: 03.02.2005 KP - Created the class from RenderingManager

 Selli 2 includes the following persons:
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 
 Copyright (c) 2005 Selli 2 Project.
"""

__author__ = "Selli 2 Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

#from wx.Python.wx. import *
import wx
import os.path

from PreviewFrame import *
import sys
import RenderingInterface
import Logging
import Dialogs

import wx.lib.scrolledpanel as scrolled
import wx.lib.buttons as buttons
import vtk



class TimepointSelectionPanel(wx.Panel):
    """
    Class: TimepointSelectionPanel
    Created: 10.2.2005
    Creator: KP
    Description: A class containing the basic timepoint selection functionality
                 in a panel. This is a class separete from TimepointSelection
                 so that this can be also embedded in any other dialog.
    """
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.mainsizer=wx.GridBagSizer(10,10)
        self.configFrame=None

        self.timepointButtonSizer=wx.GridBagSizer()
        self.buttonFrame = scrolled.ScrolledPanel(self, -1,style=wx.RAISED_BORDER,size=(640,100))
        self.buttonFrame.SetSizer(self.timepointButtonSizer)
        self.buttonFrame.SetAutoLayout(True)
        self.buttonFrame.SetupScrolling()
        self.timepointLbl=wx.StaticText(self,-1,"Select timepoints")
        
        self.mainsizer.Add(self.timepointLbl,(0,0))        
        self.mainsizer.Add(self.buttonFrame,(1,0),span=(1,2),flag=wx.EXPAND|wx.ALL)
        
        
        self.buttonList=[]
        self.selectedFrames={}
        self.createConfigFrame()
    
        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.mainsizer.SetSizeHints(self)
        
    def getSelectedTimepoints(self):
        timepoints=[]
        for i in self.selectedFrames.keys():
            print "%d selected: %s"%(i,(self.selectedFrames[i]==1))
            if self.selectedFrames[i]:
                timepoints.append(i)
        return timepoints
        
    def createConfigFrame(self):
        """
        Method: createConfigFrame(self)
        Created: 17.11.2004
        Creator: KP
        Description: A callback that is used to close this window
        """
        self.configFrame=wx.Panel(self)
        self.mainsizer.Add(self.configFrame,(2,0),span=(1,2),flag=wx.EXPAND|wx.ALL)
        
        self.configSizer=wx.GridBagSizer()

        box=wx.BoxSizer(wx.HORIZONTAL)
        self.nthLbl=wx.StaticText(self.configFrame,-1,"Select every")
        box.Add(self.nthLbl)
        self.configSizer.Add(box,(0,0))

        self.nthEntry=wx.TextCtrl(self.configFrame,-1,"1",size=(50,-1))
        box.Add(self.nthEntry)
        self.nthEntry.Bind(EVT_TEXT,self.updateSelection)
        
        self.nthLbl2=wx.StaticText(self.configFrame,-1,"Nth timepoints")
        box.Add(self.nthLbl2)

                
        self.configFrame.SetSizer(self.configSizer)
        self.configFrame.SetAutoLayout(True)            
        self.configSizer.Fit(self.configFrame)
        
    def updateSelection(self,event=None):
        """
        Method: updateSelection(event)
        Created: 17.11.2004
        Creator: KP
        Description: A callback that is used to select every nth button, where
                     N is the value of the nthEntry entry
        """
        try:
            n=int(self.nthEntry.GetValue())
        except:
            n=1
        
        if not n:
            for i in range(len(self.buttonList)):
                self.selectedFrames[i]=0
                self.setButtonState(self.buttonList[i],0)
            return
        for i in range(len(self.buttonList)):
            btn=self.buttonList[i]
            if not (i)%n:
                self.selectedFrames[i]=1
                self.setButtonState(btn,1)
            else:
                self.selectedFrames[i]=0
                self.setButtonState(btn,0)
        
    def createButtons(self):
        """
        Method: createButtons()
        Created: 10.11.2004
        Creator: KP
        Description: A method that creates as many buttons as the dataunit
                 has timepoints, so that each button represent one time point
        """
        nrow=0
        ncol=0
        for i in range(self.dataUnit.getLength()):
            if ncol==30:
                nrow+=1
                ncol=0
            btn=buttons.GenButton(self.buttonFrame,-1,"%d"%i,size=(24,24))
            btn.SetFont(wx.Font(7,wx.SWISS,wx.NORMAL,wx.NORMAL))
            btn.Bind(EVT_BUTTON,lambda e,btn=btn,i=i: self.buttonClickedCallback(btn,i))
            btn.origColor=btn.GetBackgroundColour()
            btn.origFgColor=btn.GetForegroundColour()
            self.buttonList.append(btn)
            self.timepointButtonSizer.Add(btn,(nrow,ncol))
            ncol=ncol+1
        self.timepointButtonSizer.Fit(self.buttonFrame)
        self.mainsizer.Fit(self)

    def buttonClickedCallback(self,button,number):
        """
        Method: buttonClickedCallback(button,number)
        Created: 10.11.2004
        Creator: KP
        Description: A method called when user clicks a button representing 
                     a time point
        """
        if not self.selectedFrames.has_key(number):
            self.selectedFrames[number]=0

        if self.selectedFrames[number]:
            self.selectedFrames[number]=0
            self.setButtonState(button,0)
        else:
            self.selectedFrames[number]=1
            self.setButtonState(button,1)

    def setButtonState(self,button,flag):
        """
        Method: setButtonState(button,flag)
        Created: 09.02.2005
        Creator: KP
        Description: A method to set the state of a button to selected/deselected
        Paremeters:
                button  The button to configure
                flag    Should the button be selected or deselected
        """
        if not flag:
            button.SetBackgroundColour(button.origColor)
            button.SetForegroundColour(button.origFgColor)
        else:
            button.SetBackgroundColour("#333333")
            button.SetForegroundColour((255,255,255)) 
        
            
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(dataUnit)
        Created: 10.11.2004
        Creator: KP
        Description: A method to set the data unit we use to do the
                     actual rendering
        Paremeters:
            dataUnit    The data unit we use
        """
        self.dataUnit=dataUnit
        self.createButtons()
        self.updateSelection()
        data=self.dataUnit.getTimePoint(0)
        self.mainsizer.Fit(self)
        
        

class TimepointSelection(wx.Dialog):
    """
    Class: TimepointSelection
    Created: 10.11.2004
    Creator: KP
    Description: A base class for creating windows where the user can select        
                 the timepoints that should be operated upon.
    """
    def __init__(self,parent):
        """
        Method: __init__
        Created: 10.11.2004
        Creator: KP
        Description: Initialization
        """
        wx.Dialog.__init__(self,parent,-1,"Timepoint selection",style=wx.CAPTION|wx.STAY_ON_TOP|wx.CLOSE_BOX|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.RESIZE_BORDER,size=(640,480))
        self.parent=parent
        self.Bind(EVT_CLOSE,self.closeWindowCallback)
        self.mainsizer=wx.GridBagSizer(10,10)

        self.rendering=0
        self.SetTitle("Timepoint Selection")
        ico=reduce(os.path.join,["..","Icons","Selli.ico"])
        self.icon = wx.Icon(ico,wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.panel=TimepointSelectionPanel(self)
        
        self.mainsizer.Add(self.panel,(0,0),flag=wx.EXPAND|wx.ALL)
        
        self.createButtonBox()
        
        self.status=wx.ID_OK

        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Fit(self)
        self.mainsizer.SetSizeHints(self)
        
    def setLabel(self,lbl):
        self.panel.timepointLbl.SetLabel(lbl)
        
    def createButtonBox(self):
        """
        Method: createButtonBox()
        Created: 31.1.2005
        Creator: KP
        Description: Creates the standard control buttons
        """
        self.buttonsSizer=wx.BoxSizer(wx.HORIZONTAL)
        
        self.buttonsSizer1=wx.BoxSizer(wx.HORIZONTAL)
        
        self.actionBtn=wx.Button(self,-1,"Ok")
        #self.actionBtn.Bind(EVT_BUTTON,self.doRendering)
        self.buttonsSizer1.Add(self.actionBtn,flag=wx.ALIGN_LEFT)

        self.closeBtn=wx.Button(self,-1,"Close")
        self.closeBtn.Bind(EVT_BUTTON,self.closeWindowCallback)
        self.buttonsSizer1.Add(self.closeBtn,flag=wx.ALIGN_LEFT)
        self.buttonsSizer1.AddSizer((100,-1))
        self.buttonsSizer.Add(self.buttonsSizer1,flag=wx.ALIGN_LEFT)
        self.staticLine=wx.StaticLine(self)
        self.mainsizer.Add(self.staticLine,(3,0),span=(1,2),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.mainsizer.Add(self.buttonsSizer,(4,0),span=(1,2))

    def getSelectedTimepoints(self):
        return self.panel.getSelectedTimepoints()


    def closeWindowCallback(self,event):
        """
        Method: closeWindowCallback
        Created: 10.11.2004
        Creator: KP
        Description: A callback that is used to close this window
        """
        self.EndModal(self.status)

        
            
    def setDataUnit(self,dataUnit):
        """
        Method: setDataUnit(dataUnit)
        Created: 10.11.2004
        Creator: KP
        Description: A method to set the data unit we use to do the
                     actual rendering
        Paremeters:
            dataUnit    The data unit we use
        """
        self.panel.setDataUnit(dataUnit)
