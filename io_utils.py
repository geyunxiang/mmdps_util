import shutil
import os
import gzip
import random

from mmdps.proc import netattr, atlas
from mmdps.util import loadsave

def ungzip(fgz):
	with gzip.open(fgz, 'rb') as fin,\
		 open(fgz[:-3], 'wb') as fout:
		shutil.copyfileobj(fin, fout)

def process_subject_list(subjectList):
	"""
	This helper function decides whether the input list is a string
	It reads in names from the file specified by the string
	or just returns if the argument is already a list
	"""
	ret = None
	if type(subjectList) is str:
		ret = []
		# read in subjectList
		with open(subjectList) as f:
			for line in f.readlines():
				ret.append(line.strip())
	elif type(subjectList) is list:
		ret = subjectList
	return ret

def loadAllTemporalNets(boldPath, totalTimeCase, atlasobj, subjectList = None, specificTime = None):
	"""
	This function is used to load temporal scans. All person with up
	to totalTimeCase number of scans will be loaded and returned in a dict. 
	The key of the dict is the subject name.
	Each element in the dict is the temporal scans of one person. The data are stored
	as a list of BrainNet.
	Parameters:
		- subjectList: a list of strs or a path to a text file
		- specificTime: a dict, with key = subject name, value = [timeStr1, timeStr2, ...]
				The length of value should equal to totalTimeCase
	"""
	subjectList = process_subject_list(subjectList)
	ret = {}
	currentPersonScans = []
	currentPersonTime = []
	subjectName = 'None'
	lastSubjectName = 'Unknown'
	occurrenceCounter = 0
	for scan in sorted(os.listdir(boldPath)):
		subjectName = scan[:scan.find('_')]
		if subjectName != lastSubjectName:
			if occurrenceCounter >= totalTimeCase:
				if specificTime is not None and lastSubjectName in specificTime:
					ret[lastSubjectName] = [currentPersonScans[currentPersonTime.index(timeStr)] for timeStr in specificTime[lastSubjectName]]
				else:
					ret[lastSubjectName] = currentPersonScans[:totalTimeCase]
			occurrenceCounter = 0
			lastSubjectName = subjectName
			currentPersonScans = []
			currentPersonTime = []
		if subjectList is not None and subjectName not in subjectList:
			continue
		occurrenceCounter += 1
		currentPersonScans.append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scan, atlasobj.name, 'bold_net', 'corrcoef.csv')), atlasobj))
		currentPersonTime.append(scan[scan.find('_')+1:])
	return ret

def loadSpecificNets(boldPath, atlasobj, timeCase = 1, subjectList = None):
	"""
	This function is an implementation on the new mmdps version.
	This function is used to load the first/second/etc scans of subjects.
	Specify which subjects to load as a list of strings or a file path in subjectList.
	If no subjectList is given, load all scans.
	"""
	subjectList = process_subject_list(subjectList)
	ret = []
	subjectName = 'None'
	lastSubjectName = 'Unknown'
	for scan in sorted(os.listdir(boldPath)):
		if scan.find('_') != -1:
			subjectName = scan[:scan.find('_')]
		else:
			subjectName = scan
		if subjectName != lastSubjectName:
			occurrenceCounter = 0
			lastSubjectName = subjectName
		occurrenceCounter += 1
		if subjectList is not None and subjectName not in subjectList:
			continue
		if occurrenceCounter == timeCase:
			try:
				ret.append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scan, atlasobj.name, 'bold_net.csv')), atlasobj))
			except FileNotFoundError as e:
				print('File %s not found.' % os.path.join(boldPath, scan, atlasobj.name, 'bold_net.csv'))
				print(e)
	return ret

def loadRandomDynamicNets(boldPath, atlasobj, totalNum = 0, scanList = None):
	"""
	This function is used to randomly load the dynamic nets of subjects.
	Specify how many nets in total you would like to get in totalNum.
	Specify which scans to load as a list of strings or a file path in scanList.
	Logic: Randomly load one dynamic net for each scan (make sure not repeat) and add it.
		   If the total number is enough, return.
		   If not, continue load one more dynamic net.
	"""
	retList = []
	scanList = process_subject_list(scanList)
	ret = {}
	scanName = 'None'
	lastScanName = 'Unknown'
	iterationCounter = 0 # counter for total iteration, equals num of dynamic nets of each scan in ret
	while len(retList) < totalNum:
		iterationCounter += 1
		currentList = []
		for scanName in sorted(os.listdir(boldPath)):
			if scanName != lastScanName:
				occurrenceCounter = 0
				lastScanName = scanName
			occurrenceCounter += 1
			if scanList is not None and scanName not in scanList:
				continue
			# randomly load one dynamic net in this subject
			if scanName not in ret:
					ret[scanName] = []
			else:
				pass
			try:
				# randomly search for one non-in net
				dynamicList = sorted(os.listdir(os.path.join(boldPath, scanName, atlasobj.name, 'bold_net')))
				dynamicList.remove('corrcoef.csv')
				dynamicList.remove('timeseries.csv')
				flag = True
				while flag:
					flag = False
					# get a random
					idx = random.randint(0, len(dynamicList)-1)
					for net in ret[scanName]:
						if net.name == dynamicList[idx]:
							flag = True
							break
				ret[scanName].append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scanName, atlasobj.name, 'bold_net', dynamicList[idx])), atlasobj, name = dynamicList[idx]))
				currentList.append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scanName, atlasobj.name, 'bold_net', dynamicList[idx])), atlasobj, name = dynamicList[idx]))
			except FileNotFoundError as e:
				print('File %s not found.' % os.path.join(boldPath, scanName, atlasobj.name, 'bold_net', 'corrcoef.csv'))
				print(e)
		# check if we add all these people in, the total amount would exceed
		if len(currentList) + len(retList) > totalNum:
			# only add some people in
			random.shuffle(currentList)
			retList += currentList[:(totalNum - len(retList))]
		else:
			# add all people in
			retList += currentList
	return retList

def loadAllDynamicNets(boldPath, atlasobj, dynamicDict, timeCase = 1, subjectList = None):
	"""
	This function loads all dynamic networks from the given subjects in the list
	Only data from timeCase session are loaded
	DynamicDict contains: 'windowLength' and 'stepSize', specified as integers
	"""
	subjectList = process_subject_list(subjectList)
	ret = []
	subjectName = 'None'
	lastSubjectName = 'Unknown'
	for scan in sorted(os.listdir(boldPath)):
		if scan.find('_') != -1:
			subjectName = scan[:scan.find('_')]
		else:
			subjectName = scan
		if subjectName != lastSubjectName:
			occurrenceCounter = 0
			lastSubjectName = subjectName
		occurrenceCounter += 1
		if subjectList is not None and subjectName not in subjectList:
			continue
		if occurrenceCounter == timeCase:
			try:
				for file in sorted(os.listdir(os.path.join(boldPath, scan, atlasobj.name, 'bold_net'))):
					if file.find('-') != -1:
						ret.append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scan, atlasobj.name, 'bold_net', file)), atlasobj))
			except FileNotFoundError as e:
				print('File %s not found.' % os.path.join(boldPath, scan, atlasobj.name, 'bold_net', 'corrcoef.csv'))
				print(e)
	return ret

def loadAllNets(boldPath, atlasobj, scanList = None):
	"""
	This script is used to load all scans.
	The given list contains scan names.
	"""
	scanList = process_subject_list(scanList)
	ret = []
	if scanList is None:
		scanList = sorted(os.listdir(boldPath))
	for scan in sorted(os.listdir(boldPath)):
		if scan not in scanList:
			continue
		try:
			ret.append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scan, atlasobj.name, 'bold_net', 'corrcoef.csv')), atlasobj))
		except FileNotFoundError:
			print('File %s not found.' % os.path.join(boldPath, scan, atlasobj.name, 'bold_net', 'corrcoef.csv'))
	return ret

def save_matrix_csv_style(mat, filePath):
	xlim = mat.shape[0]
	ylim = mat.shape[1]
	xidx = 0
	with open(filePath, 'w') as f:
		while xidx < xlim:
			yidx = 0
			while yidx < ylim:
				if yidx + 1 < ylim:
					f.write('%f\t' % mat[xidx, yidx])
				elif xidx + 1 < xlim:
					f.write('%f\n' % mat[xidx, yidx])
				else:
					f.write('%f' % mat[xidx, yidx])
				yidx += 1
			xidx += 1