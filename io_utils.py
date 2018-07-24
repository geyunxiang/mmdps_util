import shutil
import os
import gzip
import random

from mmdps.proc import netattr, atlas
from mmdps.util import loadsave
from mmdps_old import brain_net

def ungzip(fgz):
	with gzip.open(fgz, 'rb') as fin,\
		 open(fgz[:-3], 'wb') as fout:
		shutil.copyfileobj(fin, fout)

def loadAllTemporalNets(boldPath, totalTimeCase, atlasobj, subjectList = None):
	"""
	This function is used to load temporal scans. All person with up
	to totalTimeCase number of scans will be loaded and returned in a dict. 
	The key of the dict is the subject name.
	Each element in the dict is the temporal scans of one person. The data are stored
	as a list of BrainNet.
	"""
	if type(subjectList) is str:
		# read in subjectList
		with open(subjectList) as f:
			subjectList = []
			for line in f.readlines():
				subjectList.append(line.strip())
	ret = {}
	currentPersonScans = []
	subjectName = 'None'
	lastSubjectName = 'Unknown'
	occurrenceCounter = 0
	for scan in sorted(os.listdir(boldPath)):
		subjectName = scan[:scan.find('_')]
		if subjectList is not None and subjectName not in subjectList:
			continue
		if subjectName != lastSubjectName:
			if occurrenceCounter >= totalTimeCase:
				ret[lastSubjectName] = currentPersonScans[:totalTimeCase]
			occurrenceCounter = 0
			lastSubjectName = subjectName
			currentPersonScans = []
		occurrenceCounter += 1
		currentPersonScans.append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scan, atlasobj.name, 'bold_net', 'corrcoef.csv')), atlasobj))
	return ret

def loadSpecificNets(boldPath, atlasobj, timeCase = 1, subjectList = None):
	"""
	This function is an implementation on the new mmdps version.
	This function is used to load the first/second/etc scans of subjects.
	Specify which subjects to load as a list of strings or a file path in subjectList.
	If no subjectList is given, load all scans.
	"""
	if type(subjectList) is str:
		# read in subjectList
		with open(subjectList) as f:
			subjectList = []
			for line in f.readlines():
				subjectList.append(line.strip())
	elif type(subjectList) is list:
		pass
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
				ret.append(netattr.Net(loadsave.load_csvmat(os.path.join(boldPath, scan, atlasobj.name, 'bold_net', 'corrcoef.csv')), atlasobj))
			except FileNotFoundError as e:
				print('File %s not found.' % os.path.join(boldPath, scan, atlasobj.name, 'bold_net', 'corrcoef.csv'))
				print(e)
	return ret

def loadRandomDynamicNets(boldPath, atlasobj, totalNum = 0, scanList = None):
	"""
	This function is used to randomly load the dynamic nets of subjects.
	Specify how many nets in total you would like to get in totalNum.
	Specify which scans to load as a list of strings or a file path in scanList.
	Logic: Randomly load one dynamic net for each scan (make sure not repeat).
		   If the total number is enough, randomly shuffle and return.
		   If not, continue load one more dynamic net.
	"""
	if type(scanList) is str:
		# read in scanList
		with open(scanList) as f:
			scanList = []
			for line in f.readlines():
				scanList.append(line.strip())
	elif type(scanList) is list:
		pass
	ret = {}
	scanName = 'None'
	lastScanName = 'Unknown'
	iterationCounter = 0 # counter for total iteration, equals num of dynamic nets of each scan in ret
	while len(ret) * iterationCounter < totalNum:
		iterationCounter += 1
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
			except FileNotFoundError as e:
				print('File %s not found.' % os.path.join(boldPath, scanName, atlasobj.name, 'bold_net', 'corrcoef.csv'))
				print(e)
	# convert ret to list
	retList = []
	for key, value in ret.items():
		retList += value
	random.shuffle(retList)
	return retList[:totalNum]

def loadAllNets(boldPath, atlasobj, scanList = None):
	"""
	This script is used to load all scans.
	The given list contains scan names.
	"""
	if type(scanList) is str:
		# read in scanList
		with open(scanList) as f:
			scanList = []
			for line in f.readlines():
				scanList.append(line.strip())
	elif type(scanList) is list:
		pass
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