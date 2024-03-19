#=================================================================================
# Python script to grep real time Solar wind parameters from API

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
observers = {}
######################################################################################################

def exit_after_error(utc_time, msg, error_type):
   with open(root_dir+'/Flare/log.txt', 'a') as log_file:
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
             model_mode = 'forecast'
else:
       utc_datetime = datetime.strptime(run_time, '%Y%m%d_%H%M')
       if (model_mode == ""):
             model_mode = 'historical'

utc_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
utc_time_json = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
print("Run time:", utc_time, file=sys.stderr)
print("Model mode:", model_mode, file=sys.stderr)
######################################################################################################


# start date for flare search: last 7 days
enddate = utc_datetime.strftime("%Y-%m-%d")
startdate = (utc_datetime - timedelta(days=7) ).strftime("%Y-%m-%d")


#------ get the list for target date -----
url_flare = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR?startDate="+startdate+"&endDate="+enddate
print('DONKI URL:', url_flare, file=sys.stderr)

# constants to avoid infinite loops during DONKI requests
MAX_REQUESTS = 100
REQUEST_WAIT_TIME = 1 # seconds

nreqs = 0
while nreqs < MAX_REQUESTS:
   try:
      print('Requesting flares [{}/{}]'.format(nreqs+1, MAX_REQUESTS), file=sys.stderr)
      f1 = urllib.request.urlopen(url_flare)
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

print('Retrieved {} flares'.format(len(data)), file=sys.stderr)

flare_index=[]

#### check flares in the last 48 hours, every 15 mins

dt_start = utc_datetime - timedelta(minutes=2879)
print('Looking for flares between {} and {}'.format(dt_start, utc_datetime), file=sys.stderr)

# load list of flares already simulated
with open(root_dir+'/Flare/past.json') as flare_list:
    list_obj = json.load(flare_list)

MAX_REQUESTS = 10
for i in range(0, len(data)):
   try:
      # expected ID format: yyyy-mm-ddTHH:MM:SS-CME-xxx
      flare_id = data[i].get('flrID')
      flare_start_time = flare_id.split("-FLR-")[0]

      flare_link       = data[i].get('link')
      flare_class      = data[i].get('classType', '')
      flare_location   = data[i].get('sourceLocation', '')
      flare_begin_time = data[i].get('beginTime', '')
      flare_peak_time  = data[i].get('peakTime', '')

      datetime_flare = datetime.strptime(flare_start_time, '%Y-%m-%dT%H:%M:%S')
      print('[{:2d}] Flare date: {}, link: {}'.format(i, datetime_flare, flare_link), file=sys.stderr)

      # skip automatic DONKI >=M5 alerts, since they don't have an actual peak time and class yet
      if flare_peak_time == flare_begin_time and flare_class == 'M5':
         print('     Found DONKI automatic alert: skipping', file=sys.stderr)
         continue

      if datetime_flare > dt_start and datetime_flare <= utc_datetime:
         # retrieve flare version number from flare URL
         nreqs = 0
         while nreqs < MAX_REQUESTS:
            try:
               response = urllib.request.urlopen(flare_link)
               if response.getcode() == 200:
                  break
            except Exception:
               time.sleep(REQUEST_WAIT_TIME)
               nreqs += 1
         if nreqs == MAX_REQUESTS:
            # skip this flare, will be retried next time
            continue

         flare_version = response.geturl().split('/')[-1]

         # check whether this flare has been simulated before
         # first condition: check flare id (old past.json format)
         # second condition: check link (new past.json format, March 13, 2024)
         # NB: this should at most return 1 item; in case of more items,
         # the most recent flare will be the last item
         result = [x for x in list_obj if (x.get('link') is None and x.get('flrID') == flare_id) or
                                          (x.get('link') is not None and x.get('link') == flare_link)]

         if result == []:
            # no run found for this flare, new flare detected:
            flare_index.append(i)
            data[i]['only_time_changed'] = False
            data[i]['version'] = flare_version
            print('     New flare found:', flare_id, flare_link, flare_version, flare_begin_time, flare_peak_time, flare_class, flare_location, file=sys.stderr)
         elif result[-1].get('version') is None or result[-1].get('version') == flare_version:
            # (old past.json format) or (new past.json format, same flare version)
            print('     Previous simulation run found:', result, file=sys.stderr)
         else:
            # new past.json format, different version
            if result[-1].get('classType') != flare_class or result[-1].get('sourceLocation') != flare_location:
               # class and/or location changed => new simulation
               flare_index.append(i)
               data[i]['only_time_changed'] = False
               data[i]['version'] = flare_version
               print('     Previous flare with different class and/or location found:', flare_class, flare_location, result, file=sys.stderr)
            elif result[-1].get('peakTime') != flare_peak_time or result[-1].get('beginTime') != flare_begin_time:
               # start and/or peak time changed, but class and location still the same => reuse previous version simulation
               flare_index.append(i)
               data[i]['only_time_changed'] = True
               data[i]['version'] = flare_version
               print('     Previous flare with different start and/or peak time found:', flare_begin_time, flare_peak_time, result, file=sys.stderr)
            else:
               # different version, but none of the relevant properties changed => skip it
               print('     Previous flare with different version but same relevant properties found:', result, file=sys.stderr)

   except Exception as e:
      traceback.print_exception(e, file=sys.stderr)
      print('[{:2d}] JSON data:'.format(i), file=sys.stderr)
      json.dump(data[i], sys.stderr, indent=3)
      print(file=sys.stderr)

print('New flares found in the last 48 hours:', len(flare_index), file=sys.stderr)
ii = len(flare_index)-1 # index number for the latest flare

f4 = open(root_dir+'/Flare/log.txt', 'a')

#### check if there is a background solar wind setup in the most recent 8-hour window
# now assuming there can be only at most 1 flare in the 15 mins time window
print('Last flare_index:', ii, file=sys.stderr)

if len(flare_index) != 0:
    try:
       only_time_changed = data[flare_index[ii]].get('only_time_changed')

       flare_id         = data[flare_index[ii]].get('flrID')
       flare_link       = data[flare_index[ii]].get('link')
       flare_version    = data[flare_index[ii]].get('version')
       flare_class      = data[flare_index[ii]].get('classType')
       flare_location   = data[flare_index[ii]].get('sourceLocation')
       flare_begin_time = data[flare_index[ii]].get('beginTime')
       flare_peak_time  = data[flare_index[ii]].get('peakTime')
       flare_end_time   = data[flare_index[ii]].get('endTime')

       flare_start_time = flare_id.split("-FLR-")[0]
       datetime_flare = datetime.strptime(flare_start_time, '%Y-%m-%dT%H:%M:%S')

       target_date = datetime_flare.strftime('%Y-%m-%d')
       t1 = datetime.strptime(target_date, '%Y-%m-%d')     # 00:00
       t2 = t1 + timedelta(hours=8)                        # 08:00
       t3 = t2 + timedelta(hours=8)                        # 16:00

       # derive CME speed from flare class
       class_tokens = list(flare_class)
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

       loc_tokens = list(flare_location)
       angle = int(loc_tokens[4]+loc_tokens[5])
       if loc_tokens[3]=='W':
           phi_e = 100 - angle
       if loc_tokens[3]=='E':
           phi_e = 100 + angle

       print('Flare class = {} -> Vcme = {}, location = {} -> phi_e = {}'.format(
          flare_class, Vcme, flare_location, phi_e), file=sys.stderr)

    except Exception as e:
       traceback.print_exception(e, file=sys.stderr)
       print('[{:2d}] JSON data:'.format(flare_index[ii]), file=sys.stderr)
       json.dump(data[flare_index[ii]], sys.stderr, indent=3)
       print(file=sys.stderr)
       f4.close()
       exit_after_error(utc_time, 'Wrong format in DONKI data', 'ERROR:DONKI_WRONG_DATA_FORMAT')

    f4.write('Checking Time:{} | flare found:{} version:{} class:{} location:{} begin:{} peak:{} end:{}\n'.format(
      utc_time, flare_id, flare_version, flare_class, flare_location,
      flare_begin_time, flare_peak_time, flare_end_time))

    # assuming the background solar wind setup can finish in 15 mins
    if datetime_flare < t2:
        bgsw_folder_name =t1.strftime('%Y%m%d_%H%M')
    elif datetime_flare < t3:
        bgsw_folder_name =t2.strftime('%Y%m%d_%H%M')
    else:
        bgsw_folder_name =t3.strftime('%Y%m%d_%H%M')

    # handle missing background folder here, so errors from accesing input.json are avoided
    # note that we exit the script here, just to avoid putting the rest of the code after an else block
    # printing MISSING_BKG will force flare.sh to check for files in the background folder, so
    # when it fails it will correctly identify a missing background simulation error
    if not os.path.exists(root_dir + '/Background/' + bgsw_folder_name):
       print('MISSING_BKG:' + bgsw_folder_name, file=sys.stderr)
       print('Trying previous background simulation folder', file=sys.stderr)

       # try to use the previous background simulation
       current_bkg_dir = bgsw_folder_name
       prev_bkg_dt = datetime.strptime(bgsw_folder_name, '%Y%m%d_%H%M') - timedelta(hours=8)
       bgsw_folder_name = prev_bkg_dt.strftime('%Y%m%d_%H%M')
       if not os.path.exists(root_dir + '/Background/' + bgsw_folder_name):
            print('MISSING_BKG:' + current_bkg_dir + ',' + bgsw_folder_name)
            f4.close()
            exit_after_error(utc_time, 'Missing background folder', 'ERROR:MISSING_BKG')

    list_obj.append({
      "flrID": flare_id,
      "link": flare_link,
      "version": flare_version,
      "beginTime": flare_begin_time,
      "peakTime": flare_peak_time,
      "classType": flare_class,
      "sourceLocation": flare_location
    })
    with open(root_dir+'/Flare/past.json', 'w') as write_file:
       json.dump(list_obj, write_file, indent=4)

    #### modify input.json for the flare run
    with open(root_dir+'/Background/'+bgsw_folder_name+'/input.json', 'r') as f2:
       input_data = json.load(f2)

    input_data['cme_speed'] = Vcme
    input_data['cme_width'] = int(width)
    input_data['phi_e'] = phi_e

    # change density multiplier based on CME speed
    if Vcme >= 1500:
        n_multi = 4.0
    else:
        n_multi = Vcme*2e-3 + 1.
    input_data['n_multi'] = n_multi

    with open(root_dir+'/Background/'+bgsw_folder_name+'/'+run_time+'_flare_earth_input.json', 'w') as f3:
       json.dump(input_data, f3, indent=4)

    earth_r, earth_lat, earth_lon = find_location('planets/earth', datetime_flare, root_dir)

    # setup input files for all other observers
    for obs, loc in observers.items():
       if obs == 'PSP' and datetime_flare < datetime.strptime('2018-249', "%Y-%j"):
            continue

       rad, lat, lon = find_location(loc, datetime_flare, root_dir)

       input_data['phi_e'] = phi_e + lon - earth_lon
       input_data['r0_e'] = rad

       with open(root_dir+'/Background/'+bgsw_folder_name+'/'+run_time+'_CME_'+obs+'_input.json', 'w') as f3:
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

    if flare_end_time is None:
       flare_end_time = flare_peak_time

    flare = {
           "flare":{
           "last_data_time": flare_end_time,
           "start_time": flare_begin_time,
           "peak_time": flare_peak_time,
           "end_time": flare_end_time,
           "location": flare_location,
           "intensity": FSXR,
           "urls": [ flare_link, flare_link.replace('-1', str(flare_version)) ]
           }
    }
    cme = {
           "cme":{
           "start_time": flare_begin_time,
           "half_width": width/2.,
           "speed": Vcme,
           }
    }

    json_data["sep_forecast_submission"]["triggers"].append(flare)
    json_data["sep_forecast_submission"]["triggers"].append(cme)

    with open(root_dir+'/Background/'+bgsw_folder_name+'/'+run_time+'_flare_earth_output.json', 'w') as write_file:
        json.dump(json_data, write_file, indent=4)
    flare_id = flare_id.replace('-', '', 2).replace(':', '', 2) + '_' + flare_version
else:
    bgsw_folder_name=''
    flare_id = ''
    only_time_changed = ''
    if len(data) > 0:
        f4.write('Checking Time:{} | No new flare found, last flare in 7 days: {}\n'.format(
            utc_time, data[len(data)-1].get('flrID') ))
    else:
        f4.write('Checking Time:{} | No new flare found, no flare in past 7 days.\n'.format(utc_time))
f4.close()
print(bgsw_folder_name, flare_id, only_time_changed)
