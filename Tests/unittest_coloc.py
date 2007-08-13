import unittest

import vtk

import os
DATA_PATH = "/Users/kallepahajoki/BioImageXD/Data"

def getChannel(datafile, chn):
	datafile = os.path.join(DATA_PATH, datafile)
	chrdr = vtk.vtkLSMReader()
	chrdr.SetFileName(datafile)
	chrdr.SetUpdateChannel(chn)
	chrdr.Update()
	ch = chrdr.GetOutput()
	return ch
	
PValueResults = {}
ThresholdingResults = {}
# Format of the data structure
# [ # of iterations, "method", R-Obs, R-rand mean,R-rand sd, P-value,  PSF width if applicable ]
PValueResults["sample1_single.lsm"] = [20, "Costes", 0.190, 0.095, 0.001, 1.0, 10]

# Format of the data structure [ ch1th, ch2th ]
ThresholdingResults["sample1_single.lsm"] = [45, 11]

methods = ["Fay", "Costes", "van Steensel"]
class TestColoc(unittest.TestCase):
	"""Class for testing the colocalization functionality"""
	
	def testPValue(self):
		"""Test the P-value calculation against all the measured data points"""
		for key, data in PValueResults.items():            
			ch1 = getChannel(key, 0)
			ch2 = getChannel(key, 1)

			coloctest = vtk.vtkImageColocalizationTest()
			coloctest.AddInput(ch1)
			coloctest.AddInput(ch2)
			
			iterations, method, robs, rrandmean, rrandsd, pvalue, psf = data
			
			
			# Set the PSF radius and # of iterations, if we're using Costes' method
			if method == "Costes":
				coloctest.SetManualPSFSize(psf)
				coloctest.SetNumIterations(iterations)
			# Set the method (0, 1 or 2 which correspond to Fay, Costes and van Steensel)
			coloctest.SetMethod(methods.index(method))
			coloctest.Update()

			resultrobs = coloctest.GetRObserved()
			resultpval = coloctest.GetPValue()
			
			self.assert_(abs(resultrobs - robs) < 0.001, "Our R(obs) (%f) differs from ImageJ's (%f)" % (resultrobs, robs))            
			self.assert_(abs(resultpval - pvalue) < 0.001, "Our P-value (%f) differs from ImageJ's (%f)" % (resultpval, pvalue))
			if iterations > 10:
				resultrrandmean = coloctest.GetRRandMean()
				self.assert_(abs(resultrrandmean - rrandmean) < 0.1, "Our R(rand) mean (%f) differs from ImageJ's (%f) by more than 0.1" % (resultrrandmean, rrandmean))
			
	
	def testAutoThreshold(self):
		"""Test that the auto thresholding gives the same results"""
		for key, data in ThresholdingResults.items():
			ch1 = getChannel(key, 0)
			ch2 = getChannel(key, 1)
			
			th1, th2 = data
			
			autothreshold = vtk.vtkImageAutoThresholdColocalization()
			autothreshold.AddInput(ch1)
			autothreshold.AddInput(ch2)

			autothreshold.Update()
			resultth1 = autothreshold.GetCh1ThresholdMax()
			resultth2 = autothreshold.GetCh2ThresholdMax()
			
			self.assertEqual((th1, th2), (resultth1, resultth2), "Our autothresholding produces different results than ImageJ's (%d, %d != %d, %d)" % (resultth1, resultth2, th1, th2))
			
if __name__ == '__main__':
	unittest.main()
