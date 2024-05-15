#=================================================================================
# Python script to grep real time Solar wind parameters from API

from math import pi
import numpy as np
import urllib.request
import datetime
from datetime import timedelta
from datetime import datetime
import time
import pytz
import json
import sys
import os
import argparse
from helioweb_locations import *
import traceback

# command-line arguments
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
observers = { 'mars': 'planets/mars', 'venus': 'planets/venus', 'STA': 'spacecraft/stereoa', 'PSP': 'spacecraft/psp' }
######################################################################################################

def exit_after_error(utc_time, msg, error_type):
   with open(root_dir+'/CME/log.txt', 'a') as log_file:
      log_file.write('Checking Time:{} | {}\n'.format(utc_time, error_type))
   print('{}: exit'.format(msg), file=sys.stderr)
   sys.exit(1)

# get current time, or parse the one provided by the command line
# resulting time is in UTC
if (run_time == ""):
       # get current time
       now = datetime.now()
       utc = pytz.timezone("UTC")
       utc_datetime = now.astimezone(utc)
       utc_datetime = utc_datetime.replace(tzinfo=None) # remove the timezone info for consistency
       if (model_mode == ""):
             model_mode = 'nowcast'
else:
       utc_datetime = datetime.strptime(run_time, '%Y%m%d_%H%M')
       if (model_mode == ""):
             model_mode = 'historical'

utc_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
utc_time_json = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
print("Run time:", utc_time, file=sys.stderr)
print("Model mode:", model_mode, file=sys.stderr)
######################################################################################################


# start date for CME search: last 7 days
enddate = utc_datetime.strftime("%Y-%m-%d")
startdate = (utc_datetime - timedelta(days=7) ).strftime("%Y-%m-%d")


#------ get the list for target date -----
url_cme = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis?startDate="+startdate+"&endDate="+enddate+"&mostAccurateOnly=true&speed=450&halfAngle=15"
print('DONKI URL:', url_cme, file=sys.stderr)

# constants to avoid infinite loops during DONKI requests
MAX_REQUESTS = 100
REQUEST_WAIT_TIME = 1 # seconds

nreqs = 0
while nreqs < MAX_REQUESTS:
   try:
      print('Requesting CMEs [{}/{}]'.format(nreqs+1, MAX_REQUESTS), file=sys.stderr)
      f1 = urllib.request.urlopen(url_cme)
      if f1.getcode() == 200:
         print('Request succeeded', file=sys.stderr)
         break

   except Exception as inst:
      print(inst, file=sys.stderr)
      print('Request failed, trying again', file=sys.stderr)
      time.sleep(REQUEST_WAIT_TIME)
      nreqs += 1
if nreqs == MAX_REQUESTS:
   exit_after_error(utc_time, 'Failed to download data', 'ERROR:DOWNLOAD_FAILED')

# ensure DONKI response is not empty, otherwise stop here
buf = f1.read()
if len(buf) == 0:
   exit_after_error(utc_time, 'Empty response from DONKI', 'ERROR:EMPTY_RESPONSE')

data = json.loads(buf)

print('Retrieved {} CMEs'.format(len(data)), file=sys.stderr)

CME_index=[]

#### check CMEs in the last 48 hours, every 15 mins

dt_start = utc_datetime - timedelta(minutes=2879)
print('Looking for CMEs between {} and {}'.format(dt_start, utc_datetime), file=sys.stderr)

# load list of CMEs already simulated
with open(root_dir+'/CME/past.json') as cme_list:
    list_obj = json.load(cme_list)

for i in range(0, len(data)):
   try:
      # expected ID format: yyyy-mm-ddTHH:MM:SS-CME-xxx
      CME_id = data[i].get('associatedCMEID')
      CME_start_time = CME_id.split("-CME-")[0]

      # expected URL format for CME analyses:
      #    https://kauai.ccmc.gsfc.nasa.gov/DONKI/view/CMEAnalysis/xxxxx/-1
      CME_link = data[i].get('link')
      CME_analysis_id = CME_link.split('/')[6]

      datetime_CME = datetime.strptime(CME_start_time, '%Y-%m-%dT%H:%M:%S')
      print('[{:2d}] CME date: {}, analysis: {}'.format(i, datetime_CME, CME_analysis_id), file=sys.stderr)

      if datetime_CME > dt_start and datetime_CME <= utc_datetime:
         # check whether this CME has been simulated before
         # use either associatedCMEID or (associatedCMEID + link) if link is available in past.json
         result = [x for x in list_obj if x.get('associatedCMEID') == CME_id and (x.get('link') is None or x.get('link') == CME_link) ]

         if result == []:
            # no run found for this CME, new CME detected:
            CME_index.append(i)
            print('     New CME found:', CME_id, CME_link, file=sys.stderr)
         else:
            print('     Previous simulation run found:', result, file=sys.stderr)

   except Exception as e:
      traceback.print_exception(e, file=sys.stderr)
      print('[{:2d}] JSON data:'.format(i), file=sys.stderr)
      json.dump(data[i], sys.stderr, indent=3)
      print(file=sys.stderr)

print('New CMEs found in the last 48 hours:', len(CME_index), file=sys.stderr)
ii = len(CME_index)-1 # index number for the latest CME

f4 = open(root_dir+'/CME/log.txt', 'a')

#### check if there is a background solar wind setup in the most recent 8-hour window
# now assuming there can be only at most 1 CME in the 15 mins time window
print('Last CME_index:', ii, file=sys.stderr)

if len(CME_index) != 0:
    try:
       CME_id        = data[CME_index[ii]].get('associatedCMEID')
       CME_link      = data[CME_index[ii]].get('link')
       CME_speed     = data[CME_index[ii]].get('speed')
       CME_halfAngle = data[CME_index[ii]].get('halfAngle')
       CME_latitude  = data[CME_index[ii]].get('latitude')
       CME_longitude = data[CME_index[ii]].get('longitude')
       CME_time21_5  = data[CME_index[ii]].get('time21_5')

       CME_start_time = CME_id.split("-CME-")[0]
       datetime_CME = datetime.strptime(CME_start_time, '%Y-%m-%dT%H:%M:%S')

       # expected URL format for CME analyses:
       #    https://kauai.ccmc.gsfc.nasa.gov/DONKI/view/CMEAnalysis/xxxxx/-1
       CME_analysis_id = CME_link.split('/')[6]

       target_date = datetime_CME.strftime('%Y-%m-%d')
       t1 = datetime.strptime(target_date, '%Y-%m-%d')     # 00:00
       t2 = t1 + timedelta(hours=8)                        # 08:00
       t3 = t2 + timedelta(hours=8)                        # 16:00

       phi_e = 100.0 - CME_longitude

    except Exception as e:
       traceback.print_exception(e, file=sys.stderr)
       print('[{:2d}] JSON data:'.format(CME_index[ii]), file=sys.stderr)
       json.dump(data[CME_index[ii]], sys.stderr, indent=3)
       print(file=sys.stderr)
       f4.close()
       exit_after_error(utc_time, 'Wrong format in DONKI data', 'ERROR:DONKI_WRONG_DATA_FORMAT')

    f4.write('Checking Time:{} | CME found:{}_{} speed:{} width:{} lat:{} lon:{} time_21.5:{}\n'.format(
      utc_time, CME_id, CME_analysis_id, CME_speed,
      CME_halfAngle*2, CME_latitude, CME_longitude, CME_time21_5))

    # assuming the background solar wind setup can finish in 15 mins
    if datetime_CME < t2:
        bgsw_folder_name =t1.strftime('%Y%m%d_%H%M')
    elif datetime_CME < t3:
        bgsw_folder_name =t2.strftime('%Y%m%d_%H%M')
    else:
        bgsw_folder_name =t3.strftime('%Y%m%d_%H%M')
    bkg_root_dir = root_dir + '/Background/' + bgsw_folder_name[0:4] + '/'

    # handle missing background folder here, so errors from accesing input.json are avoided
    # note that we exit the script here, just to avoid putting the rest of the code after an else block
    # printing MISSING_BKG will force CME.sh to check for files in the background folder, so
    # when it fails it will correctly identify a missing background simulation error
    if not os.path.exists(bkg_root_dir + bgsw_folder_name):
       print('MISSING_BKG:' + bgsw_folder_name, file=sys.stderr)
       print('Trying previous background simulation folder', file=sys.stderr)

       # try to use the previous background simulation
       current_bkg_dir = bgsw_folder_name
       prev_bkg_dt = datetime.strptime(bgsw_folder_name, '%Y%m%d_%H%M') - timedelta(hours=8)
       bgsw_folder_name = prev_bkg_dt.strftime('%Y%m%d_%H%M')
       bkg_root_dir = root_dir + '/Background/' + bgsw_folder_name[0:4] + '/'
       if not os.path.exists(bkg_root_dir + bgsw_folder_name):
            print('MISSING_BKG:' + current_bkg_dir + ',' + bgsw_folder_name)
            f4.close()
            exit_after_error(utc_time, 'Missing background folder', 'ERROR:MISSING_BKG')

    list_obj.append({
      "associatedCMEID": CME_id,
      "link": CME_link
    })
    with open(root_dir+'/CME/past.json', 'w') as write_file:
       json.dump(list_obj, write_file, indent=4)

    #### modify input.json for the CME run
    with open(bkg_root_dir+bgsw_folder_name+'/input.json', 'r') as f2:
       input_data = json.load(f2)

    input_data['cme_speed'] = CME_speed * np.cos(CME_latitude*pi/180.0)
    input_data['cme_width'] = CME_halfAngle*2
    input_data['phi_e'] = phi_e

    # change density multiplier based on CME speed
    if CME_speed >= 1500:
        n_multi = 4.0
    else:
        n_multi = CME_speed*2e-3 + 1.
    input_data['n_multi'] = n_multi

    with open(bkg_root_dir+bgsw_folder_name+'/'+run_time+'_CME_earth_input.json', 'w') as f3:
       json.dump(input_data, f3, indent=4)

    earth_r, earth_lat, earth_lon = find_location('planets/earth', datetime_CME, root_dir)

    # setup input files for all other observers
    for obs, loc in observers.items():
       if obs == 'PSP' and datetime_CME < datetime.strptime('2018-249', "%Y-%j"):
            continue

       rad, lat, lon = find_location(loc, datetime_CME, root_dir)

       input_data['phi_e'] = phi_e + lon - earth_lon
       input_data['r0_e'] = rad

       with open(bkg_root_dir+bgsw_folder_name+'/'+run_time+'_CME_'+obs+'_input.json', 'w') as f3:
          json.dump(input_data, f3, indent=4)

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
               "event_lengths":[ { "start_time": "",  "end_time": "", "threshold_start": "", "threshold_units": ""  }],
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
               "event_lengths": [{ "start_time": "",  "end_time": "", "threshold_start": "", "threshold_units": ""  }],
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

    cme_start_time_fixed = CME_start_time+"Z"
    cme = {
           "cme":{
           "start_time":cme_start_time_fixed,
           "half_width": CME_halfAngle,
           "speed": CME_speed,
           "lat": CME_latitude,
           "lon": CME_longitude,
           "height": 21.5,
           "time_at_height": { "time": CME_time21_5, "height": 21.5 },
           "coordinates": "HEEQ",
           "catalog": "DONKI",
           "catalog_id": CME_id,
           "urls": [ CME_link ]
           }
    }

    json_data["sep_forecast_submission"]["triggers"].append(cme)

    with open(bkg_root_dir+bgsw_folder_name+'/'+run_time+'_CME_earth_output.json', 'w') as write_file:
        json.dump(json_data, write_file, indent=4)
    CME_id = CME_id.replace('-', '', 2).replace(':', '', 2) + '_' + CME_analysis_id
else:
    bgsw_folder_name=''
    CME_id = ''
    if len(data) > 0:
        f4.write('Checking Time:{} | No new CME found, last CME in 7 days: {}_{}\n'.format(
            utc_time, data[len(data)-1].get('associatedCMEID'), data[-1].get('link').split('/')[6]))
    else:
        f4.write('Checking Time:{} | No new CME found, no CME in past 7 days.\n'.format(utc_time))
f4.close()
print(bgsw_folder_name, CME_id)
