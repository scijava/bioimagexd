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
import scripting

import Modules

tasks = Modules.DynamicLoader.getTaskModules()
readers = Modules.DynamicLoader.getReaders()
print "got ", readers
# The first element of the tuple is the reader class
# The tuple containst the following elements
# ( reader class, None, reader module )
rdrclass = readers["LSMDataSource"][0]
# we instantiate the class 
reader = rdrclass()
lsmreaders = reader.loadFromFile("/Users/kallepahajoki/BioImageXD/Data/sample1_series12.lsm")
print lsmreaders

ch1 = lsmreaders[0]
ch2 = lsmreaders[1]

# Again, the task module class is the first element in the tuple
# The tuple contains the following elements:
# ( processing module class, task panel (GUI) class, the module)
processingClass = tasks["Merging"][0]
mergingModule = tasks["Merging"][2]


mergeClass = mergingModule.getDataUnit()

mergedUnit = mergeClass()
mergedUnit.setModule(processingClass())


mergedUnit.addSourceDataUnit(ch1)
mergedUnit.addSourceDataUnit(ch2)


# Do the merging, writing out timepoint 0
# This will produce a directory called "merge" with 
# a .bxd, a .bxc and a .vti file
mergedUnit.doProcessing("merge.bxd", timepoints=[0])

# Do a preview also, that we write to png
# We use a special flag as the first argument, indicating we want the whole image to be processed
# instead of just one slice (if the first parameter is an integer, it is interpreted as the slice
# to be processed)
# we also indicate that we do not want an alpha channel (so merging produces RGB, instead of RGBA dataset)
# this can also be achieved by setting bxd.wantAlphaChannel to 0
imageData = mergedUnit.doPreview(scripting.WHOLE_DATASET_NO_ALPHA, renew = 1)

simpleMip = vtk.vtkImageSimpleMIP()
simpleMip.SetInputConnection(imageData.GetProducerPort())

pngwriter = vtk.vtkPNGWriter()
pngwriter.SetInputConnection(simpleMip.GetOutputPort())
pngwriter.SetFileName("mip.png")

simpleMip.Update()
pngwriter.Write()
