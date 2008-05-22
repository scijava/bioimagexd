import lib.FilterTypes
import scripting
import vtk
import lib.ProcessingFilter

class HybridMedianFilter(lib.ProcessingFilter.ProcessingFilter):
	"""
    A 2D median filter that preserves edges and corners
	"""     
	name = "Hybrid median 2D"
	category = lib.FilterTypes.FILTERING
	level = scripting.COLOR_BEGINNER
	
	def __init__(self):
		"""
		Initialization
		"""        
		lib.ProcessingFilter.ProcessingFilter.__init__(self)
		self.vtkfilter = vtk.vtkImageHybridMedian2D()
		self.vtkfilter.AddObserver('ProgressEvent', lib.messenger.send)
		lib.messenger.connect(self.vtkfilter, "ProgressEvent", self.updateProgress)
		self.eventDesc = "Performing hybrid median filtering"

	def getParameters(self):
		"""
		Return the list of parameters needed for configuring this GUI
		"""  
		return []

	def execute(self, inputs, update = 0, last = 0):
		"""
		Execute the filter with given inputs and return the output
		"""            
		if not lib.ProcessingFilter.ProcessingFilter.execute(self, inputs):
			return None        
		image = self.getInput(1)
		self.vtkfilter.SetInput(image)
		if update:
			self.vtkfilter.Update()
		return self.vtkfilter.GetOutput()         