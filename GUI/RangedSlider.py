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

 BioImageXD includes the following persons:

 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi

 Copyright (c) 2005 BioImageXD Project.
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
    def __init__(self, parent, id = -1, value = 0, minValue = 0, maxValue = 100, **kws):
        wx.Slider.__init__(self,parent,id,value,minValue, maxValue, **kws)
        self.ranges=[]
        self.totalValues = 0

    def setRange(self, startPercent, endPercent, rangeStart, rangeEnd, n):
        self.totalValues += n
        self.SetRange(0, self.totalValues)
        self.ranges.append((startPercent,endPercent,rangeStart,rangeEnd,n))

    def getRealValue(self,val):
        currRange=None
        mytot = 0
        for r in self.ranges:
            if val >=  r[2] and val <= r[3]:
                currRange=r
                break
            else:
                currRange=self.ranges[-1]
            mytot+=r[4]
        percent = float(val) / currRange[3]
#        print "percent = ",percent,"mytot=",mytot
        #diff = currRange[3]-currRange[2]
        #return 100*(diff * percent)
        return mytot+ percent * currRange[4]


    def getScaledValue(self,val=None):
        if val == None:
            val = self.GetValue()
        percent = float(val) / self.totalValues
        currRange=None
        percent*=100
#       print "percent = ",percent

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
        return currRange[2]+distance * percentOfRange



if __name__=='__main__':
    d=RangedSlider(0,0,0)
    d.setRange(0,50,0,1.0,100)
    d.setRange(51,100,1.0,20.0,100)
    for i in range(0,210,10):
        print "Scaled value for %d is %f"%(i,d.getScaledValue(i))
    vals=[0.1,0.5,0.9,1.5,8.0,12.0,20.0]
    for fl in vals:
        print "Real value for %f is %d"%(fl,d.getRealValue(fl))
