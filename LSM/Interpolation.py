# -*- coding: iso-8859-1 -*-

"""
 Unit: Interpolation.py
 Project: Selli
 Created: 09.12.2004
 Creator: KP
 Description:

 A module used to interpolate the intensity transfer functions based on given 
 parameters.

 Modified 09.12.2004 KP - Created the module
          11.01.2005 JV - Added comments

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma,varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
"""
__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.3 $"
__date__ = "$Date: 2005/01/13 13:42:03 $"


def linearInterpolation(paramlist1,paramlist2,n):
        """
        --------------------------------------------------------------
        Function: linearInterpolation(paramlist1,paramlist2,n)
        Created: 09.12.2004
        Creator: KP
        Description: A function that interpolates n new parameter lists between 
                     two given parameterlists
        Parameters:
            paramlist1      The starting parameters
            paramlist2      The ending parameters
            n               How many parameter lists are interpolated between 
                            paramlist1 and paramlist2
        -------------------------------------------------------------
        """
        paramlen=len(paramlist1)
        if len(paramlist1) != len(paramlist2):
            raise ("Length of parameter lists do no match: length of first "
            "%d != length of second %d"%(len(paramlist1),len(paramlist2)))
        diffs=[]
        results=[]
        # Calculate differences of each parameter
        for i in range(paramlen):
            p1,p2=paramlist1[i],paramlist2[i]
            diff=p2-p1
            diff/=float(n+1)
            diffs.append(diff)
        # Create new parameter lists with interpolated parameters
        for newnumber in range(n):
            newlist=[]
            for i in range(paramlen):
                p=paramlist1[i]
                p=p+(newnumber+1)*diffs[i]
                newlist.append(p)
            results.append(newlist)
        return results

interpolate=linearInterpolation


