#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: VideoGeneration
 Project: BioImageXD
 Created: 10.02.2005
 Creator: KP
 Description:

 URM/AS - The Unified Rendering Manager / Animator for Selli
 
 This module contains a panel that can be used to control the creation of a movie
 out of a set of rendered images.
 
 Modified: 10.02.2005 KP - Created the module
 
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
__version__ = "$Revision: 1.22 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import Dialogs
import RenderingInterface
import os,sys

class VideoGeneration(wx.Dialog):
    """
    Class: VideoGeneration
    Created: 23.02.2005, KP
    Description: A panel for controlling the movie generation.        
    """
    def __init__(self,parent,control):
        wx.Dialog.__init__(self,parent,-1,"Rendering %s"%control.getDataUnit().getName())
        self.renderingInterface = RenderingInterface.getRenderingInterface(1)
        self.renderingInterface.setParent(parent)

        self.control = control
        self.frames = self.control.getFrames()
        self.fps = self.control.getFrames() / float(self.control.getDuration())
        self.dur=self.control.getDuration()

        self.outputExts=[["png","bmp","jpg","tif"],["mpg","mpg","avi","wmv","avi","avi"]]
        self.outputFormats=[["PNG","BMP","JPEG","TIFF"],["MPEG1","MPEG2","MPEG4","WMV1","MS MPEG4","MS MPEG4 v2"]]
        self.outputCodecs = ["mpeg1video","mpeg2video","mpeg4","wmv1","msmpeg4","msmpeg4v2"]
        self.padding = [1,1,0,0,0,0]
        self.needpad=1
        self.mainsizer=wx.GridBagSizer()
        self.generateGUI()
        self.btnsizer=self.CreateButtonSizer(wx.OK|wx.CANCEL)
        self.launchBtn=wx.Button(self,-1,"Launch Mayavi")
        self.btnsizer.Add(self.launchBtn)
        self.launchBtn.Bind(wx.EVT_BUTTON,self.onLaunchMayavi)
        
        self.mainsizer.Add(self.btnsizer,(5,0),flag=wx.EXPAND|wx.RIGHT|wx.LEFT)
        
        wx.EVT_BUTTON(self,wx.ID_OK,self.onOkButton)
        
        self.SetSizer(self.mainsizer)
        self.SetAutoLayout(True)
        self.mainsizer.Fit(self)

    def onOkButton(self,event):
        """
        Method: onButtonOk()
        Created: 26.04.2005, KP
        Description: Render the whole damn thing
        """ 
        
        path=self.rendir.GetValue()
        file=self.videofile.GetValue()
        print "Setting duration to ",self.dur,"and frames to",self.frames
        self.control.configureTimeline(self.dur,self.frames)
        
        print "Will produce %s, rendered frames go to %s"%(file,path)
        size=self.frameSize.GetStringSelection()
        x,y=size.split("x")
        x=int(x)
        y=int(y)
        size=(x,y)
        print "Will set render window to ",size
        flag=self.control.renderProject(0,renderpath=path,size=size)
        if flag==-1:
            return
        if self.formatMenu.GetSelection()==1:
            print "Will produce video"
            self.encodeVideo(size,path,file)
        self.Close()
        
    def encodeVideo(self,size,path,file):
        """
        Method: encodeVideo()
        Created: 27.04.2005, KP
        Description: Encode video from the frames produced
        """ 
        renderingInterface=RenderingInterface.getRenderingInterface()
        pattern=renderingInterface.getFilenamePattern()
        framename=renderingInterface.getFrameName()
        # FFMPEG uses %3d instead of %.3d for files numbered 000 - 999
        pattern=pattern.replace("%.","%")
        pattern=pattern.split(os.path.sep)[-1]
        pattern=pattern.replace("%s",framename)
        pattern=os.path.join(path,pattern)
        print "Pattern for files = ",pattern
        
        frameRate = int(self.frameRate.GetValue())
        codec=self.outputFormat.GetSelection()
        vcodec = self.outputCodecs[codec]
        x,y=size
        ffmpegs={"linux":"ffmpeg","win":"bin/ffmpeg.exe","darwin":"bin/ffmpeg.osx"}
        ffmpeg="ffmpeg"
        for i in ffmpegs.keys():
            if i in sys.platform:
                ffmpeg=ffmpegs[i]
                break
        print "Using ffmpeg %s"%ffmpeg
        commandLine="%s -r %d -s %dx%d -i %s -vcodec %s %s"%(ffmpeg,frameRate,x,y,pattern,vcodec,file)
        print "Command line for ffmpeg=",commandLine
        os.system(commandLine)
        if os.path.exists(file):
            Dialogs.showmessage(self,"Encoding was successful!","Encoding done")
        else:
            Dialogs.showmessage(self,"Encoding failed: File %s does not exist!"%file,"Encoding failed")
        
    def onLaunchMayavi(self,event):
        """
        Method: onLaunchMayavi()
        Created: 26.04.2005, KP
        Description: Launch mayavi
        """ 
        self.control.startMayavi()
        
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
        self.outputFormat.SetSelection(0)
    
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
            self.padFrames.Enable(self.needpad)
            self.onPadFrames(None)
            
    def generateGUI(self):
        """
        Method: generateGUI
        Created: 26.04.2005, KP
        Description: Generate the GUI
        """ 
        self.outputsizer=wx.GridBagSizer(5,5)
        box=wx.StaticBox(self,wx.HORIZONTAL,"Rendering")
        self.outputstaticbox=wx.StaticBoxSizer(box,wx.HORIZONTAL)
        self.outputstaticbox.Add(self.outputsizer)
        
        self.formatLabel=wx.StaticText(self,-1,"Output Format")
        self.formatMenu=wx.Choice(self,-1,choices=["Images","Video"])
        self.formatMenu.Bind(wx.EVT_CHOICE,self.onUpdateFormat)
        
        
        self.totalFramesLabel=wx.StaticText(self,-1,"Frames:")
        self.durationLabel=wx.StaticText(self,-1,"Duration:")
        self.fpsLabel=wx.StaticText(self,-1,"Rendered frames:\t%.3f / second"%self.fps)
        self.padfpsLabel=wx.StaticText(self,-1,"Padding frames:\t%.3f / second"%(24-self.fps))

        self.totalFrames=wx.TextCtrl(self,-1,"%d"%self.frames,size=(50,-1),style=wx.TE_PROCESS_ENTER)
        self.totalFrames.Bind(wx.EVT_TEXT,self.onUpdateFrames)
        
        t=self.dur
        h=t/3600
        m=t/60
        s=t%60
        t="%.2d:%.2d:%.2d"%(h,m,s)
        self.duration=wx.StaticText(self,-1,t,size=(100,-1))
        
        self.outputFormatLbl = wx.StaticText(self,-1,"Video codec:")
        self.outputFormat = wx.Choice(self,-1,choices = self.outputFormats[1])
        self.outputFormat.Bind(wx.EVT_CHOICE,self.onUpdateCodec)
        self.formatMenu.SetSelection(1)
        
        self.frameSizeLbl = wx.StaticText(self,-1,"Frame size:")
        self.frameSize = wx.Choice(self,-1,choices=["320 x 240","640 x 480"])
        self.frameSize.SetSelection(1)
        
        self.frameRateLbl=wx.StaticText(self,-1,"Frame rate:")
        self.frameRate = wx.TextCtrl(self,-1,"24")
        self.padFrames = wx.CheckBox(self,-1,"Duplicate frames to achieve framerate")
        self.padFrames.Bind(wx.EVT_CHECKBOX,self.onPadFrames)
        self.padFrames.SetValue(1)
        n=0
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
        self.outputsizer.Add(self.padFrames,(n,0))
        n+=1
        self.outputsizer.Add(self.durationLabel,(n,0))
        self.outputsizer.Add(self.duration,(n,1))        
        n+=1
        self.outputsizer.Add(self.totalFramesLabel,(n,0))
        self.outputsizer.Add(self.totalFrames,(n,1))
        n+=1
        self.outputsizer.Add(self.fpsLabel,(n,0))
        n+=1
        self.outputsizer.Add(self.padfpsLabel,(n,0))
        
        self.mainsizer.Add(self.outputstaticbox,(0,0))
        
        self.rendir=wx.TextCtrl(self,size=(350,-1))
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
        
        self.videofile=wx.TextCtrl(self,size=(350,-1))
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
            print "val=",val
            self.frames = val
            self.fps = self.frames / float(self.dur)
            print "frames per second = ",self.fps
            self.fpsLabel.SetLabel("Rendered frames:\t%.3f / second"%self.fps)
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
