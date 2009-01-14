import math

def meanstdeverr(x):
	n, mean, std = len(x), 0, 0 
	for a in x: 
		mean = mean + a
	mean = mean / float(n)
	for a in x: 
		std = std + (a - mean)**2 
	std = math.sqrt(std / float(n-1))
	stderr = std/math.sqrt(n)
	return mean, std, stderr
	

def meanstdev(x): 
	return meanstdeverr(x)[0:2]

def averageValue(lst):
		if len(lst) == 0:
			return 0.0	
		return sum(lst) / len(lst)
