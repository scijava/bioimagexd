# -*- coding: iso-8859-1 -*-

"""
 Unit: HelpViewer
 Project: BioImageXD
 Created: 02.08.2005, KP
 Description:

 A widget for viewing HTML help files for the application. The code is based
 on the wxPython HtmlWindow demo.
         
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
import  os
import  sys

import  wx
import  wx.html as  html


# This shows how to catch the OnLinkClicked non-event.  (It's a virtual
# method in the C++ code...)
def opj(path):
    """Convert paths to the platform-specific separator"""
    str = apply(os.path.join, tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        str = '/' + str
    return str
    
class HelpViewer(html.HtmlWindow):
    def __init__(self, parent, id):
        html.HtmlWindow.__init__(self, parent, id,size=(640,480), style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll )
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnScroll( self, event ):
        #print 'event.GetOrientation()',event.GetOrientation()
        #print 'event.GetPosition()',event.GetPosition()
        event.Skip()

    def OnLinkClicked(self, linkinfo):
        # Virtuals in the base class have been renamed with base_ on the front.
        self.base_OnLinkClicked(linkinfo)

    def OnSetTitle(self, title):
        self.base_OnSetTitle(title)

    def OnCellMouseHover(self, cell, x, y):
        self.base_OnCellMouseHover(cell, x, y)

    def OnCellClicked(self, cell, x, y, evt):
        self.base_OnCellClicked(cell, x, y, evt)


class HelpViewerFrame(wx.Frame):
    def __init__(self, parent,**kws):
        wx.Frame.__init__(self,parent,-1,"BioImageXD",size=(640,480))
        self.page="index.html"
        if "page" in kws:
            self.page=kws["page"]
        self.panel = wx.Panel(self,-1)
        #wx.Panel.__init__(self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.CreateStatusBar()
        self.titleBase = self.GetTitle()
        self.sizer=wx.BoxSizer(wx.VERTICAL)

        self.html = HelpViewer(self.panel, -1)
        self.html.SetRelatedFrame(self, "BioImageXD" + " - %s")
        self.html.SetRelatedStatusBar(0)
        self.cwd = os.path.split(sys.argv[0])[0]
        self.printer = html.HtmlEasyPrinting()
        self.iconSize=(32,32)
        self.ctrlbox = wx.BoxSizer(wx.HORIZONTAL)
        #self.sizer.Add(self.ctrlbox)
        self.sizer.Add(self.html,1,wx.GROW)
        
        tb = self.CreateToolBar( wx.TB_HORIZONTAL
                                 | wx.NO_BORDER
                                 | wx.TB_FLAT
                                 | wx.TB_TEXT
                                 )
        tb.SetToolBitmapSize(self.iconSize)
        bmp = wx.ArtProvider_GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR, self.iconSize)
        self.BACK=wx.NewId()
        tb.AddSimpleTool(self.BACK, bmp, "Back", "Go back to previous help page")
        self.Bind(wx.EVT_TOOL, self.OnBack, id=self.BACK)

        bmp = wx.ArtProvider_GetBitmap(wx.ART_GO_TO_PARENT, wx.ART_TOOLBAR, self.iconSize)
        self.PARENT=wx.NewId()
        tb.AddSimpleTool(self.PARENT, bmp, "Up", "Go to the index page")
        self.Bind(wx.EVT_TOOL, self.OnShowDefault, id=self.PARENT)
        
        bmp = wx.ArtProvider_GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, self.iconSize)
        self.FORWARD=wx.NewId()
        tb.AddSimpleTool(self.FORWARD, bmp, "Forward", "Go forward")
        self.Bind(wx.EVT_TOOL, self.OnForward, id=self.FORWARD)
        
        bmp = wx.ArtProvider_GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR, self.iconSize)
        self.PRINT=wx.NewId()
        tb.AddSimpleTool(self.PRINT, bmp, "Print", "Print this page")
        self.Bind(wx.EVT_TOOL, self.OnPrint, id=self.PRINT)
        tb.Realize()
        
        self.panel.SetSizer(self.sizer)
        self.panel.SetAutoLayout(True)
        self.sizer.Fit(self.panel)
        # A button with this ID is created on the widget test page.

        self.OnShowDefault(None)


    def OnShowDefault(self, event):
        if event:self.page="index.html"
        name = os.path.join(self.cwd, opj('Help/%s'%self.page))
        self.html.LoadPage(name)

    def OnLoadFile(self, event):
        dlg = wx.FileDialog(self, wildcard = '*.htm*', style=wx.OPEN)

        if dlg.ShowModal():
            path = dlg.GetPath()
            self.html.LoadPage(path)

        dlg.Destroy()

    def OnBack(self, event):
        if not self.html.HistoryBack():
            wx.MessageBox("No more items in history!")


    def OnForward(self, event):
        if not self.html.HistoryForward():
            wx.MessageBox("No more items in history!")


    def OnPrint(self, event):
        self.printer.GetPrintData().SetPaperId(wx.PAPER_LETTER)
        self.printer.PrintFile(self.html.GetOpenedPage())
