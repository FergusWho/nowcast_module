import math
import numpy as np
import matplotlib.pyplot as plt

import json
import argparse
from osgeo import gdal

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

phi_num = int(input_obj.get('cme_width')/5+1)

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


phi_0 = []
phi_rad = []
for i in range(0, phi_num):
       phi_0.append(int(cme_center +del_phi*(i-math.floor(phi_num/2.))))
       phi_rad.append((round(cme_center +del_phi*(i-math.floor(phi_num/2.))))*pi/180.)
print (phi_0)

foot_phi = [x for x in range(phi_num)]
# xtime =[]

time_index = [2,7,12,17,22]


shell_time =[]
for i in range(0, shell_num):
       shell_time.append('%(time).1F %(unit)s' %{"time":time_all[i*phi_num], "unit":"hrs"})



phi_min = cme_center - np.floor(phi_num/2.)*5
phi_max = cme_center + np.floor(phi_num/2.)*5


xdims = 500
x1min = 0.05
x1max = 2.0
max_n = 50.0



x1a = [0.0]*xdims

for i in range(0, xdims):
       x1a[i] = x1min+ i * (x1max-x1min)/(xdims-1)


x3a = []

for i in range(0, 360):
       x3a.append(float(i)*361./360.)
azimuths = np.radians(x3a)

r, theta = np.meshgrid(x1a, azimuths)
#print r.shape, theta.shape


# for field lines:
num = 8  # number of field lines
theta_space = 360./num
dx1a = x1a[2] - x1a[1]
dt = 0.001/2
maxt = 20000
pi = 3.14159265359

for ii in range(0, shell_num):
       ifile = 26 + ii
       file_no = root_dir + "../zhto{:03d}JH".format(ifile)
       # read the solar wind values from HDF files
       print('HDF4_SDS:UNKNOWN:{:s}:3'.format(file_no))
       v1_data = gdal.Open('HDF4_SDS:UNKNOWN:{:s}:3'.format(file_no))  # (360,1,x)
       b1_data = gdal.Open('HDF4_SDS:UNKNOWN:{:s}:15'.format(file_no))
       b3_data = gdal.Open('HDF4_SDS:UNKNOWN:{:s}:23'.format(file_no))
       dens_data = gdal.Open('HDF4_SDS:UNKNOWN:{:s}:27'.format(file_no))
       inter_energy_data= gdal.Open('HDF4_SDS:UNKNOWN:{:s}:31'.format(file_no))
       
       v1 = v1_data.ReadAsArray()
       b1 = b1_data.ReadAsArray()
       b3 = b3_data.ReadAsArray()
       dens = dens_data.ReadAsArray()
       inter_energy = inter_energy_data.ReadAsArray()
       
       dens_norm = np.ndarray((360, xdims))

       for i in range(0, 360):
              for j in range(0,xdims):
                     dens_norm[i,j] = dens[i,0,j]*x1a[j]**2.

       # plot field lines

       print(b1.shape, np.ndim(b1))
       fl0_r = []
       fl0_th = []
       for i in range(0,num):
              mfl_r = []
              mfl_th = []
              temp_r = x1max
              temp_th = (1.0 + i*theta_space)
       
              while temp_r >= x1min:
                     r_index = (temp_r-x1min)/dx1a

                     # print temp_th , r_index
                     # print b1[int(round(temp_th))-1, 0, int(r_index)], b1[int(round(temp_th)), 1, int(r_index)]
                     # pause
                     dr  = -b1[int(round(temp_th))-1, 0, int(r_index)] * dt
                     dth = -b3[int(round(temp_th))-1, 0, int(r_index)] * dt / temp_r *180./pi

                     temp_r = temp_r + dr
                     temp_th = temp_th + dth
                     
                     while temp_th < 0:
                            temp_th += 360.
                     while temp_th >= 360:
                            temp_th -= 360.         

                     mfl_r.append(temp_r)
                     mfl_th.append(temp_th/180.*pi)

              fl0_r.append(mfl_r)
              fl0_th.append(mfl_th)


       all_fl_r =[]
       all_fl_th =[]


       # # plot field lines that go through certain points
       # mid_pos = [[1.0, 80], [0.5, 100],[1., 100],[1, 100]]
       # target = []
       # for i in range(0,4):
       #        mfl_r = []
       #        mfl_th = []

       #        temp_r = mid_pos[i][0]
       #        temp_th = mid_pos[i][1]
       #        target.append([temp_th/180.*pi, temp_r])

       #        while temp_r >= x1min:
       #               mfl_r.append(temp_r)
       #               mfl_th.append(temp_th/180.*pi)

       #               r_index = (temp_r-x1min)/dx1a

       #               dr  = b1[int(round(temp_th))-1, 0, int(r_index)] * dt
       #               dth = b3[int(round(temp_th))-1, 0, int(r_index)] * dt / temp_r *180./pi

       #               temp_r = temp_r - dr
       #               temp_th = temp_th - dth

       #               if temp_th < 0:
       #                      temp_th += 360.
       #               if temp_th >= 360:
       #                      temp_th -= 360.

       #        mfl_r.reverse()
       #        mfl_th.reverse()

       #        temp_r = mid_pos[i][0]
       #        temp_th = mid_pos[i][1]

       #        while temp_r <= x1max:

       #               r_index = (temp_r-x1min)/dx1a

       #               dr  = b1[int(round(temp_th))-1, 0, int(r_index)] * dt
       #               dth = b3[int(round(temp_th))-1, 0, int(r_index)] * dt / temp_r *180./pi

       #               temp_r = temp_r + dr
       #               temp_th = temp_th + dth
                     
       #               if temp_th < 0:
       #                      temp_th += 360.
       #               if temp_th >= 360:
       #                      temp_th -= 360.

       #               mfl_r.append(temp_r)
       #               mfl_th.append(temp_th/180.*pi)

       #        all_fl_r.append(mfl_r)
       #        all_fl_th.append(mfl_th)                     

       ticks = []
       
       for i in range(0,6):
              ticks.append(i*max_n/5.)

       #---------------------------------------
       #   plotting
       #---------------------------------------
       fig = plt.figure(0, figsize=(18,11))
       grid = plt.GridSpec(2,4, left = 0.06, right=0.96, bottom =0.08, wspace=0.28, hspace =0.25  )


       ax0 = plt.subplot(grid[0,0])
       ax0.plot(phi_0, comp_rat[ii*phi_num:(ii+1)*phi_num])
       ax0.set_ylabel('s', fontsize=15)
       ax0.set_title('Compression ratio', fontsize=20)
       ax0.set_xlim([phi_min, phi_max])
       ax0.set_ylim([1,4])
       ax0.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
       ax0.tick_params(axis='both', which='major', labelsize=14)


       ax1 = plt.subplot(grid[0,1])
       ax1.plot(phi_0, shk_spd[ii*phi_num:(ii+1)*phi_num],'r')
       ax1.set_ylabel('$V_{shk} (km/s)$', fontsize=15)
       ax1.set_title('shock speed', fontsize=20)
       ax1.set_xlim([phi_min, phi_max])
       ax1.set_ylim([200,3000])
       ax1.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
       ax1.tick_params(axis='both', which='major', labelsize=14)



       ax2 = plt.subplot(grid[:, 2:], projection='polar')
       pcm = ax2.contourf(theta, r, dens_norm,  extend='max', fontsize=25,\
          levels = np.linspace(0,max_n,150), cmap ='coolwarm', vmin=0.0, vmax=max_n, yunits ='AU')
    
       ax2.plot(phi_rad, shock_loc[ii*phi_num:(ii+1)*phi_num], 'k--', linewidth=2.0)
       ax2.set_rlim([0, 2.0])

       ax2.tick_params(axis='both', labelsize=20)
       ax2.set_rlabel_position(10)
       ax2.set_rticks([0.5, 1, 1.5, 2])

       # 1AU circle
       ax2.plot(np.linspace(0,2*pi,360), [1.0]*360, 'k', linewidth=2.5)
       
       for i in range(0,num):
              ax2.plot(fl0_th[i], fl0_r[i], 'k')
       
       cbaxes = fig.add_axes([0.55, 0.9, 0.38, 0.03]) 
       cb = plt.colorbar(pcm, cax = cbaxes,orientation='horizontal', ticks= ticks)
       cbaxes.tick_params(labelsize=18)
       cbaxes.set_title('$R^2 N(AU^2cm^{-3})$', fontsize=25)
       
       ax3 = plt.subplot(grid[1,0])
       ax3.plot(phi_0, theta_bn[ii*phi_num:(ii+1)*phi_num],'g')
       ax3.set_ylabel('$\\theta_{BN} (^\circ)$', fontsize=15)
       ax3.set_title('$\\theta_{BN}$', fontsize=20)
       ax3.set_xlim([phi_min, phi_max])
       ax3.set_ylim([0,90])
       ax3.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
       ax3.tick_params(axis='both', which='major', labelsize=14)
       
       ax4 = plt.subplot(grid[1,1])
       ax4.plot(phi_0, max_e[ii*phi_num:(ii+1)*phi_num],'b')
       ax4.set_yscale('log')
       ax4.set_xlim([phi_min, phi_max])
       ax4.set_ylim([1,5000])
       ax4.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
       ax4.set_ylabel('$Emax (MeV)$', fontsize=15)
       ax4.set_title('maximum energy', fontsize=20)


       plt.savefig(root_dir+'CME{:03d}.png'.format(ii))












