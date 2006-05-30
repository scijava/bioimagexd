#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: ManipulationFilterGUI
 Project: BioImageXD
 Created: 15.04.2006, KP
 Description:

 A module containing the classes for building a GUI for all the manipulation filters
                            
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
__version__ = "$Revision: 1.42 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"

import wx
import types
import Histogram
import wx.lib.buttons as buttons
import messenger

RADIO_CHOICE="RADIO_CHOICE"
THRESHOLD="THRESHOLD"
PIXEL="PIXEL"
PIXELS="PIXELS"

class GUIBuilder(wx.Panel):
    """
    Class: GUIBuilder
    Created: 13.04.2006, KP
    Description: A GUI builder for the manipulation filters
    """      
    def __init__(self,parent,myfilter):
        """
        Method: __init__()
        Created: 13.04.2007, KP
        Description: Initialization
        """ 
        wx.Panel.__init__(self,parent,-1)
        self.filter = myfilter
        self.sizer = wx.GridBagSizer()
        # store the histograms so that the filters can access them if they need
        # to
        self.histograms=[]
        
        self.buildGUI(myfilter)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        
    def buildGUI(self,currentFilter):
        """
        Method: buildGUI
        Created: 13.04.2007, KP
        Description: Build the GUI for a given filter
        """ 
        self.currentFilter = currentFilter
        parameters = currentFilter.getParameters()
        gy=0
            
        sbox=wx.StaticBox(self,-1,currentFilter.getName())
        sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)
        self.sizer.Add(sboxsizer,(0,0))
        sizer=wx.GridBagSizer()
        sboxsizer.Add(sizer)
        
        chlSel = self.buildChannelSelection()
        
        sizer.Add(chlSel,(gy,0),span=(1,2))
        
        gy+=1
        
        for param in parameters:
            # If it's a list with header name and items
            if type(param) == types.ListType:
                sboxname,items = param
                itemsizer = wx.GridBagSizer()

                y=0                
                skip=0
                for n,item in enumerate(items):
                    if skip:
                        skip-=1
                        continue
                    if type(item) != types.TupleType:
                        self.processItem(currentFilter,itemsizer,item,x=0,y=y)
                        y+=1
                    else: # Items that are contained in a tuple ask to be grouped
                          # together
                        print "Handling ",item,"as a group"
                        if currentFilter.getType(item[0]) == RADIO_CHOICE:
                            # Indicate that we need to skip next item
                            skip=1
                            print item
                            print "Creating radio choice"
                            if items[n+1][0] == "cols":
                                majordim=wx.RA_SPECIFY_COLS
                            else:
                                majordim=wx.RA_SPECIFY_ROWS
                            
                            choices=[]
                            for i in item:
                                d = currentFilter.getDesc(i)
                                choices.append(d)
                            box = wx.RadioBox(self,-1,sboxname,choices=choices,
                            majorDimension = items[n+1][1],style=majordim)
                            func=lambda evt,its=item,f=currentFilter:self.onSelectRadioBox(evt,its,f)
                            box.Bind(wx.EVT_RADIOBOX,func)
                            sboxname=""
                            itemsizer.Add(box,(0,0))
                        elif currentFilter.getType(item[0]) == PIXEL:
                            print "Creating pixel selection"
                            lbl = wx.StaticText(self,-1,"(%d,%d,%d)"%(0,0,0),size=(80,-1))
                            btn = wx.Button(self,-1,"Set seed")
                            def f(l):
                                l.selectPixel=1
                            func=lambda evt,l=lbl:f(l)
                            btn.Bind(wx.EVT_BUTTON,func)
                            box=wx.BoxSizer(wx.HORIZONTAL)
                            box.Add(lbl)
                            box.Add(btn)
                            itemsizer.Add(box,(0,0))
                            func = lambda obj,evt,rx,ry,rz,r,g,b,alpha,currentCt,its=item,f=currentFilter:self.onSetPixel(obj,evt,rx,ry,rz,r,g,b,alpha,currentCt,its,f,lbl)
                            messenger.connect(None,"get_voxel_at",func)
                            
                        elif currentFilter.getType(item[0]) == PIXELS:
                            print "Creating multiple pixels selection"
                            pixelsizer = wx.GridBagSizer()
                            seedbox = wx.ListBox(self,-1,size=(100,150))
                            pixelsizer.Add(seedbox,(0,0),span=(2,1))
                            
                            addbtn = wx.Button(self,-1,"Add seed")
                            def f(l):
                                l.selectPixel=1
                            func=lambda evt,l=seedbox:f(l)
                            addbtn.Bind(wx.EVT_BUTTON,func)
                            pixelsizer.Add(addbtn,(0,1))
                            print "ITEM=",item
                            rmbtn = wx.Button(self,-1,"Remove")
                            seedbox.itemName = item
                            func=lambda evt,its=item,f=currentFilter:self.removeSeed(seedbox,f)
                            rmbtn.Bind(wx.EVT_BUTTON,func)
                            pixelsizer.Add(rmbtn,(1,1))
                            
                            func = lambda obj,evt,rx,ry,rz,r,g,b,alpha,currentCt,its=item,f=currentFilter:self.onAddPixel(obj,evt,rx,ry,rz,r,g,b,alpha,currentCt,its,f,seedbox)
                            messenger.connect(None,"get_voxel_at",func)
                            itemsizer.Add(pixelsizer,(0,0))
                            
                        elif currentFilter.getType(item[0]) == THRESHOLD:
                            print "Creating threshold selection"
                            histogram = Histogram.Histogram(self)
                            self.histograms.append(histogram)
                            func=lambda evt,its=item,f=currentFilter:self.onSetThreshold(evt,its,f)
                            histogram.Bind(Histogram.EVT_SET_THRESHOLD,func)
                            
                            histogram.setThresholdMode(1)
                            du=self.filter.getDataUnit().getSourceDataUnits()[0]
                            histogram.setDataUnit(du,noupdate=1)

                            itemsizer.Add(histogram,(0,0))
                        else:
                            groupsizer=wx.GridBagSizer()
                            x=0
                            for it in item:
                                self.processItem(currentFilter, groupsizer, it, x=x,y=0)
                                x+=1
                            span=(1,x)
                            itemsizer.Add(groupsizer,(y,0),span=span)
                            # If the name is an empty string, don't create a static box around
                
                # the items
                if sboxname:
                    sbox = wx.StaticBox(self,-1,sboxname)
                    sboxsizer=wx.StaticBoxSizer(sbox,wx.VERTICAL)
                
                    sizer.Add(sboxsizer,(gy,0),flag=wx.EXPAND)
                    sboxsizer.Add(itemsizer)
                else:
                    sizer.Add(itemsizer,(gy,0),flag=wx.EXPAND)            
            # If it's just a header name
            elif type(param) == types.StringType:
                lbl = wx.StaticText(self,-1,param)
                sizer.Add(lbl,(gy,0))
            gy+=1
        
    def buildChannelSelection(self):
        """
        Method: buildChannelSelection
        Created: 17.04.2007, KP
        Description: Build a GUI for selecting the source channels
        """                     
        chmin,chmax = self.currentFilter.getNumberOfInputs()
        sizer = wx.GridBagSizer()
        y=0
        choices=["Input from filter stack"]
        for i,dataunit in enumerate(self.currentFilter.dataUnit.getSourceDataUnits()):
            choices.append(dataunit.getName())
        
        
        for i in range(1,chmax+1):
            lbl = wx.StaticText(self,-1,self.currentFilter.getInputName(i))
            sizer.Add(lbl,(y,0))
            chlChoice = wx.Choice(self,-1,choices=choices)
            sizer.Add(chlChoice,(y,1))
            chlChoice.SetSelection(0)
            func=lambda evt,f=self.currentFilter,n=i: self.onSetInputChannel(f,n,evt)
            chlChoice.Bind(wx.EVT_CHOICE,func)

            y+=1
        return sizer
        
    def onSetInputChannel(self,currentFilter,inputNum,evt):
        """
        Method: onSetInputChannel
        Created: 17.04.2007, KP
        Description: Set the input channel number #inputNum
        """              
        n = evt.GetSelection()
        self.currentFilter.setInputChannel(inputNum,n)
        
    def processItem(self,currentFilter, itemsizer, item, x,y):
        """
        Method: processItem
        Created: 15.04.2007, KP
        Description: Build the GUI related to one specific item
        """              
        desc = currentFilter.getDesc(item)
        
        itemType = currentFilter.getType(item)
        if itemType not in [types.BooleanType]:
            lbl = wx.StaticText(self,-1,desc)
        else:
            lbl = None
        defaultValue = currentFilter.getDefaultValue(item)
        
        if itemType in [types.IntType,types.FloatType]:
            input = self.createNumberInput(currentFilter, item, itemType, defaultValue, desc)
        elif itemType == types.BooleanType:
            input = self.createBooleanInput(currentFilter, item, itemType, defaultValue, desc)
        else:
            raise "Unrecognized input type: %s"%str(itemType)
        txt = currentFilter.getLongDesc(item)
        if txt:
            input.SetHelpText(txt)

        x2=x
        if lbl:
            itemsizer.Add(lbl,(y,x))
            x2+=1
        itemsizer.Add(input,(y,x2))
    
        
                        
    def createNumberInput(self,currentFilter,item,itemType,defaultValue,label = ""):
        """
        Method: createIntInput
        Created: 15.04.2007, KP
        Description: Return the input for int type
        """        
        input = wx.TextCtrl(self,-1,str(defaultValue))
        valid=lambda evt,f=currentFilter,p=item,t=itemType,i=input:self.validateAndPassOn(evt,i,p,itemType,f)
        input.Bind(wx.EVT_TEXT,valid)
        return input
                    
    def createBooleanInput(self,currentFilter,item,itemType,defaultValue, label = ""):
        """
        Method: createBooleanInput
        Created: 15.04.2007, KP
        Description: Return the input for boolean type
        """        
        input = wx.CheckBox(self,-1,label)
        input.SetValue(defaultValue)
        valid=lambda evt,f=currentFilter,p=item,t=itemType,i=input:self.validateAndPassOn(evt,i,p,itemType,f)
        input.Bind(wx.EVT_CHECKBOX,valid)
        return input
        
    def removeSeed(self,listbox,currFilter):
        """
        Method: removeSeed
        Created: 29.05.2007, KP
        Description: Remove a seed from filter
        """         
        item=listbox.itemName
        print "item in removeSeed=",item
        n = listbox.GetSelection()
        if n != wx.NOT_FOUND:
            s = listbox.GetString(n)
            seedpt = eval(s)
            listbox.Delete(n)
            
        print "Getting parameter",item[0]
        seeds = currFilter.getParameter(item[0])   
        print "Removing ",seedpt,"from ",seeds
        seeds.remove(seedpt)
        currFilter.setParameter(item[0],seeds)

    def onAddPixel(self,obj,evt,rx,ry,rz,r,g,b,alpha,ctf,item,currFilter,listbox):
        """
        Method: onAddPixel
        Created: 29.05.2007, KP
        Description: Add a value to the pixel listbox
        """             
        #print "Set pixel",obj,evt,rx,ry,rz,r,g,b,alpha,item,currFilter
        print "item=",item
        if listbox.selectPixel:
            seeds = currFilter.getParameter(item[0])
            seeds.append((rx,ry,rz))
            print "Settng parameter",item,"to",seeds            
            
            currFilter.setParameter(item[0],seeds)
            listbox.Append("(%d, %d, %d)"%(rx, ry, rz))            
            listbox.selectPixel = 0

            
    def onSetPixel(self,obj,evt,rx,ry,rz,r,g,b,alpha,ctf,item,currFilter,valuelbl):
        """
        Method: onSetPixel
        Created: 26.05.2007, KP
        Description: Set the value of the pixel label
        """             
        #print "Set pixel",obj,evt,rx,ry,rz,r,g,b,alpha,item,currFilter
        if valuelbl.selectPixel:
            print "Settng parameter",item,"to",rx,ry,rz
            
            currFilter.setParameter(item[0],(rx,ry,rz))
            valuelbl.SetLabel("(%d,%d,%d)"%(rx,ry,rz))
            valuelbl.selectPixel = 0
        
            
    def onSetThreshold(self,evt,items,currentFilter):
        """
        Method: onSelectRadioBox
        Created: 15.04.2007, KP
        Description: Process an event from a radio box
        """      
        thresholds = evt.getThresholds()
        for i,item in enumerate(items):
            currentFilter.setParameter(item,thresholds[i])            
            
    def onSelectRadioBox(self,evt,items,currentFilter):
        """
        Method: onSelectRadioBox
        Created: 15.04.2007, KP
        Description: Process an event from a radio box
        """      
        sel = evt.GetSelection()
        
        for i,item in enumerate(items):
            flag=(i==sel)
            currentFilter.setParameter(item,flag)
        
    def validateAndPassOn(self,event,input,parameter,itemType,currentFilter):
        """
        Method: buildGUI
        Created: 13.04.2007, KP
        Description: Build the GUI for a given filter
        """
        if itemType == types.IntType:
            conv=int
        elif itemType == types.FloatType:
            conv=float
        elif itemType == types.BooleanType:
            conv = bool
        try:
            value=conv(input.GetValue())
        except:
            return
        currentFilter.setParameter(parameter,value)
