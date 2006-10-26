# -*- coding: iso-8859-1 -*-
"""
 Unit: ChannelListBox
 Project: BioImageXD
 Created: 26.07.2005, KP
 Description:

 A HTML listbox that shows information about each dataset and allows
 the user to select one.

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
__author__ = "BioImageXD Project <http://www.bioimagexd.org>"
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 14:36:20 $"

import wx
import os.path
import messenger
import base64
import StringIO

class ChannelListBox(wx.HtmlListBox):
    def __init__(self,parent,**kws):
        """
        Method: __init__(parent,kws)
        Created: 26.07.2005, KP
        Description: Initialization
        """
        wx.HtmlListBox.__init__(self,parent,-1,**kws)
        self.Bind(wx.EVT_LISTBOX,self.onSelectItem)
        self.dataUnit = None
        self.previews={}
        self.SetItemCount(0)
        self.units=[]
        
    def onSelectItem(self,event):
        """
        Method: onSelectItem
        Created: 26.07.2005, KP
        Description: Callback called when a user selects a channel in this listbox
        """
        item=self.GetSelection()
        messenger.send(None,"channel_selected",item)
        
        
    def setDataUnit(self,dataunit):
        """
        Method: setDataUnit()
        Created: 26.07.2005, KP
        Description: Set the dataunit to be listed
        """
        self.dataUnit=dataunit
        try:
            units=self.dataUnit.getSourceDataUnits()
        except:
            units = [self.dataUnit]
        self.units=[]
        for unit in units:
            name=unit.getName()
            filename="(no file)"
            if hasattr(unit,"dataSource"):
                filename=unit.dataSource.getFileName()
                filename=os.path.basename(filename)
            x,y,z=unit.getDimensions()
            dims="%d x %d x %d"%(x,y,z)
            ctf = unit.getColorTransferFunction()
            if ctf:
                val=[0,0,0]
                ctf.GetColor(255,val)
                r,g,b=val
                r*=255
                g*=255
                b*=255
                color="#%.2x%.2x%.2x"%(r,g,b)
            else:
                color="#000000"
            self.units.append((color,name,filename,dims))
            
    def setPreview(self,n,image):
        """
        Method: setPreview(n,image)
        Created: 26.07.2005, KP
        Description: Set the preview of a given channel to the given wxImage
        """    
        if not n in self.previews:
            #s=wx.StringOutputStream()
            #image.SaveMimeFile(s,"image/png")
            self.previews[n]=image
            pngdata=self.previews[n]
            wx.FileSystem_AddHandler(wx.MemoryFSHandler())
            wx.MemoryFSHandler_AddFile("%d.png"%(n), pngdata)
        self.SetItemCount(n+1)
            
    def __del__(self):
        """
        Method: __del__
        Created: 27.07.2005, KP
        Description: Destructor
        """        
        for i in self.previews.keys():
            wx.MemoryFSHandler_RemoveFile("%d.png"%i)
        
    def OnGetItem(self, n):
        """
        Method: OnGetItem
        Created: 26.07.2005, KP
        Description: Return the HTML code for given item
        """        
        if len(self.units)<=n:return ""
        data=self.units[n]
        
        #print "data=",data
        return """<table>
<tr><td valign="top">
<img align="left" src="memory:%d.png" width="64" height="64"></td>
<td valign="top"><font color="%s"><b>%s</font></b><br>
<font size="-1">%s</font><br>
<font color="#808080" size="-1">%s</font></td></tr>
</table>
"""%(n,data[0],data[1],data[2],data[3])
