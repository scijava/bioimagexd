#! /bin/sh
if [ "$1" = "" ]; then
   echo "Usage: code_code.sh <vtk directory> [copy]"
   echo "Where <vtk directory> is the directory for the VTK source code"
   exit
fi
VTKDIR=$1

function add_to_cmakelist() {
   CMAKELISTS=$1
   ADD_FILE=$2
   cat $CMAKELISTS|sed s/"Kit_SRCS"/"Kit_SRCS\n$ADD_FILE"/ > $CMAKELISTS.new
   echo "Writing $ADD_FILE to $CMAKELISTS..."
   mv -f $CMAKELISTS $CMAKELISTS.old
   mv -f $CMAKELISTS.new $CMAKELISTS
}

CMD="ln -s"
if [ "$2" = "copy" ]; then
   CMD=cp
fi

for i in `grep -H IMAGING *.h|cut -d: -f1`
do
  FILE=$PWD/$i
  $CMD $FILE $VTKDIR/Imaging/$i
  cxxfile=`echo $i|sed s/h$/cxx/`
  $CMD $PWD/$cxxfile $VTKDIR/Imaging/$cxxfile
  add_to_cmakelist $VTKDIR/Imaging/CMakeLists.txt $cxxfile
done
for i in `grep -H FILTERING *.h|cut -d: -f1`
do
  FILE=$PWD/$i
  $CMD $FILE $VTKDIR/Filtering/$i
  cxxfile=`echo $i|sed s/h$/cxx/`
  $CMD $PWD/$cxxfile $VTKDIR/Filtering/$cxxfile
  add_to_cmakelist $VTKDIR/Filtering/CMakeLists.txt $cxxfile

done
