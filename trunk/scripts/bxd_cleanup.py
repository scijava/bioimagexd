#!/usr/bin/python

"""
bxd_cleanup.py - Python script for cleaning up python source code created for use with the BioImageXD
project.
Development started June 2007, by Sam Grönblom sgronblo@gmail.com

The script checks that the input file runs through the python interpreter without syntax errors before
doing anything to it.
If the input file has no errors, the script makes a copy of it with .backup at the end of the new name
and then does the substitutions on the original file.

The script adds spaces to the sides of operators.
	Example: a=4+5-7 -> a = 4 + 5 - 7
The script adds spaces after commas.
	Example: someList=[1,2,3,4] -> someList = [1, 2, 3, 4]
The script adds spaces after colons in dictionaries.
	Example: someDict={"country":"Finland","capital":"Helsinki"} ->
		someDict = {"country": "Finland", "capital": "Helsinki"}
It should also not do any replacements inside strings.
	Example "\"%s\" är 3,14"%"pi" -> "\"%s\" är 3,14" % "pi"
The program should be able to deal with triple-quoted strings as well.

Known Problems:
	The program can't deal with scientific notation of number literals.
	Example 1e-9 where it will think that you have a variable called 1e to be subtracted with 9.

Please e-mail me if you find any errors
"""

import os
import os.path
import shutil
import sys
import re

def printUsage():
	print "bxd_cleanup.py - Cleans up python source files using regular expressions."
	print "usage: bxd_cleanup.py source.py"
	print "The program will overwrite the old file, so make a backup copy if you're worried about"
	print "your source file."

def cleanupString(inString):
	subedString, subsMade = doAllSubstitutions(inString)
	while subsMade > 0:
		subedString, subsMade = doAllSubstitutions(subedString)
	#return "<" + subedString + ">"
	return subedString

def doAllSubstitutions(inString):
	totalSubs = 0
	subedString, subsMade = addSpaceAfterOperatorRe.subn(r'\1\2 \3', inString)
	totalSubs += subsMade
	subedString, subsMade = addSpaceBeforeOperatorRe.subn(r'\1 \2\3', subedString)
	totalSubs += subsMade
	subedString, subsMade = addSpaceOnSidesOfOperatorRe.subn(r'\1 \2 \3', subedString)
	totalSubs += subsMade
	subedString, subsMade = addSpaceAfterCommaRe.subn(r', \1', subedString)
	totalSubs += subsMade
	subedString, subsMade = addSpacesInDictDef.subn(r'": "', subedString)
	totalSubs += subsMade
	return (subedString, totalSubs)

def changeSpacesToTabs(inLine):
	subsMade = 0
	subedString = ""
	subedString, subsMade = spaceToTabRe.subn(r'\1\t', inLine)
	while subsMade > 0:
		subedString, subsMade = spaceToTabRe.subn(r'\1\t', subedString)
	return subedString

# This method is gonna need refactoring soon...
def substituteNonStrings(inFileName, outFileName):
	outFile = open(outFileName, "w")
	#outFile = sys.stdout
	inFile = open(inFileName, "r")
	inString = False
	stringStartChar = ""
	stringBuffer = ""
	escapeNextChar = False
	inTripleString = False
	for line in inFile:
		line = changeSpacesToTabs(line)
		nextCharsAreComment = False
		charIndex = 0
		while charIndex < len(line):
			char = line[charIndex]
			if not nextCharsAreComment:
				if char == commentStartChar and not inString and not inTripleString:
					nextCharsAreComment = True
					outFile.write(cleanupString(stringBuffer))
					stringBuffer = ""
					outFile.write(char)
					charIndex += 1
					continue
				if inString:
					if escapeNextChar:
						outFile.write(char)
						escapeNextChar = False
					else:
						if char == escapeChar:
							outFile.write(char)
							escapeNextChar = True
						elif char == stringStartChar:
							stringBuffer += char
							inString = False
						else:
							outFile.write(char)
				elif inTripleString:
					if char == stringStartChar:
						outFile.write(char)
						charIndex += 1
						if charIndex < len(line):
							char = line[charIndex]
							if char == stringStartChar:
								outFile.write(char)
								charIndex += 1
								if charIndex < len(line):
									char = line[charIndex]
									if char == stringStartChar:
										inTripleString = False
										stringBuffer += char
									else:
										outFile.write(char)
							else:
								outFile.write(char)
					else:
						outFile.write(char)
				else: # We are not in a string
					if char in stringDelimiters:
						stringBuffer += char
						outFile.write(cleanupString(stringBuffer))
						stringBuffer = ""
						inString = True
						stringStartChar = char
						if line[charIndex+1] == stringStartChar and line[charIndex+2] == stringStartChar:
							inString = False
							inTripleString = True
					else:
						stringBuffer += char
			else: # We are in a comment
				outFile.write(char)
			charIndex += 1
	if stringBuffer:
		outFile.write(cleanupString(stringBuffer))

escapeChar = "\\"
commentStartChar = '#'
operators = r'(?:==|=|\+|-|\*|!=|<>|<|<=|>=|\+=|-=|\*=|>|/=|%|/|\||//|\*\*|&|>>|<<)'
lhs = r'(\w|\)|\]|"|\')'
rhs = r'(\w|\[|\(|"|' + "'" + r'|{|\+|-|~)'
tabsize = 4
#mathExprPattern = lhs + '((?: (?:' + operators + '))|(?:'+ operators + ')|(?:(?:' + operators + ') ))' + rhs
#print mathExprPattern
#mathExprRe = re.compile(mathExprPattern)
addSpaceAfterOperatorRe = re.compile(lhs + '( ' + operators + ')' + rhs)
addSpaceBeforeOperatorRe = re.compile(lhs + '(' + operators + ' )' + rhs)
addSpaceOnSidesOfOperatorRe = re.compile(lhs + '(' + operators + ')' + rhs)
addSpaceAfterCommaRe = re.compile(r',(\S)')
addSpacesInDictDef = re.compile(r'":"')
spaceToTabRe = re.compile('^(\\t*) {%d}' % tabsize)
stringDelimiters = "\"'"

if (len(sys.argv)) != 2:
	printUsage()
	sys.exit()
else:
	fileName = sys.argv[1]
	sourceFilePipe = os.popen('python %s' % fileName)
	errors = sourceFilePipe.close()
	if errors:
		print "Errors found in the file, correct these and try again."
		sys.exit()
	else:
		if not os.path.isfile(fileName):
			print "File does not exist or is not a standard file."
			sys.exit()
		else:
			newFileName = fileName + ".backup"
			shutil.copyfile(fileName, newFileName)
			substituteNonStrings(newFileName, fileName)
