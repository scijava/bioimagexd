# -*- coding: iso-8859-1 -*-
"""
 Unit: Reslice
 Project: BioImageXD
 Created: 04.04.2005
 Creator: KP
 Description:

 A module for slicing a dataset in various ways

 Modified: 04.04.2005 KP - Created the module

 BioImageXD includes the following persons:
 
 DW - Dan White, dan@chalkie.org.uk
 KP - Kalle Pahajoki, kalpaha@st.jyu.fi
 PK - Pasi Kankaanpää, ppkank@bytl.jyu.fi
 """
__author__ = "BioImageXD Project"
__version__ = "$Revision: 1.40 $"
__date__ = "$Date: 2005/01/13 14:52:39 $"


import vtk
import time
from Module import *

class Reslice(Module):
    """
    Class: Reslice
    Created: 04.04.2005, KP
    Description: Slices a dataset
    """

    def __init__(self,**kws):
        """
        Method: __init__(**keywords)
        Created: 04.04.2005, KP
        Description: Initialization
        """
        Module.__init__(self,**kws)

        # TODO: remove attributes that already exist in base class!
        self.images=[]
        self.x,self.y,self.z=0,0,0
        self.extent=None
        self.running=0
        self.angle = (0,0,0)

        self.reset()

    def reset(self):
        """
        Method: reset()
        Created: 25.11.2004, KP
        Description: Resets the module to initial state. This method is
                     used mainly when doing previews, when the parameters
                     that control the colocalization are changed and the
                     preview data becomes invalid.
        """
        Module.reset(self)
        self.preview=None
        self.extent=None
        self.n=-1

    def addInput(self,data):
        """
        Method: addInput(data)
        Created: 1.12.2004, KP, JV
        Description: Adds an input for the single dataunit processing filter
        """
        Module.addInput(self,data)
        self.n+=1
        settings=self.settings
        x=settings.get("ResliceXAngle")
        y=settings.get("ResliceYAngle")
        z=settings.get("ResliceZAngle")
        self.angle=(x,y,z)
        
    def getPreview(self,z):
        """
        Method: getPreview(z)
        Created: 1.12.2004, KP
        Description: Does a preview calculation for the x-y plane at depth z
        """
        self.z=z
        if not self.preview:
            self.preview=self.doOperation()
        return self.preview


    def doOperation(self):
        """
        Method: doOperation
        Created: 1.12.2004, KP, JV
        Description: Processes the dataset in specified ways
        """
        t1=time.time()

        # Map scalars with intensity transfer list

        print "We are processing %d arrays"%len(self.images)
        if len(self.images)>1:
            raise "More than one source dataset for Single DataUnit Processing"

        reslice=vtk.vtkImageReslice()
        t=vtk.vtkTransform()
        t.Identity()
        angle=self.angle
        t.RotateX(angle[0])
        t.RotateY(angle[1])
        t.RotateZ(angle[2])
        print "Using matrix ",t.GetMatrix()
        reslice.SetResliceAxes(t.GetMatrix())
        #reslice.SetResliceAxesOrigin(0,0,self.z)
        reslice.SetInput(self.images[0])
        reslice.Update()
        #reslice.SetOutputDimensionality(2)
        data=reslice.GetOutput()
        print "resliced data=",data
        t2=time.time()
        print "Processing took %f seconds"%(t2-t1)

        return data
