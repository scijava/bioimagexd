#! /bin/sh
if [ "$1" = "" ]; then
   echo "Usage: build_installer.sh <svn revision>"
   exit
fi
echo "VERSION=\"beta-$1\"" > bxdversion.py
#cmd /C 'bin\runpy2exe.bat'
TGT=BioImageXD-beta-r$1.exe
/bin/sh bin/create_iss.sh
"/cygdrive/c/Program Files/Inno Setup 5/iscc" BioImageXD.iss
mv /cygdrive/c/temp/setup.exe /cygdrive/c/temp/${TGT}
