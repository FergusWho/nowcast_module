import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import csv
import datetime
from datetime import timedelta
from datetime import datetime
import json

import pickle

def total_func_numerical(energy0, time_intensity0, time, lower_energy):
       # calculate the > lower_energy fluence integrated over time
       int_fluence = 0.0
       int_flux = []

       for i in range(0, p_num_trsp-1):
              if energy0[i] <= lower_energy: #both in MeV
                     i_start = i+1

       if_temp1 = []
       for itime in range(0, t_num):
              temp11 =0.0
              for j in range(i_start, p_num_trsp-1):  # integral on logarithmic scale
                     y1 = time_intensity0[j][itime] + 1e-11
                     y2 = time_intensity0[j][itime] + 1e-11
                     x1 = energy0[j]
                     x2 = energy0[j+1]
                     m1 = (np.log10(y1) - np.log10(y2) )/( np.log10(x1) - np.log10(x2))
                     n1 = np.log10(y1) - m1* np.log10(x1)

                     if m1 != -1.:
                            int_temp = 10.**n1 /(m1+1)*(x2**(m1+1) - x1**(m1+1))
                     if m1 == -1.:
                            int_temp = 10.**n1 * np.log10(x2/x1)

                     temp11 = temp11 + int_temp

              int_fluence = int_fluence + temp11 * (time[2] - time[1])*3600. *4. *pi

       return int_fluence

root_dir = './'
# Test_case_trspt2.0/
# First_attempt/
plot_title = 'Observer'
anno = '0'

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

#print (r_e, t_num)


# Open and read trspt_params
f2 = open('../trspt_params', 'r')
f2.close()


f4 = open(root_dir + 'fp_total', 'r')

#=======================================================================

p_num = 400

emin = 1e5    #eV
emax = 1e9	

AU = 1.5e11
cme_center =100.
del_phi = 5.
pi = 3.14159265359


#normalization factors
t_o = 2858068.3
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
       

bg_ti_temp  = []
#===== background J(T), empirical

for i in range(0, p_num_trsp):
       coeff = 5e-12  # base on observation
       vel = p_0[i]/mp*(1./math.sqrt(1.+(p_0[i]/(mp*co))**2.0))
       # bg_ti_temp.append(2.* coeff * energy1[i]**2. * (energy1[i]/energy1[0])**(-3.5) \
       #               * (r_e/1.0)**-2.0)
       bg_ti_temp.append(0.0)
       print ('vel:', energy1[i], vel)
'''
for i in range(0, p_num_trsp):
       vel = p_0[i]/mp*(1./math.sqrt(1.+(p_0[i]/(mp*co))**2.0))
       bg_ti_temp.append( 4.0*40000000./energy1[i]*1e6 /4./pi* (energy1[i]/energy1[0])**(-3.5) )
       print 'vel:', energy1[i], vel
'''

       
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
int_flux_linear = []
int_flux_linear2 = []
int_e_legd =[]
for i in range(0, p_num_trsp-1):
       int_e_legd.append('>%(energy).1F %(unit)s' %{"energy":energy1[i]/1e6, "unit":"MeV"})
       if_temp1 = []
       if_temp2 = []
       if_temp3 = []
       for itime in range(0, t_num):
              temp11 =0.0
              temp22 =0.0
              temp33 =0.0
              for j in range(i, p_num_trsp-1):  # integral on logarithmic scale
                     y1 = fp_transport1[itime][j]*eo*100.*no*(mp*vo)**(-3.)/(4.* pi) + 1e-11
                     y2 = fp_transport1[itime][j+1]*eo*100.*no*(mp*vo)**(-3.)/(4.* pi) + 1e-11
                     x1 = energy1[j]/1e6
                     x2 = energy1[j+1]/1e6
                     m1 = (np.log10(y1) - np.log10(y2) )/( np.log10(x1) - np.log10(x2))
                     n1 = np.log10(y1) - m1* np.log10(x1)

                     if m1 != -1.:
                            int_temp = 10.**n1 /(m1+1)*(x2**(m1+1) - x1**(m1+1))
                     if m1 == -1.:
                            int_temp = 10.**n1 * np.log10(x2/x1)

                     temp11 = temp11 + int_temp
                     temp22 = temp22 + (energy1[j+1] - energy1[j])/1e6*(y1+y2)/2.
                     temp33 = temp33 + y2*(energy1[j+1] - energy1[j])/1e6

              if temp11 < 1e-4:
                     temp11 = np.nan

              if_temp1.append(temp11)
              if_temp2.append(temp22)
              if_temp3.append(temp33)

       int_flux.append(if_temp1)
       int_flux_linear.append(if_temp2)
       int_flux_linear2.append(if_temp3)



print (int_flux[5][5],int_flux_linear[5][5],int_flux_linear2[5][5])



# #=======================================================================       
# # calculate event integrated spectrum  

total_fp1=[]
half_fp =[]

total_time = raw_time[len(raw_time)-1] # in hours

print ("time interval in hours:", total_time/t_num)

for i in range(0, p_num_trsp):
       total_fp1.append(0.0)
       half_fp.append(0.0)
       for j in range(0, t_num):
              total_fp1[i] = total_fp1[i]+ (fp_t1[j*p_num_trsp+i]* p_0[i]*p_0[i] *eo*100.*no*(mp*vo)**(-3.))

#       for jj in range(0, t_num/2):
#              half_fp[i] = half_fp[i]+ (fp_t[jj*p_num_trsp+i]* p_0[i]*p_0[i] *eo*100.*no*(mp*vo)**(-3.))
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

print (count1, count2, count3, count4)



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
       FSXR=json_data["sep_forecast_submission"]["triggers"][0]["flare"]["intensity"]
       Vcme = 2.4e4*FSXR**0.3 # km/s
       time_to_inner = 0.05*AU/(Vcme*1000.)/3600.*2/3.
       print(time_to_inner)
       simulation_zero_time = flare_start_time + timedelta(hours=time_to_inner)
else:
       if "cme" in json_data["sep_forecast_submission"]["triggers"][0]:
              print('triggered by CME')
              cme_start_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["start_time"], '%Y-%m-%dT%H:%M:%SZ')
              time21_5 = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["time_at_height"]["time"],'%Y-%m-%dT%H:%MZ')
              simulation_zero_time = cme_start_time + (time21_5 - cme_start_time)/3.
       else:
              print('ERROR - No trigger info in output.json')


simulation_end_time = simulation_zero_time + timedelta(hours=xtime[t_num-1])
start_time = simulation_zero_time.strftime('%Y-%m-%dT%H:%M:%SZ')
end_time = simulation_end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

#calculate peak intensity and time
peak10 = 0.0
peak100 = 0.0
peak10_index = -1
peak100_index = -1
crossing10_index = -1
crossing100_index = -1

for i in range(0, t_num):
       if int_flux[energy_index[1]][i] > peak10:
              peak10 = int_flux[energy_index[1]][i]
              peak10_index = i

       print(int_flux[energy_index[1]][i], peak10, peak10_index)

       if int_flux[energy_index[4]][i] > peak100:
              peak100 = int_flux[energy_index[4]][i]
              peak100_index = i

peak10time = (simulation_zero_time + timedelta(hours=xtime[peak10_index])).strftime('%Y-%m-%dT%H:%MZ')
peak100time = (simulation_zero_time + timedelta(hours=xtime[peak100_index])).strftime('%Y-%m-%dT%H:%MZ')


for i in range(t_num-2, -1, -1):
       if int_flux[energy_index[1]][i]<10.0 and int_flux[energy_index[1]][i+1]>10.0:
              crossing10_index=i+1
       if int_flux[energy_index[4]][i]<1.0 and int_flux[energy_index[4]][i+1]>1.0:
              crossing100_index=i+1

if int_flux[energy_index[1]][0]>10:
       crossing10_index = 0
if int_flux[energy_index[4]][0]>1.0:
       crossing100_index = 0
       
#calculate threshold crossing and time

if crossing10_index == -1:
       cross_time_10 = "no crossing"
       all_clear_10 = True
else:
       cross_time_10 = (simulation_zero_time + timedelta(hours=xtime[crossing10_index])).strftime('%Y-%m-%dT%H:%MZ')
       all_clear_10 = False

if crossing100_index == -1:
       cross_time_100 = "no crossing"
       all_clear_100 = True
else:
       cross_time_100 = (simulation_zero_time + timedelta(hours=xtime[crossing100_index])).strftime('%Y-%m-%dT%H:%MZ')
       all_clear_100 = False

#calculate integral fluence:
gt10_fluence = total_func_numerical(energy1Mev, time_intensity1, xtime, 10.)/4./pi
gt100_fluence = total_func_numerical(energy1Mev, time_intensity1, xtime, 100.)/4./pi

#utc_time = datetime.strptime(json_data["sep_forecast_submission"]["issue_time"], "%Y-%m-%dT%H:%M:%SZ")
run_time = simulation_zero_time.strftime('%Y-%m-%d')

channel10MeV ={
              "energy_channel": { "min": 10, "max": -1, "units": "MeV"},
              "species": "proton",
              "location": "earth",
              "prediction_window": { "start_time": start_time, "end_time": end_time },
              "peak_intensity": { "intensity": peak10, "units": "pfu", "time": peak10time},
              "fluences": [{ "fluence": gt10_fluence, "units": "cm^-2*sr^-1"}],
              "threshold_crossings": [ { "crossing_time": cross_time_10, "threshold": 10.0, "threshold_units": "pfu" } ],
              "all_clear":{"all_clear_boolean": all_clear_10, "threshold": 10.0, "threshold_units": "pfu"},
              "sep_profile": ""
           }
channel100MeV ={
              "energy_channel": { "min": 100, "max": -1, "units": "MeV"},
              "species": "proton",
              "location": "earth",
              "prediction_window": { "start_time": start_time, "end_time": end_time },
              "peak_intensity": { "intensity": peak100, "units": "pfu", "time": peak100time}, 
              "fluences": [{ "fluence": gt100_fluence, "units": "cm^-2*sr^-1"}],             
              "threshold_crossings": [ { "crossing_time": cross_time_100, "threshold": 1.0, "threshold_units": "pfu" } ],
              "all_clear":{"all_clear_boolean": all_clear_100, "threshold": 1.0, "threshold_units": "pfu"},
              "sep_profile": ""
           }

#print(type(json_data["sep_forecast_submission"]["forecasts"]))

# json_data["sep_forecast_submission"]["forecasts"].append(channel10MeV)
# json_data["sep_forecast_submission"]["forecasts"].append(channel100MeV)



# with open('./'+run_time+'_output.json', 'w') as write_file:
#        json.dump(json_data, write_file, indent=4)

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


# f21 = open('./simulation_data/'+plot_title+'_differential_flux', 'w')
# f21.write('Time [hrs],    Energy [MeV],     Intensity J_T [protons/(cm^2 s sr MeV)]\n')

# for i in range(0, t_num):
#        for j in range(0, p_num_trsp):
#               f21.write('{:<15.4f}{:<#18.8g}{:<10.6e}\n'.format(xtime[i], energy1Mev[j], time_intensity1[j][i]))

#f21.close()


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
# plt.suptitle(plot_title+" ($\phi$ ="+str(phi_e)+"$^\circ$, "+str(r_e)+"AU)", fontsize=35)

# plot1 = plt.subplot2grid((6, 5), (0, 0), colspan=3, rowspan=6)
# plot2 = plt.subplot2grid((6, 5), (3, 3), rowspan=3, colspan=2)
# plot3 = plt.subplot2grid((6, 5), (0, 3), rowspan=3, colspan=2)

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

plot1.set_title("Time-intensity profile", fontsize=25)
plot1.set_yscale('log')
plot1.set_ylim([1e-2,1e4])
plot1.set_xlabel('time (hours)', fontsize=22)
#plt.axvline(total_time, color='black', linestyle='dashed', linewidth=2)
#plt.annotate(anno, xy=(0.83,0.81), xycoords='figure fraction', color='red',fontsize = 70 )
#plt.axvline(leave_time, color='black', linestyle='dashed', linewidth=2)
plot1.set_ylabel('$J_T(T)$ $[\#/(cm^2 \  s \ sr\  MeV)]$', fontsize=22)
#plt.legend(['iPATH 1 MeV', 'iPATH 10 MeV', 'FLRW 1 MeV', \
#            'FLRW 10 MeV', 'FP+FLRW 1 MeV', 'FP+FLRW 10 MeV', 'Decoupled 1 MeV', 'Decoupled 10 MeV'], \
#            loc=2, ncol = 3, borderaxespad=0., shadow = True, fontsize=25)
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


plot2.set_title('integral flux', fontsize=25)

plot2.set_yscale('log')
plot2.set_ylim([1e-2, 1e5])
#plt.xlim([-1, 50])
plot2.set_xlabel('time (hours)', fontsize=22)
#plt.axvline(total_time, color='black', linestyle='dashed', linewidth=2)
#plt.annotate(anno, xy=(0.83,0.81), xycoords='figure fraction', color='red',fontsize = 70 )
#plt.axvline(leave_time, color='black', linestyle='dashed', linewidth=2)
#plt.ylabel('$J_T(T)$ $(counts/(cm^2 s sr MeV))$', fontsize=30)
plot2.set_ylabel('Integral Flux (pfu)', fontsize=22)
#plt.legend(['iPATH 1 MeV', 'iPATH 10 MeV', 'FLRW 1 MeV', \
#            'FLRW 10 MeV', 'FP+FLRW 1 MeV', 'FP+FLRW 10 MeV', 'Decoupled 1 MeV', 'Decoupled 10 MeV'], \
#            loc=2, ncol = 3, borderaxespad=0., shadow = True, fontsize=25)
plot2.legend([#e_legd[energy_index[1]], e_legd[energy_index[2]], e_legd[energy_index[3]], \
#             e_legd[energy_index[4]], 
             int_e_legd[energy_index[1]],int_e_legd[energy_index[2]],\
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

# plt.gcf().text(0.02, 0.95, '(a)', fontsize=34, weight='bold')
# plt.gcf().text(0.62, 0.95, '(b)', fontsize=34, weight='bold')
# plt.gcf().text(0.62, 0.48, '(c)', fontsize=34, weight='bold')
# Packing all the plots and displaying them
plt.tight_layout()

plt.savefig('./'+run_time+'_plot.png')

#plt.show()
