#! /bin/sh -x

# This script should be run from the main BioImageXD directory

if [ -d "ITK-pkg" ]; then
  	echo "ITK-pkg already exists"
  	exit
fi
mkdir "ITK-pkg" # Makes directory ITK-pkg where ITK files will be copied
cd ITK-pkg
mkdir lib
mkdir lib/Release
mkdir Python
mkdir Python/Release
mkdir Python/Configuration
mkdir Python/Release/itkExtras

echo "Created ITK-pkg directory"

# Next we copy all dlls from the directory where ITK was build to
# ITK-pkg/lib/Release and rename those by pyd file type, except two exceptions
for i in /cygdrive/c/BioImageXD/wrapITK/lib/Release/*.dll
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

# Next copy ITKCommon.dll
cp /cygdrive/c/BioImageXD/ITK-3.20/bin/Release/ITKCommon.dll lib/Release
# Next copy every pyd file from the directory where ITK was build
cp /cygdrive/c/BioImageXD/wrapITK/lib/Release/*.pyd lib/Release
# Copy specific manifest file from BioImageXD/bin directory
cp /cygdrive/c/BioImageXD/trunk/bin/Microsoft.VC90.CRT.ITK.manifest lib/Release/Microsoft.VC90.CRT.manifest

# Then we copy all py files from the ITK installation directory created by
# WrapITK. These files include all python modules for ITK classes
# (example file itkThresholdImageFilter.py)
cp /cygdrive/c/BioImageXD/wrapITK/lib/*.py Python/Release
# Copy all py files installed in ITK/Wrapping/WrapITK.
# These files include different ITK modules like Filtering.py and Review.py
cp /cygdrive/c/BioImageXD/wrapITK/Languages/Python/Release/*.py Python/Release

# Then copy rest of the stuff build when ITK was wrapped. This is probably not
# even needed but copy it to be sure.
cp /cygdrive/c/BioImageXD/wrapITK/Languages/Python/itkExtras/__init__.py Python/Release/itkExtras
# Copy configuration files of Python wrapping like FilteringConfig.py.
# These as well are not even needed. But haven't tested without those.
cp /cygdrive/c/BioImageXD/wrapITK/Languages/Python/Configuration/*.py Python/Configuration

# Copy ItkVtkGlue and labelShape external projects. BASE here defines base
# directory that includes both projects. Copy all py, pyd and configuration
# files. If these are originally build where ITK is also build then these
# steps can be skipped as all of these files are already copied when ITK
# was copied.
for extproj in ItkVtkGlue #labelShape
do
	BASE="/cygdrive/c/BioImageXD/wrapITK/maint-read-only/ExternalProjects/${extproj}"
	cp $BASE/lib/*.py Python/Release
	cp $BASE/lib/Release/*.pyd lib/Release
	cp $BASE/Wrapping/Languages/Python/Configuration/* Python/Configuration
	#cp $BASE/Wrapping/Languages/Python/*.py Python/Release
done

# Do same as earlier for external projects to itkBXD
for extproj in itkBXD
do
	BASE="/cygdrive/c/BioImageXD/trunk/${extproj}"
	cp $BASE/lib/*.py Python/Release
	cp $BASE/lib/Release/*.pyd lib/Release
	cp $BASE/Wrapping/Languages/Python/Configuration/* Python/Configuration
	#cp $BASE/Python/Release/*.py Python/Release
done

# Change rights in Cygwin that it is possible to make a package out of these
# files.
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
