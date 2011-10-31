Before running the program you need to add paths of VTK and ITK libraries to
the DYLD_LIBRARY_PATH variable. These are:

${BXD_PATH}/Libraries/
${BXD_PATH}/Libraries/python2.7/site-packages/vtkbxd/
${BXD_PATH}/Libraries/vtk-5.6/
${BXD_PATH}/Libraries/InsightToolkit/

For example add following lines to your .bashrc file:
BXD_PATH="Put your path to BioImageXD here"
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:${BXD_PATH}/Libraries/:${BXD_PATH}/Libraries/python2.7/site-packages/vtkbxd/:${BXD_PATH}/Libraries/vtk-5.6/:${BXD_PATH}/Libraries/InsightToolkit/
