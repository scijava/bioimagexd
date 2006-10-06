#! /bin/sh
FROMDIR='C:\\BioImageXD\\trunk\\dist'
cd dist
for dir in `find . -type d`
do
for file in `find $dir -type f -maxdepth 1`
do
  FILE="`echo $file|sed s/"."/"$FROMDIR"/|tr / '\\\\'`"
  DIR="`echo $dir|sed s/"."/"{app}"/|tr / '\\\\'`"
  if [ "$DIR" = "." ]; then
     TODIR="{app}"
  else
    TODIR=$DIR
  fi
  echo "Source: \"$FILE\"; DestDir: \"$TODIR\";  Flags: ignoreversion"
done
done

FROMDIR2='C:\\BioImageXD\\trunk\\ITK-pkg'
cd ../ITK-pkg
for dir in `find . -type d`
do
for file in `find $dir -type f -maxdepth 1`
do
  FILE="`echo $file|sed s/"."/"$FROMDIR2"/|tr / '\\\\'`"
  DIR="`echo $dir|sed s/"."/"{app}\\ITK-pkg"/|tr / '\\\\'`"
  if [ "$DIR" = "." ]; then
     TODIR="{app}"
  else
    TODIR="$DIR\\"
  fi
  echo "Source: \"$FILE\"; DestDir: \"$TODIR\";  Flags: ignoreversion"
done
done
