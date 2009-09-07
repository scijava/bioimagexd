#! /bin/sh -x
if [ -d "ITK-pkg" ]; then
  	echo "ITK-pkg already exists"
  	exit
fi
mkdir "ITK-pkg"
cd ITK-pkg
mkdir lib
mkdir lib/Release
mkdir Python
mkdir Python/Release
mkdir Python/Configuration
mkdir Python/Release/itkExtras

echo "Created ITK-pkg directory"
for i in /cygdrive/c/BioImageXD/ITK/bin/Release/*.dll
do
	TGT="`basename $i | sed s/dll/pyd/g`"
	if [ "$TGT" = "ITKCommon.pyd" ]; then
		TGT="ITKCommon.dll"
	fi
	if [ "$TGT" = "SwigRuntimePython.pyd" ]; then
	  	TGT="SwigRuntimePython.dll"
	fi
    cp $i lib/Release/$TGT
done

cp /cygdrive/c/BioImageXD/ITK/bin/Release/*.pyd lib/Release
cp /cygdrive/c/BioImageXD/trunk/bin/Microsoft.VC90.CRT.ITK.manifest lib/Release/Microsoft.VC90.CRT.manifest
#cp /cygdrive/c/BioImageXD/InsightToolkit/lib/Release/*.pyd lib


cp /cygdrive/c/BioImageXD/ITK/bin/Release/*.py Python/Release
cp /cygdrive/c/BioImageXD/ITK/Wrapping/WrapITK/Python/Release/*.py Python/Release

cp /cygdrive/c/BioImageXD/ITK/Wrapping/WrapITK/Python/itkExtras/__init__.py Python/Release/itkExtras
cp -fr /cygdrive/c/BioImageXD/ITK/Wrapping/WrapITK/Python/Configuration Python

#cp /cygdrive/c/BioImageXD/InsightToolkit/lib/Release/*.py Python
#cp /cygdrive/c/BioImageXD/InsightToolkit/Python/Release/*.py Python
#cp /cygdrive/c/BioImageXD/InsightToolkit/Python/Configuration/*.py Python

for extproj in ItkVtkGlue labelShape
do
	BASE="/cygdrive/c/BioImageXD/InsightToolkit-3.14.0/Wrapping/WrapITK/ExternalProjects/${extproj}"
	cp $BASE/lib/Release/*.py Python/Release
	cp $BASE/lib/Release/*.pyd lib/Release
	#for i in $BASE/lib/Release/*.dll
	#do
	#	TGT="`basename $i | sed s/dll/pyd/g`"
	#	cp $BASE/lib/Release/$TGT lib/Release/$TGT
	#done

	cp -fr $BASE/Python/Configuration/ Python
	cp $BASE/Python/Release/*.py Python/Release
done

for extproj in itkBXD
do
	BASE="/cygdrive/c/BioImageXD/trunk/${extproj}"
	cp $BASE/lib/Release/*.py Python/Release
	cp $BASE/lib/Release/*.pyd lib/Release
	#for i in $BASE/lib/Release/*.dll
	#do
	#	TGT="`basename $i | sed s/dll/pyd/g`"
	#	cp $BASE/lib/Release/$TGT lib/Release/$TGT
	#done

	cp -fr $BASE/Python/Configuration/ Python
	cp $BASE/Python/Release/*.py Python/Release
done

chmod 644 lib/*
chmod 755 lib/Release/*
chmod 644 Python/*
chmod 644 Python/Release/*
chmod 644 Python/Configuration/*
chmod 644 Python/Release/itkExtras/*
chmod 755 lib
chmod 755 lib/Release
chmod 755 Python
chmod 755 Python/Release
chmod 755 Python/Configuration
chmod 755 Python/Release/itkExtras