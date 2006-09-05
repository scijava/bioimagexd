# -*- coding: iso-8859-1 -*-

"""
 Unit: ScriptEditor
 Project: BioImageXD
 Created: 13.02.2006, KP
 Description:

 A module containing a script editor for scripting BioImageXD:
 
 Copyright (C) 2006  BioImageXD Project
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
__version__ = "$Revision: 1.21 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"

import wx
import  wx.lib.editor    as  editor
import  wx.py   as  py
import Logging
import inspect
import os
import messenger
import Dialogs
import scripting as bxd
import re
import types
import MenuManager
import StringIO
import imp
import tempfile

intro="""Welcome to BioImageXD Script Editor"""

class ScriptEditor(editor.Editor):
    """

    Created: 13.02.2006, KP
    Description: A class that implements a script editor for BioImageXD
    """ 
    def __init__(self,parent):
        """
        Method: __init__
        Created: 13.02.2006, KP
        Description: Initialize the editor component of script editor
        """    
        editor.Editor.__init__(self,parent,-1,style=wx.SUNKEN_BORDER)
        self.imports=[]
        messenger.connect(None,"record_code",self.onRecordCode)
        self.code=[]
    
    def onRecordCode(self,obj,evt,code, imports):
        """
        Method: onRecordCode()
        Created: 13.02.2006, KP
        Description: Record a piece of code to the script
        """     
        text=self.code
        for i in imports:
            if i not in self.imports:
                self.imports.append(i.strip())
                
        lines=code.split("\n")
        text+=lines
        self.code=text
        imports=[]
        for i in self.imports:
            if type(i)==types.TupleType:
                m,f=i
                imports.append("from %s import %s"%(m,f))
            else:
                imports.append("import %s"%i)
        
        self.SetText(imports+[]+text)
        
        
    def setScript(self,lines,imports):
        """
        Created: 13.02.2006, KP
        Description: Sets the script in the editor to the given list of lines. Also sets the imports required for the current script to work
        """        
        self.code = lines
        self.imports = imports
        imports=[]
        for i in self.imports:
            if type(i)==types.TupleType:
                m,f=i
                imports.append("from %s import %s"%(m,f))
            else:
                imports.append("import %s"%i)
        
        
        self.SetText(imports+[]+lines)
        
class ScriptEditorFrame(wx.Frame):
    """
    Created: 13.02.2006, KP
    Description: A class that implements a script editor for BioImageXD
    """ 
    def __init__(self,parent):
        """
        Method: __init__
        Created: 13.02.2006, KP
        Description: Initialize the script editor frame
        """    
        self.parent = parent
        wx.Frame.__init__(self,parent,-1,"BioImageXD Script Editor",size=(800,600))
        self.splitter = wx.SplitterWindow(self,-1,style = wx.SP_LIVE_UPDATE)
        
        self.editor = ScriptEditor(self.splitter)
        self.shell = py.shell.Shell(self.splitter, -1, introText=intro)
        
        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitHorizontally(self.editor, self.shell, -100)

        self.createMenubar()
        self.createToolbar()
        
        self.Layout()
        
    def createMenubar(self):
        """
        Created: 13.02.2006, KP
        Description: Creates the menubar for the script editor
        """
        self.menu = wx.MenuBar()
        self.SetMenuBar(self.menu)
        
        self.wc = "BioImageXD Script (*.bxs)|*.bxs;*.BXS;"
        
        self.file = wx.Menu()
        self.script = wx.Menu()
        
        self.menu.Append(self.file,"&File")
        self.menu.Append(self.script,"&Script")
        
        self.file.Append(MenuManager.ID_SAVE_SCRIPT,"&Save script...\tCtrl-S")
        wx.EVT_MENU(self,MenuManager.ID_SAVE_SCRIPT,self.onSaveScript)
        
        self.file.Append(MenuManager.ID_LOAD_SCRIPT,"&Open script...\tCtrl-O")
        wx.EVT_MENU(self,MenuManager.ID_LOAD_SCRIPT,self.onLoadScript)
        self.file.AppendSeparator()
        self.file.Append(MenuManager.ID_CLOSE_SCRIPTEDITOR,"&Close...\tAlt-F4")
        wx.EVT_MENU(self,MenuManager.ID_CLOSE_SCRIPTEDITOR,self.onClose)
        
        
        self.script.Append(MenuManager.ID_RUN_SCRIPT,"&Run script")
        wx.EVT_MENU(self,MenuManager.ID_RUN_SCRIPT,self.onRunScript)
        
        self.script.AppendSeparator()
        self.script.Append(MenuManager.ID_RECORD_SCRIPT,"R&ecord script")
        wx.EVT_MENU(self,MenuManager.ID_RECORD_SCRIPT,self.onRecordScript)
        
        
        self.script.Append(MenuManager.ID_STOP_RECORD,"&Pause recording")
        wx.EVT_MENU(self,MenuManager.ID_STOP_RECORD,self.onStopRecord)
        self.script.Enable(MenuManager.ID_STOP_RECORD,0)
   
    def onClose(self,evt):
        """
        Created: 13.02.2006, KP
        Description: Close the script editor
        """   
        self.Destroy()
        
    def onSaveScript(self,evt):
        """
        Created: 13.02.2006, KP
        Description: Save the script to a file
        """
        filename=Dialogs.askSaveAsFileName(self,"Save script file","script.bxs",self.wc)
        self.writeScript(filename)
    def writeScript(self, filename):
        """
        Created: 15.08.2006, KP
        Description: Actually write the script out
        """
        
        try:
            f=open(filename,"w")
            ind=""
            lines = self.editor.GetText()
                
            s="\n".join(lines)
            if "def run" not in s:
                ind="    "                
                f.write("def run():\n")
            for i,line in enumerate(lines):
                
                lines[i]=ind+lines[i].rstrip()
            f.write("\n".join(lines))
        except:
            pass
        
    def onLoadScript(self,evt):
        """
        Created: 13.02.2006, KP
        Description: Load a script from file
        """
        filenames=Dialogs.askOpenFileName(self,"Open script file",self.wc)
        if not filenames:
            return
        file=filenames[0]
    
    
        self.readFile(file)
    
    def readFile(self,file):
        """
        Created: 13.02.2006, KP
        Description: Read a script from file
        """
        f=open(file,"r")
        lines=f.readlines()
        imports=[]
        r1=re.compile("import (\S+)")
        r2=re.compile("from (\S+) import (\S+)")
        remove=[]
        
        for line in lines:
            l=line.strip()
            m=r1.match(l)
            im=None
            if m:
               im=m.group(1) 
            if not m:
                m=r2.match(l)
                if m:
                    im=(m.group(1),m.group(2))
                
            if im:
                imports.append(im)
                remove.append(line)
        for line in remove:
            lines.remove(line)
        self.editor.setScript(lines,imports)
        
        
    def createToolbar(self):
        """
        Created: 13.02.2006, KP
        Description: Creates the toolbar for the script editor
        """
        flags=wx.NO_BORDER|wx.TB_HORIZONTAL|wx.TB_TEXT
        self.CreateToolBar(flags)
        tb=self.GetToolBar()            
        tb.SetToolBitmapSize((32,32))
        
        iconpath=bxd.get_icon_dir()
        bmp = wx.Image(os.path.join(iconpath,"record.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_RECORD_SCRIPT,"Record",bmp,shortHelp="Record script")
        wx.EVT_TOOL(self,MenuManager.ID_RECORD_SCRIPT,self.onRecordScript)
        
        bmp = wx.Image(os.path.join(iconpath,"pause.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_STOP_RECORD,"Pause",bmp,shortHelp="Pause recording") 
        wx.EVT_TOOL(self,MenuManager.ID_STOP_RECORD,self.onStopRecord)
        tb.EnableTool(MenuManager.ID_STOP_RECORD,0)

        bmp = wx.Image(os.path.join(iconpath,"play.gif"),wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        tb.DoAddTool(MenuManager.ID_RUN_SCRIPT,"Run",bmp,shortHelp="Run recorded script") 
        wx.EVT_TOOL(self,MenuManager.ID_RUN_SCRIPT,self.onRunScript)
        
        tb.Realize()        
        self.tb = tb
        
    def onRunScript(self,evt):
        """
        Created: 13.02.2006, KP
        Description: Run the recorded script
        """         
        x,filename = tempfile.mkstemp(".py","BioImageXD")
        
        self.writeScript(filename)
        
        self.parent.loadScript(filename)
        os.remove(filename)
        #os.remove(filename)
        
        
        
    def onRecordScript(self,evt):
        """
        Method: onRecordScript
        Created: 13.02.2006, KP
        Description: Enable the recording of scripts
        """         
        self.tb.EnableTool(MenuManager.ID_STOP_RECORD,1)
        self.tb.EnableTool(MenuManager.ID_RECORD_SCRIPT,0)
        self.script.Enable(MenuManager.ID_STOP_RECORD,1)
        self.script.Enable(MenuManager.ID_RECORD_SCRIPT,0)
        bxd.record = 1
        self.Show(0)
    
    def onStopRecord(self,evt):
        """
        Method: onStopRecord
        Created: 13.02.2006, KP
        Description: Stop recording of scripts
        """         
        self.tb.EnableTool(MenuManager.ID_STOP_RECORD,0)
        self.tb.EnableTool(MenuManager.ID_RECORD_SCRIPT,1)
        self.script.Enable(MenuManager.ID_STOP_RECORD,0)
        self.script.Enable(MenuManager.ID_RECORD_SCRIPT,1)        
        bxd.record = 0
