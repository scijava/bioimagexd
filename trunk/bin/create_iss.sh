#! /bin/sh
/bin/sh bin/build_innosetup.sh > temp.txt
REPL="`cat temp.txt`"
cat BioImageXD_template.iss | sed s/__FILES__/$REPL/g > BioImageXD.iss