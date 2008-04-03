"""
Created: 08.06.2007, SG
Description: Module containing exceptions used by the different bxd modules
The exception hierarchy is not completely planned out yet
"""
class ParameterException(Exception):
	"""
	Created: 08.06.2007, SG
	Description: Base ParameterException class to be raised when a method is called with incorrect parameter(s)
	"""
	def __init__(self, message):
		"""
		Basic constructor that sets a message for the message
		"""
		Exception.__init__(self)
		self.message = message


class IncorrectSizeException(ParameterException):
	"""
	Created: 08.06.2007, SG
	Description: Exception to raise when a method has received an incorrectly sized parameter (a list for example)
	"""
	def __init__(self, message):
		"""
		Basic overriden constructor, nothing special for this subclass
		"""
		ParameterException.__init__(self, message)


class MissingParameter(ParameterException):
	"""
	Exception to raise for example when a method is called with an important parameter set to None
	@since: 26.07.2007
	@author: SG
	"""
	def __init__(self, message):
		"""
		Basic overriden constructor, nothing special for this subclass
		@since: 26.07.2007
		@author: SG
		"""
		ParameterException.__init__(self, message)


class AbstractMethodCalled(Exception):
	"""
	To be raised when an abstract method is called
	@since: 27.07.2007
	@author: SG
	"""
	def __init__(self, *args):
		"""
		Basic constructor
		@since: 27.07.2007
		@author: SG
		"""
		Exception.__init__(self, *args)
