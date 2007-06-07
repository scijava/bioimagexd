#! /bin/bash
VTK_SOURCE_DIR="/Users/kallepahajoki/VTK/bin/"
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
cd /Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/VTK-*.egg/vtk
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
