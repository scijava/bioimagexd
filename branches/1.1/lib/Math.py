import math

def meanstdeverr(x):
	n, mean, std = len(x), 0, 0
	if n == 0:
		return 0.0, 0.0, 0.0
	for a in x: 
		mean = mean + a
	mean = mean / float(n)
	for a in x: 
		std = std + (a - mean)**2 
	std = math.sqrt(std / float(n))
	stderr = std/math.sqrt(n)
	return mean, std, stderr

def meanstdev(x): 
	return meanstdeverr(x)[0:2]

def averageValue(lst):
	if len(lst) == 0:
		return 0.0	
	return sum(lst) / float(len(lst))

def angle(vector1, vector2):
	"""
	Measure the angle between two unit vectors
	"""
	inner = 0.0
	dim = min(len(vector1), len(vector2))
	for i in range(dim):
		inner += vector1[i] * vector2[i]

	try: # There can be rounding problems
		ang = abs(math.acos(inner) * 180 / math.pi)
	except:
		ang = 0.0
	return ang
