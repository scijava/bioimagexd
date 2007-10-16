#! /bin/sh
if [ "$1" = "" ]; then
   echo "Usage: build_installer.sh <svn revision>"
   exit
fi
TGT=BioImageXD-beta-r$1.exe
/bin/sh bin/create_iss.sh
"/cygdrive/c/Program Files/Inno Setup 5/iscc" BioImageXD.iss
mv /cygdrive/c/Temp/Setup.exe /cygdrive/c/temp/${TGT}
echo curl -T "C:\\Temp\\${TGT}" -u anonymous:kalle.pahajoki@gmail.com ftp://upload.sourceforge.net/incoming/

