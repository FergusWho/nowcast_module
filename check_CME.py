#=================================================================================
# Python script to grep real time Solar wind parameters from API

import math
import numpy as np
import matplotlib.pyplot as plt

import urllib.request
import datetime
from datetime import timedelta
from datetime import datetime
import pytz
import json
import sys
import os
import argparse

# some parameters 
AU  = 1.5e11        
eo  = 1.6e-19
pi  = 3.141592653589793116
bo  = 2.404e-9       
t_o = 2858068.3
vo  = 52483.25 
co  = 3.0e8
n_0 = 1.0e6


#### Get the current time
now = datetime.utcnow()

LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo
local_time = now.strftime("%Y-%m-%d %H:%M:%S")

utc = pytz.timezone("UTC")

#utc_datetime = now.astimezone(utc)

utc_datetime = datetime.strptime('2022-01-14T16:15Z', '%Y-%m-%dT%H:%MZ')

utc_datetime= utc_datetime.replace(tzinfo=utc)


dt_start = utc_datetime - timedelta(minutes=15)
utc_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

print("Current Local Time =", local_time, '\nUTC Time =', utc_time)
print("Current Local Time =", utc_datetime, '\nUTC Time =', dt_start)


# text: 
url_cme = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis.txt?mostAccurateOnly=true&speed=500&halfAngle=35"

# JSON:
url_cme = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis?&mostAccurateOnly=true&speed=500&halfAngle=35&catalog=ALL"

f1 = urllib.request.urlopen(url_cme)
data = json.load(f1)




print (len(data))

print (data[0].get('speed'))

print (data[1])

CME_index=[]

#### check CMEs in the last 15 mins
for i in range(0, len(data)):
    datetime_CME = datetime.strptime(data[i].get('time21_5'), '%Y-%m-%dT%H:%MZ')
    datetime_CME = datetime_CME.replace(tzinfo=utc) # make it an aware datetime object
    print (datetime_CME)

    if datetime_CME > dt_start and datetime_CME <= utc_datetime:
        CME_index.append(i)

print ('total CME counts in the last 15 mins:', len(CME_index))

#### check if there is a background solar wind setup in the most recent 8-hour window
# now assuming there can be only at most 1 CME in the 15 mins time window

if len(CME_index) != 0:
    dt_start = dt_start.replace(tzinfo=None)

    target_date = dt_start.strftime('%Y-%m-%d')
    t1 = datetime.strptime(target_date, '%Y-%m-%d')     # 00:00
    t2 = t1 + timedelta(hours=8)                        # 08:00
    t3 = t2 + timedelta(hours=8)                        # 16:00
    # assuming the background solar wind setup can finish in 15 mins
    if dt_start < t2: 
        bgsw_folder_name =t1.strftime('%Y-%m-%d_%H:%M')
    elif dt_start < t3:
        bgsw_folder_name =t2.strftime('%Y-%m-%d_%H:%M')
    else:
        bgsw_folder_name =t3.strftime('%Y-%m-%d_%H:%M')

    print(bgsw_folder_name)

#### modify input.json for the CME run
    f2 = open(bgsw_folder_name+'/input.json', 'r')
    input_data = json.load(f2)
    f2.close()

    input_data['cme_speed'] = data[CME_index[0]].get('speed') 
    input_data['cme_width'] = data[CME_index[0]].get('halfAngle')*2 
    input_data['phi_e'] = 100.0-data[CME_index[0]].get('longitude') 
    
    f3 = open(bgsw_folder_name+'/'+data[CME_index[0]].get('associatedCMEID')+'input.json', 'w')
    json.dump(input_data, f3)
    f3.close()