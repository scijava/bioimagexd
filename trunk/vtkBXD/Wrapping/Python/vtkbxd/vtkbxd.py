""" This module loads all the classes from the BioImageXD Processing Imaging library into
its namespace.  This is a required module."""

import os

if os.name == 'posix':
    from libvtkBXDProcessingPython import *
else:
    from vtkBXDProcessingPython import *
