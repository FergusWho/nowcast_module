#=================================================================================
# Python script to grep real time Solar wind parameters from API
import math
import numpy as np
import matplotlib.pyplot as plt

import urllib.parse
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
parser.add_argument("--root_dir", type=str, default='/home/junxiang/nowcast_module', \
       help=("Root directory"))
parser.add_argument("--run_time", type=str, default='', \
       help=("timestamp for the run, in %Y-%m-%d_%H:%M"))
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
print ("test timestamp:", utc_time)

### define folder name
# separate date and %H:%M:%S
date_str= utc_datetime.strftime("%Y-%m-%d")
time_str= utc_datetime.strftime("%H:%M:%S")

print("time is", time_str)
date = datetime.strptime(date_str, '%Y-%m-%d')

seconds = (utc_datetime - date).total_seconds()

if (seconds < 8*3600):
       run_name = date_str+'_00:00'
elif (seconds < 16*3600):
       run_name = date_str+'_08:00'
else:
       run_name = date_str+'_16:00' 

print ("folder name:", run_name)

f0 = open(root_dir+'/temp.txt','w')
f0.write(run_name)
f0.close()

######################################################################################################



#### Find the API urls 
# the output files contains magnetic field and plasma data during the last 24 hours
# See https://ccmc.gsfc.nasa.gov/support/iswa/iswa-webservices.php for source
#encoded_endtime = urllib.parse.urlencode({'end-time':utc_time})
endtime = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
encoded_endtime = date_str+'%20'+time_str

# starttime = (utc_datetime - timedelta(days=5) ).strftime("%Y-%m-%d %H:%M:%S")
# print (endtime)
# print (starttime)

url_mag =  "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/DatabaseDataStreamServlet?format=TEXT&resource=DSCOVR&quantity=B_t&duration=1&end-time="+encoded_endtime
url_pla =  "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/DatabaseDataStreamServlet?format=TEXT&resource=DSCOVR,DSCOVR,DSCOVR&quantity=BulkSpeed,ProtonDensity,IonTemperature&duration=1&end-time="+encoded_endtime
url_seed = "https://iswa.gsfc.nasa.gov/IswaSystemWebApp/DatabaseDataStreamServlet?format=TEXT&resource=ACE&quantity=ProtonFlux_115_195&duration=1&end-time="+encoded_endtime

url_cme = "https://kauai.ccmc.gsfc.nasa.gov/DONKI/WS/get/CMEAnalysis.txt?mostAccurateOnly=true&speed=500&halfAngle=35"
# most accurate only, speed lower limit: 500km/s, half width lower limit 35 degrees.

print(url_mag)
print(url_pla)
print(url_seed)
print(url_cme)
##### Read data from the URL

line_no1 = 0
line_no2 = 0

time1 = [] # time stamp for mag
time2 = [] # time stamp for plasma

B_data = []   # nT
n_data = []   # p/cc
usw_data = [] # km/s
T_data = []   # K





f1 = urllib.request.urlopen(url_mag)
f2 = urllib.request.urlopen(url_pla)

# if fail to open then set to default
      #add this later 


       
for line in f1:
       line = line.decode("utf-8")
       line = line.strip()
       
       if line_no1 >0 and line != '':
              columns = line.split()
              time1.append(str(columns[0]) + ' '+ str(columns[1]))
              B_data.append(float(columns[2])) 
       line_no1 +=1

# print(time1[0], B_data[0])
# print(len(time1), line_no1)
# print(time1[len(time1)-1], B_data[len(time1)-1])


for line in f2:
       line = line.decode("utf-8")
       line = line.strip()
       
       if line_no2 >0 and line != '':
              columns = line.split()

              time2.append(str(columns[0]) + ' '+ str(columns[1]))
              usw_data.append(float(columns[2]))
              n_data.append(float(columns[3])) 
              T_data.append(float(columns[4]))
       line_no2 +=1

#print(time2[0], usw_data[0], n_data[0], T_data[0])



f1.close()
f2.close()

#### Find if there is any CME during the last 8 hours
# To be added

#### average the observation values during the 8 hours prior to the current time

B_mean = 0.0
count = 0
end_time1 = datetime.strptime(time1[len(time1)-1], "%Y-%m-%d %H:%M:%S.%f")
#print (end_time1)

for i in range(0, len(time1)):
       tobj = datetime.strptime(time1[i], "%Y-%m-%d %H:%M:%S.%f")
       diff = end_time1-tobj
       if diff.seconds/3600 < 8:
              B_mean += B_data[i]
              count += 1

B_mean = B_mean/count

#print (B_mean, count)


n_mean = 0.0
v_mean = 0.0
T_mean = 0.0

count = 0
end_time2 = datetime.strptime(time2[len(time2)-1], "%Y-%m-%d %H:%M:%S.%f")
#print (end_time2)

for i in range(0, len(time2)):
       tobj = datetime.strptime(time2[i], "%Y-%m-%d %H:%M:%S.%f")
       diff = end_time2-tobj
       if diff.seconds/3600 < 8:
              n_mean += n_data[i]
              v_mean += usw_data[i]
              T_mean += T_data[i]
              count += 1

n_mean = n_mean/count
v_mean = v_mean/count
T_mean = T_mean/count


#print (n_mean, v_mean, T_mean, count)



#### Create Input files for the iPATH

f3 = open(root_dir+'/cronlog.txt', 'a')
f3.write('{}  {:5.2f}  {:5.2f}  {:6.1f}  {:9.1f}\n'.format(utc_time, B_mean, n_mean, v_mean, T_mean))
f3.close()

data ={
# Solar Wind parameters
    'nbl': 500,                                  
    'x1min': 0.05,
    'x1max': 2.0,
    'idtag': 'JH',
    'tlim': 0.5,
    'FCOMP': 'gfortran',
    'gln': n_mean,
    'TinMK': 0.07,
    'glv': v_mean,
    'glb': B_mean,
    'Omega': 2.87e-6,
# CME parameters
       'i_heavy': 2,
       'seed_spec': 3.5,
       'inj_rate': 0.004,
       'run_time': 80.0,
       'cme_speed': 2500.0,
       'cme_width': 120.0,
       'duration': 1.0,
       'n_multi': 4.0,
# Transport Setup
       'p_num': 25,
       't_num': 50,
       'seed_num': 50,
       'if_arrival': 0,
       'r0_e': 1.0,
       'phi_e': 80.0,
       'cturb_au': 0.5,
       'MPI_compiler': 'mpif90'
}

with open(root_dir+'/'+run_name+'_input.json', 'w') as write_file:
    json.dump(data, write_file)