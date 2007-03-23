# -*- coding: iso-8859-1 -*-
"""
 Unit: ColorTransferEditor
 Project: BioImageXD
 Created: 30.10.2004, KP
 Description:

 A widget used to view and modify a color transfer function. The widget
 draws the graph of the function and allows the user to modify the function.

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
__version__ = "$Revision: 1.28 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import os.path
import sys
import time
import math
import Logging
import wx.lib.buttons as buttons
import wx.lib.colourselect as csel

import messenger

if __name__=='__main__':
    import sys
        
    sys.path.append(os.path.normpath(os.path.join(os.getcwd(),"..")))
    sys.path.append(os.path.normpath(os.path.join(os.getcwd(),"../lib")))
    sys.path.insert(0,os.path.normpath(os.path.join(os.getcwd(),"../Libraries/VTK/bin")))
    sys.path.insert(0,os.path.normpath(os.path.join(os.getcwd(),"../Libraries/VTK/Wrapping/Python")))

import vtk
import time
import ImageOperations
import Dialogs  

class CTFPaintPanel(wx.Panel):
    """
    Class: CTFPaintPanel
    Created: 16.04.2005, KP
    Description: A widget onto which the transfer function is painted
    """
    def __init__(self,parent,**kws):
        self.maxx=255
        self.maxy=255
        self.scale=1
        
        self.xoffset=16
        self.yoffset=22
        if kws.has_key("width"):
            w=kws["width"]
        else:
            w=self.xoffset+self.maxx/self.scale
            w+=15
        if kws.has_key("height"):
            h=kws["height"]
        else:
            h=self.yoffset+self.maxy/self.scale
            h+=15
        wx.Panel.__init__(self,parent,-1,size=(w,h))
        self.buffer = wx.EmptyBitmap(w,h,-1)
        self.w=w
        self.h=h
        self.dc = None
        self.Bind(wx.EVT_PAINT,self.onPaint)
        

        
    def toGraphCoords(self,x,y):
        """
        Method: toGraphCoords(x,y)
        Created: 16.04.2005, KP
        Description: Returns x and y of the graph for given coordinates
        """
        rx,ry=x-self.xoffset,255-(y-self.yoffset)
        if rx<0:rx=0
        if ry<0:ry=0
        if rx>255:rx=255
        if ry>255:ry=255
        return (rx,ry)
        
    def onPaint(self,event):
        dc=wx.BufferedPaintDC(self,self.buffer)#,self.buffer)

    def createLine(self,x1,y1,x2,y2,color="WHITE",brush=None,**kws):
        """
        Method: createLine(x1,y1,x2,y2)
        Created: 30.10.2004, KP
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
        try:
            self.dc.DrawLine(x12/self.scale,y12/self.scale,
            x22/self.scale,y22/self.scale)
        except:
            Logging.info("Failed to draw line from %f/%f,%f/%f to %f/%f,%f/%f"%(x12,self.scale,y12,self.scale,x22,self.scale,y22,self.scale),kw="ctf")
        if kws.has_key("arrow"):
            if kws["arrow"]=="HORIZONTAL":
                lst=[(x22/self.scale-3,y22/self.scale-3),(x22/self.scale,y22/self.scale),(x22/self.scale-3,y22/self.scale+3)]            
            elif kws["arrow"]=="VERTICAL":
                lst=[(x22/self.scale-3,y22/self.scale+3),(x22/self.scale,y22/self.scale),(x22/self.scale+3,y22/self.scale+3)]            
            
            self.dc.DrawPolygon(lst)
            

    def createOval(self,x,y,r,color="GREY"):
        """
        Method: createOval(x,y,radius)
        Created: 30.10.2004, KP
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
        Created: 30.10.2004, KP
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
        self.dc.DrawText(text,ox,y/self.scale)
        

    def paintTransferFunction(self,ctf,pointlist,otf=None,alphaMode=None,selectedPoint=None):
        """
        Method: paintTransferFunction()
        Created: 30.10.2004, KP
        Description: Paints the graph of the function specified by the six points
        """
        self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)

        self.dc.SetBackground(wx.Brush("BLACK"))
        self.dc.Clear()
        self.dc.BeginDrawing()
        x0=0
        r0,g0,b0=0,0,0
        a0=0
        for point in pointlist:
            x,y=point
            self.createOval(x,y,2)
        if selectedPoint:
            x,y=selectedPoint
            self.createOval(x,y,2,(255,255,255))
        
        self.createLine(0,0,0,260,arrow="VERTICAL")
        self.createLine(0,0,260,0,arrow="HORIZONTAL")

        for i in range(32,255,32):
            # Color gray and stipple with gray50
            self.createLine(i,0,i,255,'GREY',wx.LIGHT_GREY_BRUSH)
            self.createLine(0,i,255,i,'GREY',wx.LIGHT_GREY_BRUSH)
    
        for x1 in range(0,256):
            val=[0,0,0]
            ctf.GetColor(x1,val)
            r,g,b = val
            r*=255
            g*=255
            b*=255
            if otf:
                a=otf.GetValue(x1)
                a*=255
                a=int(a)
                self.createLine(x0,a0,x1,a,'#ffffff')
                a0=a
            r=int(r)
            g=int(g)
            b=int(b)
            if not alphaMode:
                self.createLine(x0,r0,x1,r,'#ff0000')
                self.createLine(x0,g0,x1,g,'#00ff00')
                self.createLine(x0,b0,x1,b,'#0000ff')
            x0=x1
            r0,g0,b0=r,g,b


        textcol="GREEN"
        self.createText(0,-5,"0",textcol)
        self.createText(127,-5,"127",textcol)
        self.createText(255,-5,"255",textcol)

        self.createText(-10,127,"127",textcol)
        self.createText(-10,255,"255",textcol)
        self.dc.EndDrawing()
        self.dc = None

        

class CTFValuePanel(CTFPaintPanel):
    """
    Class: CTFValuePanel
    Created: 17.04.2005, KP
    Description: A widget onto which the colors transfer function is painted
    """
    def __init__(self,parent):
        self.lineheight = 32
        CTFPaintPanel.__init__(self,parent,height=self.lineheight,width=256+16)       
        self.xoffset = 16
        self.yoffset = 0

    def paintTransferFunction(self,ctf,pointlist=[]):
        """
        Method: paintTransferFunction()
        Created: 30.10.2004, KP
        Description: Paints the graph of the function specified by the six points
        """
        self.dc = wx.BufferedDC(wx.ClientDC(self),self.buffer)

        self.dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        self.dc.Clear()
        self.dc.BeginDrawing()
        bmp = ImageOperations.paintCTFValues(ctf,self.lineheight)
        self.dc.DrawBitmap(bmp,self.xoffset,0)
        self.dc.EndDrawing()
        self.dc = None
        
class CTFButton(wx.BitmapButton):
    """
    Class: CTFButton
    Created: 18.04.2005, KP
    Description: A button that shows a ctf as a palette and lets the user modify it
                 by clicking on the button
    """    
    def __init__(self,parent,alpha=0):
        """
        Method: __init__
        Created: 18.04.2005, KP
        Description: Initialization
        """    
        wx.BitmapButton.__init__(self,parent,-1)
        self.changed=0
        self.alpha=alpha
        self.ctf = vtk.vtkColorTransferFunction()
        self.ctf.AddRGBPoint(0,0,0,0)
        self.ctf.AddRGBPoint(255,1,1,1)
        self.bmp = ImageOperations.paintCTFValues(self.ctf)
        self.SetBitmapLabel(self.bmp)
        self.Bind(wx.EVT_BUTTON,self.onModifyCTF)
        
    def isChanged(self):
        """
        Method: isChanged
        Created: 28.04.2005, KP
        Description: Was the ctf or otf changed
        """        
        return self.changed
        
    def setColorTransferFunction(self,ctf):
        """
        Method: setColorTransferFunction
        Created: 18.04.2005, KP
        Description: Set the color transfer function that is edited
        """   
        self.ctf = ctf
        self.bmp = ImageOperations.paintCTFValues(self.ctf)
        self.SetBitmapLabel(self.bmp)
        
    def getColorTransferFunction(self):
        """
        Method: getColorTransferFunction
        Created: 25.04.2005, KP
        Description: Return the color transfer function that is edited
        """        
        return self.ctf
        
    def onModifyCTF(self,event):
        """
        Method: onModifyCTF
        Created: 18.04.2005, KP
        Description: Modify the color transfer function
        """        
        dlg = wx.Dialog(self,-1,"Edit color transfer function")
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel = ColorTransferEditor(dlg,alpha=self.alpha)
        panel.setColorTransferFunction(self.ctf)
        self.panel = panel
        sizer.Add(panel)
        dlg.SetSizer(sizer)
        dlg.SetAutoLayout(1)
        self.changed=1
        sizer.Fit(dlg)
        dlg.ShowModal()
        self.bmp = ImageOperations.paintCTFValues(self.ctf)
        self.SetBitmapLabel(self.bmp)
        messenger.send(None,"data_changed",0)
        
    def getOpacityTransferFunction(self):
        """
        Method: getOpacityTransferFunction()
        Created: 28.04.2005, KP
        Description: Returns the opacity function
        """
        return self.panel.getOpacityTransferFunction()
        
    def setOpacityTransferFunction(self,otf):
        """
        Method: setOpacityTransferFunction()
        Created: 25.07.2005, KP
        Description: Returns the opacity function
        """
        return self.panel.setOpacityTransferFunction(otf)
        
        
        
class ColorTransferEditor(wx.Panel):
    """
    Class: ColorTransferEditor
    Created: 30.10.2004, KP
    Description: A widget used to view and modify an intensity transfer function
    """
    def __init__(self,parent,**kws):
        """
        Method: __init__
        Created: 30.10.2004, KP
        Description: Initialization
        """
        self.parent=parent
        self.selectedPoint = None
        wx.Panel.__init__(self,parent,-1)
        self.updateT=0
        if kws.has_key("alpha"):
            self.alpha=kws["alpha"]
        self.updateCallback=0
        self.ctf = vtk.vtkColorTransferFunction()
        self.doyield=1
        self.calling=0
        self.guiupdate=0
        self.freeMode = 0
        self.selectThreshold=5.0
        self.ptThreshold=0.0
        self.color = 0
        self.otf = vtk.vtkPiecewiseFunction()
        self.restoreDefaults(None)
        self.mainsizer=wx.BoxSizer(wx.VERTICAL)

        self.canvasBox=wx.BoxSizer(wx.VERTICAL)
        
        self.value=CTFValuePanel(self)
        self.canvasBox.Add(self.value,0,wx.EXPAND|wx.LEFT|wx.RIGHT,10)
        
        self.canvas=CTFPaintPanel(self)
        self.canvasBox.Add(self.canvas,1,wx.ALL|wx.EXPAND,10)

        self.mainsizer.Add(self.canvasBox)
        
        self.itemBox=wx.BoxSizer(wx.HORIZONTAL)
        
        self.alphaMode=0
        
        self.redBtn=buttons.GenToggleButton(self,-1,"",size=(32,32))
        self.redBtn.SetValue(1)
        self.redBtn.SetBackgroundColour((255,0,0))
        self.greenBtn=buttons.GenToggleButton(self,-1,"",size=(32,32))
        self.greenBtn.SetBackgroundColour((0,255,0))
        self.blueBtn=buttons.GenToggleButton(self,-1,"",size=(32,32))
        self.blueBtn.SetBackgroundColour((0,0,255))
        
        if self.alpha:
            self.alphaBtn=buttons.GenToggleButton(self,-1,"Alpha",size=(32,32))
            self.alphaBtn.Bind(wx.EVT_BUTTON,self.onEditAlpha)
            self.alphaBtn.SetBackgroundColour((255,255,255))
        #self.freeBtn = wx.ToggleButton(self,-1,)
        iconpath=reduce(os.path.join,["Icons"])        
        self.freeBtn = buttons.GenBitmapToggleButton(self, -1, None)
        self.freeBtn.SetBestSize((32,32))
        bmp = wx.Image(os.path.join(iconpath,"draw.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.freeBtn.SetBitmapLabel(bmp)
        self.colorBtn = csel.ColourSelect(self,-1,"",size=(32,32))
        self.colorBtn.Bind(csel.EVT_COLOURSELECT,self.onSetToColor)

        openGif = wx.Image(os.path.join(iconpath,"open.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        saveGif = wx.Image(os.path.join(iconpath,"save.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.openBtn = wx.BitmapButton(self,-1,openGif,size=(32,32))
        self.saveBtn = wx.BitmapButton(self,-1,saveGif,size=(32,32))
        
        self.maxNodes=wx.SpinCtrl(self,-1,"256",min=2,max=9999,size=(54,-1),style=wx.TE_PROCESS_ENTER)
        self.maxNodes.SetToolTip(wx.ToolTip("Set the maximum number of nodes in the graph."))
        self.maxNodes.SetHelpText("Use this control to set the maximum number of nodes in the graph. This is useful if you have a hand drawn palette that you wish to edit by dragging the nodes.")
        self.maxNodes.Bind(wx.EVT_SPINCTRL,self.onSetMaxNodes)
        self.maxNodes.Bind(wx.EVT_TEXT_ENTER,self.onSetMaxNodes)
        
        self.itemBox.Add(self.redBtn)
        self.itemBox.Add(self.greenBtn)
        self.itemBox.Add(self.blueBtn)
        if self.alpha:
            self.itemBox.Add(self.alphaBtn)
        
        self.itemBox.Add(self.freeBtn)
        self.itemBox.Add(self.colorBtn)
        self.itemBox.Add(self.openBtn)
        self.itemBox.Add(self.saveBtn)
        self.itemBox.Add(self.maxNodes)
        
        self.redBtn.Bind(wx.EVT_BUTTON,self.onEditRed)
        self.greenBtn.Bind(wx.EVT_BUTTON,self.onEditGreen)
        self.blueBtn.Bind(wx.EVT_BUTTON,self.onEditBlue)
        
        self.freeBtn.Bind(wx.EVT_BUTTON,self.onFreeMode)
        
        self.openBtn.Bind(wx.EVT_BUTTON,self.onOpenLut)
        self.saveBtn.Bind(wx.EVT_BUTTON,self.onSaveLut)
        
        self.mainsizer.Add(self.itemBox)

        self.SetAutoLayout(True)
        self.SetSizer(self.mainsizer)
        self.mainsizer.SetSizeHints(self)

        self.canvas.Bind(wx.EVT_LEFT_DOWN,self.onEditFunction)
        self.canvas.Bind(wx.EVT_LEFT_DCLICK,self.onDeletePoint)
        
        self.canvas.Bind(wx.EVT_RIGHT_DOWN,self.onCreatePoint)
        self.canvas.Bind(wx.EVT_MOTION,self.onDrawFunction)
        
        self.updateGraph()
        self.pos = (0,0)
        
    def onSetMaxNodes(self,evt):
        """
        Method: onSetMaxNodes
        Created: 08.08.2005, KP
        Description: Sets the maximum number of nodes
        """                
        n=len(self.points)
        tot=0
        for i,pts in enumerate(self.points):
            tot+=len(pts)
        
        maxpts=self.maxNodes.GetValue()
        if maxpts>=tot:
            return
        everyNth=float(tot)/maxpts
        Logging.info("Removing every %f pts (pts=%d)"%(everyNth,maxpts))
        n=0
        k=1
        toRemove=[]
        for i,pts in enumerate(self.points):
            for j,point in enumerate(pts):
                firstOrLast=(j==0 or j==len(pts)-1)
                n+=1
                #print n,k,n%k,everyNth
                if not firstOrLast and k<everyNth:
                    toRemove.append(point)
                    k+=1
                else:
                    k=1
            for point in toRemove:
                pts.remove(point)
            toRemove=[]
        
        tot=0
        for i,pts in enumerate(self.points):
            tot+=len(pts)
        Logging.info("Points left = %d"%tot)
        self.updateGraph()
                
        
        
        
        
    def onDeletePoint(self,event):
        """
        Method: onDeletePoint
        Created: 08.08.2005, KP
        Description: Delete the selected point
        """        
        if self.selectedPoint:
            for i,pts in enumerate(self.points):
                if self.selectedPoint in pts:
                    pts.remove(self.selectedPoint)
            self.selectedPoint=None
            self.updateGraph()
            
    def setAlphaMode(self,flag):
        """
        Method: setAlphaMode
        Created: 29.05.2005, KP
        Description: Show only alpha channel
        """
        self.alphaMode=flag
        
        self.colorBtn.Show(flag)
        self.redBtn.Show(flag)
        self.greenBtn.Show(flag)
        self.blueBtn.Show(flag)
        self.updateGraph()
        
    def onSaveLut(self,event):
        """
        Method: onSaveLut
        Created: 17.04.2005, KP
        Description: Save a lut file
        """    
        
        dlg=wx.FileDialog(self,"Save lookup table",wildcard="Lookup table (*.lut)|*.lut",style=wx.SAVE)
        filename=None
        if dlg.ShowModal()==wx.ID_OK:
            filename=dlg.GetPath()
            ImageOperations.saveLUT(self.ctf,filename)

    def onOpenLut(self,event):
        """
        Method: onOpenLut
        Created: 17.04.2005, KP
        Description: Load a lut file
        """    
        filename=Dialogs.askOpenFileName(self,"Load lookup table","Lookup table (*.lut)|*.lut")
        if filename:
            filename=filename[0]
            Logging.info("Opening palette",filename,kw="ctf")
            self.freeMode = 0
            ImageOperations.loadLUT(filename,self.ctf)
            self.setFromColorTransferFunction(self.ctf)
            self.getPointsFromFree()
            self.updateGraph()
        
    def onSetToColor(self,event):
        """
        Method: onSetToColor
        Created: 17.04.2005, KP
        Description: Set the ctf to be a specific color
        """    
        col=event.GetValue()
        color=col.Red(),col.Green(),col.Blue()
        if 255 not in color:
            mval=max(color)
            coeff=255.0/mval
            ncolor=[int(x*coeff) for x in color]
            Logging.info("New color = ",ncolor,kw="ctf")
            dlg=wx.MessageDialog(self,
                "The color you selected: %d,%d,%d is incorrect."
                "At least one of the R, G or B components\n"
                "of the color must be 255. Therefore, "
                "I have modified the color a bit. "
                "It is now %d,%d,%d. Have a nice day."%(color[0],
                color[1],color[2],ncolor[0],ncolor[1],ncolor[2]),"Selected color is incorrect",wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            color = ncolor
        r,g,b=color
        self.redpoints=[(0,0),(255,r)]
        self.greenpoints=[(0,0),(255,g)]
        self.bluepoints=[(0,0),(255,b)]
        #self.alphapoints=[(0,0),(255,51)]
        self.points=[self.redpoints,self.greenpoints,self.bluepoints,self.alphapoints]
        self.freeMode = 0
        self.updateGraph()
        messenger.send(None,"data_changed",0)
        self.colorBtn.SetColour(col)
        
        
        
        
    def onCreatePoint(self,event):
        """
        Method: onCreatePoint
        Created: 16.04.2005, KP
        Description: Add a point to the function
        """    
        x,y=event.GetPosition()
        x,y=self.canvas.toGraphCoords(x,y)
        if not self.freeMode:
            d=10
            currd=255
            hasx=0
            pt=(x,y)
            self.points[self.color].append(pt)
            self.points[self.color].sort()
            self.updateGraph()

        

    def onEditFunction(self,event):
        """
        Method: onEditFunction
        Created: 16.04.2005, KP
        Description: Edit the function
        """    
        x,y=event.GetPosition()
        x,y=self.canvas.toGraphCoords(x,y)
        if self.freeMode:
            self.pos = (x,y)
        else:
            d=10
            currd=255
            hasx=0
            Logging.info("points for color %d = "%self.color,self.points[self.color])
            for pt in self.points[self.color]:
                d=self.dist((x,y),pt)
                if pt[0]==x:hasx=1
                if d<self.selectThreshold and d<currd:
                    self.selectedPoint=pt
                    currd=d
                    break
                
    def dist(self,p1,p2):
        """
        Method: dist(p1,p2)
        Created: 16.04.2005, KP
        Description: Return the distance between points p1 and p2
        """        
        return math.sqrt( (p1[0]-p2[0])**2+(p1[1]-p2[1])**2)
    
        
    def onDrawFunction(self,event):
        """
        Method: onDrawFunction
        Created: 16.04.2005, KP
        Description: Draw the function
        """        
        if event.Dragging():
            x,y=event.GetPosition()
            x,y=self.canvas.toGraphCoords(x,y)
            if y<=0:y=0
            if y>=255:y=255
            if x<=0:x=0
            if x>=255:x=255
            if self.freeMode:
                if self.pos[0]:
                    x0=min(self.pos[0],x)
                    x1=max(self.pos[0],x)
                    n=(x1-x0)
                    if n:
                        d=abs(y-self.pos[1])/float(n)
                        Logging.info("Fixing range %d,%d,d=%f, steps = %d"%(x0,x1,d,n),kw="ctf")
                        if x>self.pos[0] and y<self.pos[1]:d*=-1
                        if x<self.pos[0] and y>self.pos[1]:d*=-1
                    
                        for i in range(x0,x1):
                            ny=int(y+(i-x0)*d)
                            if ny<0:ny=0
                            if ny>=255:ny=255
                            self.funcs[self.color][i]=ny
                
                self.funcs[self.color][x]=y
                self.updateGraph()     
                self.pos = (x,y)
            else:
                if self.selectedPoint and self.selectedPoint in self.points[self.color]:
                    for point in self.points[self.color]:
                        if point[0] == x:
                            x=x+1
                            break
                    i=self.points[self.color].index(self.selectedPoint)

                    self.points[self.color][i]=(x,y)
                    self.selectedPoint = (x,y)
                    self.updateGraph()
            wx.FutureCall(500,self.updatePreview)
    def updatePreview(self):
        """
        Method: updatePreview
        Created: 08.08.2005, KP
        Description: Send an event updating the preview
        """            
        if abs(time.time()-self.updateT)>0.5:
            self.updateT=time.time()
            messenger.send(None,"data_changed",0)
    
    def onFreeMode(self,event):
        """
        Method: onFreeMode
        Created: 16.04.2005, KP
        Description: Toggle free mode on / off
        """
        was=0
        if self.freeMode:was=1
        if not was and event.GetIsDown():
            self.updateGraph()
            self.setFromColorTransferFunction(self.ctf)
        self.freeMode = event.GetIsDown()
        Logging.info("Points before=",self.points,kw="ctf")

        if not self.freeMode and was:
            Logging.info("Analyzing free mode for points",kw="ctf")
            self.getPointsFromFree()
        Logging.info("Points after=",self.points,kw="ctf")      

        self.updateGraph()
                
    def onEditRed(self,event):
        """
        Method: onEditRed
        Created: 16.04.2005, KP
        Description: Edit the red channel
        """
        self.blueBtn.SetValue(0)
        self.greenBtn.SetValue(0)
        if self.alpha:self.alphaBtn.SetValue(0)
        self.color = 0
        self.updateGraph()

    def onEditAlpha(self,event):
        """
        Method: onEditAlpha
        Created: 28.04.2005, KP
        Description: Edit the alpha channel
        """
        self.blueBtn.SetValue(0)
        self.greenBtn.SetValue(0)
        self.redBtn.SetValue(0)
        Logging.info("Editing alpha channel")
        self.color = 3
        self.updateGraph()
        
    def onEditGreen(self,event):
        """
        Method: onEditRed
        Created: 16.04.2005, KP
        Description: Edit the red channel
        """
        self.blueBtn.SetValue(0)
        self.redBtn.SetValue(0)
        if self.alpha:self.alphaBtn.SetValue(0)
        self.color = 1
        self.updateGraph()

    def onEditBlue(self,event):
        """
        Method: onEditRed
        Created: 16.04.2005, KP
        Description: Edit the red channel
        """
        self.redBtn.SetValue(0)
        self.greenBtn.SetValue(0)
        if self.alpha:self.alphaBtn.SetValue(0)
        self.color = 2
        self.updateGraph()


    def restoreDefaults(self,event):
        """
        Method: restoreDefaults()
        Created: 8.12.2004, KP
        Description: Restores the default settings for this widget
        """
        self.redfunc=[0]*256
        self.greenfunc=[0]*256
        self.bluefunc=[0]*256
        self.alphafunc=[0]*256
        self.funcs=[self.redfunc,self.greenfunc,self.bluefunc,self.alphafunc]
        
        self.redpoints=[(0,0),(255,255)]
        self.greenpoints=[(0,0),(255,255)]
        self.bluepoints=[(0,0),(255,255)]
        self.alphapoints=[(0,0),(255,51)]
        self.points=[self.redpoints,self.greenpoints,self.bluepoints,self.alphapoints]
        for i in xrange(256):
            self.redfunc[i]=i
            self.greenfunc[i]=i
            self.bluefunc[i]=i
            self.alphafunc[i]=int(i*0.2)
        self.ctf.RemoveAllPoints()
        
            
    def updateGraph(self):
        """
        Method: updateGraph()
        Created: 30.10.2004, KP
        Description: Clears the canvas and repaints the function
        """
        self.ctf.RemoveAllPoints()
        if self.freeMode:
            for i in xrange(256):
                r,g,b=self.redfunc[i],self.greenfunc[i],self.bluefunc[i]
                r/=255.0
                g/=255.0
                b/=255.0
                self.ctf.AddRGBPoint(i,r,g,b)
                if self.alpha:
                    a=self.alphafunc[i]
                    a/=255.0
                    self.otf.AddPoint(i,a)
        else:
            func=[]
            for i in range(256):func.append([0,0,0,0])
            for col,pointlist in enumerate(self.points):
                pointlist.sort()
                for i in xrange(1,len(pointlist)):
                    x1,y1=pointlist[i-1]
                    x2,y2=pointlist[i]
                    
                    dx=x2-x1
                    if dx and (y2!=y1):
                        dy=(y2-y1)/float(dx)
                    else:dy=0
                    if x2>255:
                        x2=255
                        x1=x1-1
                        
                    for x in range(x1,x2+1):
                        func[x][col]=y1+(x-x1)*dy
                        
                        
            for i in xrange(256):
                r,g,b,a=func[i]
                r/=255.0
                g/=255.0
                b/=255.0
                a/=255.0
                self.ctf.AddRGBPoint(i,r,g,b)
                if self.alpha:
                    self.otf.AddPoint(i,a)
                                            
        pts=[]
        if not self.freeMode:
            if not self.alphaMode:
                pts.extend(self.redpoints)
                pts.extend(self.greenpoints)
                pts.extend(self.bluepoints)
            pts.extend(self.alphapoints)
        otf=None
        if self.alpha:
            otf=self.otf
        
        self.canvas.paintTransferFunction(self.ctf,pts,otf,self.alphaMode,self.selectedPoint)
        self.value.paintTransferFunction(self.ctf)
        
    def getColorTransferFunction(self):
        """
        Method: getColorTransferFunction()
        Created: 11.11.2004, JV
        Description: Returns the color transfer function
        """
        return self.ctf
        
    def setFromColorTransferFunction(self,TF):
        """
        Method: setFromColorTransferFunction(TF)
        Created: 17.04.2005, KP
        Description: Sets the colors of this graph
        """
        for i in range(256):
            val = [0,0,0]
            TF.GetColor(i,val)
            r,g,b = val
            r*=255
            g*=255
            b*=255
            r=int(r)
            g=int(g)
            b=int(b)
            self.redfunc[i]=r
            self.greenfunc[i]=g
            self.bluefunc[i]=b

    def getPointsFromFree(self):
        """
        Method: getPointsFromFree
        Created: 18.04.2005, KP
        Description: Method that analyzes the color transfer function to
                     determine where to insert control points for the user
                     to edit
        """
        dr,dg,db=0,0,0
        dr2,dg2,db2=0,0,0
        r2,g2,b2=0,0,0
        da=0
        da2=0
        a2=0
        self.redpoints=[]
        self.greenpoints=[]
        self.bluepoints=[]
        self.alphapoints=[]
        for x in range(256):
            if self.alpha:
                a=self.otf.GetValue(x)
                a*=255
                a=int(a)
                da = a-a2
                
            val = [0,0,0]
            self.ctf.GetColor(x,val)
            r,g,b=val
            
            r*=255
            g*=255
            b*=255
            
            r=int(r)
            g=int(g)
            b=int(b)
            dr = r-r2
            dg = g-g2
            db = b-b2
            
            if x in [0,255]:
                self.redpoints.append((x,r))
                self.greenpoints.append((x,g))
                self.bluepoints.append((x,b))
                if self.alpha:
                    self.alphapoints.append((x,a))
            else:
                if abs(dr - dr2)>self.ptThreshold:
                    self.redpoints.append((x,r))
                if abs(dg - dg2)>self.ptThreshold:
                    self.greenpoints.append((x,g))
                if abs(db - db2)>self.ptThreshold:
                    self.bluepoints.append((x,b))
                if self.alpha:
                    if abs(da - da2)>self.ptThreshold:
                        self.alphapoints.append((x,a))
                    da2=da
                    a2=a
            dr2,dg2,db2=dr,dg,db
            
            r2,g2,b2=r,g,b
        self.points=[self.redpoints,self.greenpoints,self.bluepoints,self.alphapoints]
        
        self.updateGraph()
            
    def setColorTransferFunction(self,TF):
        """
        Method: setColorTransferFunction(TF)
        Created: 24.11.2004, KP
        Description: Sets the color transfer function that is configured
                     by this widget
        """
        self.ctf=TF
        self.getPointsFromFree()
        self.alphapoints=[(0,0),(255,51)]
        self.points=[self.redpoints,self.greenpoints,self.bluepoints,self.alphapoints]
        val=[0,0,0]
        self.ctf.GetColor(255,val)
        r,g,b=val
        r*=255
        g*=255
        b*=255
        col=wx.Colour(int(r),int(g),int(b))
        print "Setting to ",(int(r),int(g),int(b))
        self.colorBtn.SetColour(((int(r),int(g),int(b))))
        self.colorBtn.Refresh()

        self.updateGraph()
        
    def getOpacityTransferFunction(self):
        """
        Method: getOpacityTransferFunction()
        Created: 28.04.2005, KP
        Description: Returns the opacity function
        """
        return self.otf
        
    def setOpacityTransferFunction(self,otf):
        """
        Method: getOpacityTransferFunction()
        Created: 28.04.2005, KP
        Description: Returns the opacity function
        """
        self.otf=otf
        print "\n\n\nSetting otf to ",otf.GetValue(255)
        self.getPointsFromFree()
        self.updateGraph()        

if __name__=='__main__':
 
    class MyApp(wx.App):
        def OnInit(self):
            frame=wx.Frame(None,size=(400,400))
            alpha=("alpha" in sys.argv)
            self.panel=ColorTransferEditor(frame,alpha=alpha)
            
            self.SetTopWindow(frame)
            frame.Show(True)
            return True

    app = MyApp()
    app.MainLoop()

