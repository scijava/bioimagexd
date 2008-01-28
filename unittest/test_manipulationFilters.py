# TestCase for Modules.Task.Manipulation.ManipulationFilters

import os.path
import sys
import unittest

runningScriptPath = os.path.abspath(sys.argv[0])
unittestPath = os.path.dirname(runningScriptPath)
bioimagepath = os.path.abspath(os.path.join(unittestPath, ".."))

import Modules.DynamicLoader

class ManipulationFiltersTest(unittest.TestCase):
	"""
	Created: 24.7.2007 SS
	Description: A test class for Module ManipulationFilters
	"""
	
	def setUp(self):
		"""
		Description:
		"""
		os.chdir(bioimagepath)

		# importing Modules.Task.Manipulation.*Filters dynamically:
		taskdict = Modules.DynamicLoader.getTaskModules()

		self.ManipulationFilters = taskdict["Process"][2].ManipulationFilters
		ManipulationFilters = taskdict["Process"][2].ManipulationFilters
		MorphologicalFilters = taskdict["Process"][2].MorphologicalFilters
		MathFilters = taskdict["Process"][2].MathFilters
		SegmentationFilters = taskdict["Process"][2].SegmentationFilters
		TrackingFilters = taskdict["Process"][2].TrackingFilters
		RegistrationFilters = taskdict["Process"][2].RegistrationFilters

		# creating test values:
		self.expectedFilterList = [MorphologicalFilters.ErodeFilter, MorphologicalFilters.DilateFilter, 
									MorphologicalFilters.RangeFilter, MorphologicalFilters.SobelFilter, 
									MorphologicalFilters.MedianFilter, ManipulationFilters.AnisotropicDiffusionFilter, 
									ManipulationFilters.SolitaryFilter, ManipulationFilters.ShiftScaleFilter, 
									MathFilters.AddFilter, MathFilters.SubtractFilter, MathFilters.MultiplyFilter, 
									MathFilters.DivideFilter, MathFilters.SinFilter, MathFilters.CosFilter, 
									MathFilters.LogFilter, MathFilters.ExpFilter, MathFilters.SQRTFilter, 
									ManipulationFilters.GradientFilter, ManipulationFilters.GradientMagnitudeFilter, 
									MathFilters.AndFilter, MathFilters.OrFilter, MathFilters.XorFilter, 
									MathFilters.NotFilter, MathFilters.NandFilter, MathFilters.NorFilter, 
									SegmentationFilters.ThresholdFilter, MorphologicalFilters.VarianceFilter, 
									MorphologicalFilters.HybridMedianFilter, ManipulationFilters.ITKAnisotropicDiffusionFilter, 
									ManipulationFilters.ITKGradientMagnitudeFilter, ManipulationFilters.ITKCannyEdgeFilter, 
									SegmentationFilters.ITKWatershedSegmentationFilter, 
									SegmentationFilters.MorphologicalWatershedSegmentationFilter, 
									SegmentationFilters.MeasureVolumeFilter, SegmentationFilters.ITKRelabelImageFilter, 
									SegmentationFilters.ITKConnectedThresholdFilter, 
									SegmentationFilters.ITKNeighborhoodConnectedThresholdFilter, 
									ManipulationFilters.ITKLocalMaximumFilter, SegmentationFilters.ITKOtsuThresholdFilter, 
									SegmentationFilters.ITKConfidenceConnectedFilter, 
									SegmentationFilters.MaskFilter,	ManipulationFilters.ITKSigmoidFilter, 
									SegmentationFilters.ITKInvertIntensityFilter, SegmentationFilters.ConnectedComponentFilter,
									SegmentationFilters.MaximumObjectsFilter, ManipulationFilters.TimepointCorrelationFilter, 
									ManipulationFilters.ROIIntensityFilter, ManipulationFilters.CutDataFilter, 
									ManipulationFilters.GaussianSmoothFilter, TrackingFilters.CreateTracksFilter, 
									TrackingFilters.ViewTracksFilter, ManipulationFilters.ExtractComponentFilter, 
									RegistrationFilters.RegistrationFilter, TrackingFilters.AnalyzeTracksFilter]

	def testGetFilterList(self):
		"""
		A test for method getFilterList()
		"""
		self.assertEqual(set(self.ManipulationFilters.getFilterList()), set(self.expectedFilterList))


# run
if __name__ == "__main__":
	unittest.main()
