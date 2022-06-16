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

parser = argparse.ArgumentParser()
parser.add_argument("--root_dir", type=str, default='/data/iPATH/nowcast_module', \
       help=("Root directory"))
parser.add_argument("--run_time", type=str, default='', \
       help=("folder name for the run"))
args = parser.parse_args()


root_dir = args.root_dir
run_time = args.run_time

######################################################################################################

if (run_time == ""):
       # get current time
       now = datetime.now()
       LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo
       local_time = now.strftime("%Y-%m-%d %H:%M:%S")

       utc = pytz.timezone("UTC")
       utc_datetime = now.astimezone(utc)
       utc_datetime = utc_datetime.replace(tzinfo=None) # remove the timezone info for consistency
       
       #print("Current Local Time =", local_time, '\nUTC Time =', utc_time)
else:
       utc_datetime = datetime.strptime(run_time, '%Y-%m-%d_%H:%M')


utc_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
utc_time_json = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
print ("test timestamp:", utc_time)

### define folder name
# separate date and %H:%M:%S
date_str= utc_datetime.strftime("%Y-%m-%d")
date = datetime.strptime(date_str, '%Y-%m-%d')

seconds = (utc_datetime - date).total_seconds()

# if (seconds < 8*3600):
#        run_name = date_str+'_00:00'
# elif (seconds < 16*3600):
#        run_name = date_str+'_08:00'
# else:
#        run_name = date_str+'_16:00' 

# print ("folder name:", run_name)

# f0 = open(root_dir+'/temp.txt','w')
# f0.write(run_name)
# f0.close()

######################################################################################################


enddate = utc_datetime.strftime("%Y-%m-%d")
startdate = (utc_datetime - timedelta(days=7) ).strftime("%Y-%m-%d")





#------ get the current list ------
# # text: 
# url_cme = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis.txt?startmostAccurateOnly=true&speed=500&halfAngle=35"
# # JSON:
# url_cme = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis?&mostAccurateOnly=true&speed=500&halfAngle=35&catalog=ALL"

#------ get the list for target date -----
url_cme = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis?startDate="+startdate+"&endDate="+enddate+"&mostAccurateOnly=true&speed=500&halfAngle=35"


print (url_cme)


f1 = urllib.request.urlopen(url_cme)
data = json.load(f1)




print (len(data))

#print (data[0].get('speed'))
#print (data[1])

CME_index=[]




#### check CMEs in the last 48 hours, every 15 mins

dt_start = utc_datetime - timedelta(minutes=2879)

with open(root_dir+'/pastCME.json') as cme_list:
    list_obj = json.load(cme_list)

for i in range(0, len(data)):
    cme_start_time = data[i].get('associatedCMEID').split("-CME-")[0]

    datetime_CME = datetime.strptime(cme_start_time, '%Y-%m-%dT%H:%M:%S')
    #datetime_CME = datetime_CME.replace(tzinfo=utc) # make it an aware datetime object
    print (datetime_CME, dt_start, utc_datetime)

    if datetime_CME > dt_start and datetime_CME <= utc_datetime:        
        # check whether this CME has been simulated before
        result = [x for x in list_obj if x.get('associatedCMEID')==data[i].get('associatedCMEID')]
        
        if result == []:
        # no run found for this CME, new CME detected:
            CME_index.append(i)
        else:
            print ('Previous simulation run found:', result)

print ('total NEW CME counts in the last 48 hours:', len(CME_index))
ii = len(CME_index)-1 # index number for the latest CME

list_obj.append({"associatedCMEID":data[CME_index[ii]].get('associatedCMEID')})
with open(root_dir+'/pastCME.json', 'w') as write_file:
    json.dump(list_obj, write_file, indent=4)

f4 = open(root_dir+'/CMElog.txt', 'a')

#### check if there is a background solar wind setup in the most recent 8-hour window
# now assuming there can be only at most 1 CME in the 15 mins time window
print ('CME_index', len(CME_index))

if len(CME_index) != 0:
    cme_start_time = data[CME_index[ii]].get('associatedCMEID').split("-CME-")[0]
    datetime_CME = datetime.strptime(cme_start_time, '%Y-%m-%dT%H:%M:%S')

    target_date = datetime_CME.strftime('%Y-%m-%d')
    t1 = datetime.strptime(target_date, '%Y-%m-%d')     # 00:00
    t2 = t1 + timedelta(hours=8)                        # 08:00
    t3 = t2 + timedelta(hours=8)                        # 16:00
    
    f4.write('Checking Time:{} | CME found:{} speed:{}\n'.format(utc_time, data[CME_index[ii]].get('associatedCMEID'), data[CME_index[ii]].get('speed')))

    # assuming the background solar wind setup can finish in 15 mins
    if datetime_CME < t2: 
        bgsw_folder_name =t1.strftime('%Y-%m-%d_%H:%M')
    elif datetime_CME < t3:
        bgsw_folder_name =t2.strftime('%Y-%m-%d_%H:%M')
    else:
        bgsw_folder_name =t3.strftime('%Y-%m-%d_%H:%M')



    #### modify input.json for the CME run
    f2 = open(root_dir+'/'+bgsw_folder_name+'/input.json', 'r')
    input_data = json.load(f2)
    f2.close()

    input_data['cme_speed'] = data[CME_index[ii]].get('speed') 
    input_data['cme_width'] = data[CME_index[ii]].get('halfAngle')*2 
    input_data['phi_e'] = 100.0-data[CME_index[ii]].get('longitude') 
    
    f3 = open(root_dir+'/'+bgsw_folder_name+'/'+run_time+'_input.json', 'w')
    json.dump(input_data, f3, indent=4)
    f3.close()
    #### Generating Output JSON 

    json_data={"sep_forecast_submission":{
           "model": { "short_name": "iPATH", "spase_id": "spase://CCMC/SimulationModel/MODEL_NAME/VERSION" },
           "issue_time": utc_time_json,       
           "mode": "forecast",
           "triggers": [],
           "inputs": [],
           "forecasts": []
    }}

    cme = {
           "cme":{
           "start_time":cme_start_time,
           "lat": data[CME_index[ii]].get('latitude'),
           "lon": data[CME_index[ii]].get('longitude'),
#           "pa": 261,          
           "half_width": data[CME_index[ii]].get('halfAngle'),
           "speed": data[CME_index[ii]].get('speed'),
           "height": 21.5,
           "time_at_height": { "time":data[CME_index[ii]].get('time21_5'), "height": 21.5 },
           "coordinates": "HEEQ",
           "catalog": data[CME_index[ii]].get('catalog'),
           "catalog_id": data[CME_index[ii]].get('associatedCMEID'),
           "urls": [ data[CME_index[ii]].get('link') ]
           }
    }

    json_data["sep_forecast_submission"]["triggers"].append(cme)

    inputs = {
        "magnetic_connectivity":{
        "method": "Parker Spiral",
        "lat": 0.0,
        "lon": 0.0,
        "solar_wind":{
            "observatory":"DSCOVR",
            "speed":input_data['glv'],
            "proton_density":input_data['gln'],
            "magnetic_field":input_data['glb']
        }
        }
    }
    
    json_data["sep_forecast_submission"]["inputs"].append(inputs)

    with open(root_dir+'/'+bgsw_folder_name+'/'+run_time+'_output.json', 'w') as write_file:
        json.dump(json_data, write_file, indent=4)
else:
    bgsw_folder_name=''
    if len(data) > 0:
        f4.write('Checking Time:{} | No new CME found, last CME in 7 days: {}\n'.format(utc_time, data[len(data)-1].get('associatedCMEID') ))
    else:
        f4.write('Checking Time:{} | No new CME found, no CME in past 7 days.\n'.format(utc_time))
f4.close()
print (bgsw_folder_name)


