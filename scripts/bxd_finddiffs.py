#!/usr/bin/python
import os
import os.path
import commands

def getFileList(directory):
	directory = os.path.expanduser(directory)
	filetuplegenerator = os.walk(directory)
	filelist = []
	for filetuple in filetuplegenerator:
		dirpath = filetuple[0]
		filenames = filetuple[2]
		for filename in filenames:
			filelist.append(os.path.join(dirpath, filename))
	return filelist

#pythonfiles = [filename for filename in filelist if filename.endswith(".py")]

def writeSvnDiffs(filelist, fromrev, torev, dirprefix):
	for filename in filelist:
		if filename.endswith(".py") and not "lib/email" in filename and not ".svn" in filename:
			subpath = filename.rsplit("bio-rev1037/", 1)[1]
			subpathdir = os.path.dirname(subpath)
			print "PROCESSING", filename
			svncommand = "svn diff -r %d:%d %s > %s/%s.diff" % (fromrev, torev, subpath, dirprefix, subpath)
			print svncommand
			diffFileDir = os.path.expanduser(os.path.join(dirprefix,subpathdir))
			if not os.path.exists(diffFileDir):
				os.makedirs(diffFileDir)
			os.system(svncommand)
			#filehandle = open(filename, "w")
			#filehandle.write("Code comments for %s" % filename)
			#filehandle.close()
			#newfilename = filename + ".txt"
			#os.rename(filename, newfilename)
		else:
#			print "SKIPPING", filename
			#os.remove(filename)
			pass
pythonFiles = getFileList("~/bioimage/bio-rev1037")
writeSvnDiffs(pythonFiles, 988, 1037, "~/bioimage/svndiffs")
