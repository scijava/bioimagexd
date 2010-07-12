Before running the program you need to add paths of VTK and ITK libraries to
the LD_LIBRARY_PATH variable. These are:

${path_to_BioImageXD}/VTK/lib
${path_to_BioImageXD}/VTK/lib/vtk-5.6
${path_to_BioImageXD}/ITK/lib/InsightToolkit
${path_to_BioImageXD}/ITK/lib/InsightToolkit/WrapITK/lib

For example add following line to you .bashrc file (and replace all ${path_to_BioImageXD} by real path to the program):
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${path_to_BioImageXD}/VTK/lib:${path_to_BioImageXD}/VTK/lib/vtk-5.6:${path_to_BioImageXD}/ITK/lib/InsightToolkit:${path_to_BioImageXD}/ITK/lib/InsightToolkit/WrapITK/lib
