# A short intro into what's going on
# 1. We load the task modules and readers using the dynamicloader
# 2. We take the LSM reader and load all channels from an LSM file (change the path!)
# 3. We take a merging data unit (a unit specific to merging task that inherits from CombinedDataUnit)
#    and give it the loaded lsm channels as source data units
# 4. We set the processing module of the merging dataunit to the merging processing module
# 5. We process the first timepoint of the data, which writes out the processed dataset
# 6. We also do a preview, which instead of writing the data out, returns it
# 7. We then do a MIP of the data we got from preview

import sys
import os
import vtk
# This is currently necessary, but should ideally be eliminated
#bxddir = os.path.join(os.getcwd(),"..")
os.chdir("..")
bxddir  = os.getcwd()
sys.path.insert(0, bxddir)

sys.path.insert(0, os.path.join(bxddir, "lib"))
sys.path.insert(0, os.path.join(bxddir, "GUI"))
import scripting as bxd

import lib
import Modules
import lib.Module
import lib.DataUnit

tasks = Modules.DynamicLoader.getTaskModules()
readers = Modules.DynamicLoader.getReaders()
# The first element of the tuple is the reader class
# The tuple containst the following elements
# ( reader class, None, reader module )
rdrclass = readers["LSMDataSource"][0]
# we instantiate the class 
reader = rdrclass()
lsmreaders = reader.loadFromFile("/Users/kallepahajoki/BioImageXD/Data/sample1_series12.lsm")

ch1 = lsmreaders[0]

# Again, the task module class is the first element in the tuple
# The tuple contains the following elements:
# ( processing module class, task panel (GUI) class, the module)


procUnit = lib.DataUnit.CombinedDataUnit()
procUnit.setModule(lib.Module.Module())

procUnit.addSourceDataUnit(ch1)


# Do the processing (that will return the input as the output), writing out timepoint 0
# This will produce a directory called "noop" with 
# a .bxd, a .bxc and a .vti file
procUnit.doProcessing("noop.bxd", timepoints=[0])

# Do a preview also, that we write to png
# We use a special flag as the first argument, indicating we want the whole image to be processed
# instead of just one slice (if the first parameter is an integer, it is interpreted as the slice
# to be processed)
imageData = procUnit.doPreview(bxd.WHOLE_DATASET, renew = 1)

simpleMip = vtk.vtkImageSimpleMIP()
simpleMip.SetInputConnection(imageData.GetProducerPort())

pngwriter = vtk.vtkPNGWriter()
pngwriter.SetInputConnection(simpleMip.GetOutputPort())
pngwriter.SetFileName("mip.png")

simpleMip.Update()
pngwriter.Write()
