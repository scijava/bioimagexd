#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
 Unit: RangedSlider
 Project: BioImageXD
 Created: 06.03.2005
 Creator: KP
 Description:

 Ranged slider is a slider for which you can specify integer ranges and values that those
 ranges map into. For example, you can specify that 50% of the slider (from 0 to 50) map to range 0.0 - 1.0
 and another 50% (from 50 to 100) map to range 1.0 - 25.0

 Modified: 06.03.2005 KP - Created the module
           10.03.2005 KP - Added support for ranges that start < 0
           11.03.2005 KP - Added support for "snap points"

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

class RangedSlider(wx.Slider):
#class RangedSlider:
    """
    Class: RangedSlider
    Created: 06.03.2005, KP
    Description: A slider that can map values of a certain range to certain values
    """
    def __init__(self, parent, id , numberOfPoints , **kws):
        """
        Method: __init__
        Created: 06.03.2005, KP
        Description: Initialization
        Parameters:
            numberOfPoints  The number of points the slider will in reality have
        """    
        wx.Slider.__init__(self,parent,id,0,0,0, **kws)
        self.ranges=[]
        self.totalValues = numberOfPoints
        self.SetRange(0, self.totalValues)        
        self.snapPoints=[]
        
    def setRange(self, startPercent, endPercent, rangeStart, rangeEnd):
        """
        Method: setRange(startPercent, endPercent, rangeStart,rangeEnd)
        Created: 06.03.2005, KP
        Description: Initialization
        """        
        self.ranges.append((startPercent,endPercent,rangeStart,rangeEnd))
    
    def setScaledValue(self,val):
        """
        Method: setScaledValue(value)
        Created: 06.03.2005, KP
        Description: Set the value of the slider to the given value
        """            
        self.SetValue(self.getRealValue(val))
        
    def setSnapPoint(self, snapValue, snapRange):
        """
        Method: setSnapPoint(snapValue, snapRange)
        Created: 06.03.2005, KP
        Description: Add a snap point, i.e. a point to which all values
                     that are on the snapRange will be mapped. I.e.
                     snapValue of 1.0 and snapRange of 0.1 will map values
                     0.95 - 1.05 to 1.0
        """            
        self.snapPoints.append( (snapValue-snapRange/2,snapValue,snapValue+snapRange/2))

    def getRealValue(self,val):
        """
        Method: getRealValue(value)
        Created: 06.03.2005, KP
        Description: For a given scaled value, return the real slider position
        """            
        currRange=None
        mytot=0
        for r in self.ranges:
            if val >=  r[2] and val <= r[3]:
                currRange=r
                break
            else:
                currRange=self.ranges[-1]
            mytot+=r[4]

        distance =  (abs(currRange[3])+abs(currRange[2]))
        val+=abs(currRange[2])
        percent = float(val) / distance
#        print "percent = ",percent,"mytot=",mytot,"distance=",distance
        n = self.totalValues / len(self.ranges)
        return mytot + percent * n


    def getScaledValue(self,val=None):
        """
        Method: getScaledValue()
        Created: 06.03.2005, KP
        Description: Return the scaled value of this slider
        """            
        if val == None:
            val = self.GetValue()
        percent = float(val) / self.totalValues
        currRange=None
        percent*=100
        #print "percent = ",percent

        for r in self.ranges:
            # If we found the right range
            if percent >= r[0] and percent <= r[1]:
                currRange=r
                break
            else:
               currRange=self.ranges[-1]

        distance=(currRange[3]-currRange[2])
        # This tells us how far in percent we are along the current range
        percentOfRange = (percent-currRange[0])/(currRange[1]-currRange[0])
#        print "distance = ",distance," percentsOfRange=",percentOfRange
        ret=currRange[2]+distance * percentOfRange
        #print "ret=",ret,"percent=",percent
        for i in self.snapPoints:
            if ret>= i[0] and ret<=i[2]:
                return i[1]
        return ret



if __name__=='__main__':
   d=RangedSlider(0,0,0)
   d.setRange(0,100,-255,255,2000)
   for i in range(-255,265,10):
       print "Real value for %d is %f"%(i,d.getRealValue(i))

if __name__=='__main__2':
    d=RangedSlider(0,0,0)
    d.setRange(0,50,0,1.0,100)
    d.setRange(51,100,1.0,20.0,100)
    for i in range(0,210,10):
        print "Scaled value for %d is %f"%(i,d.getScaledValue(i))
    vals=[0.1,0.5,0.9,1.5,8.0,12.0,20.0]
    for fl in vals:
        print "Real value for %f is %d"%(fl,d.getRealValue(fl))
