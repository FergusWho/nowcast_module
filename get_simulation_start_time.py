import datetime
from datetime import timedelta
from datetime import datetime
import json

root_dir = './'
AU = 1.5e11 # [m]

with open('./trspt_input', 'r') as f1:
   f1.readline()
   f1.readline()
   f1.readline()
   f1.readline()
   f1.readline()
   f1.readline()
   t_num, if_arrival = f1.readline().split()
   f1.readline()
   p_num_trsp, phi_num = f1.readline().split()
t_num = int(t_num)
p_num_trsp = int(p_num_trsp)

raw_time=[]
with open(root_dir + 'fp_total', 'r') as f4:
   for line in f4:
       columns = line.strip().split()
       raw_time.append(float(columns[3]))

xtime = [] # [hours]
for i in range(0, t_num):
   xtime.append(raw_time[i*p_num_trsp])

with open('./output.json', 'r') as read_file:
   json_data = json.load(read_file)

if "flare" in json_data["sep_forecast_submission"]["triggers"][0]:
   flare_start_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["flare"]["start_time"], '%Y-%m-%dT%H:%MZ')
   FSXR=json_data["sep_forecast_submission"]["triggers"][0]["flare"]["intensity"]
   Vcme = 2.4e4*FSXR**0.3 # [km/s]
   time_to_inner = 0.05*AU/(Vcme*1000.)/3600.*2/3.
   simulation_zero_time = flare_start_time + timedelta(hours=time_to_inner)
elif "cme" in json_data["sep_forecast_submission"]["triggers"][0]:
   cme_start_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["start_time"], '%Y-%m-%dT%H:%M:%SZ')
   time21_5 = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["time_at_height"]["time"],'%Y-%m-%dT%H:%MZ')
   simulation_zero_time = cme_start_time + (time21_5 - cme_start_time)/3.
else:
   print('ERROR - No trigger info in output.json')

simulation_end_time = simulation_zero_time + timedelta(hours=xtime[t_num-1])
start_time = simulation_zero_time.strftime('%Y%m%d_%H%M%S')

print(start_time)
