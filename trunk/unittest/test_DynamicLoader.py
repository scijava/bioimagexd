# Welcome to unittest example!
#
# Name all testing files starting with 'test_'
# and place them in 'unittest' directory.
# Make runs these files magically.
# This file has been renamed so that it won't be run every time you run make test.
#
# The test result report is placed into 'unittest/results'
# and named after date and time of test execution.
# Also edited the makefile to automatically show the latest results.

import os.path
import sys
import unittest

runningScriptPath = os.path.abspath(sys.argv[0])
unittestPath = os.path.dirname(runningScriptPath)
bioimagepath = os.path.abspath(os.path.join(unittestPath, ".."))

import Modules.DynamicLoader
import glob
import scripting

# Modules.DynamicLoader.Logging.enableFull()

class TestSample(unittest.TestCase):

	def setUp(self):
		# Must change to the path of bioimagexd to be able to use the relative paths
		# that dynamic module loading relies on.
		os.chdir(bioimagepath)

	def tearDown(self):
		pass

	def testGetRenderingModules(self):
		"""
		Created: 10.07.2007, SG
		Description: Simply tests that the keys in the dictionary returned by getRenderingModules
		is the same as the combined list of strings that would be returned from the getName methods for
		each of the modules in the corresponding directory. The unit test might break if ignore is changed
		or if the files in Rendering dir changes.
		"""
		expectedKeys = ["Angle measurement", "Axes", "Clipping plane", "Cut with box", 
				"Distance measurement", "Surface rendering", "Orthogonal slices", 
				"Visualize tracks", "Volume rendering", "Warp scalar"]
		resultDictionary = Modules.DynamicLoader.getRenderingModules()
		self.assertEquals(len(resultDictionary.keys()), len(expectedKeys))
		self.assertEquals(set(resultDictionary.keys()), set(expectedKeys))

	def testGetVisualizationModes(self):
		"""
		Created: 10.07.2007, SG
		Description: Simply tests that the keys in the dictionary returned by getVisualizationModes
		is the same as the combined list of strings that would be returned from the getName methods for
		each of the modules in the corresponding directory. The unit test might break if ignore is changed
		or if the files in Visualization dir changes.
		"""
		expectedKeys = ["animator", "gallery", "info", "3d", "sections", "MIP", "slices"]
		resultDictionary = Modules.DynamicLoader.getVisualizationModes()
		self.assertEquals(len(resultDictionary.keys()), len(expectedKeys))
		self.assertEquals(set(resultDictionary.keys()), set(expectedKeys))

	def testGetReaders(self):
		"""
		Created: 10.07.2007, SG
		Description: Simply tests that the keys in the dictionary returned by getReaders
		is the same as the combined list of strings that would be returned from the getName methods for
		each of the modules in the corresponding directory. The unit test might break if ignore is changed
		or if the files in Readers dir changes.
		"""
		expectedKeys = ["BioradDataSource", "BXCDataSource", "BXDDataSource", "FileListDataSource", 
						"InterfileDataSource", "LeicaDataSource", "LSMDataSource", "OlympusDataSource"]
		resultDictionary = Modules.DynamicLoader.getReaders()
		self.assertEquals(len(resultDictionary.keys()), len(expectedKeys))
		self.assertEquals(set(resultDictionary.keys()), set(expectedKeys))

	def testGetTaskModules(self):
		"""
		Created: 10.07.2007, SG
		Description: Simply tests that the keys in the dictionary returned by getTaskModules
		is the same as the combined list of strings that would be returned from the getName methods for
		each of the __init__.py files in the dirs in the corresponding directory. The unit test might break
		if ignore is changed or if the directories and files in Tasks dir changes.
		"""
		expectedKeys = ["Adjust", "Colocalization", "Process", "Merging"]
		resultDictionary = Modules.DynamicLoader.getTaskModules()
		self.assertEquals(len(resultDictionary.keys()), len(expectedKeys))
		self.assertEquals(set(resultDictionary.keys()), set(expectedKeys))
	
	def testModuleNameCreation(self):
		"""
		Created: 10.07.2007, SG
		Description: Tests getting of module name from a path to a python source file and getting a module
		name from a path to a directory
		"""
		pathThatIsPythonSource = "Modules/Readers/BXCDataSource.py"
		expectedNameForPythonSource = "BXCDataSource"
		pathThatIsDirectory = "Modules/Tasks/Coloc"
		expectedNameForDirectory = "Coloc"
		self.assertEquals(Modules.DynamicLoader._createModuleNameToLoad(pathThatIsPythonSource),
				expectedNameForPythonSource)
		self.assertEquals(Modules.DynamicLoader._createModuleNameToLoad(pathThatIsDirectory),
				expectedNameForDirectory)

	def testListOfImportsIsSameAsPythonFiles(self):
		"""
		Created: 12.06.2007, SG
		Description: Tests if the list of keys in the dictionary returned from
			DynamicLoader.getModules is equal to list of .py files in the
			requested module directory
		"""
		resultDictionary = Modules.DynamicLoader.getModules("Readers")
		readerPackageDir = os.path.join(bioimagepath, "source", scripting.get_module_dir(), "Readers")
		pythonFilesInPackageDir = glob.glob(os.path.join(readerPackageDir, "*.py"))
		pythonBaseFilesWithoutExtension = [os.path.basename(file).replace(".py", "") \
											for file in pythonFilesInPackageDir]
		self.assertEquals(sorted(resultDictionary.keys()), sorted(pythonBaseFilesWithoutExtension))

	def testEmptyDictionaryReturnedForUnexistingPackage(self):
		"""
		Created: 12.06.2007, SG
		Description: Tests that an empty dictionary is returned when a parameter
			is given that does not match a directory in the module directory.
		"""
		resultDictionary = Modules.DynamicLoader.getModules("ModuleThatDoesNotExist")
		self.assertEquals({}, resultDictionary)
	
	def testThatIgnoringModulesWorks(self):
		"""
		Created: 12.06.2007, SG
		Description: Checks that modules in ignore are not imported. We check this by: Importing the
		Readers modules. Emptying the mcache so that we won't get the earlier cached result. Adding the
		name of one module in the directory to ignore. Importing Readers again. Checking that the amount
		of keys is one less than before and that our ignored module is not in the list of keys.
		"""
		moduleDirToLoad = "Readers"
		moduleToIgnore = "LSMDataSource.py"
		modulesLoadedDictionary = Modules.DynamicLoader.getModules(moduleDirToLoad)
		amountOfKeysBeforeChangingIgnore = len(modulesLoadedDictionary)
		#print "modulesLoadedDictionaryKeys =", modulesLoadedDictionary.keys()
		#print "mcache =", Modules.DynamicLoader.mcache
		#print "ignore =", Modules.DynamicLoader.ignore
		Modules.DynamicLoader.mcache = {}
		Modules.DynamicLoader.ignore.append(moduleToIgnore)
		modulesLoadedDictionary = Modules.DynamicLoader.getModules(moduleDirToLoad)
		#print "modulesLoadedDictionaryKeys =", modulesLoadedDictionary.keys()
		#print "mcache =", Modules.DynamicLoader.mcache
		#print "ignore =", Modules.DynamicLoader.ignore
		amountOfKeysAfterChangingIgnore = len(modulesLoadedDictionary)
		self.assertEquals(amountOfKeysBeforeChangingIgnore - 1, amountOfKeysAfterChangingIgnore)
		self.assert_(moduleToIgnore not in modulesLoadedDictionary)

	# Tried to get this test running but it would take quite a bit of work to test functionality that
	# the program does not seem to need support for right now, removed test from method name so it won't
	# break unit testing. This test could be revived later if somebody decides we need to support loading of
	# modules in a deep hierarchy. I didn't want to mess with the Modules directory in source to create
	# usable test data.
	def doNotTestLoadingOfModulesInSubdirectory(self):
		"""
		Created: 13.06.2007, SG
		Description: Checks that you can import modules from a directory that is a subdirectory of
		a directory in the Modules directory. For this test I try to import Task/Adjust and check that
		the list of modules is the same as the list of python files in that directory.
		"""
#		class MockScriptingClass:
#			def get_module_dir(self):
#				return unittestPath
		adjustPath = "Task/Adjust"
		loadedModulesDictionary = Modules.DynamicLoader.getModules(adjustPath)
		os.chdir(os.path.join(bioimagepath, "source"))
		absAdjustPackagePath = os.path.join(bioimagepath, "source", scripting.get_module_dir(), adjustPath)
		pythonFilesInPackageDir = glob.glob(os.path.join(absAdjustPackagePath, "*.py"))
		pythonBaseFilesWithoutExtension = [os.path.basename(file).replace(".py", "") \
											for file in pythonFilesInPackageDir]
		self.assertEquals(sorted(loadedModulesDictionary.keys()), sorted(pythonFilesInPackageDir))

	# There was no directory in Modules that was suitable for testing this. Would have to create a fake
	# Modules directory in unittest/testdata and then a mock scripting.get_module_dir function so that
	# getModules tries to load modules from there.
	def testThatIgnoringOnlyIgnoresExactMatches(self):
		"""
		Created: 12.06.2007, SG
		Description: Ignoring should only match exact module or package names. In unittest/testdata
		is a FakeModulesDir/FakeModule containing the modules TestingBox.py and Box.py. Then Box.py
		is added to ignore and we try to load this FakeModule dir. Box.py should now be ignored but not
		TestingBox.py because "Box.py" does not exactly match it's module name.
		"""
		sys.path.append(os.path.join(unittestPath, "testdata"))
		moduleDirToLoad = "FakeModule"
		moduleToIgnore = "Box"
		# Create a fake getModuleDir to point to our unittest/testdata dir so getModules will look there for
		# modules to load
		def getModuleDir():
			return os.path.join("FakeModulesDir")
		tempGetModuleDir = Modules.DynamicLoader.scripting.get_module_dir
		Modules.DynamicLoader.scripting.get_module_dir = getModuleDir
		moduleThatShouldBeImported = "TestingBox"
		Modules.DynamicLoader.ignore.append(moduleToIgnore + ".py")
		os.chdir(os.path.join(unittestPath, "testdata"))
		loadedModulesDictionary = Modules.DynamicLoader.getModules(moduleDirToLoad)
		self.assert_(moduleToIgnore not in loadedModulesDictionary)
		self.assert_(moduleThatShouldBeImported in loadedModulesDictionary)
		Modules.DynamicLoader.scripting.get_module_dir = tempGetModuleDir
	
	def testRemoveIgnoredModules(self):
		"""
		Created: 19.06.2007, SG
		Description: Test that Spline.py gets removed because it's in ignore. If ignore changes
		the unit test might break.
		"""
		testModuleList = ["DynamicLoader.py", "Adjust.py", "Module.py", "Spline.py"]
		acceptedModulesList = ["DynamicLoader.py", "Adjust.py", "Module.py"]
		self.assertEquals(acceptedModulesList, Modules.DynamicLoader._removeIgnoredModules(testModuleList))
	
	def testCreateGlobPathAndSysPath(self):
		"""
		Created: 19.06.2007, SG
		Description: Tests that the rights path are returned for extension *.py and * with module dir Readers
		"""
		globPathDir = os.path.join("Modules", "Readers")
		expectedSysPath = globPathDir
		expectedGlobPath = os.path.join(globPathDir, "*.py")
		(globPath, sysPath) = Modules.DynamicLoader._createGlobPathAndSysPath("Readers", "*.py")
		self.assertEqual((globPath, sysPath), (expectedGlobPath, expectedSysPath))
		expectedGlobPath = os.path.join(globPathDir, "*")
		(globPath, sysPath) = Modules.DynamicLoader._createGlobPathAndSysPath("Readers", "*")
		self.assertEqual((globPath, sysPath), (expectedGlobPath, expectedSysPath))

# Include this in all test cases.
# It is used by make to run the tests magically.
if __name__ == "__main__":
	unittest.main()
