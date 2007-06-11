#! /bin/bash

VTK_SOURCE_DIR="/Users/kallepahajoki/VTK"

if [ "$1" != "" ]; then
    VTK_SOURCE_DIR=$1
fi

if [ ! -d $VTK_SOURCE_DIR ]; then
    echo "The VTK source directory specified does not exist"    
    echo "Current VTK directory: $VTK_SOURCE_DIRECTORY"
    echo "You can either edit this script to change it permanently, or"
    echo "Give it as an argument ot this script."
    echo "Example:"
    echo "# sudo sh fix_install_names.sh ~/VTK"
    exit
fi


VTK_SOURCE_DIR="${VTK_SOURCE_DIR}/bin"

cd /Library/Frameworks/Python.framework/Versions/2.5/lib

LIBS="`echo *.dylib`"
for lib in $LIBS
do
  DEPS="`otool -L  $lib |grep -v /|cut -d' ' -f1`"
  for dep in $DEPS
  do
     install_name_tool -change $dep /Library/Frameworks/Python.framework/Versions/2.5/lib/$dep $lib
  done
done

cd /Library/Frameworks/Python.framework/Versions/2.5/lib/InsightToolkit/WrapITK/lib
LIBS="`echo _ItkVtkGluePython.so`"
#for lib in $LIBS
#do
#  DEPS="`otool -L  $lib |grep /Users |grep -v vtk|cut -d' ' -f1`"
#  for dep in $DEPS
#  do
#     ndep="`basename $dep`"
#     install_name_tool -change $dep /Library/Frameworks/Python.framework/Versions/2.5/lib/InsightToolkit/$ndep $lib
#  done
#done
LIBS="`echo _ItkVtkGluePython.so`"
for lib in $LIBS
do
  DEPS="`otool -L  $lib |grep vtk|cut -d' ' -f1`"
  for dep in $DEPS
  do
     ndep="`basename $dep`"
     install_name_tool -change $dep /Library/Frameworks/Python.framework/Versions/2.5/lib/$ndep $lib
  done
done


LIBS="/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/vtkbxd/libvtkBXDProcessingPython.so"

cd /Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/
if [ -d vtk ]; then
    cd vtk
elif [ -d VTK-*.egg ]; then
    cd VTK-*.egg/vtk
fi

LIBS="$LIBS `echo *.so`"
for lib in $LIBS
do
    DEPS="`otool -L  $lib |grep -v /|cut -d' ' -f1`"
    for dep in $DEPS
    do
	  install_name_tool -change $dep /Library/Frameworks/Python.framework/Versions/2.5/lib/$dep $lib
    done
    DEPS="`otool -L  $lib |grep $VTK_SOURCE_DIR|cut -d' ' -f1`"
    for dep in $DEPS
    do
	  ndep="`echo $dep | sed s,$VTK_SOURCE_DIR,,`"
	  install_name_tool -change $dep /Library/Frameworks/Python.framework/Versions/2.5/lib/$ndep $lib
    done

done
