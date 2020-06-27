#!/usr/bin/python3

from pathlib import Path
import re, os, sys

class FileName:
	def __init__(self):
		self.extMatch = re.compile('^(.*)\.(.*?)$')

	def getExtension(self,filename):
		match = re.match(self.extMatch,filename)
		return match.group(2)

	def getExtendedStem(self,filename): ## Part of filename up to and excluding the final extension
		match = re.match(self.extMatch,filename)
		return match.group(1)

	def check_absolute_path(self,file,dirpath):
## We have a file and a possible absolute path of the file (without the filename).
## We want to make sure that it exists, otherwise, we check if it exists in the current directory.
## If found, returns the absolute path together with the filename.
## If not found, returns "".
		path_reg = re.search(r'/',file)
		if not path_reg:
#	        abs_treefile=dir_path+'/'+file
			abs_file=dirpath+'/'+file
			possible_file=Path(abs_file)
			if possible_file.is_file():
				return abs_file
			else:
				return ""
		else:
			if Path(file).is_file():
				return file
			else:
				return ""
