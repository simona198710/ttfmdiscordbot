import json
import traceback
import os
from os import listdir
from os.path import isfile, join
import copy

oldData = {}

def save_data(obj, name ):
	global oldData
	
	if (not isinstance(obj, (list,)) and (not isinstance(obj, str))):
		if not os.path.exists('save/'+ name):
			os.makedirs('save/'+ name)
		
		if not name in oldData:
			oldData[name] = {}
		
		for id in obj:
			needsSave = False
			if not id in oldData[name]:
				#print("id "+str(id)+" does not exist in save")
				needsSave = True
			else:
				if oldData[name][id] != obj[id]:
					#print("id "+str(id)+" has changed")
					needsSave = True
				#else:
					#print(oldData[name][id],obj[id])
			
			if needsSave:
				try:
					with open('save/'+ str(name) +"/"+str(id)+ '.json', 'w') as f:
						#print("Save data start")
						json.dump(obj[id], f)
						#print("Save data finish")
				except Exception as ex:
					print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
			#else:
				#print("id "+str(id)+" has not changed")
		
		for oldId in oldData[name]:
			validToRemove = True
			if str(oldId) in obj:
				validToRemove = False
			try:
				if int(oldId) in obj:
					validToRemove = False
			except:
				pass
			
			if validToRemove:
				try:
					os.remove('save/'+ str(name) +"/"+str(oldId)+ '.json')
				except:
					print("Error when removing unsued id from "+str(name)+" ID "+str(oldId))
			
		oldData[name] = copy.deepcopy(obj)
		
	elif isinstance(obj, str):
		#print("Going to save string")
		try:
			if not name in oldData:
				oldData[name] = ""
			oldData[name] = copy.deepcopy(obj)
			with open('save/'+ name + '.json', 'w') as f:
				#print("Save data start")
				json.dump(obj, f)
				#print("Save data finish")
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
			
	else:
		try:
			if not name in oldData:
				oldData[name] = {}
			oldData[name] = copy.deepcopy(obj)
			with open('save/'+ name + '.json', 'w') as f:
				#print("Save data start")
				json.dump(obj, f)
				#print("Save data finish")
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

def load_data(name):
	global oldData
	
	oldData[name] = {}
	#print("Trying to load folder",str(name))
	
	try:
		onlyfiles = [f for f in listdir("save/"+str(name)+"/") if isfile(join("save/"+str(name)+"/", f))]
	except:
		#print("Error reading folder "+str(name))
		onlyfiles = []
		
	for file in onlyfiles:
		#print(str(file))
		id = str(file).replace(".json","")
		if os.path.isfile('save/'+ name +"/"+str(file)):
			try:
				with open('save/'+ name +"/"+str(file), 'r') as f:
					oldData[name][id] = json.load(f)
			except Exception as ex:
				print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	
	return copy.deepcopy(oldData[name])