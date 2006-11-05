#
# Source files
#
# Here is where you can add the name of your local imaging classes.
#

SET (Processing_SRCS
vtkDistanceRepresentationScaled2D.cxx
vtkExtTIFFReader.cxx
vtkImageAlphaFilter.cxx
vtkImageAutoThresholdColocalization.cxx
vtkImageColocalizationFilter.cxx
vtkImageColocalizationTest.cxx
vtkIntensityTransferFunction.cxx
vtkImageColorMerge.cxx
vtkImageLabelAverage.cxx
vtkImageMapToIntensities.cxx
vtkImageSimpleMIP.cxx
vtkImageSolitaryFilter.cxx

vtkLSMReader.cxx
)

# --------------------------------------------------------------------------
# You probably do not need to modify anything below this line

# Create the vtkBXDProcessing C++ library
ADD_LIBRARY (vtkBXDProcessing ${Processing_SRCS})
TARGET_LINK_LIBRARIES(vtkBXDProcessing vtkImaging vtkCommon vtkIO vtkWidgets vtkFiltering  )

# Create the vtkBXDBioImageXD Python library.
IF (VTK_WRAP_PYTHON AND VTKBXD_WRAP_PYTHON)
  VTK_WRAP_PYTHON3 (vtkBXDProcessingPython ProcessingPython_SRCS "${Processing_SRCS}")
  ADD_LIBRARY (vtkBXDProcessingPythonD ${ProcessingPython_SRCS})
  ADD_LIBRARY (vtkBXDProcessingPython MODULE vtkBXDProcessingPythonInit.cxx)
  TARGET_LINK_LIBRARIES(vtkBXDProcessingPythonD vtkBXDProcessing vtkImaging vtkImagingPythonD vtkCommon vtkCommonPythonD vtkIO vtkIOPythonD vtkWidgets vtkWidgetsPythonD vtkFiltering vtkFilteringPythonD)
  TARGET_LINK_LIBRARIES(vtkBXDProcessingPython vtkBXDProcessingPythonD)
ENDIF (VTK_WRAP_PYTHON AND VTKBXD_WRAP_PYTHON)

