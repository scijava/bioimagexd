#! /bin/sh
if [ "$1" = "" ]; then
  echo "Usage: install_vtk.sh <VTK directory> [python version]"  
 echo "Python version defaults to 2.4"
echo ""
echo "Example:"
echo "install_vtk.sh /home/dan/VTK 2.4"
 exit
fi
cd $1
PYTHONVER=2.4
if [ "$2" != "" ]; then
  PYTHONVER=$2
fi
PYTHONDIR=/usr/lib/python$PYTHONVER/site-packages/
DIR=/usr/lib/python$PYTHONVER/site-packages/vtk_cvs
mkdir $DIR
echo "Copying libraries to $DIR"
cp bin/* $DIR
echo "Copying wrapping files to $DIR"

cp -f Wrapping/Python/*.{py,pth} $DIR
cp -fr Wrapping/Python/vtk $DIR
echo "Making vtk-cvs the default vtk"
echo "vtk_cvs" > $PYTHONDIR/vtk.pth
