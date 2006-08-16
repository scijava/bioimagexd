BioImageXD - A post processing program, analysis and 3D visualisation program for LSCM data

This software requires Python, wxPython, VTK and ffmpeg to function properly.
To run the software, execute the BioImageXD.py

The following may be out of date, look at the sources and you can easily see the structure:

The layout of the BioImageXD source tree:
|
|_ Module.py    - The base class for all modules
|
|_ LSM
|   |
|   |_ GUI      - The directory containing all the GUI classes
|   |
|   |_ Main.py  - The Main program
|   |
|   |_ *.py     - Data structures and various modules that do non-GUI stuff
|
|
|_ VSIA             - The module for Visualization of Sparse Intensity Aggregations
|
|_ Colocalization   - The module for creating a colocalization map
|
|_ ColorMerging     - The module for merging two or more dataset series
|
|
|_ DataUnitProcessing  - The module for processing a single dataunit
|
|_ RunTests.py      - Program that runs all the unit tests
|
|_ Tests            - A directory containing all the unit tests. There are not many of them
|   |
|   |_ __init__.py      - Initialization module, imports all other modules and returns them with the getSuites() method
|   |
|   |_ ModuleTests.py   - Module containing unit tests for the processing modules
|   |
|   |_ IntensityTransferTests.py -  Tests for the intensity transfer function
|   |
|   |_ DataUnitTests.py          -  Tests for the data structures
|
|
|
|_ mayavi       - Our version of mayavi with some modifications

