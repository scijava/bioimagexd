#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
 Unit: UIElements
 Project: BioImageXD
 Created: 30.6.2007, KP
 Description:

 A list view that will take input similiar to what the csv module takes, and view it as a list ctrl
 with the option to open it in a spreadsheet program or export it out a file
 
 Copyright (C) 2007 BioImageXD Project
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
import types

class CSVListView(wx.ListCtrl):
    """
    Created: 30.6.2007, KP
    Description: A list control that takes a list of lists and shows that
    """
    def __init__(self, parent, size = (350,200)):
        wx.ListCtrl.__init__(
            self, parent, -1, 
            size = size,
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES,
            
            )

        self.SetItemCount(1)
        self.data = []
        
        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour("white")

        self.attr2 = wx.ListItemAttr()
        self.attr2.SetBackgroundColour("light blue")
        
    def exportToCsv(self, filename, headers=[]):
        """
        Created: 30.6.2007, KP
        Description: write out the data to a .csv file
        """
        f=codecs.open(filename,"wb","latin-1")
        w = csv.writer(f, dialect="excel",delimiter=";")
        for i in headers:
            w.writerow([i])
        for line in self.data:
            w.writerow(line)
        f.close()
        
    def importFromCsv(self, filename):
        """
        Created: 30.6.2007, KP
        Description: read a .csv file and show it in the list box
        """
        pass
        
    def setContents(self, data):
        """
        Created: 30.6.2007, KP
        Description: Set the contents of the list view
        """    
        assert type(data)==types.ListType
        for i, headerName in enumerate(data[0]):
            self.InsertColumn(i, headerName)
        self.data = data[1:]
#        print "There are ",len(data[1:]),"items"
        self.SetItemCount(len(data[1:]))

    def OnGetItemText(self, item, col):
        """
        Created: 30.6.2007, KP
        Description: A method that returns the value of the given column of given row
        """            
        try:
            print "Returning",self.data[item][col]
            return str(self.data[item][col])
        except:
            return ""
 
    def OnGetItemImage(self, item):
        """
        Created: 30.6.2007, KP
        Description: Return an image for the item
        """    
        return -1

    def OnGetItemAttr(self, item):
        """
        Created: 30.6.2007, KP
        Description: Return the attribute for the given item
        """    
    
        if item % 2 == 1:
            return self.attr1
        elif item % 2 == 0:
            return self.attr2
        else:
            return None