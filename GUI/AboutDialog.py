#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: AboutDialog.py
 Project: BioImageXD
 Created: 22.02.2005
 Creator: KP
 Description:

 A wxPython wx.Dialog window that is used to show an about dialog. The about dialog is specified
 using HTML markup.

 Modified: 22.02.2005 KP - Created the module

 BioImageXD includes the following persons:
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 """
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"
import sys

import wx                  # This module uses the new wx namespace
import wx.html

class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About BioImageXD',)
        self.sizer=wx.GridBagSizer(5,5)
        
        self.notebook = wx.Notebook(self,-1)
        
        self.about = wx.html.HtmlWindow(self.notebook, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo:
            self.about.SetStandardFonts()
        col=self.GetBackgroundColour()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        dict={"bgcolor":bgcol}
        self.about.SetPage(aboutText%dict)
        ir = self.about.GetInternalRepresentation()
        self.about.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )
        self.notebook.AddPage(self.about,"About BioImageXD")
        
        self.licensing = wx.html.HtmlWindow(self.notebook, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo:
            self.licensing.SetStandardFonts()
        col=self.GetBackgroundColour()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        dict={"bgcolor":bgcol}
        self.licensing.SetPage(licensingText%dict)
        ir = self.licensing.GetInternalRepresentation()
        self.licensing.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )        
        self.notebook.AddPage(self.licensing,"Licensing")


        self.sizer.Add(self.notebook,(0,0))
               
        #self.staticLine=wx.StaticLine(self)
        #self.sizer.Add(self.staticLine,(1,0),flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        self.ok=wx.Button(self,-1,"Ok")
        self.ok.Bind(wx.EVT_BUTTON,self.closeWindow)
        self.ok.SetDefault()
        self.sizer.Add(self.ok,(2,0),flag=wx.ALIGN_CENTER)
      

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.SetSizeHints(self)
        self.sizer.Fit(self)
        
        self.CentreOnParent(wx.BOTH)
        
    def closeWindow(self,evt):
        self.EndModal(wx.ID_OK)

aboutText = u"""
<html>
<body bgcolor="%(bgcolor)s">
<center><h2>About BioImageXD</h2></center>

<p><b>BioImageXD</b> is a program for post-processing and visualizing
data produced by a confocal laser scanning microscope.</p>

<p>The BioImageXD project includes the following people:</p>
<p>
<table>
<tr><td><b>Dan White</b></td><td><a href="mailto:dan@chalkie.org.uk">&lt;dan@chalkie.org.uk&gt;</a></td></tr>
<tr><td><b>Kalle Pahajoki</b></td><td><a href="mailto:kalpaha@st.jyu.fi">&lt;kalpaha@st.jyu.fi&gt;</a></td></tr>
<tr><td><b>Pasi Kankaanpää</b></td><td><a href="mailto:ppkank@bytl.jyu.fi">&lt;ppkank@bytl.jyu.fi&gt;</a></td></tr>
</table>
</p>
<p><b>BioImageXD</b> is based on the work of 
<a href="http://sovellusprojekit.it.jyu.fi/selli/">Selli project</a> and the work of Heikki Uuksulainen on
Mayavi Animator.
</center>
</body>
</html>
"""

licensingText = u"""
<html>
<body bgcolor="%(bgcolor)s">
<center><h2>BioImageXD Licensing</h2></center>

<p><b>BioImageXD</b> is a based on many open source programs and libraries. All the relevant licenses
can be found in the source code under the <i>Licensing</i> directory.</p>
</body>
</html>
"""
