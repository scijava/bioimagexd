#! /bin/sh
if [ "$2" = "" ]; then
echo "Usage: install_classes.sh <BioImageXD directory> <VTK directory>"
exit
fi

INSTALL="IO Imaging Filtering Widgets"
CP_CMD="cp"

CPPDIR=$1/C++
IMAGING=$2/Imaging
FILTERING=$2/Filtering
WIDGETS=$2/Widgets
IO=$2/IO

insert_to_cmakelists() {
  cxxfile=$1
  cmakefile=$2/CMakeLists.txt
 
 awk '{print} 
 /^SET.*Kit_SRCS/ && already == 0 {
 print cxxfile
 already=1
 }' cxxfile="$cxxfile" < $cmakefile > CMakeLists.new

  mv -f CMakeLists.new $cmakefile

}

if [ "`echo $INSTALL|grep Imaging`" ]
then
  for i in vtkImageColorMerge vtkImageAlphaFilter vtkImageColocalizationFilter vtkImageColocalizationTest \
  vtkImageMapToIntensities vtkImageSimpleMIP vtkImageSolitaryFilter
  do
    echo "Copying $i.cxx..."
    $CP_CMD $CPPDIR/$i.cxx $IMAGING
    $CP_CMD $CPPDIR/$i.h $IMAGING
    if [ "`grep $i $IMAGING/CMakeLists.txt`" = "" ]; then
       echo "Inserting $i.cxx to CMakeLists.txt"
       insert_to_cmakelists $i.cxx $IMAGING
    else
       echo "$i.cxx already in CMakeLists.txt"
    fi
  done
fi

if [ "`echo $INSTALL|grep Filtering`" ]
  then
  for i in vtkIntensityTransferFunction vtkImageAutoThresholdColocalization
  do
    echo "Copying $i.cxx..."
    $CP_CMD $CPPDIR/$i.cxx $FILTERING
    $CP_CMD $CPPDIR/$i.h $FILTERING
    if [ "`grep $i $FILTERING/CMakeLists.txt`" = "" ]; then
       echo "Inserting $i.cxx to CMakeLists.txt"
       insert_to_cmakelists $i.cxx $FILTERING
    else
       echo "$i.cxx already in CMakeLists.txt"
    fi
  done
fi

if [ "`echo $INSTALL|grep Widgets`" ]
then
  for i in vtkDistanceRepresentationScaled2D
  do
    echo "Copying $i.cxx..."
    $CP_CMD $CPPDIR/$i.cxx $WIDGETS
    $CP_CMD $CPPDIR/$i.h $WIDGETS
    if [ "`grep $i $WIDGETS/CMakeLists.txt`" = "" ]; then
       echo "Inserting $i.cxx to CMakeLists.txt"
       insert_to_cmakelists $i.cxx $WIDGETS
    else
       echo "$i.cxx already in CMakeLists.txt"
    fi
  done
fi

if [ "`echo $INSTALL|grep IO`" ]
then
  for i in vtkExtTIFFReader vtkLSMReader
  do
    echo "Copying $i.cxx..."
    $CP_CMD $CPPDIR/$i.cxx $IO
    $CP_CMD $CPPDIR/$i.h $IO
    if [ "`grep $i $IO/CMakeLists.txt`" = "" ]; then
       echo "Inserting $i.cxx to CMakeLists.txt"
       insert_to_cmakelists $i.cxx $IO
    else
       echo "$i.cxx already in CMakeLists.txt"
    fi
  done
fi


