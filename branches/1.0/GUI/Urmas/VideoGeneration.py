#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: VideoGeneration
 Project: BioImageXD
 Created: 10.02.2005, KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This module contains a panel that can be used to control the creation of a movie
 out of a set of rendered images.
 
 Copyright (C) 2005  BioImageXD Project
 See CREDITS.txt for details

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import RenderingInterface
import Visualizer
import Configuration
import os,sys
import Dialogs
import platform
import Logging
import messenger
import math


class VideoGeneration(wx.Panel):
    """
    Class: RenderingPage
    Created: 05.05.2005, KP
    Description: A page for controlling video generation
    """
    def __init__(self,parent,control,visualizer):
        """
        Method: __init__
        Created: 05.05.2005, KP
        Description: Initialization
        """
        wx.Panel.__init__(self,parent,-1)
        self.control = control
        self.visualizer=visualizer
            
        # The slider panel will be unlocked by UrmasWindow, not 
        # VideoGeneration
        self.visualizer.getCurrentMode().lockSliderPanel(1)
        
        self.rendering = 0
        self.oldformat=None
        self.abort = 0
        self.parent = parent
        self.size = self.control.getFrameSize()
        self.frames = self.control.getFrames()
        self.fps = self.control.getFrames() / float(self.control.getDuration())
        self.dur=self.control.getDuration()

        self.outputExts=[["png","bmp","jpg","tif","pnm"],["mpg","mpg","avi","wmv","avi","avi","mov"]]
        self.outputFormats=[["PNG","BMP","JPEG","TIFF","PNM"],
                             ["MPEG1","MPEG2","WMV1",
                              "WMV2","MS MPEG4","MS MPEG4 v2",
                              "QuickTime MPEG4","AVI MPEG4"]]
        self.outputCodecs = [("mpeg1video","mpg"),("mpeg2video","mpg"),("wmv1","wmv"),("wmv2","wmv"),("msmpeg4","avi"),("msmpeg4v2","avi"),("mpeg4","mov"),("mpeg4","avi")]
        self.padding = [1,1,0,0,0,0]
        self.presets=[(0,0,0),((720,576),(25),6000),((720,480),(29.97),6000)]
        self.targets=["","pal-dvd","ntsc-dvd"]
        self.needpad=0
        self.mainsizer=wx.GridBagSizer()
        self.generateGUI()
        
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(self,-1,"Ok")
        self.cancelButton = wx.Button(self,-1,"Cancel")
        
        self.okButton.Bind(wx.EVT_BUTTON,self.onOk)
        self.cancelButton.Bind(wx.EVT_BUTTON,self.onCancel)
        
        
        self.buttonBox.Add(self.okButton)
        self.buttonBox.Add(self.cancelButton)
        

        self.mainsizer.Add(self.buttonBox,(5,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)

        self.SetSizer(self.mainsizer)
        self.SetAutoLayout(True)
        self.mainsizer.Fit(self)

    def onCancel(self,*args):
        """
        Method: onCancel()
        Created: 15.12.2005, KP
        Description: Close the video generation window
        """        
        if self.rendering:
            messenger.send(None,"stop_rendering")
            self.abort = 1
#        self.visualizer.getCurrentMode().lockSliderPanel(0)            
        messenger.send(None,"video_generation_close")
        
        
    def onOk(self,event):
        """
        Method: onOk()
        Created: 26.04.2005, KP
        Description: Render the whole damn thing
        """
        self.okButton.Enable(0)
        messenger.send(None,"set_play_mode")
        messenger.connect(None,"playback_stop",self.onCancel)
        
        self.abort = 0
        if self.visualizer.getCurrentModeName()!="3d":
            self.visualizer.setVisualizationMode("3d")
        path=self.rendir.GetValue()
        file=self.videofile.GetValue()
        
        codec=self.outputFormat.GetSelection()    
        vcodec,ext = self.outputCodecs[codec]
        file_coms=file.split(".")
        file_coms[-1]=ext
        file=".".join(file_coms)
        
        conf = Configuration.getConfiguration()
        conf.setConfigItem("FramePath","Paths",path)
        conf.setConfigItem("VideoPath","Paths",file)
        conf.writeSettings()
        
        renderingInterface=RenderingInterface.getRenderingInterface(1)
        renderingInterface.setVisualizer(self.visualizer)
        # if we produce images, then set the correct file type
        if self.formatMenu.GetSelection()==0:
            formatNum=self.outputFormat.GetSelection()
            imageExt=self.outputExts[0][formatNum]
            Logging.info("Setting output image format to ",imageExt,kw="animator")
            renderingInterface.setType(imageExt)
        
        Logging.info("Setting duration to ",self.dur,"and frames to",self.frames,kw="animator")
        self.control.configureTimeline(self.dur,self.frames)

        Logging.info("Will produce %s, rendered frames go to %s"%(file,path),kw="animator")
        size=self.size
        x,y=size
        self.file=file
        self.size=size
        self.path=path
        
        
        sel=self.preset.GetSelection()
        if sel != 0:
            (x,y),fps,br=self.presets[sel]
        
        Logging.info("Will set render window to ",size,kw="animator")
        self.visualizer.setRenderWindowSize((x,y),self.parent)
        self.rendering = 1
        messenger.connect(None,"rendering_done",self.cleanUp)
        flag=self.control.renderProject(0,renderpath=path)
        self.rendering = 0
        if flag==-1:
            return
            
    def cleanUp(self,*args):
        """
        Method: cleanUp
        Created: 30.1.2006, KP
        Description: Method to clean up after rendering is done
        """     
        # if the rendering wasn't aborted, then restore the animator
        if not self.abort:
            self.visualizer.restoreWindowSizes()
            self.parent.SetDefaultSize(self.parent.origSize)
            self.parent.parent.OnSize(None)
                    
        if self.formatMenu.GetSelection()==1:

            Logging.info("Will produce video",kw="animator")
            self.encodeVideo(self.path,self.file,self.size)

        # clear the flags so that urmaswindow will destroy as cleanly
        
        self.abort=0
        self.rendering=0
        
        
        messenger.send(None,"video_generation_close")
#        self.Close()
        messenger.disconnect(None,"rendering_done")

    def encodeVideo(self,path,file,size):
        """
        Method: encodeVideo()
        Created: 27.04.2005, KP
        Description: Encode video from the frames produced
        """ 
        renderingInterface=RenderingInterface.getRenderingInterface(1)
        
        pattern=renderingInterface.getFilenamePattern()
        framename=renderingInterface.getFrameName()
        
        # FFMPEG uses %3d instead of %.3d for files numbered 000 - 999
        pattern=pattern.replace("%.","%")
        pattern=pattern.split(os.path.sep)[-1]
        pattern=pattern.replace("%s",framename)
        pattern=os.path.join(path,pattern)
        Logging.info("Pattern for files = ",pattern,kw="animator")
        
        #frameRate = int(self.frameRate.GetValue())
        #frameRate=float(self.frameRate.GetValue())
        frameRate=self.fps
        codec=self.outputFormat.GetSelection()    
        vcodec,ext = self.outputCodecs[codec]        
        if self.needpad and frameRate not in [12.5,25]:
            scodec=self.outputFormats[1][codec]
            #if frameRate<12.5:frameRate=12
            #else:frameRate=24
            frameRate=25
            Dialogs.showmessage(self,"For the code you've selected (%s), the target frame rate must be either 12.5 or 25. %d will be used."%(scodec,frameRate),"Bad framerate")
#        try:
#            x,y=self.visualizer.getCurrentMode().GetRenderWindow().GetSize()
#            print "Render window size =",x,y
#            if x%2:x-=(x%2)
#            if y%2:y-=(y%2)
#            print "x,y=",x,y
#        except:
#            x,y=512,512

        x,y=size
        ffmpegs={"linux":"ffmpeg","win":"bin\\ffmpeg.exe","darwin":"bin/ffmpeg.osx"}
        ffmpeg="ffmpeg"
        quality=self.qualitySlider.GetValue()
        quality=11-quality
        quality =math.ceil(1+(3.333333*(quality-1)))
        
        
        target=""
        sel=self.preset.GetSelection()
        if sel != 0:
            target=self.targets[sel]
            (x,y),fps,br=self.presets[sel]
        for i in ffmpegs.keys():
            if i in sys.platform:
                ffmpeg=ffmpegs[i]
                break
        if not target:
            commandLine="%s -qscale %d -b 8192 -r %.2f -s %dx%d -i \"%s\" -vcodec %s \"%s\""%(ffmpeg,quality,frameRate,x,y,pattern,vcodec,file)
        else:
            
            commandLine="%s -qscale %d -s %dx%d -i \"%s\" -target %s \"%s\""%(ffmpeg,quality,x,y,pattern,target,file)
        Logging.info("Command line for ffmpeg=",commandLine,kw="animator")
        os.system(commandLine)
        if os.path.exists(file):
            Dialogs.showmessage(self,"Encoding was successful!","Encoding done")
        else:
            Dialogs.showmessage(self,"Encoding failed: File %s does not exist!"%file,"Encoding failed")
        
    def onUpdateFormat(self,event):
        """
        Method: onUpdateFormat
        Created: 26.04.2005, KP
        Description: Update the gui based on the selected output format
        """ 
        sel = self.formatMenu.GetSelection()
        self.outputFormat.Clear()
        if sel:
            self.outputFormatLbl.SetLabel("Video Codec:")
        else:
            self.outputFormatLbl.SetLabel("Image Format:")
        self.videofile.Enable(sel)            
        self.videofileBtn.Enable(sel)
        
        for i in self.outputFormats[sel]:
            self.outputFormat.Append(i)
            
        # Produce quicktime MPEG4 by default but MS MPEG4 v2 on windows
        sel=6
        if platform.system()=="Windows":
            sel=5
        self.outputFormat.SetSelection(sel)
        
        
    
    def onUpdateCodec(self,event):
        """
        Method: onUpdateCodec
        Created: 26.04.2005, KP
        Description: Update the gui based on the selected output codec
        """ 
        sel = self.formatMenu.GetSelection()
        if sel==1:
            codec=self.outputFormat.GetSelection()
            self.needpad=self.padding[codec]
            #self.padFrames.Enable(self.needpad)
            self.onPadFrames(None)
            
    def onUpdatePreset(self,event):
        """
        Method: onUpdatePreset
        Created: 07.02.2006, KP
        Description: Update the GUI based on the selected preset
        """ 
        sel = self.preset.GetSelection()
        flag=(sel==0)
        self.formatMenu.Enable(flag)
        self.outputFormat.Enable(flag)
        
        if not flag:
            (x,y),fps,br=self.presets[sel]
            oldformat1=self.formatMenu.GetStringSelection()
            oldformat2=self.outputFormat.GetStringSelection()
            self.oldformat = (oldformat1,oldformat2)
            self.formatMenu.SetStringSelection("Video")
            self.outputFormat.SetStringSelection("MPEG2")
            self.frameRate.SetLabel("%.2f"%fps)
            self.frameSize.SetLabel("%d x %d"%(x,y))
        else:
            if self.oldformat:
                oldformat1,oldformat2=self.oldformat
                self.formatMenu.SetStringSelection(oldformat1)
                self.outputFormat.SetStringSelection(oldformat2)
                self.frameRate.SetLabel("%.2f"%self.fps)
                self.frameSize.SetLabel("%d x %d"%self.size)
            
            
    def generateGUI(self):
        """
        Method: generateGUI
        Created: 26.04.2005, KP
        Description: Generate the GUI
        """ 
        self.outputsizer=wx.GridBagSizer(0,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Rendering")
        self.outputstaticbox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.outputstaticbox.Add(self.outputsizer)

        self.formatLabel=wx.StaticText(self,-1,"Output Format")
        self.formatMenu=wx.Choice(self,-1,choices=["Images","Video"])
        self.formatMenu.SetSelection(1)
        self.formatMenu.Bind(wx.EVT_CHOICE,self.onUpdateFormat)
        
        
        self.totalFramesLabel=wx.StaticText(self,-1,"Frames:")
        self.durationLabel=wx.StaticText(self,-1,"Duration:")
        #self.fpsLabel=wx.StaticText(self,-1,"Frames:\t%.2f / s"%self.fps)
        #self.padfpsLabel=wx.StaticText(self,-1,"Padding:\t%.2f / s"%(24-self.fps))

        #self.totalFrames=wx.TextCtrl(self,-1,"%d"%self.frames,size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.totalFrames=wx.StaticText(self,-1,"%d"%self.frames,size=(50,-1))
        #self.totalFrames.Bind(wx.EVT_TEXT,self.onUpdateFrames)
        
        t=self.dur
        h=t/3600
        m=t/60
        s=t%60
        t="%.2d:%.2d:%.2d"%(h,m,s)
        self.duration=wx.StaticText(self,-1,t,size=(100,-1))

        self.outputFormatLbl = wx.StaticText(self,-1,"Video codec:")
        self.outputFormat = wx.Choice(self,-1,choices = self.outputFormats[1])
        self.outputFormat.Bind(wx.EVT_CHOICE,self.onUpdateCodec)
        self.outputFormat.SetSelection(2)
        
        self.frameSizeLbl = wx.StaticText(self,-1,"Frame size:")
        #self.frameSize = wx.Choice(self,-1,choices=["320 x 240","512 x 512","640 x 480","800 x 600"])
        #self.frameSize.SetSelection(1)
        self.frameSize = wx.StaticText(self,-1,"%d x %d"%self.size)

        self.frameRateLbl=wx.StaticText(self,-1,"Frame rate:")
        self.frameRate = wx.StaticText(self,-1,"%.2f"%self.fps)
        
        self.qualityLbl=wx.StaticText(self,-1,"Encoding quality (1 = worst, 10 = best)")
        self.qualitySlider = wx.Slider(self,-1,value=10,minValue=1,maxValue=10,style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_AUTOTICKS,size=(250,-1))
        
        self.presetLbl = wx.StaticText(self,-1,"Preset encoding targets:")
        self.preset = wx.Choice(self,-1,choices=["Use settings below","PAL-DVD","NTSC-DVD"])
        self.preset.Bind(wx.EVT_CHOICE,self.onUpdatePreset)
        self.preset.SetSelection(0)
        n=0
        self.outputsizer.Add(self.presetLbl,(n,0))
        n+=1
        self.outputsizer.Add(self.preset,(n,0))
        
        n+=1
        self.outputsizer.Add(self.formatLabel,(n,0))
        self.outputsizer.Add(self.formatMenu,(n,1))
        n+=1
        self.outputsizer.Add(self.outputFormatLbl,(n,0))
        self.outputsizer.Add(self.outputFormat,(n,1))
        n+=1
        self.outputsizer.Add(self.frameSizeLbl,(n,0))
        self.outputsizer.Add(self.frameSize,(n,1))
        n+=1
        self.outputsizer.Add(self.frameRateLbl,(n,0))
        self.outputsizer.Add(self.frameRate,(n,1))
        n+=1
        #self.outputsizer.Add(self.padFrames,(n,0))
        #n+=1
        self.outputsizer.Add(self.durationLabel,(n,0))
        self.outputsizer.Add(self.duration,(n,1))        
        n+=1
        self.outputsizer.Add(self.totalFramesLabel,(n,0))
        self.outputsizer.Add(self.totalFrames,(n,1))
        n+=1
        self.outputsizer.Add(self.qualityLbl,(n,0),span=(1,2))
        n+=1
        self.outputsizer.Add(self.qualitySlider,(n,0),span=(1,2))
        #self.outputsizer.Add(self.fpsLabel,(n,0))
        #n+=1
        #self.outputsizer.Add(self.padfpsLabel,(n,0))
        
        self.mainsizer.Add(self.outputstaticbox,(0,0))
    
        conf = Configuration.getConfiguration()
        path = conf.getConfigItem("FramePath","Paths")
        video = conf.getConfigItem("VideoPath","Paths")
        if not path:
            path=os.path.expanduser("~")
        if not video:
            video=os.path.join(path,"video.avi")
        self.rendir=wx.TextCtrl(self,-1,path,size=(150,-1))#,size=(350,-1))
        self.rendirLbl=wx.StaticText(self,
        -1,"Directory for rendered frames:")
        
        self.dirBtn=wx.Button(self,-1,"...")
        self.dirBtn.Bind(wx.EVT_BUTTON,self.onSelectDirectory)
        
        self.renderingsizer=wx.GridBagSizer(5,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Output")
        self.renderstaticbox=wx.StaticBoxSizer(box,wx.VERTICAL)
        self.renderstaticbox.Add(self.renderingsizer)
        
        self.renderingsizer.Add(self.rendirLbl,(0,0))
        self.renderingsizer.Add(self.rendir,(1,0))
        self.renderingsizer.Add(self.dirBtn,(1,1))
        
        self.videofile=wx.TextCtrl(self,-1,video,size=(150,-1))
        self.videofileLbl=wx.StaticText(self,-1,"Output file name:")
        self.videofileBtn=wx.Button(self,-1,"...")
        self.videofileBtn.Bind(wx.EVT_BUTTON,self.onSelectOutputFile)
        
        self.renderingsizer.Add(self.videofileLbl,(2,0))
        self.renderingsizer.Add(self.videofile,(3,0))
        self.renderingsizer.Add(self.videofileBtn,(3,1))

        
        self.mainsizer.Add(self.renderstaticbox,(1,0))

    def onSelectDirectory(self,event=None):
        """
        Method: selectDirectory()
        Created: 10.11.2004, KP
        Description: A callback that is used to select the directory where
                     the rendered frames are stored
        """
        dirname=Dialogs.askDirectory(self,"Directory for rendered frames",".")
        self.rendir.SetValue(dirname)
        
    def onSelectOutputFile(self,event=None):
        """
        Method: onSelectOutputFile
        Created: 26.04.2005, KP
        Description: A callback that is used to select the video file 
                     that is produced.
        """
        sel = self.formatMenu.GetSelection()
        codec=self.outputFormat.GetSelection()
        codecname=self.outputFormats[sel][codec]
        ext=self.outputExts[sel][codec]
        wc="%s File (*.%s)|*.%s"%(codecname,ext,ext)
        filename=Dialogs.askSaveAsFileName(self,"Select output filename","movie.%s"%ext,wc)
        if filename:
            self.videofile.SetValue(filename)
            

    def onUpdateFrames(self,event):
        """
        Method: onUpdateFrames
        Created: 26.04.2005, KP
        Description: Update the frame amount
        """ 
        try:
            val=int(self.totalFrames.GetValue())
            self.frames = val
            self.fps = self.frames / float(self.dur)
            Logging.info("frames per second = ",self.fps,kw="animator")
            #self.fpsLabel.SetLabel("Rendered frames:\t%.3f / second"%self.fps)
            self.frameRate.SetLabel("%.2f"%self.fps)
            self.onPadFrames(None)
        except:
            return
        
    def onPadFrames(self,event):
        """
        Method: onPadFrames
        Created: 26.04.2005, KP
        Description: Toggle padding of frames
        """     
        if not self.needpad:
            self.padfpsLabel.SetLabel("Padding frames: 0 / second")        
            return
        
        #chk=event.IsChecked()
        chk=self.padFrames.GetValue()
        if chk:
            frames = float(self.frameRate.GetValue())
            pad = frames - self.fps
            self.padfpsLabel.SetLabel("Padding frames: %.3f / second"%pad)
        else:
            self.padfpsLabel.SetLabel("Padding frames: 0 / second")
