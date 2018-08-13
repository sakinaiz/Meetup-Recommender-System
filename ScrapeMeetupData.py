from Read_Meetup_API import *

import pandas as pd
import meetup.api

import pickle

#data folder
data_path = 'data/'

#Get the Meetup API Key
key_path = data_path+"MeetupAPIkey.txt"                   
MY_API_KEY = getApiKey(key_path) 

#Initiate the Meetup API Client¶
if MY_API_KEY:
    client = meetup.api.Client(MY_API_KEY, overlimit_wait=True)
else:
    print('No Meetup API key provided')

#Get information about Meetup Groups
#category_ids = list(pd.read_csv(data_path+'categories.csv', usecols=['id'])['id'])
#done = groupsIncategory2csv(client, data_path, category_ids)

# read the organizer ids
with open (data_path+'unique_organizerIds.pkl', 'rb') as fp:
    unique_organizer_ids = pickle.load(fp)
print('Number of unique organizers {}'.format(len(unique_organizer_ids)))

# get organizer info
done, num_organizers = organizers2csv(client, data_path, unique_organizer_ids)
print('Number of unique organizers info received: {}'.format(num_organizers))

if done:
    print('Completed Scraping Organizers')
else:
    print('Scraping Organizers Incomplete')
    
# read the selected group ids from file
min_city_cnt = 10#5 #3
min_mem_cnt = 5 #20 
with open (data_path+'unique_groupIds_top{0}Cities{1}.pkl'.format(min_city_cnt, min_mem_cnt), 'rb') as fp:
    unique_USgroup_ids = pickle.load(fp)
print('Number of unique groups in top {0} cities in US: {1}'.format(min_city_cnt, len(unique_USgroup_ids)))

#Get members of Meetup Groups
#done = membersIngroup2csv(client, data_path, unique_USgroup_ids)

#Get events of Meetup Groups
# skipped index: 15975, 17258
done = eventsIngroup2csv(client, data_path, unique_USgroup_ids)
if done:
    print('Completed Scraping Events')
else:
    print('Scraping Events Incomplete')
