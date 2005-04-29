# -*- coding: iso-8859-1 -*-

"""
 Unit: VTKScrollPanel.py
 Project: BioImageXD
 Created: 19.03.2005, KP
 Description:

 A panel that has a wxVTKRenderWindow and depending on a defined maximum
 size and the given current size, displays scrollbars.

 Modified 19.03.2005 KP - Created the class
          
 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 
 Copyright (c) 2005 BioImageXD
"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.9 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx

from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from vtk.wx.wxVTKRenderWindow import wxVTKRenderWindow

class VTKScrollPanel(wx.Panel):
    """
    Class: VTKScrollPanel
    Created: 19.03.2005, KP
    Description: A panel that contains a wxVTKRenderWindow and shows
                 scrollbars for scrolling the panel
    """
    def __init__(self,parent,id=-1,size=(512,512),scroll=1,**kws):
        """
        Method: __init__(parent)
        Created: 19.03.2005, KP
        Description: Initialization
        """    
        self.scroll=1
        self.mapper=None
        self.xdiff,self.ydiff=0,0
        
        wx.Panel.__init__(self,parent,-1,**kws)
        if kws.has_key("scrollbars"):
            self.scroll=kws["scrollbars"]
            
        self.rendersizer=wx.GridBagSizer()
        mysize=(size[0],size[1])
        self.renderpanel = wx.Panel(self,-1,style=wx.SUNKEN_BORDER,size=mysize)
        self.wxrenwin = wxVTKRenderWindow(self.renderpanel,-1,size=size)
        self.setMaximumSize(*size)
        self.renwin=self.wxrenwin.GetRenderWindow()
        
        # Alias some methods 
        self.GetRenderWindow=self.wxrenwin.GetRenderWindow
        
        self.horizontalScroll = wx.ScrollBar(self,-1,style=wx.SB_HORIZONTAL)
        self.verticalScroll = wx.ScrollBar(self,-1,style=wx.SB_VERTICAL)
        self.horizontalScroll.Show(0)
        self.verticalScroll.Show(0)        
        self.rendersizer.Add(self.renderpanel,(0,0),flag=wx.EXPAND|wx.ALL)
        self.rendersizer.Add(self.verticalScroll,(0,1),flag=wx.EXPAND|wx.TOP|wx.BOTTOM)
        self.rendersizer.Add(self.horizontalScroll,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)

        self.SetSizer(self.rendersizer)
        self.SetAutoLayout(1)
        self.rendersizer.Fit(self)
        
    
    def getwxVTKRenderWindow(self):
        """
        Method: getwxVTKRenderWindow()
        Created: 19.03.2005, KP
        Description: Returns the wxVTKRenderWindow
        """    
        return self.wxrenwin
        
    def setMaximumSize(self,x,y):
        """
        Method: setMaximumSize(x,y)
        Created: 19.03.2005, KP
        Description: Sets the maximum size for this widget
        """    
        self.maxX,self.maxY=x,y
    
    def setMapper(self,mapper):
        """
        Method: setMapper(mapper)
        Created: 19.03.2005, KP
        Description: Sets the mapper that the scrolling should control
        """    
        self.mapper=mapper
       
    def scrollTo(self,xdiff,ydiff):
        """
        Method: scrollTo(xdiff,ydiff)
        Created: 19.03.2005, KP
        Description: Scrolls the preview to given position
        """
        self.mapper.UseCustomExtentsOn()
        
        xend=xdiff+self.width
        yend=self.height-ydiff
        ystart=self.height-ydiff-self.maxY
    
        #if xend>self.xdim:
        #    xend=self.xdim
        #if yend>self.ydim:
        #    yend=self.ydim
        if xdiff<0:
            xdiff=0
        if ydiff<=0:
            ydiff=0

        print "Viewing from %d,%d to %d,%d"%(xdiff,ydiff,xend,yend)
        self.mapper.SetCustomDisplayExtents([xdiff,xend,ystart,yend])
        self.renwin.Render()
        #self.updatePreview(0)
        
    def getScrolledXY(self,x,y):
        """
        Method: getScrolledXY(x,y)
        Created: 19.03.2005, KP
        Description: Returns the x and y coordinates moved by the 
                     x and y scroll offset
        """
        if self.ydiff==0:
            return self.xdiff+x,self.height-y
        else:
            return self.xdiff+x,self.height-(self.ydiff+y)
       
    def scrollRenderWidget(self,event):
        """
        Method: scrollRenderWidget(self,event)
        Created: 19.03.2005, KP
        Description: Scrolls the preview according to the mouse events received
        """
        if not self.mapper:
            return
        
        if event.GetOrientation()==wx.HORIZONTAL:
            self.xdiff=event.GetPosition()            
        else:
            self.ydiff=event.GetPosition()
        self.scrollTo(self.xdiff,self.ydiff)
    
    def resetScroll(self):
        """
        Method: resetScroll()
        Created: 19.03.2005, KP
        Description: Sets the scrollbars to their initial values
        """    
        self.xdiff=0
        self.ydiff=0
        self.mapper.UseCustomExtentsOff()
        self.horizontalScroll.SetThumbPosition(0)
        self.verticalScroll.SetThumbPosition(0)
        
    def setScrollbars(self,xdim,ydim):
        """
        Method: setScrollbars(x,y)
        Created: 19.03.2005
        Creator: KP
        Description: Configures scroll bar behavior depending on the
                     size of the dataset, which is given as parameters.
        """
        x,y=xdim,ydim
        self.width,self.height=xdim,ydim
        print "x,y=",x,y,"maxX=",self.maxX
        if x>self.maxX:
            x=self.maxX
            if self.scroll:
                print "Have to use horizontal scroll"
                self.horizontalScroll.Show(1)
                self.horizontalScroll.SetScrollbar(0,x,xdim,1)
                self.horizontalScroll.Bind(wx.EVT_SCROLL,self.scrollRenderWidget)
                self.scrollTo(0,0)
        else:
            self.resetScroll()
            self.horizontalScroll.Show(0)
        if y>self.maxY:
            y=self.maxY
            if self.scroll:
                print "Have to use vertical scroll"
                self.verticalScroll.Show(1)
                self.verticalScroll.SetScrollbar(0,y,ydim,1)
                self.verticalScroll.Bind(wx.EVT_SCROLL,self.scrollRenderWidget)    
                self.scrollTo(0,0)
        else:
            self.resetScroll()
            self.verticalScroll.Show(0)

