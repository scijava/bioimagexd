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

import wx
import os.path
import sys



if __name__=='__main__':
    import sys
    sys.path.append(os.path.normpath(os.path.join(os.getcwd(),"../LSM")))
    sys.path.insert(0,os.path.normpath(os.path.join(os.getcwd(),"../Libraries/VTK/bin")))
    sys.path.insert(0,os.path.normpath(os.path.join(os.getcwd(),"../Libraries/VTK/Wrapping/Python")))

import vtk    
    

class PaintPanel(wx.Panel):
    def __init__(self,parent):
        self.maxx=255
        self.maxy=255
        self.scale=1
        self.xoffset=16
        self.yoffset=22
        w=self.xoffset+self.maxx/self.scale
        h=self.yoffset+self.maxy/self.scale
        wx.Panel.__init__(self,parent,-1,size=(w+15,h+15))
        self.buffer=wx.EmptyBitmap(w+15,h+15)
        dc = wx.BufferedDC(None,self.buffer)
        dc.SetBackground(wx.Brush("BLACK"))
        dc.Clear()
        self.dc=dc
        self.Bind(wx.EVT_PAINT,self.onPaint)
      
    def onPaint(self,event):
        dc=wx.BufferedPaintDC(self,self.buffer)                
        
    def createLine(self,x1,y1,x2,y2,color="WHITE",brush=None,**kws):
        """
        Method: createLine(x1,y1,x2,y2)
        Created: 30.10.2004
        Creator: KP
        Description: Draws a line from (x1,y1) to (x2,y2). The method
                     takes into account the scale factor
        """
        if brush:
            self.dc.SetBrush(brush)
        
        self.dc.SetPen(wx.Pen(color))
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
        Method: createOval(x,y,radius)
        Created: 30.10.2004
        Creator: KP
        Description: Draws an oval at point (x,y) with given radius
        """
        self.dc.SetBrush(wx.Brush(color,wx.SOLID))
        self.dc.SetPen(wx.Pen(color))        
        y=self.maxy-y+self.yoffset
        ox=x/self.scale
        ox+=self.xoffset
        self.dc.DrawCircle(ox,y/self.scale,r)

    def createText(self,x,y,text,color="WHITE",**kws):
        """
        Method: createText(x,y,text,font="Arial 6")
        Created: 30.10.2004
        Creator: KP
        Description: Draws a text at point (x,y) using the given font
        """
        self.dc.SetTextForeground(color)
        self.dc.SetFont(wx.Font(8,wx.SWISS,wx.NORMAL,wx.NORMAL))
        
        useoffset=1
        if kws.has_key("use_offset"):
            useoffset=kws["use_offset"]
        y=self.maxy-y
        if useoffset:
            y+=self.yoffset
        ox=x/self.scale
        if useoffset:
            ox+=self.xoffset
        #print "Drawing %s at %d,%d"%(text,ox,y/self.scale)
        self.dc.DrawText(text,ox,y/self.scale)
        

    def paintTransferFunction(self,iTF):
        """
        Method: paintTransferFunction()
        Created: 30.10.2004
        Creator: KP
        Description: Paints the graph of the function specified by the six points
        """
        print "Painting..."
        self.dc.Clear()
        self.dc.BeginDrawing()
        # get the slope start and end points
        # TF=iTF.GetAsList()
        x0,y0=0,0
        
        self.createLine(0,0,0,260,arrow="VERTICAL")
        self.createLine(0,0,260,0,arrow="HORIZONTAL")

        for i in range(32,255,32):
            # Color gray and stipple with gray50
            self.createLine(i,0,i,255,'GREY',wx.LIGHT_GREY_BRUSH)
            self.createLine(0,i,255,i,'GREY',wx.LIGHT_GREY_BRUSH)

        for x1 in range(0,256):
            # y1=TF[x1]
            y1 = iTF.GetValue(x1)
            # We cheat a bit here to get the line from point 
            # (maxthreshold,maxvalue) to (maxthreshold+1,0) to be straight
            if y1==0:
                x1-=1
            l=self.createLine(x0,y0,x1,y1,'#00ff00')
            x0,y0=x1,y1

        x,y=iTF.GetReferencePoint()
        self.createOval(x,y,2)
        
        gammaPoints=[iTF.GetGammaStart(),iTF.GetGammaEnd()]
        if 1 and gammaPoints:
            [x0,y0],[x1,y1]=gammaPoints
            self.createOval(x0,y0,2,"GREEN")
            self.createOval(x1,y1,2,"GREEN")

        textcol="GREEN"
        self.createText(0,-5,"0",textcol)
        self.createText(127,-5,"127",textcol)
        self.createText(255,-5,"255",textcol)

        self.createText(-10,127,"127",textcol)
        self.createText(-10,255,"255",textcol)
        self.dc.EndDrawing()
        
        

class IntensityTransferEditor(wx.Panel):
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
        wx.Panel.__init__(self,parent,-1)
        self.updateCallback=0
        if kws.has_key("update"):
            print "Got update callback"
            self.updateCallback=kws["update"]

        self.iTF=vtk.vtkIntensityTransferFunction()
        
        self.mainsizer=wx.BoxSizer(wx.VERTICAL)

        self.canvasBox=wx.BoxSizer(wx.HORIZONTAL)
        self.contrastBox=wx.BoxSizer(wx.VERTICAL)
        self.gammaBox=wx.BoxSizer(wx.HORIZONTAL)
        self.brightnessBox=wx.BoxSizer(wx.HORIZONTAL)

        print "Creating sliders..."
        self.contrastLbl=wx.StaticText(self,wx.NewId(),"%.3f"%1)
        self.contrastSlider=wx.Slider(self,value=0,minValue=-255,maxValue=255,size=(-1,290),
        style=wx.SL_VERTICAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.Bind(wx.EVT_SCROLL,self.setContrast,self.contrastSlider)

        print "Creating paint panel"
        self.canvas=PaintPanel(self)
        self.canvasBox.Add(self.canvas,1,wx.ALL|wx.EXPAND,10)
        self.canvasBox.Add(self.contrastBox)
        self.contrastBox.Add(self.contrastLbl)
        self.contrastBox.Add(self.contrastSlider,1,wx.TOP|wx.BOTTOM,10)
        print "Done"
        ID_CONTRASTEDIT=wx.NewId()
#        self.contrastEdit=wx.TextCtrl(self,ID_CONTRASTEDIT)
#        self.contrastBox.Add(self.contrastEdit)

        ID_BRIGHTNESSEDIT=wx.NewId()
        self.brightnessEdit=wx.TextCtrl(self,ID_BRIGHTNESSEDIT,size=(50,-1),style=wx.TE_PROCESS_ENTER)
        ID_GAMMAEDIT=wx.NewId()
        self.gammaEdit=wx.TextCtrl(self,ID_GAMMAEDIT,size=(50,-1),style=wx.TE_PROCESS_ENTER)

        self.brightnessSlider=wx.Slider(self,value=0,minValue=-255,maxValue=255,size=(260,-1),
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.Bind(wx.EVT_SCROLL,self.setBrightness,self.brightnessSlider)

        self.gammaSlider=wx.Slider(self,value=0,minValue=-100,maxValue=100,size=(260,-1),
        style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS)#|wx.SL_LABELS)
        self.Bind(wx.EVT_SCROLL,self.setGamma,self.gammaSlider)

    
        self.gammaBox.Add(self.gammaSlider)
        self.gammaBox.Add(self.gammaEdit,0,wx.ALIGN_CENTER_VERTICAL|wx.ALL)

        self.brightnessBox.Add(self.brightnessSlider)
        self.brightnessBox.Add(self.brightnessEdit,0,wx.ALIGN_CENTER_VERTICAL|wx.ALL)
    
#        ID_RESTORE_DEFAULTS=wx.NewId()
#        self.defaultBtn=wx.Button(self,ID_RESTORE_DEFAULTS,"Restore Defaults")
#        EVT_BUTTON(self,ID_RESTORE_DEFAULTS,self.restoreDefaults)

        self.minValueLbl=wx.StaticText(self,wx.NewId(),"Minimum value:")
        self.maxValueLbl=wx.StaticText(self,wx.NewId(),"Maximum value:")

        ID_MINVALUE=wx.NewId()
        ID_MAXVALUE=wx.NewId()
        self.minValue=wx.TextCtrl(self,ID_MINVALUE,style=wx.TE_PROCESS_ENTER)
        self.maxValue=wx.TextCtrl(self,ID_MAXVALUE,style=wx.TE_PROCESS_ENTER)
        
        fieldsizer=wx.GridBagSizer(0,5)
        

        valuesizer=wx.BoxSizer(wx.HORIZONTAL)
        fieldsizer.Add(self.minValueLbl,(0,0))
        fieldsizer.Add(self.minValue,(0,1))
        fieldsizer.Add(self.maxValueLbl,(0,2))
        fieldsizer.Add(self.maxValue,(0,3))
        
        self.minthresholdLbl=wx.StaticText(self,wx.NewId(),"Minimum threshold:")
        self.maxthresholdLbl=wx.StaticText(self,wx.NewId(),"Maximum threshold:")

        ID_MINTHRESHOLD=wx.NewId()
        ID_MAXTHRESHOLD=wx.NewId()
        self.minthreshold=wx.TextCtrl(self,ID_MINTHRESHOLD,style=wx.TE_PROCESS_ENTER)
        self.maxthreshold=wx.TextCtrl(self,ID_MAXTHRESHOLD,style=wx.TE_PROCESS_ENTER)
        
        fieldsizer.Add(self.minthresholdLbl,(1,0))
        fieldsizer.Add(self.minthreshold,(1,1))
        fieldsizer.Add(self.maxthresholdLbl,(1,2))
        fieldsizer.Add(self.maxthreshold,(1,3))

        ID_DONTPROCESS=wx.NewId()
        self.minProcessLbl=wx.StaticText(self,wx.NewId(),"Processing threshold:")
        self.minProcess=wx.TextCtrl(self,ID_DONTPROCESS,style=wx.TE_PROCESS_ENTER)

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

        self.minProcess.Bind(wx.EVT_KILL_FOCUS,self.updateProcessingThreshold)
        self.minProcess.Bind(wx.EVT_TEXT_ENTER,self.updateProcessingThreshold)
        
        self.setMinimumThreshold(0)
        self.setMaximumThreshold(255)
        self.setProcessingThreshold(0)

        self.setMinimumValue(0)
        self.setMaximumValue(255)

        
        print "Adding sizers..."
        self.mainsizer.Add(self.canvasBox)

        self.gammaLbl=wx.StaticText(self,-1,"Gamma")
        self.brightnessLbl=wx.StaticText(self,-1,"Brightness")

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
        Method: restoreDefaults()
        Created: 8.12.2004
        Creator: KP
        Description: Restores the default settings for this widget
        """
        print "Restoring..."
        self.iTF.Reset()
        self.setIntensityTransferFunction(self.iTF)

    def setAlphaMode(self,mode):
        """
        Method: setAlphaMode(mode)
        Created: 7.12.2004
        Creator: KP
        Description: Sets the widget to/from alpha editing mode
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
        Method: setGamma(event)
        Created: 30.10.2004
        Creator: KP
        Description: Updates the gamma part of the function according to the
                     gamma slider in the GUI
        """
        gamma=event.GetPosition()
        gammaEx=0;
        print "Setting gamma to %d"%gamma
        if abs(gamma)>10:
            gammaEx=gamma/10.0
        elif gamma!=0:
            gammaEx=1

        if gamma<0:
            gammaEx=1.0/abs(gamma)
        elif gamma==0:
            gammaEx=1
        
        self.iTF.SetGamma(gammaEx)
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
        contrast=event.GetPosition()
        if abs(contrast) > 10:
            coeff=contrast/10.0;
        elif contrast!=0:
            coeff=1
            
        if contrast<0:
            coeff=1.0/abs(contrast)
        elif contrast==0:
            coeff=1
        
        print "Value of slider",contrast
        self.iTF.SetContrast(coeff)
        self.updateAll()
        self.updateGUI()
        self.contrastLbl.SetLabel("%.3f"%coeff)
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
        self.iTF.SetBrightness(val)
        self.updateAll()
        self.updateGUI()
        event.Skip()
        


    def setProcessingThreshold(self,x):
        """
        Method: setProcessingThreshold(x)
        Created: 1.12.2004
        Creator: KP
        Description: Sets the minimum processing threshold and updates 
                     the GUI accordingly
        """
        self.iTF.SetProcessingThreshold(x)
        self.minProcess.SetValue("%d"%x)

    def setMinimumThreshold(self,x):
        """
        Method: setMinimumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the minimum threshold and updates the GUI accordingly
        """
        self.iTF.SetMinimumThreshold(x)
        self.minthreshold.SetValue("%d"%x)

    def setMaximumThreshold(self,x):
        """
        Method: setMaximumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the maximum threshold and updates the GUI accordingly
        """
        self.maxthreshold.SetValue("%d"%x)
        self.iTF.SetMaximumThreshold(x)

    def setMinimumValue(self,x):
        """
        Method: setMinimumValue(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the minimum value and updates the GUI accordingly
        """
        self.minValue.SetValue("%d"%x)
        self.iTF.SetMinimumValue(x)

    def setMaximumValue(self,x):
        """
        Method: setMaximumValue(x)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the maximum value and updates the GUI accordingly
        """
        self.maxValue.SetValue("%d"%x)
        self.iTF.SetMaximumValue(x)

    def updateMinimumThreshold(self,event):
        """
        Method: updateMinimumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the minimum threshold
                     to reflect the GUI settings
        """
        self.setMinimumThreshold(int(self.minthreshold.GetValue()))
        self.updateAll()
        event.Skip()

    def updateProcessingThreshold(self,event):
        """
        Method: updateProcessingThreshold(x)
        Created: 1.12.2004
        Creator: KP
        Description: A callback used to update the minimum processing threshold
                     to reflect the GUI settings
        """
        self.setProcessingThreshold(int(self.minProcess.GetValue()))
        self.updateAll()
        event.Skip()


    def updateMaximumThreshold(self,event):
        """
        Method: updateMaximumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the maximum threshold
                     to reflect the GUI settings
        """
        self.setMaximumThreshold(int(self.maxthreshold.GetValue()))
        self.updateAll()
        event.Skip()

    def updateMinimumValue(self,event):
        """
        Method: updateMinimumValue(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the minimum value
                     to reflect the GUI settings
        """
        self.setMinimumValue(int(self.minValue.GetValue()))
        self.updateAll()
        event.Skip()

    def updateGamma(self,event):
        """
        Method: updateGamma(x)
        Created: 09.12.2004
        Creator: KP
        Description: A callback used to update the gamma
                     to reflect the entry value
        """
        gamma=float(self.gammaEdit.GetValue())
        self.iTF.SetGamma(gamma)
        self.updateAll()
        self.updateGUI()
        event.Skip()

    def updateContrast(self,event):
        """
        Method: updateContrast(x)
        Created: 09.12.2004
        Creator: KP
        Description: A callback used to update the contrast
                     to reflect the entry value
        """
        cont=float(self.contrastEdit.GetValue())
        self.iTF.SetContrast(cont)
        self.updateAll()
        self.updateGUI()
        event.Skip()

    def updateBrightness(self,event):
        """
        Method: updateBrightness(x)
        Created: 09.12.2004
        Creator: KP
        Description: A callback used to update the brightness
                     to reflect the entry value
        """
        br=float(self.brightnessEdit.GetValue())
        self.iTF.SetBrightness(br)
        self.updateAll()
        self.updateGUI()
        event.Skip()

    def updateMaximumValue(self,event):
        """
        Method: updateMaximumThreshold(x)
        Created: 30.10.2004
        Creator: KP
        Description: A callback used to update the maximum threshold
                     to reflect the GUI settings
        """
        self.setMaximumValue(int(self.maxValue.GetValue()))
        self.updateAll()
        event.Skip()

    def updateGUI(self):
        """
        Method: updateGUI()
        Created: 07.12.2004
        Creator: KP
        Description: Updates the GUI settings to correspond to those of 
                     the transfer function
        """
        self.minValue.SetValue("%d"%self.iTF.GetMinimumValue())
        self.maxValue.SetValue("%d"%self.iTF.GetMaximumValue())
        self.minthreshold.SetValue("%d"%self.iTF.GetMinimumThreshold())
        self.maxthreshold.SetValue("%d"%self.iTF.GetMaximumThreshold())
        self.minProcess.SetValue("%d"%self.iTF.GetProcessingThreshold())

        contrast=self.iTF.GetContrast()
        gamma=self.iTF.GetGamma()
        if contrast<1:
            contrast=-1.0/contrast
        if gamma<1:
            gamma=-1.0/gamma
        self.contrastSlider.SetValue(contrast)
        self.brightnessSlider.SetValue(self.iTF.GetBrightness())
        self.gammaSlider.SetValue(gamma)

        self.gammaEdit.SetValue("%.3f"%self.iTF.GetGamma())
        self.brightnessEdit.SetValue("%.3f"%self.iTF.GetBrightness())
        #self.contrastEdit.SetValue("%.3f"%self.iTF.getLineCoeff())

    def updateAll(self):
        """
        Method: updateAll()
        Created: 30.10.2004
        Creator: KP
        Description: Clears the canvas and repaints the function
        """
        self.canvas.paintTransferFunction(self.iTF)
        self.canvas.onPaint(None)
        if self.updateCallback:
            print "Calling updateCallback"
            self.updateCallback()
        
    def getIntensityTransferFunction(self):
        """
        Method: getIntensityTransferFunction()
        Created: 11.11.2004
        Creator: JV
        Description: Returns the intensity transfer function
        """
        return self.iTF

    def setIntensityTransferFunction(self,TF):
        """
        Method: setIntensityTransferFunction(TF)
        Created: 24.11.2004
        Creator: KP
        Description: Sets the intensity transfer function that is configured
                     by this widget
        """
        self.iTF=TF
        self.updateGUI()
        self.updateAll()


if __name__=='__main__':
    class MyApp(wx.App):
        def OnInit(self):
            frame=wx.Frame(None,size=(640,480))
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


