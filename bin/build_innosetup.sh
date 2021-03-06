#! /bin/sh
# This is the directory where py2exe build everything needed bu BXD except ITK
FROMDIR='C:\\BioImageXD\\sourceforge\\dist'
cd dist

function add_files {
    FILES=$*
    for file in $FILES
    do
        if [ ! -d "$file" ]; then
            DIR=`dirname $file`
            echo "Source: \"$file\"; DestDir: \"$DIR\"; Flags: ignoreversion"
        fi
    done | sed s/'DestDir: ".'/'DestDir: "{app}'/g
}

function add_itk_files {
    FILES=$*
    for file in $FILES
    do
        if [ ! -d "$file" ]; then
            DIR=`dirname $file`
            echo "Source: \"$file\"; DestDir: \"$DIR\"; Flags: ignoreversion"
        fi
    done | sed s/'DestDir: ".'/'DestDir: "{app}\\ITK-pkg'/g
}


FILES=`find .`
add_files $FILES|tr / '\\\\'|sed s/'Source: ".'/"Source: \"$FROMDIR"/g
cd ..

cd 'C:\\BioImageXD\\trunk\\ITK-pkg'
FROMDIR='C:\\BioImageXD\\trunk\\ITK-pkg'
FILES=`find .`
add_itk_files  $FILES|tr / '\\\\'|sed s/'Source: ".'/"Source: \"$FROMDIR"/g

