#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: AboutDialog.py
 Project: BioImageXD
 Created: 22.02.2005, KP
 Description:

 A wxPython wx.Dialog window that is used to show an about dialog. The about dialog is specified
 using HTML markup.

 Modified: 22.02.2005 KP - Created the module
 
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
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"
import sys

import wx                  # This module uses the new wx namespace
import wx.html
import  wx.lib.scrolledpanel as scrolled

class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About BioImageXD',)
        self.sizer=wx.GridBagSizer(5,5)
        x,y=(600,400)
        
        self.notebook = wx.Notebook(self,-1)
        
        self.about = wx.html.HtmlWindow(self.notebook, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo:
            self.about.SetStandardFonts()
        col=self.GetBackgroundColour()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        dict={"bgcolor":bgcol}
        self.about.SetPage(aboutText%dict)
        ir = self.about.GetInternalRepresentation()
        
        #self.about.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )
        self.about.SetSize( (x,y) )
        self.notebook.AddPage(self.about,"About BioImageXD")
        
        #self.gplPanel = scrolled.ScrolledPanel(self.notebook,-1,size=(x,y))
        #box= wx.BoxSizer(wx.VERTICAL)
        self.gpl = wx.html.HtmlWindow(self.notebook,-1,size=(420,-1))
        if "gtk2" in wx.PlatformInfo:
            self.gpl.SetStandardFonts()
        #box.Add(self.gpl)
        #self.gplPanel.SetSizer(box)
        #self.gplPanel.SetAutoLayout(1)
        #self.gplPanel.SetupScrolling()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        dict={"bgcolor":bgcol}
        self.gpl.SetPage(gplText%dict)
        self.gpl.SetSize( (x,y) )        
        self.notebook.AddPage(self.gpl,"BioImageXD License")

        
        #self.licensingPanel = scrolled.ScrolledPanel(self.notebook,-1,size=(420,200))
        #box=wx.BoxSizer(wx.VERTICAL)
        self.licensing = wx.html.HtmlWindow(self.notebook, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo:
            self.licensing.SetStandardFonts()
        #box.Add(self.licensing)
        #self.licensingPanel.SetSizer(box)
        #self.licensingPanel.SetAutoLayout(1)
        #self.licensingPanel.SetupScrolling()
        col=self.GetBackgroundColour()
        bgcol="#%2x%2x%2x"%(col.Red(),col.Green(),col.Blue())
        dict={"bgcolor":bgcol}
        self.licensing.SetPage(licensingText%dict)
        
        self.licensing.SetSize( (x,y) )        
        self.notebook.AddPage(self.licensing,"Libraries")


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
<center><img src="Icons/logo_medium.jpg"></center><br>
<p><b>BioImageXD</b> is a program for post-processing and visualizing
data produced by a confocal laser scanning microscope.</p>

<h2>The BioImageXD Project</h2>
<p><b>The main development team</b></p><p>
Pasi Kankaanp��<br>
Kalle Pahajoki<br>
Varpu Marjom�ki<br>
Jyrki Heino<br>
Daniel White<br>
</p>
<p>
<b>Former member of the main development team (and the developer of the Zeiss LSM file format reader and the rendering animator):</b>
</p><p>
Heikki Uuksulainen
</p>
<p>
<b>BioImageXD is largely based on the work of the Selli project, which included the following people:</b></p><p>
Juha Hyyti�inen<br>
Jaakko M�ntymaa<br>
Kalle Pahajoki<br>
Jukka Varsaluoma<br>
</p><p>
<b>The following people have significantly contributed to the development of BioImageXD:</b></p><p>
Jorma Virtanen<br>
</p><p>
<b>The following companies have supported the development of BioImageXD:</b></p><p>
N / A
</p>
</body>
</html>
"""

gplText = u"""
<html>
<body bgcolor="%(bgcolor)s">
<center><h2>BioImageXD License</h2></center>

<!--<p><b>BioImageXD</b> is licensed under the General Public License.</p>-->
<p>
BioImageXD will be licensed under the General Public License.
This version, however, is NOT yet a public release as specified by that license. 
This version is incomplete and intended for private testing purposes only. 
You must NOT modify or distribute this program, the source code or parts of it to anyone. 
You are also expected to keep detailed information of this software confidential, and give 
feedback only to the developers whose contact information you have been given. Use of this version
for scientific work is not recommended, because some features and functions have not yet been confirmed to 
perform properly and correctly.
</p>
<hr>
<p><h2>GNU GENERAL PUBLIC LICENSE</h2>
</p><p>
Version 2, June 1991</p><p>
Copyright (C) 1989, 1991 Free Software Foundation, Inc.
59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
</p><p>
<h3>Preamble</h3>
</p><p>
  The licenses for most software are designed to take away your
freedom to share and change it.  By contrast, the GNU General Public
License is intended to guarantee your freedom to share and change free
software--to make sure the software is free for all its users.  This
General Public License applies to most of the Free Software
Foundation's software and to any other program whose authors commit to
using it.  (Some other Free Software Foundation software is covered by
the GNU Library General Public License instead.)  You can apply it to
your programs, too.
</p><p>
  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
this service if you wish), that you receive source code or can get it
if you want it, that you can change the software or use pieces of it
in new free programs; and that you know you can do these things.
</p><p>
  To protect your rights, we need to make restrictions that forbid
anyone to deny you these rights or to ask you to surrender the rights.
These restrictions translate to certain responsibilities for you if you
distribute copies of the software, or if you modify it.
</p><p>
  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must give the recipients all the rights that
you have.  You must make sure that they, too, receive or can get the
source code.  And you must show them these terms so they know their
rights.
</p><p>
  We protect your rights with two steps: (1) copyright the software, and
(2) offer you this license which gives you legal permission to copy,
distribute and/or modify the software.
</p><p>
  Also, for each author's protection and ours, we want to make certain
that everyone understands that there is no warranty for this free
software.  If the software is modified by someone else and passed on, we
want its recipients to know that what they have is not the original, so
that any problems introduced by others will not reflect on the original
authors' reputations.
</p><p>
  Finally, any free program is threatened constantly by software
patents.  We wish to avoid the danger that redistributors of a free
program will individually obtain patent licenses, in effect making the
program proprietary.  To prevent this, we have made it clear that any
patent must be licensed for everyone's free use or not licensed at all.
</p><p>
  The precise terms and conditions for copying, distribution and
modification follow.
</p><p>

<h3>GNU GENERAL PUBLIC LICENSE</h3>
<h3>TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION</h3>
</p><p>
  0. This License applies to any program or other work which contains
a notice placed by the copyright holder saying it may be distributed
under the terms of this General Public License.  The "Program", below,
refers to any such program or work, and a "work based on the Program"
means either the Program or any derivative work under copyright law:
that is to say, a work containing the Program or a portion of it,
either verbatim or with modifications and/or translated into another
language.  (Hereinafter, translation is included without limitation in
the term "modification".)  Each licensee is addressed as "you".
</p><p>
Activities other than copying, distribution and modification are not
covered by this License; they are outside its scope.  The act of
running the Program is not restricted, and the output from the Program
is covered only if its contents constitute a work based on the
Program (independent of having been made by running the Program).
Whether that is true depends on what the Program does.
</p><p>
  1. You may copy and distribute verbatim copies of the Program's
source code as you receive it, in any medium, provided that you
conspicuously and appropriately publish on each copy an appropriate
copyright notice and disclaimer of warranty; keep intact all the
notices that refer to this License and to the absence of any warranty;
and give any other recipients of the Program a copy of this License
along with the Program.
</p><p>
You may charge a fee for the physical act of transferring a copy, and
you may at your option offer warranty protection in exchange for a fee.
</p><p>
  2. You may modify your copy or copies of the Program or any portion
of it, thus forming a work based on the Program, and copy and
distribute such modifications or work under the terms of Section 1
above, provided that you also meet all of these conditions:
</p><p>
    a) You must cause the modified files to carry prominent notices
    stating that you changed the files and the date of any change.
</p><p>
    b) You must cause any work that you distribute or publish, that in
    whole or in part contains or is derived from the Program or any
    part thereof, to be licensed as a whole at no charge to all third
    parties under the terms of this License.
</p><p>
    c) If the modified program normally reads commands interactively
    when run, you must cause it, when started running for such
    interactive use in the most ordinary way, to print or display an
    announcement including an appropriate copyright notice and a
    notice that there is no warranty (or else, saying that you provide
    a warranty) and that users may redistribute the program under
    these conditions, and telling the user how to view a copy of this
    License.  (Exception: if the Program itself is interactive but
    does not normally print such an announcement, your work based on
    the Program is not required to print an announcement.)
</p><p>
These requirements apply to the modified work as a whole.  If
identifiable sections of that work are not derived from the Program,
and can be reasonably considered independent and separate works in
themselves, then this License, and its terms, do not apply to those
sections when you distribute them as separate works.  But when you
distribute the same sections as part of a whole which is a work based
on the Program, the distribution of the whole must be on the terms of
this License, whose permissions for other licensees extend to the
entire whole, and thus to each and every part regardless of who wrote it.
</p><p>
Thus, it is not the intent of this section to claim rights or contest
your rights to work written entirely by you; rather, the intent is to
exercise the right to control the distribution of derivative or
collective works based on the Program.
</p><p>
In addition, mere aggregation of another work not based on the Program
with the Program (or with a work based on the Program) on a volume of
a storage or distribution medium does not bring the other work under
the scope of this License.
</p><p>
  3. You may copy and distribute the Program (or a work based on it,
under Section 2) in object code or executable form under the terms of
Sections 1 and 2 above provided that you also do one of the following:
</p><p>
    a) Accompany it with the complete corresponding machine-readable
    source code, which must be distributed under the terms of Sections
    1 and 2 above on a medium customarily used for software interchange; or,
</p><p>
    b) Accompany it with a written offer, valid for at least three
    years, to give any third party, for a charge no more than your
    cost of physically performing source distribution, a complete
    machine-readable copy of the corresponding source code, to be
    distributed under the terms of Sections 1 and 2 above on a medium
    customarily used for software interchange; or,
</p><p>
    c) Accompany it with the information you received as to the offer
    to distribute corresponding source code.  (This alternative is
    allowed only for noncommercial distribution and only if you
    received the program in object code or executable form with such
    an offer, in accord with Subsection b above.)
</p><p>
The source code for a work means the preferred form of the work for
making modifications to it.  For an executable work, complete source
code means all the source code for all modules it contains, plus any
associated interface definition files, plus the scripts used to
control compilation and installation of the executable.  However, as a
special exception, the source code distributed need not include
anything that is normally distributed (in either source or binary
form) with the major components (compiler, kernel, and so on) of the
operating system on which the executable runs, unless that component
itself accompanies the executable.
</p><p>
If distribution of executable or object code is made by offering
access to copy from a designated place, then offering equivalent
access to copy the source code from the same place counts as
distribution of the source code, even though third parties are not
compelled to copy the source along with the object code.
</p><p>
  4. You may not copy, modify, sublicense, or distribute the Program
except as expressly provided under this License.  Any attempt
otherwise to copy, modify, sublicense or distribute the Program is
void, and will automatically terminate your rights under this License.
However, parties who have received copies, or rights, from you under
this License will not have their licenses terminated so long as such
parties remain in full compliance.
</p><p>
  5. You are not required to accept this License, since you have not
signed it.  However, nothing else grants you permission to modify or
distribute the Program or its derivative works.  These actions are
prohibited by law if you do not accept this License.  Therefore, by
modifying or distributing the Program (or any work based on the
Program), you indicate your acceptance of this License to do so, and
all its terms and conditions for copying, distributing or modifying
the Program or works based on it.
</p><p>
  6. Each time you redistribute the Program (or any work based on the
Program), the recipient automatically receives a license from the
original licensor to copy, distribute or modify the Program subject to
these terms and conditions.  You may not impose any further
restrictions on the recipients' exercise of the rights granted herein.
You are not responsible for enforcing compliance by third parties to
this License.
</p><p>
  7. If, as a consequence of a court judgment or allegation of patent
infringement or for any other reason (not limited to patent issues),
conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot
distribute so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you
may not distribute the Program at all.  For example, if a patent
license would not permit royalty-free redistribution of the Program by
all those who receive copies directly or indirectly through you, then
the only way you could satisfy both it and this License would be to
refrain entirely from distribution of the Program.
</p><p>
If any portion of this section is held invalid or unenforceable under
any particular circumstance, the balance of the section is intended to
apply and the section as a whole is intended to apply in other
circumstances.
</p><p>
It is not the purpose of this section to induce you to infringe any
patents or other property right claims or to contest validity of any
such claims; this section has the sole purpose of protecting the
integrity of the free software distribution system, which is
implemented by public license practices.  Many people have made
generous contributions to the wide range of software distributed
through that system in reliance on consistent application of that
system; it is up to the author/donor to decide if he or she is willing
to distribute software through any other system and a licensee cannot
impose that choice.
</p><p>
This section is intended to make thoroughly clear what is believed to
be a consequence of the rest of this License.
</p><p>
  8. If the distribution and/or use of the Program is restricted in
certain countries either by patents or by copyrighted interfaces, the
original copyright holder who places the Program under this License
may add an explicit geographical distribution limitation excluding
those countries, so that distribution is permitted only in or among
countries not thus excluded.  In such case, this License incorporates
the limitation as if written in the body of this License.
</p><p>
  9. The Free Software Foundation may publish revised and/or new versions
of the General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.
</p><p>
Each version is given a distinguishing version number.  If the Program
specifies a version number of this License which applies to it and "any
later version", you have the option of following the terms and conditions
either of that version or of any later version published by the Free
Software Foundation.  If the Program does not specify a version number of
this License, you may choose any version ever published by the Free Software
Foundation.
</p><p>
  10. If you wish to incorporate parts of the Program into other free
programs whose distribution conditions are different, write to the author
to ask for permission.  For software which is copyrighted by the Free
Software Foundation, write to the Free Software Foundation; we sometimes
make exceptions for this.  Our decision will be guided by the two goals
of preserving the free status of all derivatives of our free software and
of promoting the sharing and reuse of software generally.
</p><p>
<h3>NO WARRANTY</h3>
</p><p>
  11. BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
REPAIR OR CORRECTION.
</p><p>
  12. IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
POSSIBILITY OF SUCH DAMAGES.
</p>
</body>
</html>
"""

licensingText = u"""
<html>
<body bgcolor="%(bgcolor)s">
<center><h2>Licensing of Libraries</h2></center>

<p><b>BioImageXD</b> is a based on many open source programs and libraries. The licenses of these programs are
presented here. You can also find the full licenses of each program or library at
at the <i>Licensing</i> directory.</p>
<p>
<ul>
<li><a href="#python">Python</a></li>
<li><a href="#vtk">The Visualization Toolkit</a></li>
<li><a href="#mayavi">MayaVi</a></li>
</ul>
</p>
<hr>
<p><a name="python"><h2>Python</h2></a>
The license presented here is for Python version 2.4. For licenses of older versions of Python,
see the file <i>Python-License</i> file in directory <i>Licensing</i>.
</p>
<p>
<b>PSF LICENSE AGREEMENT FOR PYTHON 2.4<b><br>
</p>
<p>
1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using Python 2.4 software in source or binary form and its
associated documentation.
</p><p>
2. Subject to the terms and conditions of this License Agreement, PSF
hereby grants Licensee a nonexclusive, royalty-free, world-wide
license to reproduce, analyze, test, perform and/or display publicly,
prepare derivative works, distribute, and otherwise use Python 2.4
alone or in any derivative version, provided, however, that PSF's
License Agreement and PSF's notice of copyright, i.e., "Copyright (c)
2001, 2002, 2003, 2004 Python Software Foundation; All Rights Reserved"
are retained in Python 2.4 alone or in any derivative version prepared
by Licensee.
</p><p>
3. In the event Licensee prepares a derivative work that is based on
or incorporates Python 2.4 or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python 2.4.
</p><p>
4. PSF is making Python 2.4 available to Licensee on an "AS IS"
basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON 2.4 WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.
</p><p>
5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
2.4 FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 2.4,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
</p><p>
6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.
</p><p>
7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between PSF and
Licensee.  This License Agreement does not grant permission to use PSF
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.
</p><p>
8. By copying, installing or otherwise using Python 2.4, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.
</p>
<hr>
<p>
<p><a name="vtk"><h2>The Visualization Toolkit</h2></a>
</p>
<p>
This is an open-source copyright as follows:</p>
Copyright (c) 1993-2002 Ken Martin, Will Schroeder, Bill Lorensen<br>
 All rights reserved.</p><p>
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
</p><p>
* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
</p><p>
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
</p><p>
* Neither name of Ken Martin, Will Schroeder, or Bill Lorensen nor the names of any contributors may be used to endorse or promote products derived from this software without specific prior written permission.
</p><p>
* Modified source versions must be plainly marked as such, and must not be misrepresented as being the original software.
</p><p>

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
</p>
<hr>
<p>
<p><a name="mayavi"><h2>MayaVi</h2></a>
</p>
<p>
Copyright (c) 2000-2005, Prabhu Ramachandran.<br>
All rights reserved.</p>
<p>
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
</p><p>
<ol>
<li>
Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.</li>
<li>
Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.</li>
<li>
Neither the name of the author nor the names of any contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.</li>
</ol>
</p><p>
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
</p>
</body>
</html>
"""
