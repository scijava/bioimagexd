import unittest
import os
import sys

os.chdir("..")
bxddir  = os.getcwd()
sys.path.insert(0, bxddir)
sys.path.insert(0, os.path.join(bxddir, "lib"))
sys.path.insert(0, os.path.join(bxddir, "GUI"))

import Module
import lib.DataUnit
import vtkbxd
import vtk


class TestModuleFunctions(unittest.TestCase):
    """Test the Module class from Module.py"""
    def setUp(self):
        """Set up the testing environment"""
        self.module = Module.Module()
        self.dataunit = lib.DataUnit.CombinedDataUnit()
        self.ch1rdr = vtk.vtkLSMReader()
        self.ch2rdr = vtk.vtkLSMReader()
        self.ch1rdr.SetFileName("/Users/kallepahajoki/BioImageXD/Data/sample1_series12.lsm")
        self.ch2rdr.SetFileName("/Users/kallepahajoki/BioImageXD/Data/sample1_single.lsm")
        
    def testControlUnit(self):
        """Test that setting the control unit works"""
        self.module.setControlDataUnit(self.dataunit)
        assert self.module.getControlDataUnit() == self.dataunit
        
    def testNoopness(self):
        """Test that the processing is essentially a noop"""
        self.ch1rdr.SetUpdateChannel(1)
        self.ch1rdr.Update()        
        self.module.addInput(None, self.ch1rdr.GetOutput())
        assert self.module.getPreview(0) == self.ch1rdr.GetOutput()
        
    def testDimensionChecks(self):
        """Test that module correctly catches the case when two datasets with differin dimensions
           are given as sources
        """
        self.ch1rdr.SetUpdateChannel(0)
        self.ch2rdr.SetUpdateChannel(0)
        self.ch1rdr.Update()
        self.ch2rdr.Update()
        caughtError = 0
        try:
            self.module.addInput(None, self.ch1rdr.GetOutput())
            self.module.addInput(None, self.ch2rdr.GetOutput())
        except:
            caughtError = 1
            pass
        assert caughtError, "Failed to catch differing dimensions"


if __name__=='__main__':
    unittest.main()
            