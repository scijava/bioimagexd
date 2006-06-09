; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
AppName=BioImageXD
AppVerName=BioImageXD prebeta 0.9.1-5
AppPublisher=BioImageXD development team
AppPublisherURL=http://www.bioimagexd.org/
AppSupportURL=http://www.bioimagexd.org/
AppUpdatesURL=http://www.bioimagexd.org/
DefaultDirName={pf}\BioImageXD
DefaultGroupName=BioImageXD
SourceDir=C:\BioImageXD
AllowNoIcons=yes
LicenseFile=C:\BioImageXD\GPL.txt
OutputDir=C:\temp
OutputBaseFilename=setup
SetupIconFile=C:\BioImageXD\trunk\Icons\logo.ico
Compression=lzma/max
SolidCompression=yes

[Languages]
Name: "eng"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\BioImageXD\trunk\dist\BioImageXD.exe"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\bz2.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\multiarray.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\py2exe_util.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\pyexpat.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\python24.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\python_libs.zip"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\umath.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\unicodedata.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkCommon.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkCommonPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkCommonPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkDICOMParser.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkexoIIc.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkexpat.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkFiltering.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkFilteringPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkFilteringPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkfreetype.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkftgl.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkGenericFiltering.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkGenericFilteringPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkGenericFilteringPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkGraphics.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkGraphicsPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkGraphicsPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkHybrid.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkHybridPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkHybridPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkImaging.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkImagingPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkImagingPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkIO.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkIOPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkIOPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkjpeg.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkNetCDF.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkParallel.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkParallelPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkParallelPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkpng.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkRendering.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkRenderingPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkRenderingPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtksys.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtktiff.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkVolumeRendering.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkVolumeRenderingPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkVolumeRenderingPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkWidgets.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkWidgetsPython.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkWidgetsPythonD.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\vtkzlib.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\w9xpopen.exe"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\wxmsw26uh_gl_vc.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\wxmsw26uh_stc_vc.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\wxmsw26uh_vc.dll"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\zlib.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_controls_.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_core_.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_gdi_.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_glcanvas.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_html.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_misc_.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_numpy.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_socket.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_ssl.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_stc.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_tkinter.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_windows_.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\_wizard.pyd"; DestDir: "{app}";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Bin\build_innosetup.sh"; DestDir: "{app}\Bin";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Bin\copy_code.sh"; DestDir: "{app}\Bin";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Bin\ffmpeg.exe"; DestDir: "{app}\Bin";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Bin\install_classes.sh"; DestDir: "{app}\Bin";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Bin\install_vtk.sh"; DestDir: "{app}\Bin";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\3d.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\adjust.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\colocalization.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\contents.hhc"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\gallery.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\help.hhp"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\Index.hhk"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\index.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\merge.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\process.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\reference.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\sections.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\slices.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\starthere.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\tips.txt"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Help\usersguide.html"; DestDir: "{app}\Help";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\add_keyframe.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\arrow.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\BioImageXD.icns"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\camera.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\circle.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\delete_annotation.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\draw.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\keyframe_track.JPG"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\leftarrow.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\logo.ico"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\logo.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\logo_medium.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\open.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\open_dataset.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\open_settings.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\pause.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\play.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\polygon.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\rectangle.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\rightarrow.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\save.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\save_settings.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\save_snapshot.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\scale.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\splash.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\splash2.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\spline_random.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\spline_rotate_x.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\spline_rotate_y.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\spline_stop.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\spline_track.JPG"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\stop.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\task_adjust.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\task_animator.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\task_colocalization.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\task_manipulate.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\task_measure.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\task_merge.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\task_process.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\timepoint.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\timepoint_track.JPG"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\tree.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\view_gallery.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\view_rendering.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\view_rendering_3d.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\view_sections.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\view_slices.jpg"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\zoom-in.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\zoom-object.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\zoom-out.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Icons\zoom-to-fit.gif"; DestDir: "{app}\Icons";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\DynamicLoader.py"; DestDir: "{app}\Modules";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\__init__.py"; DestDir: "{app}\Modules";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Readers\BioradDataSource.py"; DestDir: "{app}\Modules\Readers";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Readers\BXDDataSource.py"; DestDir: "{app}\Modules\Readers";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Readers\LeicaDataSource.py"; DestDir: "{app}\Modules\Readers";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Readers\LSMDataSource.py"; DestDir: "{app}\Modules\Readers";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Readers\OlympusDataSource.py"; DestDir: "{app}\Modules\Readers";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\Angle.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\ArbitrarySlicer.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\Axes.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\ClippingPlane.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\Distance.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\Orthogonal.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\ScaleBar.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\Spline.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\Surface.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\Volume.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Rendering\WarpScalar.py"; DestDir: "{app}\Modules\Rendering";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\Adjust.py"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\Adjust.pyc"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\AdjustDataUnit.py"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\AdjustDataUnit.pyc"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\AdjustPanel.py"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\AdjustPanel.pyc"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\AdjustSettings.py"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\AdjustSettings.pyc"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\__init__.py"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Adjust\__init__.pyc"; DestDir: "{app}\Modules\Task\Adjust";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\Colocalization.py"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\Colocalization.pyc"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\ColocalizationPanel.py"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\ColocalizationPanel.pyc"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\ColocalizationSettings.py"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\ColocalizationSettings.pyc"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\__init__.py"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Coloc\__init__.pyc"; DestDir: "{app}\Modules\Task\Coloc";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\Manipulation.py"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\Manipulation.pyc"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationDataUnit.py"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationDataUnit.pyc"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationFilters.py"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationFilters.pyc"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationPanel.py"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationPanel.pyc"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationSettings.py"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\ManipulationSettings.pyc"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\__init__.py"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Manipulation\__init__.pyc"; DestDir: "{app}\Modules\Task\Manipulation";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\Merging.py"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\Merging.pyc"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\MergingDataUnit.py"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\MergingDataUnit.pyc"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\MergingPanel.py"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\MergingPanel.pyc"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\MergingSettings.py"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\MergingSettings.pyc"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\__init__.py"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Task\Merging\__init__.pyc"; DestDir: "{app}\Modules\Task\Merging";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Visualization\Animator.py"; DestDir: "{app}\Modules\Visualization";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Visualization\Gallery.py"; DestDir: "{app}\Modules\Visualization";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Visualization\Info.py"; DestDir: "{app}\Modules\Visualization";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Visualization\Rendering.py"; DestDir: "{app}\Modules\Visualization";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Visualization\Sections.py"; DestDir: "{app}\Modules\Visualization";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Visualization\Simple.py"; DestDir: "{app}\Modules\Visualization";  Flags: ignoreversion
Source: "C:\BioImageXD\trunk\dist\Modules\Visualization\Slices.py"; DestDir: "{app}\Modules\Visualization";  Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files
;
;
; ALWAYS LEAVE THESE HERE
Source: "vcredist_x86.exe"; Flags: dontcopy
Source: "C:\BioImageXD\trunk\bin\BioImageXD.exe.manifest"; DestDir: "{app}";  Flags: ignoreversion

[Code]
function InitializeSetup: Boolean;
var
  ResultCode: Integer;
begin
  // Show the contents of Readme.txt in a message box
  ExtractTemporaryFile('vcredist_x86.exe');
  MsgBox('The installer will first install the C++ Runtime libraries required to run the software.',mbInformation, MB_OK);
  // Launch Notepad and wait for it to terminate
  if Exec(ExpandConstant('{tmp}\vcredist_x86.exe'), '', '', SW_SHOW,     ewWaitUntilTerminated, ResultCode) then
  begin
    // handle success if necessary; ResultCode contains the exit code
    if ResultCode = 0 then
    begin
       Result := True;
    end
    else begin
       Result := False;
    end
  end
//    MsgBox('Result code='+IntToStr(ResultCode)+'.',mbInformation,MB_OK);

end;


[INI]
Filename: "{app}\BioImageXD.url"; Section: "InternetShortcut"; Key: "URL"; String: "http://www.bioimagexd.org/"

[Icons]
Name: "{group}\BioImageXD"; Filename: "{app}\BioImageXD.exe";
Name: "{group}\{cm:ProgramOnTheWeb,BioImageXD}"; Filename: "{app}\BioImageXD.url"
Name: "{group}\{cm:UninstallProgram,BioImageXD}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\BioImageXD"; Filename: "{app}\BioImageXD.exe"; Tasks: desktopicon;

[Run]
Filename: "{app}\BioImageXD.exe"; Description: "{cm:LaunchProgram,BioImageXD}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\BioImageXD.url"
Type: filesandordirs; Name: "{app}\Modules"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\BioImageXD.ini"
