## Quick update for GUIDS: Iterate through a csv list of ndar files to get S3 links 

import requests
import json
from getpass import getpass
import pandas as pd

username = getpass("what is your NDA username?:")
password = getpass("What is your NDA password?:")

guidlist=list(pd.read_csv('ndar_sample.csv',sep=' '))

for guid in guidlist:
	print(str(guid))
	gui=str(guid)
	r = requests.get("https://ndar.nih.gov/api/guid/{}/data?short_name=image03".format(gui),
	auth=requests.auth.HTTPBasicAuth(username, password),
	headers={'Accept': 'application/json'})
	guid_data = json.loads(r.text)
	
# 
	experiments = []
	ages = []
	for age in guid_data['age']:
		age_value=age['value']
		for row in age['dataStructureRow']:
			for element in row['dataElement']:
				if element['name']=='EXPERIMENT_ID':
					if element['value'] not in experiments:
						experiments.append(element['value'])
						
	for experiment in experiments:
		query=str(experiment)
		print(query)
		r = requests.get("https://ndar.nih.gov/api/experiment/{}".format(query),
		headers={'Accept':'application/json'})
        
		experiment = json.loads(r.text)

	image_files = []
	ages = []
	for age in guid_data['age']:
		age_value = age['value']
		for row in age['dataStructureRow']:
			for link in row['links']['link']:
				if link['rel']=='data_file':
					image_files.append(link['href'])
					ages.append(age_value)
	guid_list = []
	for i,image in enumerate(image_files):
		print("age:{}, url:{}".format(ages[i],image))
		guid_list.append(image)