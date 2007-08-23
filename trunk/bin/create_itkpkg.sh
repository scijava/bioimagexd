#! /bin/sh -x
if [ -d "ITK-pkg" ]; then
  	echo "ITK-pkg already exists"
  	exit
fi
mkdir "ITK-pkg"
cd ITK-pkg
mkdir lib
mkdir Python

echo "Created ITK-pkg directory"
for i in /c/BioImageXD/InsightToolkit/bin/*.dll
do
	TGT="`basename $i | sed s/dll/pyd/g`"
	if [ "$TGT" = "ITKCommon.pyd" ]; then
		TGT="ITKCommon.dll"
	fi
	if [ "$TGT" = "SwigRuntimePython.pyd" ]; then
	  	TGT="SwigRuntimePython.dll"
	fi
    cp $i lib/$TGT

done
for i in /c/BioImageXD/InsightToolkit/bin/*.py
do
	cp $i Python
done

cp /c/BioImageXD/InsightToolkit/Wrapping/WrapITK/Python/*.py Python

cp -fr /c/BioImageXD/InsightToolkit/Wrapping/WrapITK/Python/itkExtras Python
cp -fr /c/BioImageXD/InsightToolkit/Wrapping/WrapITK/Python/Configuration Python

for extproj in ItkVtkGlue labelShape
do
	BASE="/c/BioImageXD/InsightToolkit/Wrapping/WrapITK/ExternalProjects/${extproj}"
	cp $BASE/lib/*.py Python
	for i in $BASE/lib/*.dll
	do
		TGT="`basename $i | sed s/dll/pyd/g`"
		cp $i lib/$TGT
	done


	cp -fr $BASE/Python/Configuration/ Python
	cp $BASE/Python/*.py Python
done