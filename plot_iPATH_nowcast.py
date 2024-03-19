import math
from math import pi
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import csv
import datetime
from datetime import timedelta
from datetime import datetime
import json
import re
import os

import pickle

root_dir = './'

# Open and read trspt_input
f1 = open('./trspt_input', 'r')

f1.readline()
f1.readline()
r_e, phi_e = f1.readline().split()
f1.readline()
f1.readline()
f1.readline()
t_num, if_arrival = f1.readline().split()
f1.readline()
p_num_trsp, phi_num = f1.readline().split()

f1.close()

r_e = float(r_e)
t_num = int(t_num)
if_arrival = int(if_arrival)
p_num_trsp = int(p_num_trsp)
phi_num = int(phi_num)


# Open and read trspt_params
f2 = open('../trspt_params', 'r')
f2.close()


f4 = open(root_dir + 'fp_total', 'r')

#=======================================================================

emin = 1e5    #eV
emax = 1e9

AU = 1.5e11
cme_center =100.
del_phi = 5.


#normalization factors
mp = 1.67e-27
co = 3e8
eo = 1.6e-19
vo = 52483.25
no = 1e6

if p_num_trsp == 25:
       energy_index = [8, 10, 12, 14, 16, 18]
if p_num_trsp == 20:
       energy_index = [6,8,10,12,14,16]
if p_num_trsp == 10:
       energy_index = [3,4,5,6,7,8]
if p_num_trsp == 15:
       energy_index = [4,5,6, 7,8, 9]

time_index = [2,5,8,11,14]



phi_0 = []
for i in range(0, phi_num):
       phi_0.append(int(cme_center +del_phi*(i-math.floor(phi_num/2.))))






xtime = [] # in hours
xdatetime = [] # in datetime

####################################################################################################
energy1 = []
energy1Mev = []
p_0 = []

# now read the fp
p_num_a =[]
raw_time=[]
fp_t1 = []
for line in f4:
       line = line.strip()
       columns = line.split()

       p_num_a.append(columns[0])
       fp_t1.append(float(columns[1])) #*(mp*vo*AU)**(-3.))
       raw_time.append(float(columns[3]))

for i in range(0, t_num):
       xtime.append(raw_time[i*p_num_trsp])


for i in range(0, p_num_trsp):
       e_0 = emin * ((emax/emin)**(1./(p_num_trsp-1)))**i
       energy1.append(e_0)
       energy1Mev.append(e_0/1.e6)
       gamma0 = (e_0*eo + mp*co**2.0)/(mp*co**2.0)
       p_0.append(math.sqrt(((e_0*eo + mp*co**2.0)**2. -(mp*co**2.0)**2.0))/co)


fp_transport1 = []
for time_no in range(0, t_num):  # convert f(p) into J(T) = f(p)*p^2
       fp_temp1 = []
       for i in range(0, p_num_trsp):
              fp_temp1.append(fp_t1[time_no*p_num_trsp+i]* p_0[i]*p_0[i] )
       fp_transport1.append(fp_temp1)


#===== background J(T), empirical
bg_ti_temp  = []
for i in range(0, p_num_trsp):
       vel = p_0[i]/mp*(1./math.sqrt(1.+(p_0[i]/(mp*co))**2.0))
       bg_ti_temp.append(0.0)
       print('Energy = {:.12e}; velocity = {:.12e}'.format(energy1[i], vel))


#=======================================================================
#calculate time intensity profiles  J(T,t)
e_legd =[]
time_intensity1 = []
for i in range(0, p_num_trsp):
       e_legd.append('%(energy).1F %(unit)s' %{"energy":energy1[i]/1e6, "unit":"MeV"})
       ti_temp1 = []
       for itime in range(0, t_num):
              ti_temp1.append(fp_transport1[itime][i]*eo*100.*no*(mp*vo)**(-3.)/(4.* pi) +bg_ti_temp[i]/r_e**2.)
                                                   #{-------- normalization factors-----------------}
       time_intensity1.append(ti_temp1)

#=======================================================================
#calculate integral fluences
int_flux = []
int_e_legd =[]
for i in range(0, p_num_trsp-1):
       int_e_legd.append('>%(energy).1F %(unit)s' %{"energy":energy1[i]/1e6, "unit":"MeV"})
       if_temp1 = []
       for itime in range(0, t_num):
              temp11 =0.0
              for j in range(i, p_num_trsp-1):  # integral on logarithmic scale
                     y1 = fp_transport1[itime][j]*eo*100.*no*(mp*vo)**(-3.)/(4.* pi) + 1e-11
                     y2 = fp_transport1[itime][j+1]*eo*100.*no*(mp*vo)**(-3.)/(4.* pi) + 1e-11
                     x1 = energy1[j]/1e6
                     x2 = energy1[j+1]/1e6

                     if y1 <= 0:
                        y1 = 1e-11
                     if y2 <= 0:
                        y2 = 1e-11

                     m1 = (np.log10(y1) - np.log10(y2) )/( np.log10(x1) - np.log10(x2))
                     n1 = np.log10(y1) - m1* np.log10(x1)

                     if m1 != -1.:
                            int_temp = 10.**n1 /(m1+1)*(x2**(m1+1) - x1**(m1+1))
                     if m1 == -1.:
                            int_temp = 10.**n1 * np.log10(x2/x1)

                     temp11 = temp11 + int_temp

              if temp11 < 1e-4:
                     temp11 = np.nan

              if_temp1.append(temp11)

       int_flux.append(if_temp1)






# #=======================================================================
# # calculate event integrated spectrum

total_fp1=[]
half_fp =[]

total_time = raw_time[len(raw_time)-1] # in hours

print("Time interval in hours:", total_time/t_num)

for i in range(0, p_num_trsp):
       total_fp1.append(0.0)
       half_fp.append(0.0)
       for j in range(0, t_num):
              total_fp1[i] = total_fp1[i]+ (fp_t1[j*p_num_trsp+i]* p_0[i]*p_0[i] *eo*100.*no*(mp*vo)**(-3.))

       total_fp1[i] = total_fp1[i] * total_time *3600./t_num

# accumulative integrated spectrum for different time intervals
ti_fp1 = [] # 0-10 hrs
ti_fp2 = [] # 10-20 hrs
ti_fp3 = [] # 20-30 hrs
ti_fp4 = [] # 30-40 hrs

for i in range(0, p_num_trsp):
       ti_fp1.append(0.0)
       ti_fp2.append(0.0)
       ti_fp3.append(0.0)
       ti_fp4.append(0.0)

       count1 = 0
       count2 = 0
       count3 = 0
       count4 = 0


       for j in range(0, t_num):
              if xtime[j] <= 10. :
                     ti_fp1[i] = ti_fp1[i] + (fp_t1[j*p_num_trsp+i]* p_0[i]*p_0[i] *eo*100.*no*(mp*vo)**(-3.))
                     count1 += 1
              elif xtime[j] <= 20. :
                     ti_fp2[i] = ti_fp2[i] + (fp_t1[j*p_num_trsp+i]* p_0[i]*p_0[i] *eo*100.*no*(mp*vo)**(-3.))
                     count2 += 1
              elif xtime[j] <= 30. :
                     ti_fp3[i] = ti_fp3[i] + (fp_t1[j*p_num_trsp+i]* p_0[i]*p_0[i] *eo*100.*no*(mp*vo)**(-3.))
                     count3 += 1
              elif xtime[j] <= 40. :
                     ti_fp4[i] = ti_fp4[i] + (fp_t1[j*p_num_trsp+i]* p_0[i]*p_0[i] *eo*100.*no*(mp*vo)**(-3.))
                     count4 += 1

       ti_fp1[i] = ti_fp1[i] * total_time *3600./t_num
       ti_fp2[i] = ti_fp2[i] * total_time *3600./t_num
       ti_fp3[i] = ti_fp3[i] * total_time *3600./t_num
       ti_fp4[i] = ti_fp4[i] * total_time *3600./t_num



######################################################################################################
#           modify the output.json file
#              - now optional since we are using OpSEP for output
#                but we still need to calculate start_time for differential flux output file
######################################################################################################

with open('./output.json', 'r') as read_file:
       json_data = json.load(read_file)


if "flare" in json_data["sep_forecast_submission"]["triggers"][0]:
       print('triggered by flare')
       flare_start_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["flare"]["start_time"], '%Y-%m-%dT%H:%MZ')
       flare_peak_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["flare"]["peak_time"], '%Y-%m-%dT%H:%MZ')
       FSXR=json_data["sep_forecast_submission"]["triggers"][0]["flare"]["intensity"]
       Vcme = 2.4e4*FSXR**0.3 # km/s
       time_to_inner = 0.05*AU/(Vcme*1000.)/3600.*2/3.
       simulation_zero_time = flare_start_time + timedelta(hours=time_to_inner)
       run_time = flare_peak_time.strftime('%Y%m%d')
       trigger = flare_start_time.strftime('%Y-%m-%dT%H:%M:%S-FLR-001') # build catalog_id from start_time; so far, all of DONKI flares ends with '-001'
elif "cme" in json_data["sep_forecast_submission"]["triggers"][0]:
       print('triggered by CME')
       cme_start_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["start_time"], '%Y-%m-%dT%H:%M:%SZ')
       time21_5 = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["time_at_height"]["time"],'%Y-%m-%dT%H:%MZ')
       simulation_zero_time = cme_start_time + (time21_5 - cme_start_time)/3.
       run_time = cme_start_time.strftime('%Y%m%d')
       trigger = json_data.get('sep_forecast_submission').get('triggers')[0].get('cme').get('catalog_id') + '/' + \
          json_data.get('sep_forecast_submission').get('triggers')[0].get('cme').get('urls')[0].split('/')[6]
else:
       print('ERROR - No trigger info in output.json')
       print('Extracting simulation start time from directory name:', os.getcwd())
       res = re.search(r'.*/([0-9]+T[0-9]+)-.*', os.getcwd())
       if res is None:
            print('Extraction failed: default to 1970-01-01')
            simulation_zero_time = datetime.strptime('1970-01-01', '%Y-%m-%d')
       else:
            simulation_zero_time = datetime.strptime(res.group(1), '%Y%m%dT%H%M%S')
       run_time = simulation_zero_time.strftime('%Y%m%d')
       if 'CME' in os.getcwd():
         trigger = 'CME'
       elif 'Flare' in os.getcwd():
         trigger = 'Flare'
       else:
         trigger = 'Unknown'

res = re.search(r'.*/transport_(.*)', os.getcwd())
location = res.group(1)
location = location[:1].upper() + location[1:]

print('Simulation start time:', simulation_zero_time)
print('Run time:', run_time)
print('Trigger:', trigger)
print('Location:', location)

#=======================================================================
# save flux to file


f31 = open('./'+run_time+'_differential_flux.csv', 'w')
writer = csv.writer(f31)

writer.writerow(['#time(h)', 'differential flux[protons/(cm^2 s sr MeV)] at the energy [MeV]'])


row = []
row.append('#')
for j in range(0, p_num_trsp):
       row.append('{:<#18.8g}'.format(energy1Mev[j]))

writer.writerow(row)

for i in range(0,t_num):
       row = []
       time_str = (simulation_zero_time + timedelta(hours=xtime[i])).strftime('%Y-%m-%d %H:%M:%S')
       row.append(time_str)
       for j in range(0, p_num_trsp):
              row.append('{:<10.6e}'.format(time_intensity1[j][i]))
       writer.writerow(row)
f31.close()


f41 = open('./'+run_time+'_event_integrated_fluence.txt','w')
f41.write('Energy [MeV],     Fluence [cm^{-2} MeV^{-1}]\n')
for j in range(0, p_num_trsp):
       f41.write('{:<#18.8g}{:<10.6e}\n'.format(energy1Mev[j], total_fp1[j]))
f41.close()

with open('./'+run_time+'_save.pkl', 'wb') as f51:
       pickle.dump([xtime, time_intensity1, energy_index, simulation_zero_time, int_flux, energy1Mev],f51)

#############################################################################################################################
#             PLOTTING
#############################################################################################################################
plt.figure(4, figsize=(20,13))

plot1 = plt.subplot2grid((6, 6), (0, 0), colspan=3, rowspan=3)
plot2 = plt.subplot2grid((6, 6), (3, 0), rowspan=3, colspan=3)
plot3 = plt.subplot2grid((6, 6), (0, 3), rowspan=6, colspan=3)
# Using Numpy to create an array x
x = np.arange(1, 10)

# Plot for square root
plot1.plot(xtime, time_intensity1[energy_index[0]], 'k-o', xtime, time_intensity1[energy_index[1]], 'r-o', \
         xtime, time_intensity1[energy_index[2]], 'g-o', xtime, time_intensity1[energy_index[3]], 'b-o', \
         xtime, time_intensity1[energy_index[4]], 'm-o', xtime, time_intensity1[energy_index[5]], 'c-o',\
         linewidth = 2.5)

plot1.set_title("Time-intensity profile at "+location, fontsize=25)
plot1.set_yscale('log')
plot1.set_ylim([1e-2,1e4])
plot1.set_xlabel('time (hours)', fontsize=22)
plot1.set_ylabel('$J_T(T)$ $[\#/(cm^2 \  s \ sr\  MeV)]$', fontsize=22)
plot1.legend([e_legd[energy_index[0]], e_legd[energy_index[1]], e_legd[energy_index[2]], \
             e_legd[energy_index[3]], e_legd[energy_index[4]], e_legd[energy_index[5]]], \
             loc=2, ncol = 3, borderaxespad=0., shadow = True, fontsize=20)

plot1.tick_params(axis='both', which='major', labelsize=20)

plt.setp(plot1.spines.values(), linewidth=2)

energy_index = [9,12, 14, 16,18]

plot2.plot(\
         # xtime, time_intensity1[energy_index[1]], 'y-', xtime, time_intensity1[energy_index[2]], 'g-', \
         # xtime, time_intensity1[energy_index[3]], 'r-', xtime, time_intensity1[energy_index[4]], 'b-', \
         xtime, int_flux[energy_index[1]], 'ro-', xtime, int_flux[energy_index[2]], 'yo-', \
         xtime, int_flux[energy_index[3]], 'bo-', xtime, int_flux[energy_index[4]], 'go-', \
         linewidth = 2.5)


plot2.set_title('Integral flux', fontsize=25)

plot2.set_yscale('log')
plot2.set_ylim([1e-2, 1e5])
plot2.set_xlabel('time (hours)', fontsize=22)
plot2.set_ylabel('Integral Flux (pfu)', fontsize=22)
plot2.legend([int_e_legd[energy_index[1]],int_e_legd[energy_index[2]],\
             int_e_legd[energy_index[3]],int_e_legd[energy_index[4]], \
             'GOES >10 MeV','GOES >30 MeV','GOES >60 MeV' ],
             loc=2, ncol = 2, borderaxespad=0., shadow = True,fontsize=17)
plot2.tick_params(axis='both', which='major', labelsize=20)
plt.setp(plot2.spines.values(), linewidth=2)

# Plot for Square
plot3.plot(energy1Mev, total_fp1, 'k-o', linewidth=3.0)
plot3.plot(energy1Mev, ti_fp1, 'r-o',energy1Mev, ti_fp2, 'g-o',energy1Mev,ti_fp3, 'b-o',energy1Mev, ti_fp4, 'm-o',linewidth=1.5)
plot3.legend(['event integrated', '0-10 hrs', '10-20 hrs', '20-30 hrs', '30-40 hrs'],fontsize=17)

plot3.set_xlim([1e-1,2e3])
plot3.set_ylim([1e2,1e11])
plot3.set_title('Event-Integrated Spectrum', fontsize=25)
plot3.set_xlabel('Energy[MeV]', fontsize=25)
plot3.set_ylabel('fluence $[protons/(cm^2 MeV)]$', fontsize=22)
plot3.set_xscale('log')
plot3.set_yscale('log')
plot3.tick_params(axis='both', which='major', labelsize=20)

plt.setp(plot3.spines.values(), linewidth=2)

# adding text
plt.suptitle('Trigger: ' + trigger +
   ' $-$ Simulation start time: ' + simulation_zero_time.strftime("%Y-%m-%d %H:%M:%S"),
   y=0.99, fontsize=25)

# Packing all the plots and displaying them
plt.tight_layout()

plt.savefig('./'+run_time+'_plot.png')
