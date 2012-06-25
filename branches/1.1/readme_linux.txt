Before running the program you need to add paths of VTK and ITK libraries to
the LD_LIBRARY_PATH variable. These are:

${BXD_PATH}/VTK/lib
${BXD_PATH}/VTK/lib/vtk-5.6
${BXD_PATH}/ITK/lib/InsightToolkit
${BXD_PATH}/ITK/lib/InsightToolkit/WrapITK/lib

For example add following lines to you .bashrc file:
BXD_PATH="Put your path to BioImageXD here"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${BXD_PATH}/VTK/lib:${BXD_PATH}/VTK/lib/vtk-5.6:${BXD_PATH}/ITK/lib/InsightToolkit:${BXD_PATH}/ITK/lib/InsightToolkit/WrapITK/lib
