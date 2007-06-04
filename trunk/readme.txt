BioImageXD - A post processing program, analysis and 3D visualisation program for LSCM data

The directory layout of the source code:

|
+-BioImageXD.py     The main program, used to launch the software
|
+-Configuration.py  Code for reading / writing configuration files
|
+-Logging.py        Code for doing logging with keywords that can be enabled / disabled
|
+-build_app.py      The code for building py2app or py2exe application bundles
|
+-optimize.py       Code for doing various runtime optimizations of the VTK pipeline
|
+-scripting.py      A module that provides functions, variables etc. intented specifically for 
|                   scripting. Often imported as bxd for brevity
|
+-template.py       A template file that indicates the basic coding style
|
+-GUI/              The directory containing all (or most) GUI related code
|    |
|    +-PreviewFrame     The directory containing the different 2D views
|    |
|    +-Urmas            The animator code
|    |
|    +-ogl              Code for ogl (http://wiki.wxpython.org/wxOGL) modified for Mac support
|
+-Help/              The help files used in the software
|
+-Icons/             The icons used in the software
|
+-LUT/               Palette (LUT = LookUpTable) files
|
+-Licensing/         All the different licenses
|
+-Modules/           A subdirectory for different dynamically loaded modules
|        |
|        +-DynamicLoader.py     A module with methods for the dynamic loading of the various "plugins"
|        |
|        +-Readers/             A directory for the different data sources
|        |
|        +-Rendering/           A directory for the different rendering modules for 3D view
|        |
|        +-Task/                A directory containing the different task modules
|        |
|        +-Visualization/       A directory containing the different visualization modes
|                               Note that modules in this directory utilize the classes in GUI/PreviewFrame
|
+-Visualizer/           A directory containing the code that forms the core of the visualizer
|                       Somewhat illogically, some of the code (e.g. module configuration GUI base classes)
|                       utilized by the 3D rendering mode are located here
|
+-bin/                  A directory that contains e.g. the various program binaries required
|                       by BioImageXD (e.g. ffmpeg). Also scripts that help with various 
|                       development tasks
|
+-lib/                  A directory with some basic building blocks of the software
|    |
|    +-Command.py       A class that is used for the Undo/Redo actions and recording of user actions
|    |
|    +-DataSource/      A directory with the base classes for data sources (and the writer classes)
|    |
|    +-DataUnit/        A directory with the base classes for data units 
|    |
|    +-FilterBasedModule.py     A base class for the data processing modules utilized by task modes
|    |                          that are based on the filter stack model used in e.g. the Process task
|    |
|    +-ImageOperations.py       Various functions for doing image processing related tasks
|    |
|    +-Module.py                A base class for all data processing modules used by task modes
|    |
|    +-Particle.py              Tracking related code
|    |
|    +-ProcessingFilter.py      A base class for all filters for the filter stack- type task modes
|    |
|    +-RenderingInterface.py    An interface for controlling the rendering in the animator, that used
|    |                          to direct an external rendering program but now is just an interface
|    |                          to the 3D view
|    |
|    +-Track.py         Code for reading / writing out track info
|    |
|    +-messenger.py     A module for the message passing interface utilized in the software
|    |
|    +-persistence/     A module for persisting python objects that is not utilized much
|                       messenger and persistence come from mayavi 2 codebase
|
+-vtkBXD/               The directory containing the VTK project with our own image processing classes
        |
        +-CMakeLists.txt    The file defining how the project is built
        |
        +-Processing/       The directory containing the actual processing classes
        |
        +-Wrapping/         The directory containing the wrapping code
        