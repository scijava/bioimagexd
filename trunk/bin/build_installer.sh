#! /bin/sh
if [ "$1" = "" ]; then
   echo "Usage: build_installer.sh <svn revision>"
   exit
fi
#echo "VERSION=\"beta-$1\"" > bxdversion.py
TGT=BioImageXD-beta-r$1.exe
/bin/sh bin/create_iss.sh

# Following expects that a directory of Inno Setup, change it to be something
# else if that is not correct. Also it is assumed that there is directory
# C:\temp in your system where Inno setup builds the package
"/cygdrive/c/Program Files (x86)/Inno Setup 5/iscc" BioImageXD.iss
mv /cygdrive/c/temp/setup.exe /cygdrive/c/temp/${TGT}
