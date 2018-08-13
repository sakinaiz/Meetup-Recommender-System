import os
import glob

import pandas as pd
import pickle

#folder containing csv files
data_folder = 'data/'
#folder containing Meetup events data
events_folder = data_folder+'event_data/'

#select columns to save
usecols = [ 'id', 'group.id', 'status', 'rating.average', 'rating.count',
            'yes_rsvp_count', 'maybe_rsvp_count', 'rsvp_limit', 
            'waitlist_count', 'headcount', 'fee.required',
            'created', 'updated', 'time', 'duration', 'utc_offset']

#read the events files
#num_event_files = len(glob.glob(events_folder+"*.csv"))
#all_events_df = pd.DataFrame([])
#for idx, event_file in enumerate(glob.glob(events_folder+"*.csv")):
#    df = pd.read_csv(event_file)
#    all_events_df = all_events_df.append(df,ignore_index=True)
#        
#    if not idx%100:
#        print('Done reading {0}/{1} events files'.format(idx+1, num_event_files))
#        # save the dataframe
#        all_events_df.to_csv(data_folder+'all_group_events_script.csv', columns=usecols, index=False)

# read the selected group ids from file
min_city_cnt = 10#5 #3
min_mem_cnt = 5 #20 
with open (data_folder+'unique_groupIds_top{0}Cities{1}.pkl'.format(min_city_cnt, min_mem_cnt), 'rb') as fp:
    unique_USgroup_ids = pickle.load(fp)
print('Number of unique groups in top {0} cities in US: {1}'.format(min_city_cnt, len(unique_USgroup_ids)))

num_event_files = len(unique_USgroup_ids)
all_events_df = pd.DataFrame([])
for idx, group_id in enumerate(unique_USgroup_ids):
    event_file = events_folder+'groupID_'+str(group_id)+'.csv'
    if os.path.exists(event_file):
        df = pd.read_csv(event_file)
        all_events_df = all_events_df.append(df,ignore_index=True)
        
        if not idx%100:
            print('Done reading {0}/{1} events files'.format(idx+1, num_event_files))
            # save the dataframe
            all_events_df.to_csv(data_folder+'all_group_events_script_part2.csv', columns=usecols, index=False)

print('Dimension of events dataframe: ', all_events_df.shape)  

# save the data
all_events_df.to_csv(data_folder+'all_group_events_script_part2.csv', columns=usecols, index=False)

#with open(data_folder+'all_group_events_script.pkl', "wb") as fp:  
#    pickle.dump(all_events_df, fp)
    
print('Done reading and saving {0}/{1} events files'.format(idx+1, num_event_files))