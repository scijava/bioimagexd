import unittest

import vtkbxd
import vtk

import os
DATA_PATH = "/Users/kallepahajoki/BioImageXD/Data/Leica LIFs"

	

class TestColoc(unittest.TestCase):
	"""Class for testing the vtkLIFReader"""
	
	def testDimensions(self):
		reader = vtkbxd.vtkLIFReader()
		reader.OpenFile(os.path.join(DATA_PATH, "512x_128y_10z_22t_2ch.lif"))
		reader.Update()
		data = reader.GetOutput()
		self.assert_(data.GetDimensions() == (512, 128, 10), "Dimensions do not match")
	
	def testMIP(self):
		reader = vtkbxd.vtkLIFReader()
		reader.OpenFile(os.path.join(DATA_PATH, "512x_128y_10z_22t_2ch.lif"))
		reader.Update()
		data = reader.GetOutput()
		mip = vtkbxd.vtkImageSimpleMIP()
		mip.SetInput(data)
		pngwriter  = vtk.vtkPNGWriter()
		pngwriter.SetInput(mip.GetOutput())
		mip.Update()
		pngwriter.SetFileName("lif.png")
		pngwriter.Write()
if __name__ == '__main__':
	unittest.main()