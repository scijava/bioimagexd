Before running the program you need to do these setup steps:

1)
Install python2.7 (if you don't already have that)
OSX 10.6 Snow Leopard does not have it by default (only python 2.6),
so you need to get it from here:
http://python.org/download/
and run that installer.

OSX 10.7 Lion seems to have python2.7 already.


2)
add paths of VTK and ITK libraries to
the DYLD_LIBRARY_PATH variable. These are:

${BXD_PATH}/Libraries/
${BXD_PATH}/Libraries/python2.7/site-packages/vtkbxd/
${BXD_PATH}/Libraries/vtk-5.6/
${BXD_PATH}/Libraries/InsightToolkit/

For example add following lines to your .bashrc_profile file:
BXD_PATH="Put your path to BioImageXD here"
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:${BXD_PATH}/Libraries/:${BXD_PATH}/Libraries/python2.7/site-packages/vtkbxd/:${BXD_PATH}/Libraries/vtk-5.6/:${BXD_PATH}/Libraries/InsightToolkit/
