#!/bin/sh
if [ ! -d ../sourceforge ]; then
	echo "The directory ../sourceforge does not exist"
	echo "Check out the sourceforge repository before running this script"
	echo "Command for checking out the SVN:"
	echo 
	echo "svn co https://bioimagexd.svn.sourceforge.net/svnroot/bioimagexd/bioimagexd/trunk ../sourceforge"
	exit
fi
curr=$PWD
cd ../sourceforge
svn up
cd $curr
svn update
rm -fr ../clean-exp
echo "Exporting repository to clean directory"
svn export . ../clean-exp
cd ..

echo "Copying files from clean export to sourceforge"
find clean-exp -type f | while read file
do
  cp "$file" "`echo $file|sed s/clean-exp/sourceforge/`"
done 
#echo "Remember to set the t-flag"
echo "Modifying T-flag"
perl -i -p -e 's/TFLag = 0/TFLag = 1/g' sourceforge/scripting.py
cd sourceforge
# Do not update build_innosetup.sh
echo "Remove bin/build_innosetup.sh from commit"
rm bin/build_innosetup.sh
echo
echo "Possibly modified files:"
svn stat|grep "^?"|grep -v ".pyc$"

echo "Committing to sourceforge"
if [ "$1" ]
then
	svn commit -m "$1"
else
	svn commit -m "Update from internal repository to sourceforge"
fi
