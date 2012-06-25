#!/usr/bin/python

import re
import sys
import os.path
import os

scriptname = os.path.basename(sys.argv[0])

def printUsage():
	print "usage: %s type file" % scriptname
	print "\ttype = type of construct to search for"
	print "\tfile = file to search in"
	print "\texample: findinsource.py function MainWindow.py"

def listSupportedTypes():
	print "Valid types are:"
	for key in sorted(typeToPattern.keys()):
		print "\t%s => %s" % (key, typeToPattern[key][1])

def searchFileForPattern(filename, pattern):
	searchFile = open(filename)
	foundItems = set()
	for line in searchFile:
		match = searchPattern.search(line)
		if match:
			matchstring = match.group(1).strip()
			foundItems.add(matchstring)
	return foundItems

typeToPattern = {
	"func": ("^\s*def\s*(\w+)\s*\(", "function"),
	"var": ("(\w+)\s*=", "variable"),
	"methodwithcap": ("def\s*([A-Z]\w+)\s*\(", "methods starting with a capital letter"),
	"instvar": ("self.(\w+)\s*=", "instance variable"),
	"class": ("^\s*class\s*(\w+)", "class")
}
if len(sys.argv) != 3:
	printUsage()
	listSupportedTypes()
	sys.exit()

typeArgument = sys.argv[1]
fileArgument = sys.argv[2]

if typeArgument not in typeToPattern:
	print "Unsupported type to search for"
	listSupportedTypes()
	sys.exit()

searchPattern = re.compile(typeToPattern[typeArgument][0])
searchType = typeToPattern[typeArgument][1]

if os.path.isdir(fileArgument):
	matchfound = False
	filetuplelist = os.walk(fileArgument)
	abspathlist = []
	for filetuple in filetuplelist:
		basepath = filetuple[0]
		for filename in filetuple[2]:
			abspath = os.path.join(basepath, filename)
			if abspath.endswith(".py"):
				abspathlist.append(abspath)
	for filename in abspathlist:
		matches = searchFileForPattern(filename, searchPattern)
		if len(matches) > 0:
			matchfound = True
			print "file:", filename
			for match in matches:
				print "\t", match
			print "%d %ss found" % (len(matches), searchType)
	if not matchfound:
		print "No matches found"
else:
	matches = searchFileForPattern(fileArgument, searchPattern)
	if len(matches) == 0:
		print "No matches found"
	else:
		for match in matches:
			print "\t", match
		print "%d %ss found" % (len(matches), searchType)
