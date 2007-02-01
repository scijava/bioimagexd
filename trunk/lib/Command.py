# -*- coding: iso-8859-1 -*-

"""
 Unit: Command
 Project: BioImageXD
 Created: 13.02.2006, KP
 Description:

 A module for classes implenting the command design pattern that will be used
 throughout the program to implement undo/redo and script recording.
 
 Actions given to the Command object should be as self-contained as possible.
 That means they should never assume a given context, but use absolute values,
 references etc. 
 
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
import Logging
import inspect
import messenger
import scripting as bxd

MENU_CMD="Menu command"
OPEN_CMD="Load file"
TASK_CMD="Load task"
MGMT_CMD="File management"
GUI_CMD="User interface command" 
PARAM_CMD="Parameter change"

def functionize(code,imports):
        lines=code.split("\n")
        for i,line in enumerate(lines):
            lines[i]="    %s"%line.strip()
        code="\n".join(lines)

        return code


class Command:
    """
    Created: 13.02.2006, KP
    Description: A class representing an executable action from menus etc.
    """ 
    def __init__(self,category=None,do=None,undo=None,do_code="",undo_code="",imports=None, desc=""):
        """
        Created: 13.02.2006, KP
        Description: Initialization 
        """     
        self.do=do
        self.undocmd=undo
        self.desc=desc
        self.category = category
        if not imports:imports=[]
        self.imports = imports
        icode=""
        for i in imports:
            icode="    import %s\n%s"%(i,icode)
        if not do and do_code:
            #exec(do_code,self.globals,self.locals)
            
            ncode=functionize(do_code,imports)
            
            code="""def f(x):\n%s%s\n"""%(icode,ncode)

            exec(code)
            self.do=f
        if not undo and undo_code:            
            ncode=functionize(undo_code,imports)
            code="""def f(x):\n%s%s\n"""%(icode,ncode)
            exec(code)
            self.undocmd=f
            
        self.do_code=do_code
        self.undo_code=undo_code
    
        self._undoed=0
        
        
    def getDesc(self):
        return self.desc
        
    def isUndoed(self):
        return self._undoed
    
    def canUndo(self):
        """
        Created: 13.02.2006, KP
        Description: A get method indicating whether this command can be undoed
        """     
        return not(not self.undocmd)
        

    def run(self, recordOnly = 0):
        """
        Created: 13.02.2006, KP
        Description: Execute the action associated with this command
        """ 
        if bxd.record:
            if not self.do_code:
                code = inspect.getsource(self.undo)
            else:
                code=self.do_code
            messenger.send(None,"record_code",code,self.imports)
        
        if not recordOnly:
            self.do(self)
            self._undoed=0
        messenger.send(None,"execute_command",self)
        
            
    def undo(self):
        """
        Created: 13.02.2006, KP
        Description: Execute an action that cancels the action of this command
        """         
        print "Running",self.undocmd,"code=",self.undo_code
        self.undocmd(self)
        self._undoed=1
        messenger.send(None,"execute_command",self,1)
        if bxd.record:
            if not self.undo_code:
                code = inspect.getsource(self.undo)
            else:
                code=self.undo_code
            messenger.send(None,"record_code",code,self.imports)
            
    def getCategory(self):
        return self.category
        
    def __str__(self):
        return "Command: %s (%s)"%(self.category,self.desc)
        