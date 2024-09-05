#=================================================================================
# Python script to get real time Solar wind parameters from API

import numpy as np
import urllib.request
import datetime
from datetime import timedelta
from datetime import datetime
import time
import pytz
import json
import sys
import argparse

# command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--root_dir", type=str, default='/data/iPATH/nowcast_module', \
       help=("Root directory"))
parser.add_argument("--run_time", type=str, default='', \
       help=("timestamp for the run, in %Y%m%d_%H%M"))
args = parser.parse_args()


root_dir = args.root_dir
run_time = args.run_time

def exit_after_error(utc_time, msg, error_type):
   with open(root_dir+'/Background/log.txt', 'a') as log_file:
      log_file.write('{} {}\n'.format(utc_time, error_type))
   print('{}: exit'.format(msg), file=sys.stderr)
   sys.exit(1)

######################################################################################################
# derive run folder name, based on the current or provided run time
# the run folder name is in the format yyyymmdd_HH00, where HH can be 00, 08, or 16
# this is because each background solar wind simulation has a validity of 8 hours

# get current time, or parse the one provided by command-line
# resulting time is in UTC
if (run_time == ""):
       # get current time
       now = datetime.now()
       utc = pytz.timezone("UTC")
       utc_datetime = now.astimezone(utc)
       utc_datetime = utc_datetime.replace(tzinfo=None) # remove the timezone info for consistency
else:
       utc_datetime = datetime.strptime(run_time, '%Y%m%d_%H%M')


utc_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
print("Run time:", utc_time, file=sys.stderr)

### define folder name
date_str= utc_datetime.strftime("%Y%m%d")
date = datetime.strptime(date_str, '%Y%m%d')
seconds = (utc_datetime - date).total_seconds()
if (seconds < 8*3600):
       run_name = date_str+'_0000'
elif (seconds < 16*3600):
       run_name = date_str+'_0800'
else:
       run_name = date_str+'_1600'

print("Background folder name:", run_name, file=sys.stderr)

# end time is now the fixed times (0000, 0800, or 1600)
utc_datetime = datetime.strptime(run_name, '%Y%m%d_%H%M')
utc_time = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
######################################################################################################



#### Find the API urls
# the output files contains magnetic field and plasma data during the last 24 hours
# See https://ccmc.gsfc.nasa.gov/tools/iSWA/ for source
# need to add 1 minute to utc_datetime because time.max is exclusive
utc_start_datetime = utc_datetime - timedelta(days=1)
encoded_starttime = utc_start_datetime.strftime("%Y-%m-%dT%H:%M:%S.0Z")
encoded_endtime = (utc_datetime + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S.0Z")

swpc_start_time = datetime.strptime('2016-07-24_00:00', '%Y-%m-%d_%H:%M')
# NOAA/SWPC real-time solar wind data data only available after this time
if utc_datetime > swpc_start_time:
       url_mag = "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/hapi/data?id=swpc_rtsw_mag_p1m&time.min="+encoded_starttime+"&time.max="+encoded_endtime+"&include=header&format=json&parameters=B_t,B_x,B_y,B_z"
       url_pla = "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/hapi/data?id=swpc_rtsw_plasma_p1m&time.min="+encoded_starttime+"&time.max="+encoded_endtime+"&include=header&format=json&parameters=BulkSpeed,ProtonDensity,IonTemperature"
else:
       url_mag = "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/hapi/data?id=ace_mag_p1m&time.min="+encoded_starttime+"&time.max="+encoded_endtime+"&include=header&format=json&parameters=B_t,B_x,B_y,B_z"
       url_pla = "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/hapi/data?id=ace_swepam_p1m&time.min="+encoded_starttime+"&time.max="+encoded_endtime+"&include=header&format=json&parameters=BulkSpeed,ProtonDensity,IonTemperature"

url_seed = "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/hapi/data?id=ace_epam_p5m&time.min="+encoded_starttime+"&time.max="+encoded_endtime+"&include=header&format=json&parameters=ProtonFlux_47_68"

print('iSWA URLs:', file=sys.stderr)
print(url_mag, file=sys.stderr)
print(url_pla, file=sys.stderr)
print(url_seed, file=sys.stderr)
##### Read data from the URL

time1 = [] # time stamp for mag
time2 = [] # time stamp for plasma
time3 = [] # time stamp for seed

B_data = []   # nT
n_data = []   # p/cc
usw_data = [] # km/s
T_data = []   # K
flux_data = [] #


# constants to avoid infinite loops during iSWA requests
MAX_REQUESTS = 100
REQUEST_WAIT_TIME = 1 # seconds

nreqs = 0
while nreqs < MAX_REQUESTS:
       try:
              print('Requesting magnetic field data [{}/{}]'.format(nreqs+1, MAX_REQUESTS), file=sys.stderr)
              f1 = urllib.request.urlopen(url_mag)
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

nreqs = 0
while nreqs < MAX_REQUESTS:
       try:
              print('Requesting solar wind plasma data [{}/{}]'.format(nreqs+1, MAX_REQUESTS), file=sys.stderr)
              f2 = urllib.request.urlopen(url_pla)
              if f2.getcode() == 200:
                     print('Request succeeded', file=sys.stderr)
                     break

       except Exception as inst:
              print(inst, file=sys.stderr)
              print('Request failed, trying again', file=sys.stderr)
              time.sleep(REQUEST_WAIT_TIME)
              nreqs += 1
if nreqs == MAX_REQUESTS:
   exit_after_error(utc_time, 'Failed to download data', 'ERROR:DOWNLOAD_FAILED')

nreqs = 0
while nreqs < MAX_REQUESTS:
       try:
              print('Requesting seed population data [{}/{}]'.format(nreqs+1, MAX_REQUESTS), file=sys.stderr)
              f4 = urllib.request.urlopen(url_seed)
              if f4.getcode() == 200:
                     print('Request succeeded', file=sys.stderr)
                     break

       except Exception as inst:
              print(inst, file=sys.stderr)
              print('Request failed, trying again', file=sys.stderr)
              time.sleep(REQUEST_WAIT_TIME)
              nreqs += 1
if nreqs == MAX_REQUESTS:
   exit_after_error(utc_time, 'Failed to download data', 'ERROR:DOWNLOAD_FAILED')

bx_data = []
by_data = []
bz_data = []

# read magnetic field data
for t, bx, by, bz, bt in json.load(f1).get('data', []):
   time1.append(t)
   bx_data.append(bx)
   by_data.append(by)
   bz_data.append(bz)
   B_data.append(bt)

if len(time1) != 0:
   print('Magnetic field: {} data points, from {} to {}'.format(len(time1), time1[0], time1[-1]), file=sys.stderr)
else:
   print('Warning: No magnetic field data!', file=sys.stderr)


# read solar wind plasma data
for t, n, V, T in json.load(f2).get('data', []):
   time2.append(t)
   n_data.append(n)
   usw_data.append(V)
   T_data.append(T)

if len(time2) != 0:
   print('Solar wind plasma: {} data points, from {} to {}'.format(len(time2), time2[0], time2[-1]), file=sys.stderr)
else:
   print('Warning: No solar wind plasma data!', file=sys.stderr)


# read data for proton flux in the range of 47-68 KeV
# data source: ACE
for t, F in json.load(f4).get('data', []):
   time3.append(t)
   flux_data.append(F)

if len(time3) != 0:
   print('Seed population: {} data points, from {} to {}'.format(len(time3), time3[0], time3[-1]), file=sys.stderr)
else:
   print('Warning: No seed population data!', file=sys.stderr)


f1.close()
f2.close()
f4.close()


#### average the observation values during the 8 hours prior to the current time
# it actually uses the last time point from each data stream, not run_time
# this means that if the data stream ends well before run_time, then the average does not refer to the 8 hours preceding the current time
# for proton flux data, there is a check that there must be data points in the last 8 hours, while no such check is performed for magnetic field and solar wind plasma data

B_mean = 0.0
B_sqr_mean = 0.0
count = 0
end_time1 = datetime.strptime(time1[len(time1)-1], "%Y-%m-%dT%H:%M:%SZ")

for i in range(0, len(time1)):
       tobj = datetime.strptime(time1[i], "%Y-%m-%dT%H:%M:%SZ")
       diff = end_time1-tobj
       if diff.seconds/3600 < 8 and B_data[i] > 0:
              B_mean += B_data[i]
              B_sqr_mean += B_data[i]**2.0
              count += 1

if count > 0:
   B_mean = B_mean/count
   B_sqr_mean = B_sqr_mean / count
else:
   print('Warning! Magnetic field data missing!', file=sys.stderr)
   print('Magnetic field intensity set to default!', file=sys.stderr)
   B_mean = 5.0

print('Magnetic field: {} good points, <B> = {}, sqrt(<B^2>) = {}'.format(count, B_mean, np.sqrt(B_sqr_mean)), file=sys.stderr)

### Calculate turbulence power ################################

window_count = 1
B_mean_n = []
bx_mean_n = []
by_mean_n = []
bz_mean_n = []

for j in range(0, window_count):
       B_mean_temp = 0.0
       bx_mean_temp = 0.0
       by_mean_temp = 0.0
       bz_mean_temp = 0.0
       count = 0
       for i in range(0, len(time1)):
              tobj = datetime.strptime(time1[i], "%Y-%m-%dT%H:%M:%SZ")
              diff = end_time1-tobj

              if diff.seconds/3600 < (j+1)*8/window_count and diff.seconds/3600 >= j*8/window_count and B_data[i] > 0:
                     B_mean_temp += B_data[i]
                     bx_mean_temp += bx_data[i]
                     by_mean_temp += by_data[i]
                     bz_mean_temp += bz_data[i]
                     count += 1

       if count != 0:   # normal case
              B_mean_temp = B_mean_temp / count
              bx_mean_temp = bx_mean_temp / count
              by_mean_temp = by_mean_temp / count
              bz_mean_temp = bz_mean_temp / count


              B_mean_n.append(B_mean_temp)
              bx_mean_n.append(bx_mean_temp)
              by_mean_n.append(by_mean_temp)
              bz_mean_n.append(bz_mean_temp)
       else:  # all data are bad data in this period:
              B_mean_n.append(-999)
              bx_mean_n.append(-999)
              by_mean_n.append(-999)
              bz_mean_n.append(-999)


print('Turbulence: {} windows, <B> = {}, <Bx> = {}, <By> = {}, <Bz> = {}'.format(
   len(B_mean_n), np.mean(B_mean_n), np.mean(bx_mean_n), np.mean(by_mean_n), np.mean(bz_mean_n)),
   file=sys.stderr)

db_sqr = 0.0
db_sqr_count =0
turb_power = 0

for i in range(0, len(time1)):
       tobj = datetime.strptime(time1[i], "%Y-%m-%dT%H:%M:%SZ")
       diff = end_time1-tobj
       if diff.seconds/3600 < 8 and B_data[i] > 0:
              n_count = 0
              if B_mean_n[n_count] != -999:
                     db_sqr = db_sqr + (bx_data[i] - bx_mean_n[n_count])**2. + \
                            (by_data[i] - by_mean_n[n_count])**2.+(bz_data[i] - bz_mean_n[n_count])**2.
                     db_sqr_count += 1

if db_sqr_count > 0:
   db_sqr = db_sqr/db_sqr_count
   turb_power = db_sqr/B_sqr_mean

print('Turbulence: {} good points, <deltaB^2> = {}, power = {}'.format(db_sqr_count, db_sqr, turb_power), file=sys.stderr)

if turb_power < 0.1:
       turb_power = 0.1
       print('Warning: turbulence power too small, setting it to 0.1', file=sys.stderr)




n_mean = 0.0
v_mean = 0.0
T_mean = 0.0

count = 0
end_time2 = datetime.strptime(time2[len(time2)-1], "%Y-%m-%dT%H:%M:%SZ")

for i in range(0, len(time2)):
       tobj = datetime.strptime(time2[i], "%Y-%m-%dT%H:%M:%SZ")
       diff = end_time2-tobj
       if diff.seconds/3600 < 8:
              if n_data[i] >= 0.2 and usw_data[i]> 0 and T_data[i]>0:
              # get rid of bad points
                     n_mean += n_data[i]
                     v_mean += usw_data[i]
                     T_mean += T_data[i]
                     count += 1

if count > 0:
   n_mean = n_mean/count
   v_mean = v_mean/count
   T_mean = T_mean/count
else:
   n_mean = 5
   v_mean = 400
   T_mean = 0.07e6
   print('Warning! Solar wind plasma data missing!', file=sys.stderr)
   print('Solar wind density, speed, and temperature set to default!', file=sys.stderr)

print('Solar wind plasma: {} good points, <n> = {}, <v> = {}, <T> = {}'.format(
   count, n_mean, v_mean, T_mean), file=sys.stderr)

# avoid cases with n_mean too small
if n_mean < 1.0:
       n_mean = 1.0
       print('Warning: solar wind density too small, setting it to 1.0', file=sys.stderr)


if len(time3) != 0:
       flux_mean = 0.0
       count = 0
       end_time3 = datetime.strptime(time3[len(time3)-1], "%Y-%m-%dT%H:%M:%SZ")
       diff = utc_datetime - end_time3
       if diff.seconds/3600 > 8:
              print('Warning! ACE proton flux data missing!', file=sys.stderr)
              print('Injection efficiency set to default!', file=sys.stderr)
              flux_mean = 3000.
              inj_rate = 0.004
       else:
              for i in range(0, len(time3)):
                     tobj = datetime.strptime(time3[i], "%Y-%m-%dT%H:%M:%SZ")
                     diff = end_time3-tobj
                     if diff.seconds/3600 < 8:
                            if flux_data[i] < 2e5:
                                   flux_mean += flux_data[i]
                                   count += 1
              if count > 0:
                  flux_mean = flux_mean/count

              # Calculate injection rate based on the flux:
              inj_rate = 0.002 * (flux_mean/n_mean*5.6/1554.8)**0.8
              # 0.002 corresponding to the flux of 1554.8 and density of 5.6 is based on the May 17, 2012 event.
else:
       print('Warning! ACE proton flux data missing!', file=sys.stderr)
       print('Injection efficiency set to default!', file=sys.stderr)
       flux_mean = 3000.
       inj_rate = 0.004

print('Seed population: {} good points, <flux> = {}, injection rate = {}'.format(count, flux_mean, inj_rate), file=sys.stderr)

# avoid cases with inj_rate out of range
if inj_rate > 0.01:
       print('Warning: injection rate too high, setting it to 0.01', file=sys.stderr)
       inj_rate = 0.01

if inj_rate < 0.0004:
       print('Warning: injection rate too low, setting it to 0.0004', file=sys.stderr)
       inj_rate = 0.0004

#### Create Input files for the iPATH
f3 = open(root_dir+'/Background/log.txt', 'a')
f3.write('{}  {:5.2f}  {:5.2f}  {:6.1f}  {:9.1f}  {:5.2f}  {:6.4f}  {:5.2f}\n'.format(utc_time, B_mean, n_mean, v_mean, T_mean, flux_mean, inj_rate, turb_power))
f3.close()

print('Time:{}  B:{:5.2f}  n:{:5.2f}  v:{:6.1f}  T:{:9.1f}  flux:{:5.2f}  inj_rate:{:6.4f}  turb:{:5.2f}'.format(
   utc_time, B_mean, n_mean, v_mean, T_mean, flux_mean, inj_rate, turb_power), file=sys.stderr)

data ={
# Solar Wind parameters
    'nbl': 500,
    'x1min': 0.05,
    'x1max': 2.0,
    'idtag': 'JH',
    'tlim': 0.6,
    'FCOMP': 'gfortran',
    'gln': n_mean,
    'TinMK': 0.07,
    'glv': v_mean,
    'glb': B_mean,
    'Omega': 2.87e-6,
# CME parameters
       'i_heavy': 2,
       'seed_spec': 3.5,
       'inj_rate': inj_rate,
       'run_time': 80.0,
       'cme_speed': 2500.0,
       'cme_width': 120.0,
       'duration': 1.0,
       'n_multi': 4.0,
# Transport Setup
       'p_num': 25,
       't_num': 50,
       'seed_num': 13,
       'if_arrival': 0,
       'r0_e': 1.0,
       'phi_e': 80.0,
       'cturb_au': turb_power,
       'MPI_compiler': 'mpif90'
}

with open(root_dir+'/'+run_name+'_input.json', 'w') as write_file:
    json.dump(data, write_file, indent=4)

# last line with background folder name, to be read directlyt by background.sh
print(run_name)
