#Color24bit.py
# -*- coding: cp1252 -*-
"""
 Unit: Color24bit
 Project: Selli
 Created: 13.12.2004
 Creator: JM
 Description: A Class for handling 24-bit rgb color values

 Selli includes the following persons:
 JH - Juha Hyytiäinen, juhyytia@st.jyu.fi
 JM - Jaakko Mäntymaa, jahemant@cc.jyu.fi
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 JV - Jukka Varsaluoma, varsa@st.jyu.fi

 Copyright (c) 2004 Selli Project.
 --------------------------------------------------------------
"""

class Color24bit:
    """
    --------------------------------------------------------------
    Class: Color24bit
    Created: 13.12.2004
    Creator: JM
    Description: A Class for handling 24-bit rgb color values
    --------------------------------------------------------------
    """

    def __init__(self, red = 0, green = 0, blue = 0):
        """
        --------------------------------------------------------------
        Method: __init__()
        Created: 13.12.2004
        Creator: JM
        Description: Creates a new color with the given component values
        Parameters: red     red component value
                    green   green component value
                    blue    blue component value
        -------------------------------------------------------------
        """
        self.setValues(red, green, blue)

    def setValues(self, red, green, blue):
        """
        --------------------------------------------------------------
        Method: setValues()
        Created: 13.12.2004
        Creator: JM
        Description: Gives new values for the color components
        Parameters: red     red component value
                    green   green component value
                    blue    blue component value
        -------------------------------------------------------------
        """
        # First check the validity of given color component values:
        self.checkColorValue(red, 'red')
        self.checkColorValue(green, 'green')
        self.checkColorValue(blue, 'blue')

        # If values are ok, proceed setting them:
        self.red = red
        self.green = green
        self.blue = blue

    def checkColorValue(self, value, componentName):
        """
        --------------------------------------------------------------
        Method: checkColorValue
        Created: 24.11.2004
        Creator: JM
        Description: Checks the validity of a 8-bit color component value
        Parameters: value           A color component value
                    componentName   Name of the checked color component
        -------------------------------------------------------------
        """
        if not (0 <= value and value <= 255):
            raise "Invalid " + componentName + " component value given: %d"%value

    def getColor(self):
        """
        --------------------------------------------------------------
        Method: getColor
        Created: 13.12.2004
        Creator: JM
        Description: Returns the color in a tupple (red, green, blue)
        Parameters:
        -------------------------------------------------------------
        """
        return(self.red, self.green, self.blue)
