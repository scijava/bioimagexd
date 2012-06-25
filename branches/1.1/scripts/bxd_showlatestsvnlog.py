#!/usr/bin/python
import commands
import re
import sys
import os.path

scriptname = os.path.basename(sys.argv[0])
def printUsage():
	print "Usage: %s n" % scriptname
	print "Shows the n latest change comments for svn"

if len(sys.argv) < 2:
	printUsage()
	sys.exit()

logamount = int(sys.argv[1])
svninfo = commands.getoutput("svn info")
revfindpattern = re.compile(r"Revision: (\d+)")

svnrev = revfindpattern.search(svninfo)
newestSvnRev = None

if svnrev:
	newestSvnRev = int(svnrev.groups()[0])

if newestSvnRev:
	svncmd = "svn log -r %d:%d" % (newestSvnRev - (logamount - 1), newestSvnRev)
	svnlogs = commands.getoutput(svncmd)
	print svnlogs
else:
	raise "Couldn't find the number of the latest SVN revision."
