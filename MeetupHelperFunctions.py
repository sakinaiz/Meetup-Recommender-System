# coding: utf-8

# # Load the libraries
import pandas as pd
import numpy as np
import datetime as dt
import re

us_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

# Check if any columns have null values
def check_nulls(df, check_cols, verbose = True):
    if verbose:
        print('\tChecking for NULL values...')

    df_info_array = [df[check_cols].dtypes.values.T, 
                     df[check_cols].isnull().sum().values.T, 
                     (100*df[check_cols].isnull().sum()/df.shape[0]).values.T]
    df_info = pd.DataFrame(df_info_array, 
                           index=['column_type', 'null_count', '%_null_count'],
                           columns = df[check_cols].columns)
    
    return df_info#.loc['null_count'].sum()

# Function to compute the memory usage of a dataframe
def mem_usage(pandas_obj):
    if isinstance(pandas_obj,pd.DataFrame):
        usage_b = pandas_obj.memory_usage(deep=True).sum()
    else: # we assume if not a df it's a series
        usage_b = pandas_obj.memory_usage(deep=True)
    usage_mb = usage_b / 1024 ** 2 # convert bytes to megabytes
    return "{:03.2f} MB".format(usage_mb)

# Change data types
def change_dtype(df, category_cols, verbose = True):
    if verbose:
        print('\tChanging datatypes...')

    optimized_df = df.copy()

    df_int = df.select_dtypes(include=['int']).copy()
    if list(df_int.columns.values):
        df_int = df_int.apply(pd.to_numeric, downcast='unsigned')
        optimized_df[df_int.columns] = df_int

    df_float = df.select_dtypes(include=['float']).copy()
    if list(df_float.columns.values):
        df_float = df_float.apply(pd.to_numeric, downcast='float')
        optimized_df[df_float.columns] = df_float

    df_obj = df[category_cols].copy()
    if list(df_obj.columns.values):
        df_obj = df_obj.apply(pd.Series.astype, dtype='category')
        optimized_df[df_obj.columns] = df_obj

    return optimized_df

# function to parse the 'topics' field
def parse_topics(long_text, field='name'):
    
    if isinstance(long_text, str):
        listOfTopicNames = []
        listOfTopicIds   = []
        regex = re.compile(r"{'urlkey':\s'(.*?)',\s'name':\s'(.*?)',\s'id':\s(\d+)}")
        match = regex.findall(long_text[1:-1].replace("\"","\'"))
        if match:
            if field=='name':
                for item in match:
                    listOfTopicNames.append(item[1])
                return listOfTopicNames
            else:
                for item in match:
                    listOfTopicIds.append(item[2])
                return listOfTopicIds
        else:
            return []
    else:
        return []
    

#function to flatten list of lists
flatten = lambda l: list(set([item.replace(' ','_') 
                              for sublist in l 
                              for item in sublist 
                              if len(item.strip())>0]
                            )
                        )
#function to flatten list of lists of ints as strings
flatten_int = lambda l: list(set([str(item) 
                              for sublist in l 
                              for item in sublist 
                              if item]
                            )
                        )
# clean topic ids string
topic_str2list = lambda topic_str: [topic.strip() for topic in (topic_str
                                                                .strip('[')
                                                                .strip(']')
                                                                .replace("'",'')
                                                                .replace(' ','')
                                                                .split(','))
                                   ]

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True
    
# Make twin axis
def make_twin_axis(ax, ncount, maxfreq=100):
    
    ax2=ax.twinx()

    # Switch so count axis is on right, frequency on left
    ax2.yaxis.tick_left()
    ax.yaxis.tick_right()

    # Also switch the labels over
    ax.yaxis.set_label_position('right');
    ax2.yaxis.set_label_position('left');

    ax2.set_ylabel('Frequency [%]');

    # Fix the frequency range to 0-100
    ax2.set_ylim(0,maxfreq);
    ax.set_ylim(0,ncount/(100/maxfreq));
    # Use a LinearLocator to ensure the correct number of ticks
    ax.yaxis.set_major_locator(ticker.LinearLocator(10))
    # And use a MultipleLocator to ensure a tick spacing of 10
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(maxfreq/10))
    # Need to turn the grid on ax2 off, otherwise the gridlines end up on top of the bars
    ax2.grid(None);
    # Annotate the bars
    for p in ax.patches:
        x_bar=p.get_bbox().get_points()[:,0]
        y_bar=p.get_bbox().get_points()[1,1]
        ax.annotate('{:.1f}'.format(100.*y_bar/ncount), (x_bar.mean(), y_bar), 
                    ha='center', va='bottom') # set the alignment of the text
        