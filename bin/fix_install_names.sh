#! /bin/bash
#LIBS="libvtkBXDProcessing.dylib libvtkBXDProcessingPythonD.dylib python2.5/site-packages/vtkbxd//libvtkBXDProcessingPython.so"
#LIBS=".python2.5/site-packages/vtkbxd//libvtkBXDProcessingPython.so"
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

lib="/Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/site-packages/vtkbxd/libvtkBXDProcessingPython.so"
DEPS="`otool -L  $lib |grep -v /|cut -d' ' -f1`"
for dep in $DEPS
do
    install_name_tool -change $dep /Library/Frameworks/Python.framework/Versions/2.5/lib/$dep $lib
done
