#! /bin/sh
FROMDIR='C:\\BioImageXD\\bioimagexd\\dist'
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
FROMDIR='C:\\BioImageXD\\trunk\\ITK-pkg'
cd "$FROMDIR"

FILES=`find .`
add_itk_files  $FILES|tr / '\\\\'|sed s/'Source: ".'/"Source: \"$FROMDIR"/g

