# -*- coding: iso-8859-1 -*-
"""
 Unit: TransferWidget.py
 Project: Selli
 Created: 30.10.2004
 Creator: KP
 Description:

 A widget used to view and modify an intensity transfer function. The widget
 draws the graph of the function and allows the user to modify six points that
 affect the function.

 Modified: 17.11.2004 KP - Added comments
           23.11.2004 KP - Added Gamma
           24.11.2004 KP - Moved all the logic from TransferWidget to 
                           IntensityTransferFunction
           1.12.2004 KP, JM - Added a checkbox for switching between "free" and
                              "limited" mode, made
                              the controls dis/appear accordingly

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.36 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

from wxPython.wx import *
import wx
import os.path
import sys


if __name__=='__main__':
    import sys
    sys.path.append(os.path.normpath(os.path.join(os.getcwd(),"..")))

from IntensityTransferFunction import *

class PaintPanel(wxPanel):
    def __init__(self,parent):
        self.maxx=255
        self.maxy=255
        self.scale=1
        self.xoffset=16
        self.yoffset=22
        w=self.xoffset+self.maxx/self.scale
        h=self.yoffset+self.maxy/self.scale
        wxPanel.__init__(self,parent,-1,size=(w+15,h+15))
        self.buffer=wxEmptyBitmap(w+15,h+15)
        dc = wxBufferedDC(None,self.buffer)
        dc.SetBackground(wxBrush("BLACK"))
        dc.Clear()
        self.dc=dc
        self.Bind(wx.EVT_PAINT,self.onPaint)
      
    def onPaint(self,event):
        dc=wx.BufferedPaintDC(self,self.buffer)                
        
    def createLine(self,x1,y1,x2,y2,color="WHITE",brush=None,**kws):
        """
        --------------------------------------------------------------
        Method: createLine(x1,y1,x2,y2)
        Created: 30.10.2004
        Creator: KP
        Description: Draws a line from (x1,y1) to (x2,y2). The method
                     takes into account the scale factor
        -------------------------------------------------------------
        """
        if brush:
            self.dc.SetBrush(brush)
        
        self.dc.SetPen(wxPen(color))
        # (x1,y1) and (x2,y2) are in coordinates where
        # origo is the lower left corner

        x12=x1+self.xoffset
        y12=self.maxy-y1+self.yoffset
        y22=self.maxy-y2+self.yoffset
        x22=x2+self.xoffset

        arr=None
        self.dc.DrawLine(x12/self.scale,y12/self.scale,
        x22/self.scale,y22/self.scale)
        if kws.has_key("arrow"):
            if kws["arrow"]=="HORIZONTAL":
                lst=[(x22/self.scale-3,y22/self.scale-3),(x22/self.scale,y22/self.scale),(x22/self.scale-3,y22/self.scale+3)]            
            elif kws["arrow"]=="VERTICAL":
                lst=[(x22/self.scale-3,y22/self.scale+3),(x22/self.scale,y22/self.scale),(x22/self.scale+3,y22/self.scale+3)]            
            
            self.dc.DrawPolygon(lst)
            

    def createOval(self,x,y,r,color="GREY"):
        """
        --------------------------------------------------------------
        Method: createOval(x,y,radius)
        Created: 30.10.2004
        Creator: KP
        Description: Draws an oval at point (x,y) with given radius
        -------------------------------------------------------------
        """
        self.dc.SetBrush(wxBrush(color,wxSOLID))
        self.dc.SetPen(wxPen(color))        
        y=self.maxy-y+self.yoffset
        ox=x/self.scale
        ox+=self.xoffset
        self.dc.DrawCircle(ox,y/self.scale,r)

    def createText(self,x,y,text,color="WHITE",**kws):
        """
        --------------------------------------------------------------
        Method: createText(x,y,text,font="Arial 6")
        Created: 30.10.2004
        Creator: KP
        Description: Draws a text at point (x,y) using the given font
        -------------------------------------------------------------
        """
        self.dc.SetTextForeground(color)
        self.dc.SetFont(wx.Font(8,wxSWISS,wxNORMAL,wxNORMAL))
        
        useoffset=1
        if kws.has_key("use_offset"):
            useoffset=kws["use_offset"]
        y=self.maxy-y
        if useoffset:
            y+=self.yoffset
        ox=x/self.scale
        if useoffset:
            ox+=self.xoffset
        print "Drawing %s at %d,%d"%(text,ox,y/self.scale)
        self.dc.DrawText(text,ox,y/self.scale)
        

    def paintTransferFunction(self,iTF):
        """
        --------------------------------------------------------------
        Method: paintTransferFunction()
        Created: 30.10.2004
        Creator: KP
        Description: Paints the graph of the function specified by the six points
        -------------------------------------------------------------
        """
        print "Painting..."
        self.dc.Clear()
        self.dc.BeginDrawing()
        # get the slope start and end points
        TF=iTF.getAsList()
        x0,y0=0,0
        
        self.createLine(0,0,0,260,arrow="VERTICAL")
        self.createLine(0,0,260,0,arrow="HORIZONTAL")

        for i in range(32,255,32):
            # Color gray and stipple with gray50
            self.createLine(i,0,i,255,'GREY',wxLIGHT_GREY_BRUSH)
            self.createLine(0,i,255,i,'GREY',wxLIGHT_GREY_BRUSH)

        for x1 in range(0,256):
            y1=TF[x1]
            # We cheat a bit here to get the line from point 
            # (maxthreshold,maxvalue) to (maxthreshold+1,0) to be straight
            if y1==0:
                x1-=1
            l=self.createLine(x0,y0,x1,y1,'#00ff00')
            x0,y0=x1,y1

        x,y=iTF.refpoint
        self.createOval(x,y,2)
        
        if 1 and iTF.gammaPoints:
            [x0,y0],[x1,y1]=iTF.gammaPoints
            self.createOval(x0,y0,2,"GREEN")
            self.createOval(x1,y1,2,"GREEN")

        textcol="GREEN"
        self.createText(0,-5,"0",textcol)
        self.createText(127,-5,"127",textcol)
        self.createText(255,-5,"255",textcol)

        self.createText(-10,127,"127",textcol)
        self.createText(-10,255,"255",textcol)
        self.dc.EndDrawing()
        
        

class IntensityTransferEditor(wxPanel):
    """
    Class: TransferWidget
    Created: 30.10.2004
    Creator: KP
    Description: A widget used to view and modify an intensity transfer function
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__
        Created: 30.10.2004
        Creator: KP
        Description: Initialization
        """
        self.parent=parent
        wxPanel.__init__(self,parent,-1)

        self.iTF=IntensityTransferFunction()
        
        self.mainsizer=wxBoxSizer(wxVERTICAL)

        self.canvasBox=wxBoxSizer(wxHORIZONTAL)
        self.contrastBox=wxBoxSizer(wxVERTICAL)
        self.gammaBox=wxBoxSizer(wxHORIZONTAL)
        self.brightnessBox=wxBoxSizer(wxHORIZONTAL)

        print "Creating sliders..."
        self.contrastLbl=wxStaticText(self,wxNewId(),"%.3f"%1)
        self.contrastSlider=wxSlider(self,value=0,minValue=-255,maxValue=255,size=(-1,290),
        style=wxSL_VERTICAL|wxSL_AUTOTICKS)#|wxSL_LABELS)
        self.Bind(wx.EVT_SCROLL,self.setContrast,self.contrastSlider)

        print "Creating paint panel"
        self.canvas=PaintPanel(self)
        self.canvasBox.Add(self.canvas,1,wxALL|wxEXPAND,10)
        self.canvasBox.Add(self.contrastBox)
        self.contrastBox.Add(self.contrastLbl)
        self.contrastBox.Add(self.contrastSlider,1,wxTOP|wxBOTTOM,10)
        print "Done"
        ID_CONTRASTEDIT=wxNewId()
#        self.contrastEdit=wxTextCtrl(self,ID_CONTRASTEDIT)
#        self.contrastBox.Add(self.contrastEdit)

        ID_BRIGHTNESSEDIT=wxNewId()
        self.brightnessEdit=wxTextCtrl(self,ID_BRIGHTNESSEDIT,size=(50,-1),style=wxTE_PROCESS_ENTER)
        ID_GAMMAEDIT=wxNewId()
        self.gammaEdit=wxTextCtrl(self,ID_GAMMAEDIT,size=(50,-1),style=wxTE_PROCESS_ENTER)

        self.brightnessSlider=wxSlider(self,value=0,minValue=-255,maxValue=255,size=(260,-1),
        style=wxSL_HORIZONTAL|wxSL_AUTOTICKS|wxSL_LABELS)
        self.Bind(wx.EVT_SCROLL,self.setBrightness,self.brightnessSlider)

        self.gammaSlider=wxSlider(self,value=0,minValue=-100,maxValue=100,size=(260,-1),
        style=wxSL_HORIZONTAL|wxSL_AUTOTICKS)#|wxSL_LABELS)
        self.Bind(wx.EVT_SCROLL,self.setGamma,self.gammaSlider)

    
        self.gammaBox.Add(self.gammaSlider)
        self.gammaBox.Add(self.gammaEdit,0,wxALIGN_CENTER_VERTICAL|wxALL)

        self.brightnessBox.Add(self.brightnessSlider)
        self.brightnessBox.Add(self.brightnessEdit,0,wxALIGN_CENTER_VERTICAL|wxALL)
    
#        ID_RESTORE_DEFAULTS=wxNewId()
#        self.defaultBtn=wxButton(self,ID_RESTORE_DEFAULTS,"Restore Defaults")
#        EVT_BUTTON(self,ID_RESTORE_DEFAULTS,self.restoreDefaults)

        self.minValueLbl=wxStaticText(self,wxNewId(),"Minimum value:")
        self.maxValueLbl=wxStaticText(self,wxNewId(),"Maximum value:")

        ID_MINVALUE=wxNewId()
        ID_MAXVALUE=wxNewId()
        self.minValue=wxTextCtrl(self,ID_MINVALUE,style=wxTE_PROCESS_ENTER)
        self.maxValue=wxTextCtrl(self,ID_MAXVALUE,style=wxTE_PROCESS_ENTER)
        
        fieldsizer=wxGridBagSizer(0,5)
        

        valuesizer=wxBoxSizer(wxHORIZONTAL)
        fieldsizer.Add(self.minValueLbl,(0,0))
        fieldsizer.Add(self.minValue,(0,1))
        fieldsizer.Add(self.maxValueLbl,(0,2))
        fieldsizer.Add(self.maxValue,(0,3))
        
        self.minthresholdLbl=wxStaticText(self,wxNewId(),"Minimum threshold:")
        self.maxthresholdLbl=wxStaticText(self,wxNewId(),"Maximum threshold:")

        ID_MINTHRESHOLD=wxNewId()
        ID_MAXTHRESHOLD=wxNewId()
        self.minthreshold=wxTextCtrl(self,ID_MINTHRESHOLD,style=wxTE_PROCESS_ENTER)
        self.maxthreshold=wxTextCtrl(self,ID_MAXTHRESHOLD,style=wxTE_PROCESS_ENTER)
        
        fieldsizer.Add(self.minthresholdLbl,(1,0))
        fieldsizer.Add(self.minthreshold,(1,1))
        fieldsizer.Add(self.maxthresholdLbl,(1,2))
        fieldsizer.Add(self.maxthreshold,(1,3))

        ID_DONTPROCESS=wxNewId()
        self.minProcessLbl=wxStaticText(self,wxNewId(),"Processing threshold:")
        self.minProcess=wxTextCtrl(self,ID_DONTPROCESS,style=wxTE_PROCESS_ENTER)

        fieldsizer.Add(self.minProcessLbl,(2,0))
        fieldsizer.Add(self.minProcess,(2,1))
        
        self.gammaEdit.Bind(wx.EVT_KILL_FOCUS,self.updateGamma)
        self.gammaEdit.Bind(wx.EVT_TEXT_ENTER,self.updateGamma)
#        self.contrastEdit.Bind(wx.EVT_KILL_FOCUS,self.updateContrast)
#        self.contrastEdit.Bind(wx.EVT_TEXT_ENTER,self.updateContrast)
        self.brightnessEdit.Bind(wx.EVT_KILL_FOCUS,self.updateBrightness)
        self.brightnessEdit.Bind(wx.EVT_TEXT_ENTER,self.updateBrightness)

        self.minValue.Bind(wx.EVT_KILL_FOCUS,self.updateMinimumValue)
        self.minValue.Bind(wx.EVT_TEXT_ENTER,self.updateMinimumValue)
        self.maxValue.Bind(wx.EVT_KILL_FOCUS,self.updateMaximumValue)
        self.maxValue.Bind(wx.EVT_TEXT_ENTER,self.updateMaximumValue)

        self.minthreshold.Bind(wx.EVT_KILL_FOCUS,self.updateMinimumThreshold)
        self.minthreshold.Bind(wx.EVT_TEXT_ENTER,self.updateMinimumThreshold)
        self.maxthreshold.Bind(wx.EVT_KILL_FOCUS,self.updateMaximumThreshold)
        self.maxthreshold.Bind(wx.EVT_TEXT_ENTER,self.updateMaximumThreshold)

        self.minProcess.Bind(wx.EVT_KILL_FOCUS,self.updateMinimumProcessingThreshold)
        self.minProcess.Bind(wx.EVT_TEXT_ENTER,self.updateMinimumProcessingThreshold)
        
        self.setMinimumThreshold(0)
        self.setMaximumThreshold(255)
        self.setMinimumProcessingThreshold(0)

        self.setMinimumValue(0)
        self.setMaximumValue(255)

        
        print "Adding sizers..."
        self.mainsizer.Add(self.canvasBox)

        self.gammaLbl=wxStaticText(self,-1,"Gamma")
        self.brightnessLbl=wxStaticText(self,-1,"Brightness")

        self.mainsizer.Add(self.brightnessLbl)
        self.mainsizer.Add(self.brightnessBox)
        
        self.mainsizer.Add(self.gammaLbl)
        self.mainsizer.Add(self.gammaBox)
        self.mainsizer.Add(fieldsizer)
 #       self.mainsizer.Add(self.defaultBtn)

        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.SetSizeHints(self)
        
        self.updateAll()


    def restoreDefaults(self,event):
        """
        --------------------------------------------------------------
        Method: restoreDefaults()
        Created: 8.12.2004
        Creator: KP
        Description: Restores the default settings for this widget
        -------------------------------------------------------------
        """
        print "Restoring..."
        self.iTF.restoreDefaults()
        self.setIntensityTransferFunction(self.iTF)

    def setAlphaMode(self,mode):
        """
        --------------------------------------------------------------
        Method: setAlphaMode(mode)
        Created: 7.12.2004
        Creator: KP
        Description: Sets the widget to/from alpha editing mode
        -------------------------------------------------------------
        """
        wstate="disabled"
        minvalstring="Minimum alpha value:"
        maxvalstring="Maximum alpha value:"
        if not mode:
            wstate="normal"
            minvalstring="Minimum value:"
            maxvalstring="Maximum value:"

        self.minValueLbl.SetLabel(minvalstring)
        self.maxValueLbl.SetLabel(maxvalstring)
        self.Layout()

    def setGamma(self,event):
        """
        --------------------------------------------------------------
        Method: setGamma(event)
        Created: 30.10.2004
        Creator: KP
        Description: Updates the gamma part of the function according to the
                     gamma slider in the GUI
        -------------------------------------------------------------
        """
        val=event.GetPosition()
        print "Setting gamma to %d"%val
        self.iTF.setGamma(val)
        self.updateAll()
        self.updateGUI()
        event.Skip()
        
    def setContrast(self,event):
        """
        Method: setContrast(event)
        Created: 30.10.2004
        Creator: KP
        Description: Updates the coefficient for the line according to the
                     contrast slider in the GUI
        """
        val=event.GetPosition()
        print "Value of slider",val
        oldContrast=self.iTF.getContrast()
        print "Setting contrast from event %d"%val
        self.iTF.setContrast(val)
        self.updateAll()
        self.updateGUI()
        self.contrastLbl.SetLabel("%.3f"%self.iTF.getLineCoeff())
        event.Skip()
        
    def setBrightness(self,event):
        """
        Method: setBrightness(event)
        Created: 30.10.2004
        Creator: KP
        Description: Updates the reference point for the line according to the
                     brightness slider in the GUI
        """
        val=event.GetPosition()
        self.iTF.setBrightness(val)
        self.updateAll()
        self.updateGUI()
        event.Skip()
        


    def setMinimumProcessingThreshold(self,x):
        """
        Method: setMinimumProcessingThreshold(x)
        Created: 1.12.2004
        Creator: KP
        Description: Sets the minimum processing threshold and updates 
                     the GUI accordingly
        """
        self.iTF.setMinimumProcessingThreshold(x)
        self.minProcess.SetValue("%d"%x)

    def setMinimumThreshold(self,x):
        """
        Method: setMinimumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the minimum threshold and updates the GUI accordingly
        """
        print "minimumthreshold=",x
        self.iTF.setMinimumThreshold(x)
        self.minthreshold.SetValue("%d"%x)

    def setMaximumThreshold(self,x):
        """
        Method: setMaximumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the maximum threshold and updates the GUI accordingly
        """
        self.maxthreshold.SetValue("%d"%x)
        self.iTF.setMaximumThreshold(x)

    def setMinimumValue(self,x):
        """
        Method: setMinimumValue(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the minimum value and updates the GUI accordingly
        """
        self.minValue.SetValue("%d"%x)
        self.iTF.setMinimumValue(x)

    def setMaximumValue(self,x):
        """
        --------------------------------------------------------------
        Method: setMaximumValue(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the maximum value and updates the GUI accordingly
        -------------------------------------------------------------
        """
        self.maxValue.SetValue("%d"%x)
        self.iTF.setMaximumValue(x)

    def updateMinimumThreshold(self,event):
        """
        --------------------------------------------------------------
        Method: updateMinimumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the minimum threshold
                     to reflect the GUI settings
        -------------------------------------------------------------
        """
        self.setMinimumThreshold(int(self.minthreshold.GetValue()))
        self.updateAll()
        event.Skip()

    def updateMinimumProcessingThreshold(self,event):
        """
        --------------------------------------------------------------
        Method: updateMinimumProcessingThreshold(x)
        Created: 1.12.2004
        Creator: KP
        Description: A callback used to update the minimum processing threshold
                     to reflect the GUI settings
        -------------------------------------------------------------
        """
        self.setMinimumProcessingThreshold(int(self.minProcess.GetValue()))
        self.updateAll()
        event.Skip()


    def updateMaximumThreshold(self,event):
        """
        --------------------------------------------------------------
        Method: updateMaximumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the maximum threshold
                     to reflect the GUI settings
        -------------------------------------------------------------
        """
        self.setMaximumThreshold(int(self.maxthreshold.GetValue()))
        self.updateAll()
        event.Skip()

    def updateMinimumValue(self,event):
        """
        --------------------------------------------------------------
        Method: updateMinimumValue(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the minimum value
                     to reflect the GUI settings
        -------------------------------------------------------------
        """
        self.setMinimumValue(int(self.minValue.GetValue()))
        self.updateAll()
        event.Skip()

    def updateGamma(self,event):
        """
        --------------------------------------------------------------
        Method: updateGamma(x)
        Created: 09.12.2004
        Creator: KP
        Description: A callback used to update the gamma
                     to reflect the entry value
        -------------------------------------------------------------
        """
        gamma=float(self.gammaEdit.GetValue())
        print "Setting gamma exponent to ",gamma
        self.iTF.setGammaExponent(gamma)
        self.updateAll()
        self.updateGUI()
        event.Skip()

    def updateContrast(self,event):
        """
        --------------------------------------------------------------
        Method: updateContrast(x)
        Created: 09.12.2004
        Creator: KP
        Description: A callback used to update the contrast
                     to reflect the entry value
        -------------------------------------------------------------
        """
        cont=float(self.contrastEdit.GetValue())
        self.iTF.setLineCoeff(cont)
        self.updateAll()
        self.updateGUI()
        event.Skip()

    def updateBrightness(self,event):
        """
        --------------------------------------------------------------
        Method: updateBrightness(x)
        Created: 09.12.2004
        Creator: KP
        Description: A callback used to update the brightness
                     to reflect the entry value
        -------------------------------------------------------------
        """
        br=float(self.brightnessEdit.GetValue())
        self.iTF.setBrightness(br)
        self.updateAll()
        self.updateGUI()
        event.Skip()

    def updateMaximumValue(self,event):
        """
        --------------------------------------------------------------
        Method: updateMaximumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the maximum threshold
                     to reflect the GUI settings
        -------------------------------------------------------------
        """
        self.setMaximumValue(int(self.maxValue.GetValue()))
        self.updateAll()
        event.Skip()

    def updateGUI(self):
        """
        --------------------------------------------------------------
        Method: updateGUI()
        Created: 07.12.2004
        Creator: KP
        Description: Updates the GUI settings to correspond to those of 
                     the transfer function
        -------------------------------------------------------------
        """
        self.minValue.SetValue("%d"%self.iTF.getMinimumValue())
        self.maxValue.SetValue("%d"%self.iTF.getMaximumValue())
        self.minthreshold.SetValue("%d"%self.iTF.getMinimumThreshold())
        self.maxthreshold.SetValue("%d"%self.iTF.getMaximumThreshold())
        self.minProcess.SetValue("%d"%self.iTF.getMinimumProcessingThreshold())

        self.contrastSlider.SetValue(self.iTF.getContrast())
        print "Setting brightnessslider to ",self.iTF.getBrightness()
        self.brightnessSlider.SetValue(self.iTF.getBrightness())
        self.gammaSlider.SetValue(self.iTF.getGamma())

        print "Setting gammavar to ",self.iTF.getGammaExponent()
        self.gammaEdit.SetValue("%.3f"%self.iTF.getGammaExponent())
        print "Setting brightnesvar to",self.iTF.getBrightness()
        self.brightnessEdit.SetValue("%.3f"%self.iTF.getBrightness())
        #self.contrastEdit.SetValue("%.3f"%self.iTF.getLineCoeff())



    def updateAll(self):
        """
        --------------------------------------------------------------
        Method: updateAll()
        Created: 30.10.2004
        Creator: KP
        Description: Clears the canvas and repaints the function
        -------------------------------------------------------------
        """
        self.canvas.paintTransferFunction(self.iTF)
        self.canvas.onPaint(None)

    def getIntensityTransferFunction(self):
        """
        --------------------------------------------------------------
        Method: getIntensityTransferFunction()
        Created: 11.11.2004
        Creator: JV
        Description: Returns the intensity transfer function
        -------------------------------------------------------------
        """
        return self.iTF

    def setIntensityTransferFunction(self,TF):
        """
        --------------------------------------------------------------
        Method: setIntensityTransferFunction(TF)
        Created: 24.11.2004
        Creator: KP
        Description: Sets the intensity transfer function that is configured
                     by this widget
        -------------------------------------------------------------
        """
        self.iTF=TF
        self.updateGUI()
        self.updateAll()


if __name__=='__main__':
    class MyApp(wxApp):
        def OnInit(self):
            frame=wxFrame(None,size=(640,480))
            self.panel=IntensityTransferEditor(frame)
            self.SetTopWindow(frame)
            frame.Show(True)
            return True
    def setAlphaMode(self,flag):
        if flag:
            self.panel.setAlphaMode(1)
    app=MyApp()
    flag=("alpha" in sys.argv)
    app.setAlphaMode(flag)
    app.MainLoop()


