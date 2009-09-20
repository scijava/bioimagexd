CMAKE_MINIMUM_REQUIRED(VERSION 2.0)

#
# Set the project name.
#

PROJECT (VTKBXD)

IF(COMMAND cmake_policy)
  cmake_policy(SET CMP0003 NEW)
ENDIF(COMMAND cmake_policy)

#
# Load CMake commands that you probably should not modify.
#

INCLUDE (${VTKBXD_SOURCE_DIR}/CMakeOptions.cmake)

#
# Here is where you can list the sub-directories holding your local
# classes. Sorting classes by 'package' type like VTK does (Common,
# Rendering, Filtering, Imaging, IO, etc.) is a good thing and prevents
# numerous dependencies problems.
#

SUBDIRS (
  Processing
  Wrapping
)

#
# You can put your include path(s) here
#

INCLUDE_DIRECTORIES (${VTKBXD_SOURCE_DIR}/Processing)

#
# Build examples too ?
#

OPTION(BUILD_EXAMPLES "Build examples." OFF)
IF (BUILD_EXAMPLES)
  SUBDIRS(Examples)
ENDIF (BUILD_EXAMPLES)

#
# Common configuration settings
#
# Do not worry about this one.
#

CONFIGURE_FILE(
  ${VTKBXD_SOURCE_DIR}/VTKBXDConfigure.h.in
  ${VTKBXD_BINARY_DIR}/VTKBXDConfigure.h
)

INCLUDE_DIRECTORIES(${VTKBXD_BINARY_DIR})

ENABLE_TESTING()
