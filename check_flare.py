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
from helioweb_locations import *

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
parser.add_argument("--model_mode", type=str, default='', \
       help=("historical, nowcast, or forecast"))
args = parser.parse_args()


root_dir = args.root_dir
run_time = args.run_time
model_mode = args.model_mode

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
       if (model_mode == ""):
             model_mode = "forecast"
else:
       utc_datetime = datetime.strptime(run_time, '%Y%m%d_%H%M')
       if (model_mode == ""):
             model_mode = "historical"

utc_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
utc_time_json = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
print ("test timestamp:", utc_time, file=sys.stderr)
print ("model mode:", model_mode, file=sys.stderr)

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
# url_flare = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR?"
# # JSON:
# url_flare = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR?"

#------ get the list for target date -----
url_flare = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR?startDate="+startdate+"&endDate="+enddate



print (url_flare, file=sys.stderr)


f1 = urllib.request.urlopen(url_flare)
data = json.load(f1)


print (len(data), file=sys.stderr)
#print (data[0].get('speed'))
#print (data[1])

flare_index=[]

#### check flares in the last 48 hours, every 15 mins

dt_start = utc_datetime - timedelta(minutes=2879)

with open(root_dir+'/pastflare.json') as flare_list:
    list_obj = json.load(flare_list)

for i in range(0, len(data)):
    flare_start_time = data[i].get('flrID').split("-FLR-")[0]

    datetime_flare = datetime.strptime(flare_start_time, '%Y-%m-%dT%H:%M:%S')

    print (datetime_flare, dt_start, utc_datetime, file=sys.stderr)

    if datetime_flare > dt_start and datetime_flare <= utc_datetime:        
        # check whether this flare has been simulated before
        result = [x for x in list_obj if x.get('flrID')==data[i].get('flrID')]
        
        if result == []:
        # no run found for this flare, new flare detected:
            flare_index.append(i)
        else:
            print ('Previous simulation run found:', result, file=sys.stderr)

print ('total NEW flare counts in the last 48 hours:', len(flare_index), file=sys.stderr)
ii = len(flare_index)-1 # index number for the latest flare

f4 = open(root_dir+'/flarelog.txt', 'a')

#### check if there is a background solar wind setup in the most recent 8-hour window
# now assuming there can be only at most 1 flare in the 15 mins time window
print ('flare_index', len(flare_index), file=sys.stderr)

if len(flare_index) != 0:
    list_obj.append({"flrID":data[flare_index[ii]].get('flrID')})
    with open(root_dir+'/pastflare.json', 'w') as write_file:
       json.dump(list_obj, write_file, indent=4)

    flare_start_time = data[flare_index[ii]].get('flrID').split("-FLR-")[0]
    datetime_flare = datetime.strptime(flare_start_time, '%Y-%m-%dT%H:%M:%S')

    target_date = datetime_flare.strftime('%Y-%m-%d')
    t1 = datetime.strptime(target_date, '%Y-%m-%d')     # 00:00
    t2 = t1 + timedelta(hours=8)                        # 08:00
    t3 = t2 + timedelta(hours=8)                        # 16:00
    
    f4.write('Checking Time:{} | flare found:{} class:{}\n'.format(utc_time, data[flare_index[ii]].get('flrID'), data[flare_index[ii]].get('classType')))

    # assuming the background solar wind setup can finish in 15 mins
    if datetime_flare < t2: 
        bgsw_folder_name =t1.strftime('%Y%m%d_%H%M')
    elif datetime_flare < t3:
        bgsw_folder_name =t2.strftime('%Y%m%d_%H%M')
    else:
        bgsw_folder_name =t3.strftime('%Y%m%d_%H%M')



    #### modify input.json for the flare run
    f2 = open(root_dir+'/Background/'+bgsw_folder_name+'/input.json', 'r')
    input_data = json.load(f2)
    f2.close()

    # determin CME speed based on flare class

    flare_class = data[flare_index[ii]].get('classType')
    class_tokens = list(flare_class)
    #print('flare_class:', flare_class,class_tokens[1]+class_tokens[2]+class_tokens[3])
    class_num = float(class_tokens[1]+class_tokens[2]+class_tokens[3])

    if class_tokens[0] == 'X':
        FSXR = class_num*1e-4
    if class_tokens[0] == 'M':
        FSXR = class_num*1e-5
    if class_tokens[0] == 'C':
        FSXR = class_num*1e-6
    if class_tokens[0] == 'B':
        FSXR = class_num*1e-7

    Vcme = 2.4e4*FSXR**0.3 # km/s

    width = Vcme/25.+60.
    if width >= 140.:
        width = 140.

    print('flare_class, Vcme', flare_class, Vcme, file=sys.stderr)

    location = data[flare_index[ii]].get('sourceLocation')
    loc_tokens = list(location)
    angle = int(loc_tokens[4]+loc_tokens[5])
    if loc_tokens[3]=='W':
        phi_e = 100 - angle
    if loc_tokens[3]=='E':
        phi_e = 100 + angle

    print(loc_tokens[3], phi_e, file=sys.stderr)

    input_data['cme_speed'] = Vcme
    input_data['cme_width'] = int(width)
    input_data['phi_e'] = phi_e

    # change density multiplier based on CME speed
    if Vcme >= 1500:
        n_multi = 4.0
    else:
        n_multi = Vcme*2e-3 + 1.

    input_data['n_multi'] = n_multi
    
    f3 = open(root_dir+'/Background/'+bgsw_folder_name+'/'+run_time+'_flare_earth_input.json', 'w')
    json.dump(input_data, f3, indent=4)
    f3.close()

    #### Generating Output JSON 

    json_data={"sep_forecast_submission":{
        "model": { "short_name": "", "spase_id": "" },
        "options": "",
        "issue_time": "",
        "mode": model_mode,
        "triggers": [],
        "forecasts": [           
            {
               "energy_channel": { "min": 10, "max": -1, "units": "MeV"},
               "species": "proton",
               "location": "earth",
               "prediction_window": { "start_time": "", "end_time": "" },
               "peak_intensity": { "intensity": "", "units": "", "time": ""},
               "peak_intensity_max": { "intensity": "", "units": "", "time": "" },
               "event_lengths":[ { "start_time": "",  "end_time": "", "threshold": "", "threshold_units": ""  }],
               "fluences": [{"fluence": "", "units": ""}],
               "fluence_spectra": [{"start_time": "", "end_time": "",
                   "threshold_start":"", "threshold_end":"",
                   "threshold_units":"", "fluence_units": "",
                   "fluence_spectrum":[{"energy_min": "", "energy_max":"", "fluence": ""}]}
                   ],
               "threshold_crossings": [ { "crossing_time": "", "threshold": "", "threshold_units": "" } ],
               "all_clear": { "all_clear_boolean": "", "threshold": "", "threshold_units": ""},
               "sep_profile": ""
           },
           {
               "energy_channel": { "min": 100, "max": -1, "units": "MeV"},
               "species": "proton",
               "location": "earth",
               "prediction_window": { "start_time": "", "end_time": "" },
               "peak_intensity": { "intensity": "", "units": "", "time": ""},
               "peak_intensity_max": { "intensity": "", "units": "", "time": "" },
               "event_lengths": [{ "start_time": "",  "end_time": "", "threshold": "", "threshold_units": ""  }],
               "fluences": [{"fluence": "", "units": ""}],
               "fluence_spectra": [{"start_time": "", "end_time": "",
                   "threshold_start":"", "threshold_end":"",
                   "threshold_units":"", "fluence_units": "",
                   "fluence_spectrum":[{"energy_min": "", "energy_max":"", "fluence": ""}]}
                   ],
               "threshold_crossings": [ { "crossing_time": "", "threshold": "", "threshold_units": "" } ],
               "all_clear": { "all_clear_boolean": "", "threshold": "", "threshold_units": ""},
               "sep_profile": ""
           }
        ]
    }}

    flare = {
           "flare":{
           "last_data_time": data[flare_index[ii]].get('endTime'),
           "start_time":data[flare_index[ii]].get('beginTime'),
           "peak_time": data[flare_index[ii]].get('peakTime'),
           "end_time": data[flare_index[ii]].get('endTime'),
           "location": data[flare_index[ii]].get('sourceLocation'),         
#           "CME_half_width": width/2.,
#           "CME_speed": Vcme,
#           "coordinates": "HEEQ",
           "intensity": FSXR,
#           "catalog_id": data[flare_index[ii]].get('flrID'),
           "urls": [ data[flare_index[ii]].get('link') ]
           },
           "cme":{
           "half_width": width/2.,
           "speed": Vcme,
           "catalog": "hypothetical, derived from flare info"
           }
    }

    json_data["sep_forecast_submission"]["triggers"].append(flare)

    # inputs = {
    #     "magnetic_connectivity":{
    #     "method": "Parker Spiral",
    #     "lat": 0.0,
    #     "lon": 0.0,
    #     "solar_wind":{
    #         "observatory":"DSCOVR",
    #         "speed":input_data['glv'],
    #         "proton_density":input_data['gln'],
    #         "magnetic_field":input_data['glb']
    #     }
    #     }
    # }
    
    # json_data["sep_forecast_submission"]["inputs"].append(inputs)

    with open(root_dir+'/Background/'+bgsw_folder_name+'/'+run_time+'_flare_earth_output.json', 'w') as write_file:
        json.dump(json_data, write_file, indent=4)
    flare_id = data[flare_index[ii]].get('flrID').replace('-', '', 2).replace(':', '', 2)
else:
    bgsw_folder_name=''
    flare_id = ''
    if len(data) > 0:
        f4.write('Checking Time:{} | No new flare found, last flare in 7 days: {}\n'.format(utc_time, data[len(data)-1].get('flrID') ))
    else:
        f4.write('Checking Time:{} | No new flare found, no flare in past 7 days.\n'.format(utc_time))
f4.close()
print (bgsw_folder_name, flare_id)


