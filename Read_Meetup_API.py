import time
import os.path
import re

import pandas as pd
from pandas.io.json import json_normalize

import json
from json import JSONDecodeError

import meetup.api
from meetup.exceptions import HttpTooManyRequests

# read Meetup API key
def getApiKey(key_path):
    key = ""
    f = open(key_path, 'r')
    key = f.read()
    return key

# Call the API
def callMeetupAPI(string, params):
    response = requests.get(string,params=params)
    return response.json()

#Fetching complete category,cities,topic_categories information using meetup.api package
#Categories
def categories2csv(client, path):
    categories_obj = client.GetCategories()
    categories_df  = pd.read_json(json.dumps(categories_obj.results))
    categories_df.to_csv(path+'categories.csv', index=False)
    return len(categories_df)
    
#Cities
def cities2csv(client, path):
    cities_per_page = 200
    #initial request to obtain total request pages
    cities_obj = client.GetCities(country='US')
    print("Total request cities = " + str(cities_obj.meta['total_count']))

    pages = int(cities_obj.meta['total_count']/cities_per_page)
    cities_df = pd.DataFrame([])
    for i in range(0, pages+1): #iterate over each request page
        #get offseted request by current request page
        try_flag = True
        while try_flag:
            try:
                print("Requesting page " + str(i) + "/" + str(pages))
                # (default order) number of members in the city: descending
                cities_obj = client.GetCities(country='US', pages=cities_per_page, offset=i)
                try_flag = False
            except JSONDecodeError as e:
                print('Trying again after 10 seconds..')
                time.sleep(10)

        cities_js = cities_obj.results
        # cities with less than 20 members are ignored
        if len(cities_js) != 0:
            if cities_js[-1]['member_count']>=20:
                cities_df = cities_df.append(json_normalize(cities_js))
            else:
                break
        else:
            break

        time.sleep(2)

    cities_df.to_csv(path+'cities.csv', index=False)
    return len(cities_df)
    
#Topic_Categories
def topicCategories2csv(client, path):
    topic_categories_obj = client.GetTopicCategories()
    topic_categories_df  = pd.read_json(json.dumps(topic_categories_obj.results))
    topic_categories_df.to_csv(path+'topic_categories.csv',index=False)
    return len(topic_categories_df)

#Function to fetch group for a given category
def getGroups(client, category_id, per_page, off_val):
    group_obj = client.GetGroups(category_id=category_id, 
                                 fields=['join_info,sponsors,contributions,membership_dues,last_event,next_event'],
                                 pages=per_page, offset=off_val)
    group_df  = json_normalize(group_obj.results)
    group_df  = group_df[group_df['country']=='US'].copy()
    return group_df, group_obj.meta

#Create groups files for every category
def groupsIncategory2csv(client, path, category_ids):
    done = False
    for catg_id in category_ids:
        print('Getting groups for category ID:', catg_id)
        groups_per_page = 200
        #initial request to obtain total request pages
        try_flag = True
        while try_flag:
            try:
                result, group_obj_meta = getGroups(client, catg_id, groups_per_page, 0)
                try_flag = False
            except JSONDecodeError as e:
                print('Waiting for 10 seconds..')
                time.sleep(10)
        #if there are no groups in this category move on to the next         
        if not group_obj_meta['total_count']:
                continue  
                
        pages = int(group_obj_meta['total_count']/groups_per_page)
        # more than one page
        if pages>0:
            groups_df = pd.DataFrame([])
            # add the zeroth page groups to dataframe
            groups_df = groups_df.append(result)
            for i in range(1, pages+1): #iterate over each request page
                try_flag = True
                while try_flag:
                    try:
                        print("Requesting page " + str(i) + "/" + str(pages))
                        result, _ = getGroups(client, catg_id, groups_per_page, i)
                        try_flag = False
                    except JSONDecodeError as e:
                        print('Waiting for 10 seconds..')
                        time.sleep(10)

                if len(result) != 0:
                    groups_df = groups_df.append(result)
                time.sleep(2)
        #only one page        
        else:
            groups_df = result
            
        groups_df.to_csv(path+'group_data_v2/categoryID_'+str(catg_id)+'.csv',\
                         index=False, encoding='utf-8')
        print('Number of groups: ', len(groups_df))
    done = True
    return done

#Fetch unique group ids 
def getUniqueGroupIDs(path, threshold=20):
    category_ids = list(pd.read_csv(path+'categories.csv', usecols=['id'])['id'])
    group_ids_list = []
    for catg_id in category_ids:
        #print('Reading groups in category: {}'.format(catg_id))
        df = pd.read_csv(path+'group_data/categoryID_'+str(catg_id)+'.csv',
                         usecols=['id','members'])
        group_ids_list.extend(list(df[df['members']>threshold]['id']))  

    return list(set(group_ids_list))

#Fetch unique group ids from selected cities
def getUniqueGroupIDsSelectCities(path, min_city_cnt=10, min_mem_cnt=20):
    category_ids = list(pd.read_csv(path+'categories.csv', usecols=['id'])['id'])
    df_list = []
    for catg_id in category_ids:
        #print('Reading groups in category: {}'.format(catg_id))
        df_list.append( pd.read_csv(path+'group_data/categoryID_'+str(catg_id)+'.csv',
                        usecols=['id','members', 'city']))
    df = pd.concat(df_list, ignore_index=False)
    # get top cities with max groups
    top_cities = list(df.groupby(['city'])['id'].agg('nunique').nlargest(min_city_cnt).index)
    
    group_ids_list = list(df[(df['members']>min_mem_cnt) & (df['city'].isin(top_cities))]['id'].unique())
    return top_cities, group_ids_list

#Function to fetch members data
def getMembers(client, group_id, per_page, off_val):
    member_obj = client.GetMembers(group_id=group_id, fields=['membership_count'],
                                   pages=per_page, offset=off_val)
    member_df = json_normalize(member_obj.results)
    return member_df

#Create member files for every group
def membersIngroup2csv(client, path, unique_group_ids):
    done = False
    for group_id in unique_group_ids:
        if os.path.exists(path+'member_data/groupID_'+str(group_id)+'.csv'):
            continue
        else:
            print('Getting members for group ID:', group_id)
            members_per_page = 200
            #initial request to obtain total request pages
            try_flag = True
            while try_flag:
                try:
                    member_obj = client.GetMembers(group_id=group_id, fields=['membership_count'],
                                                   pages=members_per_page, offset=0)
                    try_flag = False
                except JSONDecodeError as e:
                    print('Waiting for 10 seconds..')
                    time.sleep(10)
                    
            if not member_obj.meta['total_count']:
                continue
                
            pages = int(member_obj.meta['total_count']/members_per_page)
            
            if pages>0:
                members_df = pd.DataFrame([])
                # add the zeroth page members to dataframe
                members_df = members_df.append(json_normalize(member_obj.results))
                for i in range(1, pages+1): #iterate over each request page
                    try_flag = True
                    while try_flag:
                        try:
                            print("Requesting page " + str(i) + "/" + str(pages))
                            result = getMembers(client, group_id, members_per_page, i)
                            try_flag = False
                        except JSONDecodeError as e:
                            print('Waiting for 10 seconds..')
                            time.sleep(10)

                    if len(result) != 0:
                        members_df = members_df.append(result)

                    time.sleep(2)
            else:
                members_df = json_normalize(member_obj.results)
                
            if len(members_df):
                members_df['group_id'] = [group_id] * len(members_df)
                members_df.to_csv(path+'member_data/groupID_'+str(group_id)+'.csv',
                                  index=False,encoding='utf-8')
            print('Number of members: ', len(members_df))
    done = True
    return done

#Function to fetch members data
def getOrganizer(client, organizer_id):
    organizer_obj = client.GetMembers(member_id=organizer_id, pages=1,
                                      fields="gender,membership_count,messaging_pref,privacy,reachable")
    organizer_df = json_normalize(organizer_obj.results)
    return organizer_df

#Create member files for every group
def organizers2csv(client, path, unique_organizer_ids):
    done = False
    organizers_df = pd.DataFrame([])
    for idx, organizer_id in enumerate(unique_organizer_ids):
        print('Getting info for organizer:', organizer_id)
        
        try_flag = True
        while try_flag:
            try:
                result = getOrganizer(client, organizer_id)
                try_flag = False
            except JSONDecodeError as e:
                print('Waiting for 10 seconds..')
                time.sleep(10)
                
        if len(result) != 0:
            organizers_df = organizers_df.append(result)

        time.sleep(1)
        
        if not idx%50:
            organizers_df.to_csv(path+'organizers.csv', 
                                 index=False, encoding='utf-8')
    organizers_df.to_csv(path+'organizers.csv',index=False, encoding='utf-8')
    
    done = True
    return done, len(organizers_df)

#Function to fetch events
def getEvents(client, group_id, per_page, off_val):
    event_obj = client.GetEvents(group_id=group_id, 
                                 status="upcoming,past,proposed,suggested,cancelled",
                                 limited_events=True,
                                 text_format='plain',
                                 pages=per_page, offset=off_val)
    event_df = json_normalize(event_obj.results)
    return event_df

#Create event files for all groups
def eventsIngroup2csv(client, path, unique_group_ids):
    done = False
    for group_id in unique_group_ids:
        if os.path.exists(path+'event_data/groupID_'+str(group_id)+'.csv'):
            continue
        else:
            print('Getting events for group ID:', group_id)
            events_per_page = 200
            #initial request to obtain total request pages
            try_flag = True
            while try_flag:
                try:
                    event_obj = client.GetEvents(group_id=group_id,
                                                 status="upcoming,past,proposed,suggested,cancelled",
                                                 limited_events=True,
                                                 text_format='plain',
                                                 pages=events_per_page, offset=0)
                    try_flag = False
                except JSONDecodeError as e:
                    print('Waiting for 10 seconds..')
                    time.sleep(10)

            if not event_obj.meta['total_count']:
                continue

            pages = int(event_obj.meta['total_count']/events_per_page)
            
            if pages>0: 
                events_df = pd.DataFrame([])
                # add the zeroth page events to dataframe
                events_df = events_df.append(json_normalize(event_obj.results))
                
                for i in range(1, pages+1): #iterate over each request page
                    try_flag = True
                    while try_flag:
                        try:
                            print("Requesting page " + str(i) + "/" + str(pages))
                            result = getEvents(client, group_id, events_per_page, i)
                            try_flag = False
                        except JSONDecodeError as e:
                            print('Waiting for 10 seconds..')
                            time.sleep(10)

                    if len(result) != 0:
                        events_df = events_df.append(result)

                    time.sleep(2)
            else:
                events_df = json_normalize(event_obj.results)
                
            if len(events_df): 
                events_df.to_csv(path+'event_data/groupID_'+str(group_id)+'.csv', 
                                 index=False, encoding='utf-8')
            print('Number of events: ', len(events_df))
    
    done = True
    return done

#Function to fetch venues
def getVenues(client, group_id, per_page, off_val):
    venue_obj = client.GetVenues(group_id=group_id, pages=per_page, offset=off_val)
    venue_df = json_normalize(venue_obj.results)
    return venue_df

#Create venue file for every group
def venuesIngroup2csv(client, path, unique_group_ids):
    done = False
    for group_id in unique_group_ids:
        if os.path.exists(path+'venue_data/groupID_'+str(group_id)+'.csv'):
            continue
        else:
            print('Getting venues for group ID:', group_id)
            venues_per_page = 200
            #initial request to obtain total request pages
            try_flag = True
            while try_flag:
                try:
                    venue_obj = client.GetVenues(group_id=group_id)
                    try_flag = False
                except JSONDecodeError as e:
                    print('Waiting for 5 seconds..')
                    time.sleep(5)

            if not venue_obj.meta['total_count']:
                continue

            pages = int(venue_obj.meta['total_count']/venues_per_page)
            venues_df = pd.DataFrame([])
            for i in range(0, pages+1): #iterate over each request page
                try_flag = True
                while try_flag:
                    try:
                        print("Requesting page " + str(i) + "/" + str(pages))
                        result = getVenues(client, group_id, venues_per_page, i)
                        try_flag = False
                    except JSONDecodeError as e:
                        print('Waiting for 5 seconds..')
                        time.sleep(5)

                if len(result) != 0:
                    venues_df = venues_df.append(result)

                time.sleep(1)

            print('Number of venues: ', len(venues_df))
            if len(venues_df): 
                venues_df['group_id'] = [group_id] * len(venues_df)
                venues_df.to_csv(path+'venue_data/groupID_'+str(group_id)+'.csv',
                                 index=False, encoding='utf-8')
    done = True
    return done

def parse_topics(long_text):
    listOfTopics = []
    regex = re.compile(r"{'urlkey':\s'(.*?)',\s'name':\s'(.*?)',\s'id':\s(\d+)}")
    match = regex.findall(long_text[1:-1].replace("\"","\'"))
    if match:
        for item in match:
            listOfTopics.append(item[1].lower())
    return listOfTopics

#Function to fetch all topic names
def getTopicNames(path, category_ids):
    topic_names = []
    for cat_id in category_ids:
        print('Reading topics from {}'.format(cat_id))
        groups_df = pd.read_csv(path+'group_data/categoryID_'+str(cat_id)+'.csv')
        groups_df.dropna(subset=['topics'], inplace=True)
        topic_names.extend(groups_df['topics'].apply(parse_topics))
    all_topic_names = [item for sublist in topic_names for item in sublist ]
    return list(set(all_topic_names))
    
#Create topics file 
def topics2csv(client, path, all_topic_names):
    topics_df = pd.DataFrame([])
    for topic in all_topic_names:        
        try_flag = True
        while try_flag:
            try:
                print('Getting info for ', topic)
                topic_obj = client.GetTopics(name=topic_name)
                try_flag = False
            except JSONDecodeError as e:
                print('Waiting for 5 seconds..')
                time.sleep(5)

        if len(topic_obj) != 0:
            topics_df = topics_df.append(json_normalize(topic_obj.results))

        time.sleep(1)
        
    topics_df.to_csv(path+'topics.csv', index=False, encoding='utf-8')
    print('Number of topics: ', len(topics_df))
    return len(topics_df)
