import math
import numpy as np
import matplotlib.pyplot as plt

import json
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--root_dir", type=str, default='./', \
       help=("Root directory"))

args = parser.parse_args()

root_dir = args.root_dir
#################################

cme_center = 100.
del_phi = 5.


AU  = 1.5e11        
eo  = 1.6e-19
pi  = 3.141592653589793116
bo  = 2.404e-9       
t_o = 2858068.3
vo  = 52483.25 
co  = 3.0e8
n_0 = 1.0e6

# read phi_num
with open(root_dir+'../input.json') as input_file:
    input_obj = json.load(input_file)

print(input_obj)

phi_num = int(input_obj.get('cme_width')/5+5)

print(input_obj.get('cme_width'), phi_num)

theta_bn_t    = []
shock_loc_t   = []
shk_spd_t     = []
comp_rat_t    = []
max_e_t       = []
inter_phi     = []


f1 = open(root_dir+'shock_posn_comp.dat', 'r')
#f1 = open('/home/junxiang/Downloads/1126/normal/shock_posn_comp.dat', 'r')
shock_loc     = []
comp_rat      = []
shk_spd       = []
shk_begin     = []
shk_end       = []
theta_bn      = []
theta_vn      = []
max_e         = []
min_e         = []
real_spd      = []


line_no = 0
for line in f1:
       line = line.strip()
       columns = line.split()

       shock_loc.append(float(columns[0]))
       comp_rat.append(float(columns[1]))
       shk_spd.append(float(columns[2]))
       shk_begin.append(float(columns[3]))
       shk_end.append(float(columns[4]))
       theta_bn.append(float(columns[5]))
       theta_vn.append(float(columns[6]))
       
       real_spd.append(float(columns[2])*math.cos(float(columns[6])/180.*pi))
       line_no = line_no + 1

f1.close
shell_num = int( math.floor(line_no/phi_num))
print (shell_num)

f2 = open(root_dir+'shock_momenta.dat', 'r')
#f2 = open('/home/junxiang/Downloads/1126/normal/shock_momenta.dat', 'r')

time_all      =[]

for line in f2:
       line = line.strip()
       columns = line.split()
       time_all.append(float(columns[1]))
       min_e.append(float(columns[4]))
       max_e.append(float(columns[5])/1e6)       

f2.close


# #max energy and injection energy at the nose:
# index_nose = 12

# max_nose      = []
# inj_nose      = []
# x_nose        = []
# spd_nose      = []
# thbn_nose     = []
# comp_nose     = []
# for i in range(0, shell_num):
#        max_nose.append(max_e[i*phi_num + index_nose])
#        inj_nose.append(min_e[i*phi_num + index_nose]/1e6)
#        x_nose.append(shock_loc[i*phi_num + index_nose])
#        spd_nose.append(shk_spd[i*phi_num + index_nose])
#        thbn_nose.append(theta_bn[i*phi_num + index_nose])
#        comp_nose.append(comp_rat[i*phi_num + index_nose])

# temp_e = []
# for i in range(3, phi_num-3):
#        max_temp = []
#        for j in range(0,10):
#               max_temp.append(max_e[j*phi_num+i])
#        temp_e.append(np.max(max_temp))

       
# avg_max = np.mean(temp_e)

# print "Maximum Energy over all is", np.max(temp_e), " (MeV)"
# print "Maximum Energy averaged over all longitudes is", avg_max, " (MeV)"
       


phi_0 = []
for i in range(0, phi_num):
       phi_0.append(int(cme_center +del_phi*(i-math.floor(phi_num/2.))))
print (phi_0)

foot_phi = [x for x in range(phi_num)]
# xtime =[]

time_index = [2,7,12,17,22]
#time_index = [17, 18, 19, 20, 21]


shell_time =[]
for i in range(0, shell_num):
       shell_time.append('%(time).1F %(unit)s' %{"time":time_all[i*phi_num], "unit":"hrs"})



phi_min = cme_center - np.floor(phi_num/2.)*5
phi_max = cme_center + np.floor(phi_num/2.)*5


fig, ((ax0, ax1, ax2), (ax3, ax4, ax5)) = plt.subplots(2, 3, figsize=(22,12))

ax0.plot(phi_0, comp_rat[time_index[0]*phi_num:(time_index[0]+1)*phi_num],'b',  \
         phi_0, comp_rat[time_index[1]*phi_num:(time_index[1]+1)*phi_num],'r',  \
         phi_0, comp_rat[time_index[2]*phi_num:(time_index[2]+1)*phi_num],'g',  \
         phi_0, comp_rat[time_index[3]*phi_num:(time_index[3]+1)*phi_num],'y',  \
         phi_0, comp_rat[time_index[4]*phi_num:(time_index[4]+1)*phi_num],'k' )
ax0.set_ylabel('s', fontsize=15)
ax0.set_title('Compression ratio', fontsize=20)
ax0.set_xlim([phi_min, phi_max])
ax0.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
# ax0.legend([shell_time[time_index[0]], shell_time[time_index[1]],\
#             shell_time[time_index[2]],shell_time[time_index[3]],\
#             shell_time[time_index[4]]], loc = 8)
ax0.tick_params(axis='both', which='major', labelsize=14)

ax1.plot(phi_0, shock_loc[time_index[0]*phi_num:(time_index[0]+1)*phi_num],'b',  \
         phi_0, shock_loc[time_index[1]*phi_num:(time_index[1]+1)*phi_num],'r',  \
         phi_0, shock_loc[time_index[2]*phi_num:(time_index[2]+1)*phi_num],'g',  \
         phi_0, shock_loc[time_index[3]*phi_num:(time_index[3]+1)*phi_num],'y',  \
         phi_0, shock_loc[time_index[4]*phi_num:(time_index[4]+1)*phi_num],'k')
ax1.set_ylabel('$R_{shk} (AU)$', fontsize=15)
ax1.set_title('Shock front location', fontsize=20)
ax1.set_xlim([phi_min, phi_max])
ax1.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
ax1.tick_params(axis='both', which='major', labelsize=14)



ax2.plot(phi_0, shk_spd[time_index[0]*phi_num:(time_index[0]+1)*phi_num],'b',  \
         phi_0, shk_spd[time_index[1]*phi_num:(time_index[1]+1)*phi_num],'r',  \
         phi_0, shk_spd[time_index[2]*phi_num:(time_index[2]+1)*phi_num],'g',  \
         phi_0, shk_spd[time_index[3]*phi_num:(time_index[3]+1)*phi_num],'y',  \
         phi_0, shk_spd[time_index[4]*phi_num:(time_index[4]+1)*phi_num],'k'  )
ax2.set_ylabel('$V_{shk} (km/s)$', fontsize=15)
ax2.set_title('shock speed', fontsize=20)
ax2.set_xlim([phi_min, phi_max])
ax2.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
ax2.tick_params(axis='both', which='major', labelsize=14)


ax3.plot(phi_0, theta_bn[time_index[0]*phi_num:(time_index[0]+1)*phi_num],'b',  \
         phi_0, theta_bn[time_index[1]*phi_num:(time_index[1]+1)*phi_num],'r',  \
         phi_0, theta_bn[time_index[2]*phi_num:(time_index[2]+1)*phi_num],'g',  \
         phi_0, theta_bn[time_index[3]*phi_num:(time_index[3]+1)*phi_num],'y',  \
         phi_0, theta_bn[time_index[4]*phi_num:(time_index[4]+1)*phi_num],'k')
ax3.set_ylabel('$\\theta_{BN} (^\circ)$', fontsize=15)
ax3.set_title('$\\theta_{BN}$', fontsize=20)
ax3.set_xlim([phi_min, phi_max])
ax3.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
ax3.tick_params(axis='both', which='major', labelsize=14)
ax3.legend([shell_time[time_index[0]], shell_time[time_index[1]],\
            shell_time[time_index[2]],shell_time[time_index[3]],\
            shell_time[time_index[4]]], loc = 2, fontsize=15)


ax4.plot(phi_0, theta_vn[time_index[0]*phi_num:(time_index[0]+1)*phi_num],'b',  \
         phi_0, theta_vn[time_index[1]*phi_num:(time_index[1]+1)*phi_num],'r',  \
         phi_0, theta_vn[time_index[2]*phi_num:(time_index[2]+1)*phi_num],'g',  \
         phi_0, theta_vn[time_index[3]*phi_num:(time_index[3]+1)*phi_num],'y',  \
         phi_0, theta_vn[time_index[4]*phi_num:(time_index[4]+1)*phi_num],'k', )
ax4.set_xlim([phi_min, phi_max])
ax4.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
ax4.set_ylabel('$\\theta_{VN} (^\circ)$', fontsize=15)
ax4.set_title('$\\theta_{VN}$', fontsize=20)

ax5.plot(phi_0, max_e[time_index[0]*phi_num:(time_index[0]+1)*phi_num],'b',  \
         phi_0, max_e[time_index[1]*phi_num:(time_index[1]+1)*phi_num],'r',  \
         phi_0, max_e[time_index[2]*phi_num:(time_index[2]+1)*phi_num],'g',  \
         phi_0, max_e[time_index[3]*phi_num:(time_index[3]+1)*phi_num],'y',  \
         phi_0, max_e[time_index[4]*phi_num:(time_index[4]+1)*phi_num],'k', )         
ax5.set_yscale('log')
ax5.set_xlim([phi_min, phi_max])
ax5.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
ax5.set_ylabel('$Emax (MeV)$', fontsize=15)
ax5.set_title('maximum energy', fontsize=20)

# plt.figure(3)
# plt.plot(phi_0, theta_vn[time_index[0]*phi_num:(time_index[0]+1)*phi_num],'b',  \
#          phi_0, theta_vn[time_index[1]*phi_num:(time_index[1]+1)*phi_num],'r',  \
#          phi_0, theta_vn[time_index[2]*phi_num:(time_index[2]+1)*phi_num],'g',  \
#          phi_0, theta_vn[time_index[3]*phi_num:(time_index[3]+1)*phi_num],'y',  \
#          phi_0, theta_vn[time_index[4]*phi_num:(time_index[4]+1)*phi_num],'k')
# plt.ylabel('$\\theta_{vn} (^\circ)$', fontsize=18)
# plt.title('$\\theta_{vn}$', fontsize=20)
# plt.xlim([phi_min, phi_max])
# plt.xlabel('longitude $\phi (^\circ)$', fontsize=15)
# plt.tick_params(axis='both', which='major', labelsize=14)
# plt.legend([shell_time[time_index[0]], shell_time[time_index[1]],\
#             shell_time[time_index[2]],shell_time[time_index[3]],\
#             shell_time[time_index[4]]], loc = 2)


plt.show()

















