# -*- coding: iso-8859-1 -*-
"""
 Unit: IntensityTransferFunction
 Project: Selli
 Created: 23.11.2004
 Creator: KP
 Description: A class that represents the intensity transfer function

 Modified: 23.11.2004 KP - Created the class
           24.11.2004 KP - Moved all the logic from TransferWidget to Intensity
                           TransferFunction
           1.12.2004 KP, JM - Fixed the list creation code so that with gamma & 
                              co the graph doesn't jump up and down
           1.12.2004 KP, JM - Added minimum processing threshold - a threshold 
                              below which the function acts like an identity 
                              mapping
           04.12.2004 JV - Added getAsString
           09.12.2004 KP - Added getAsParameterList() and setFromParameterList()
                           for interpolation
           10.12.2004 JV - Added isIdentical for checking if the function is 
                           identical
           13.12.2004 JV - Fixed: setFromParameterList converts parameters to 
                           floats

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
"""

__author__ = "Selli Project <http://sovellusprojektit.it.jyu.fi/selli/>"
__version__ = "$Revision: 1.32 $"
__date__ = "$Date: 2005/01/14 14:49:22 $"


import operator
import math
class IntensityTransferFunction:
    """
    --------------------------------------------------------------
    Class: IntensityTransferFunction
    Created: 23.11.2004
    Creator: KP
    Description: A class representing the intensity transfer function
    --------------------------------------------------------------
    """

    def __init__(self,minval=0,maxval=255,minthreshold=0,maxthreshold=255,
                 contrast=0,brightness=0,gamma=1):
        """
        --------------------------------------------------------------
        Method: __init__(minval=0,maxval=255,minthreshold=0,maxthreshold=255,
                         contrast=0,brightness=0)
        Created: 23.11.2004
        Creator: KP
        Description: Constructor
        Parameters:
                minval          The minimum value of the transfer function
                maxval          The maximum value of the transfer function
                minthreshold    The minimum threshold of the transfer function
                maxthreshold    The maximum threshold of the transfer function
                contrast        The contrast for the transfer function
                brightness      The brightness for the transfer function
        -------------------------------------------------------------
        """
        self.minimumValue=minval
        self.maximumValue=maxval
        self.minimumThreshold=minthreshold
        self.maximumThreshold=maxthreshold
        self.gamma=gamma
        self.contrast=0
        self.brightness=0
        self.gammaExponent=1
        self.minimumProcessingThreshold=0


        self.coeff=1
        self.b=0
      	self.setReferencePoint((
                     (self.maximumThreshold-self.minimumThreshold)/2.0,
                     (self.maximumValue-self.minimumValue)/2.0))
        self.createList()

    def getAsParameterList(self):
        """
        --------------------------------------------------------------
        Method: getAsParameterList()
        Created: 9.12.2004
        Creator: KP
        Description: Returns the parameters defining this interpolation function
        -------------------------------------------------------------
        """
        lst=[]
        lst.append(self.getBrightness())
        lst.append(self.getContrast())
        lst.append(self.getGamma())
        lst.append(self.getMinimumThreshold())
        lst.append(self.getMinimumValue())
        lst.append(self.getMaximumThreshold())
        lst.append(self.getMaximumValue())
        lst.append(self.getMinimumProcessingThreshold())
        return lst

    def setFromParameterList(self,paramlist):
        """
        --------------------------------------------------------------
        Method: setFromParameterList(lst)
        Created: 9.12.2004
        Creator: KP
        Description: Sets the parameters defining this interpolation function
        -------------------------------------------------------------
        """
        br,cr,g,mt,mv,mat,mav,mpt=paramlist
        print "Setting brightness from parameterlist, br=",br,"float(br)=",\
              float(br)
        self.setContrast(float(cr))
        self.setGamma(float(g))
        self.setMinimumThreshold(float(mt))
        self.setMinimumValue(float(mv))
        self.setMaximumThreshold(float(mat))
        self.setMaximumValue(float(mav))
        self.setMinimumProcessingThreshold(float(mpt))

        self.setBrightness(float(br))
        self.update=1

    def isIdentical(self):
        """
        --------------------------------------------------------------
        Method: isIdentical()
        Created: 10.12.2004
        Creator: JV
        Description: Is the function identical? ( = default)
                     Returns boolean
                     Some modules need this info to know if should they
                     skip the the mapping with intensity transfer
                     function (no need if function is identical).
        -------------------------------------------------------------
        """

        # Other way?

        if self.minimumValue!=0: return False
        if self.maximumValue!=255: return False
        if self.minimumThreshold!=0: return False
        if self.maximumThreshold!=255: return False
        if self.gamma!=1: return False
        if self.contrast!=0: return False
        if self.brightness!=0: return False
        if self.minimumProcessingThreshold!=0: return False

        return True

    def restoreDefaults(self):
        """
        --------------------------------------------------------------
        Method: restoreDefaults()
        Created: 8.12.2004
        Creator: KP
        Description: Restores the default settings for this function
        -------------------------------------------------------------
        """
        self.setMinimumValue(0)
        self.setMaximumValue(255)
        self.setMinimumThreshold(0)
        self.setMaximumThreshold(255)
        self.setMinimumProcessingThreshold(0)
        self.setGamma(1)
        self.setContrast(0)
        self.setBrightness(0)
        self.update=1
        #print self.minimumValue
        self.createList()

    def setMinimumValue(self,minval):
        """
        --------------------------------------------------------------
        Method: setMinimumValue(minval)
        Created: 23.11.2004
        Creator: KP
        Description: Set the minimum value of the transfer function
        Parameters:
                minval          The minimum value of the transfer function
        -------------------------------------------------------------
        """
        if minval<0 or minval>255 or minval > self.maximumValue:
            raise "Bad minimum value for intensity transfer function: %d"%minval
        self.minimumValue=minval
        self.update=1

    def setMaximumValue(self,maxval):
        """
        --------------------------------------------------------------
        Method: setMaximumValue(maxval)
        Created: 23.11.2004
        Creator: KP
        Description: Set the maximum value of the transfer function
        Parameters:
                maxval          The maximum value of the transfer function
        -------------------------------------------------------------
        """
        if maxval<0 or maxval>255 or maxval<self.minimumValue:
            raise "Bad maximum value for intensity transfer function: %d"%maxval

        self.maximumValue=maxval
        self.update=1

    def setMinimumThreshold(self,minthreshold):
        """
        --------------------------------------------------------------
        Method: setMinimumThreshold(minthreshold)
        Created: 23.11.2004
        Creator: KP
        Description: Set the minimum threshold of the transfer function
        Parameters:
                minthreshold    The minimum threshold of the transfer function
        -------------------------------------------------------------
        """
        if minthreshold<0 or minthreshold>255:
            raise ("Bad minimum threshold for intensity "
            "transfer function: %d"%minthreshold)
        self.minimumThreshold=minthreshold
        self.update=1

    def setMaximumThreshold(self,maxthreshold):
        """
        --------------------------------------------------------------
        Method: setMaximumThreshold(maxthreshold)
        Created: 23.11.2004
        Creator: KP
        Description: Set the maximum threshold of the transfer function
        Parameters:
                maxthreshold    The maximum threshold of the transfer function
        -------------------------------------------------------------
        """
        if maxthreshold<0 or maxthreshold>255:
            raise ("Bad maximum threshold for intensity "
            "transfer function: %d"%maxthreshold)
        self.maximumThreshold=maxthreshold
        self.update=1

    def setContrast(self,contrast):
        """
        --------------------------------------------------------------
        Method: setContrast(contrast)
        Created: 23.11.2004
        Creator: KP
        Description: Set the contrast for the transfer function
        Parameters:
                contrast        The contrast for the transfer function
        -------------------------------------------------------------
        """

        self.coeff=contrast

        if abs(self.coeff)>10:
            self.coeff/=10.0
        elif self.coeff!=0:
            self.coeff=1

        if contrast<0:
            self.coeff=1.0/abs(self.coeff)
        elif contrast==0:
            self.coeff=1

        if self.coeff<0 or self.coeff>255:
            raise "Bad contrast for intensity transfer function: %f"%self.coeff


#        print "Contrast %d equals coeff %f"%(contrast,self.coeff)
        print "Setting contrast ",contrast," (coeff=",self.coeff,")"
        self.contrast=contrast
        self.update=1


    def setBrightness(self,brightness):
        """
        --------------------------------------------------------------
        Method: setBrightness(brightness)
        Created: 23.11.2004
        Creator: KP
        Description: Set the brightness for the transfer function
        Parameters:
                brightness        The brightness for the transfer function
        -------------------------------------------------------------
        """
        self.brightness=brightness
        brightness=brightness/100.0

        if self.brightness<-255 or self.brightness>255:
            raise ("Bad brightness for intensity "
            "transfer function: %d"%self.brightness)
        self.update=1

        x,y=self.refpoint


        x = 128 + self.brightness

    	print "Brightness %f equals refpoint (%d,%d)"%(brightness,x,y)
    	self.setReferencePoint((x,y))

    def setMinimumProcessingThreshold(self,x):
        """
        --------------------------------------------------------------
        Method: setMinimumProcessingThreshold(x)
        Created: 1.12.2004
        Creator: KP
        Description: Sets the minimum processing threshold below which the 
                     function acts as an identity mapping
        -------------------------------------------------------------
        """
        if x<0 or x>255:
            raise ("Bad minimum processing threshold for intensity "
            "transfer function: %d"%x)
        self.minimumProcessingThreshold=x
        self.update=1

    def getMinimumProcessingThreshold(self):
        """
        --------------------------------------------------------------
        Method: getMinimumProcessingThreshold()
        Created: 09.12.2004
        Creator: KP
        Description: Returns the minimum processing threshold
        -------------------------------------------------------------
        """
        return self.minimumProcessingThreshold


    def setReferencePoint(self,pos):
        """
        --------------------------------------------------------------
        Method: setReferencePoint(pos)
        Created: 30.10.2004
        Creator: KP
        Description: Sets the reference point used to draw the slope
        -------------------------------------------------------------
        """
        self.update=1
        self.refpoint=pos

    def setGamma(self,gamma):
        """
        --------------------------------------------------------------
        Method: setGamma(gamma)
        Created: 23.11.2004
        Creator: KP
        Description: Set the gamma for the transfer function
        Parameters:
                gamma        The gamma for the transfer function
        -------------------------------------------------------------
        """
        self.gammaExponent=gamma


        if abs(self.gammaExponent)>10:
            self.gammaExponent/=10.0
        elif self.gammaExponent!=0:
            self.gammaExponent=1


        if gamma<0:
            self.gammaExponent=1.0/abs(self.gammaExponent)
        elif gamma==0:
            self.gammaExponent=1
        self.gamma=gamma
        
        if self.gammaExponent<0:
            raise ("Bad gamma for intensity transfer "
            "function: %d"%self.gammaExponent)


        self.update=1

    def getMinimumValue(self):
        """
        --------------------------------------------------------------
        Method: getMinimumValue()
        Created: 24.11.2004
        Creator: KP
        Description: Return the minimum value
        -------------------------------------------------------------
        """
        return self.minimumValue

    def getMaximumValue(self):
        """
        --------------------------------------------------------------
        Method: getMaximumValue()
        Created: 24.11.2004
        Creator: KP
        Description: Return the maximum value
        -------------------------------------------------------------
        """
        return self.maximumValue

    def getMinimumThreshold(self):
        """
        --------------------------------------------------------------
        Method: getMinimumThreshold()
        Created: 24.11.2004
        Creator: KP
        Description: Return the minimum threshold
        -------------------------------------------------------------
        """
        return self.minimumThreshold

    def getMaximumThreshold(self):
        """
        --------------------------------------------------------------
        Method: getMaximumThreshold()
        Created: 24.11.2004
        Creator: KP
        Description: Return the maximum threshold
        -------------------------------------------------------------
        """
        return self.maximumThreshold

    def getContrast(self):
        """
        --------------------------------------------------------------
        Method: getContrast()
        Created: 24.11.2004
        Creator: KP
        Description: Return the contrast
        -------------------------------------------------------------
        """
        return self.contrast

    def getBrightness(self):
        """
        --------------------------------------------------------------
        Method: getBrightness()
        Created: 24.11.2004
        Creator: KP
        Description: Return the brightness
        -------------------------------------------------------------
        """
        return self.brightness

    def getGamma(self):
        """
        --------------------------------------------------------------
        Method: getGamma()
        Created: 24.11.2004
        Creator: KP
        Description: Return the gamma parameter of this function
        -------------------------------------------------------------
        """
        return self.gamma

    def getGammaExponent(self):
        """
        --------------------------------------------------------------
        Method: getGammaExponent()
        Created: 24.11.2004
        Creator: KP
        Description: Return the actual exponent of the gamma equation. The
                     relation between gamma exponent and the gamma parameter 
                     (getGamma(),setGamma()) is that the gamma parameter is
                     set from the GUI controls, and has to be tweaked a bit to 
                     get the real gamma exponent. This sets the gamma exponent
                     directly
        -------------------------------------------------------------
        """
        return self.gammaExponent

    def setGammaExponent(self,x):
        """
        --------------------------------------------------------------
        Method: setGammaExponent(x)
        Created: 09.12.2004
        Creator: KP
        Description: Sets the gamma exponent for this function. The relation 
                     between gamma exponent and the gamma parameter (getGamma(),
                     setGamma()) is that the gamma parameter is set from the GUI
                     controls, and has to be tweaked a bit to get the real gamma
                     exponent. This sets the gamma exponent directly
        -------------------------------------------------------------
        """
        self.gammaExponent=x
        if x<1:
            self.gamma=-1.0/x
        else:
            self.gamma=x

        self.update=1

    def getLineCoeff(self):
        """
        --------------------------------------------------------------
        Method: getLineCoeff()
        Created: 09.12.2004
        Creator: KP
        Description: Return the coeff of the slope. The coeff is calculated from
                     the contrast by the setContrast() method.
        -------------------------------------------------------------
        """
        return self.coeff

    def setLineCoeff(self,x):
        """
        --------------------------------------------------------------
        Method: setLineCoeff(x)
        Created: 09.12.2004
        Creator: KP
        Description: Set coeff of the slope. The coeff is usually calculated
                     from the contrast by the setContrast() method.
        -------------------------------------------------------------
        """
        self.coeff=x
        if x<1:
            self.contrast=-1.0/x
        else:
            self.contrast=x

        self.update=1

    def createList(self):
        """
        --------------------------------------------------------------
        Method: createList()
        Created: 23.11.2004
        Creator: KP
        Description: Creates a list of 256 values, representing
                     0-255 mapped through the function
        -------------------------------------------------------------
        """
        self.update=0
        flag=0
        self.intensityTransferList=[0]*256
        x0,y0=self.slopeStartPoint()
        x1,y1=self.slopeEndPoint()

        print "Creating list, refpoint=",self.refpoint
        for x in range(0,256):
            y=0
            #before
	    if x<self.minimumProcessingThreshold:
		self.intensityTransferList[x]=x
		continue
	    
            if x<self.minimumThreshold:
		if self.minimumProcessingThreshold < self.minimumValue:
		    self.intensityTransferList[x]=self.minimumValue
		else:
		    self.intensityTransferList[x]=self.minimumProcessingThreshold
                continue

            if x>=self.minimumThreshold:
                y=self.minimumValue

            if x>=x0 and x<=x1:
                gx0,gy0,gx1,gy1=self.getGammaPoints()
                #print "gx1=",gx1,"gy1=",gy1
#                if y1>self.maximumValue:
#                    y1=self.maximumValue
#                if y0<self.minimumValue:
#                    y0=self.minimumValue
                if x0<self.minimumThreshold:
                    x0=self.minimumThreshold
                    y0=self.coeff*x0+self.b

                if x1>self.maximumThreshold:
                    x1=self.maximumThreshold
                    y1=self.coeff*x1+self.b

                if x0<=0:
                    x0=gx0
                if x1>=255:
                    x1=gx1
                if y0<=0:
                    y0=gy0
                if y1>=255:
                    y1=gy1


                self.gammaPoints=[(x0,y0),(x1,y1)]

                #print "gammaPoints=",self.gammaPoints
                if abs(self.gammaExponent)!=1:
                    y=self.getGammaAt(x0,y0,x1,y1,x,self.gammaExponent)
                else:
                    self.gammaPoints=[]
                    y=self.coeff*x+self.b

            # From the top of the slope to maximum threshold
            if x>x1 and x<=self.maximumThreshold:
                y=self.maximumValue

            # If y is larger than the maximum value, set it to maximum value
            if y>self.maximumValue:
                y=self.maximumValue


            if x>self.minimumProcessingThreshold and \
            y>self.minimumProcessingThreshold:
                flag=1
            if self.minimumProcessingThreshold and \
            x>=self.minimumProcessingThreshold and \
            y<self.minimumProcessingThreshold and not flag:
                y=self.minimumProcessingThreshold

            #after maximum threshold y=0
            if x>self.maximumThreshold:
                y=self.minimumValue

            self.intensityTransferList[x]=y


    def getAsList(self):
        """
        --------------------------------------------------------------
        Method: getAsList()
        Created: 23.11.2004
        Creator: KP
        Description: Returns the function as a list of 256 values, representing
                     0-255 mapped through the function
        -------------------------------------------------------------
        """
        if self.update:
            self.createList()
        return self.intensityTransferList

    def __str__(self):
        """
        --------------------------------------------------------------
        Method: __str__()
        Created: 04.12.2004
        Creator: JV
        Description: Returns the function parameters in a string
        -------------------------------------------------------------
        """

        lst=map(str,self.getAsParameterList())
        resultString="|".join(lst)
        return resultString

    def setFromString(self, string):
        """
        --------------------------------------------------------------
        Method: setFromString(string)
        Created: 14.12.2004
        Creator: JV
        Description: Sets the function parameters from a string
        Parameters:  string - setting string
        -------------------------------------------------------------
        """

        lst=string.split("|")
        if len(lst)!=8:
            raise "Setting string has wrong number of settings"
        self.setFromParameterList(lst)

        self.update=1
        self.createList()

    def slopeStartPoint(self):
        """
        --------------------------------------------------------------
        Method: slopeStartPoint()
        Created: 30.10.2004
        Creator: KP
        Description: Calculates the starting point of the slope or the gamma
        -------------------------------------------------------------
        """
    	# The line equation is of the form:
    	# y=mx+b
    	# where m = the slope coefficient and b is the point where
    	# the line cuts the x axis
    	# when we know the coefficient, x and y, we can determine b:
    	# b=y-mx
        x,y=self.refpoint
    	self.b=y-self.coeff*x

    	# next we need to determine where the slope cuts the horizontal line
    	# y = minvalue
    	#
    	# so we have the equation
    	# mx+b=minvalue
    	# x=(minvalue-b)/m
    	y1=self.minimumValue
    	x1=(y1-self.b)/self.coeff
        return (x1,y1)

    def getGammaPoints(self):
        """
        Method: getGammaPoints()
        Created: 09.12.2004
        Creator: KP
        Description: Returns the starting and ending point for gamma,
                     that are on the line from (x0,y0) to (x1,y1) but inside the
                     displayed area
        """
        # y = mx+b
        # x = (y-b)/m
        # First we need to determine whether the line crosses the top or the 
        # side of the box
        # We do this by getting the line's value at 255
        y=self.coeff*255+self.b
        startpoint=(0,0)
        endpoint=(0,0)

        if y>255:         # We cross the ceiling
            x=(255-self.b)/self.coeff
            endpoint=(x,255)
#            print "Gamma endpoint=",endpoint
        else:             # We cross the right side
            endpoint=(255,y)

        # Get the value at x=0
        y=self.coeff*0+self.b
        if y<0:           # We cross the floor
            x=(0-self.b)/self.coeff
            startpoint=(x,0)
        else:
            startpoint=(0,y)

        x0,y0=startpoint
        x1,y1=endpoint
        return x0,y0,x1,y1



    def getGammaAt(self,x0,y0,x1,y1,x,g):
        """
        --------------------------------------------------------------
        Method: getGammaAt(x0,y0,x1,y1,x,g)
        Created: 23.11.2004
        Creator: KP
        Description: A method that returns the y from the following formula:
                         (y2-y1)
                 y =   ---------- * (x-x1)^g +y1
                        (x2-x1)^g

                  I.e the y coord of the gamma curve at point x, when the gamma
                  curve starts at (x0,y0) and ends at (x1,y1) and the gamma 
                  value is g

        Parameters:
                x0,y0   The starting point of the gamma curve
                x1,y1   The end point of the gamma curve
                x       The point from which we want the gamma curves y coord
                g       The gamma value


        -------------------------------------------------------------
        """


        return ( (y1-y0)/ ( (x1-x0)**g) )* ( (x-x0)**g ) + y0

    def slopeEndPoint(self):
        """
        --------------------------------------------------------------
        Method: slopeEndPoint()
        Created: 30.10.2004
        Creator: KP
        Description: Calculates the end point of the slope or the gamma. As a
                     side effect, sets self.b (where the line crosses y=0)
        -------------------------------------------------------------
        """
    	# The line equation is of the form:
        # y=mx+b
    	# where m = the slope coefficient and b is the point where
    	# the line cuts the x axis
    	# when we know the coefficient, x and y, we can determine b:
    	# b=y-mx
        x,y=self.refpoint
        self.b=y-self.coeff*x

    	# next we need to determine where the slope cuts the horizontal line
    	# y = maxvalue
    	#
    	# so we have the equation
    	# mx+b=maxvalue
        # x=(maxvalue-b)/m
    	y1=self.maximumValue
    	x1=(y1-self.b)/self.coeff
    	return (x1,y1)

    def checkLimits(self):
        """
        --------------------------------------------------------------
        Method: checkLimits()
        Created: 24.10.2004
        Creator: KP
        Description: Checks that the drawn slope doesn't extend over the
                     specified min and max value
        -------------------------------------------------------------
        """
        x,y=self.slopeEndPoint()
        if x>self.maximumThreshold:
            return 1
        if x<self.minimumThreshold:
            return 1
        if y<0:
            return 1
        if y>self.maximumValue:
            return 1

        return 0


