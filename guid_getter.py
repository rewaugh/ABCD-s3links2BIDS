## Purpose: Get slinks from NDA from known GUIDs. 
# Output is csv file, "slinks.csv" with links to imaging data

# last update 3/20/19 by R. Waugh

## Pre-requisites 
# 1. NDA username and password
# 2. Install nda_aws_token_generator
# git clone https://github.com/NDAR/nda_aws_token_generator.git
# List of GUIDs (default is ndar_sample.csv for testing purposes)

# User adds GUID file
filename='ndar_sample.csv'

import requests
import json
from getpass import getpass
import pandas as pd

username = getpass("what is your NDA username?:")
password = getpass("What is your NDA password?:")

guidlist=list(pd.read_csv('ndar_sample.csv',sep=' '))
links=pd.DataFrame(columns=['slinks'])
for guid in guidlist:
	print(str(guid))
	gui=str(guid)
	r = requests.get("https://ndar.nih.gov/api/guid/{}/data?short_name=image03".format(gui),
	auth=requests.auth.HTTPBasicAuth(username, password),
	headers={'Accept': 'application/json'})
	guid_data = json.loads(r.text)
	
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
		#print("age:{}, url:{}".format(ages[i],image))
		guid_list.append(image)
	links=links.append({'slinks' : image},ignore_index=True)

links.to_csv(r'./slinks.csv', header=False, index=False, sep=' ')