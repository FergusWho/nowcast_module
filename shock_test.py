import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import datetime
from datetime import timedelta
from datetime import datetime
import json
import argparse
#from osgeo import gdal

from pyhdf.SD import SD, SDC
import sys



parser = argparse.ArgumentParser()
parser.add_argument("--root_dir", type=str, default='./', \
       help=("Root directory"))

args = parser.parse_args()

root_dir = args.root_dir

# adding nowcast_module to the system path
sys.path.insert(0, root_dir+'../../..')

from helioweb_locations import *

#################################

cme_center = 100.
del_phi = 5.
shell_num = 25
shd = 1


AU  = 1.5e11        
eo  = 1.6e-19
pi  = 3.141592653589793116
bo  = 2.404e-9       
t_o = 2858068.3
vo  = 52483.25 
co  = 3.0e8
n_0 = 1.0e6
gamma = 5/3.

# read phi_num
with open(root_dir+'../CME_input.json') as input_file:
    input_obj = json.load(input_file)

glv = input_obj.get("glv")
glv_shock = input_obj.get("cme_speed")
cme_var = (input_obj.get("cme_width") / 2.3556 ) ** 2.0

with open('transport/output.json', 'r') as read_file:
    json_data = json.load(read_file)


if "flare" in json_data["sep_forecast_submission"]["triggers"][0]:
    print('triggered by flare')
    flare_start_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["flare"]["start_time"], '%Y-%m-%dT%H:%MZ')
    FSXR=json_data["sep_forecast_submission"]["triggers"][0]["flare"]["intensity"]
    Vcme = 2.4e4*FSXR**0.3 # km/s
    time_to_inner = 0.05*AU/(Vcme*1000.)/3600.*2/3.
    print(time_to_inner)
    simulation_zero_time = flare_start_time + timedelta(hours=time_to_inner)
    trigger = 'Flare: '+json_data.get('sep_forecast_submission').get('triggers')[0].get('flare').get('start_time')
else:
    if "cme" in json_data["sep_forecast_submission"]["triggers"][0]:
        print('triggered by CME')
        cme_start_time = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["start_time"], '%Y-%m-%dT%H:%M:%SZ')
        time21_5 = datetime.strptime(json_data["sep_forecast_submission"]["triggers"][0]["cme"]["time_at_height"]["time"],'%Y-%m-%dT%H:%MZ')
        simulation_zero_time = cme_start_time + (time21_5 - cme_start_time)/3.
        trigger = json_data.get('sep_forecast_submission').get('triggers')[0].get('cme').get('catalog_id')
    else:
        print('ERROR - No trigger info in output.json')

print(input_obj)

phi_num = int(input_obj.get('cme_width')/5+5)
phi_e = int(input_obj.get('phi_e'))

print(input_obj.get('cme_width'), phi_num)
print('trigger:', trigger)

#---------------------------------------------------
f1 = open(root_dir+'shock_posn_comp.dat', 'r')
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

       shk_spd.append(float(columns[2]))
       shk_begin.append(int(columns[3]))
       shk_end.append(int(columns[4]))
       theta_bn.append(float(columns[5]))
       theta_vn.append(float(columns[6]))
       
       real_spd.append(float(columns[2])*math.cos(float(columns[6])/180.*pi))
       line_no = line_no + 1

f1.close
shell_num = int( math.floor(line_no/phi_num))
print (shell_num)

f2 = open(root_dir+'shock_momenta.dat', 'r')

time_all      =[]

for line in f2:
       line = line.strip()
       columns = line.split()
       time_all.append(float(columns[1]))
       min_e.append(float(columns[4]))
       max_e.append(float(columns[5])/1e6)       

f2.close

#---------------------------------------------------

phi_0 = []
phi_rad = []
for i in range(0, phi_num):
       phi_0.append(int(cme_center +del_phi*(i-math.floor(phi_num/2.))))
       phi_rad.append((round(cme_center +del_phi*(i-math.floor(phi_num/2.)))-phi_e)*pi/180.)
print (phi_0)

foot_phi = [x for x in range(phi_num)]
# xtime =[]

time_index = [2,7,12,17,22]


shell_time =[]
shell_time_str = []
shell_datetime = []
shell_time_hr = []
for i in range(0, shell_num):
       shell_time.append('%(time).1F %(unit)s' %{"time":time_all[i*phi_num], "unit":"hrs"})
       real_time = simulation_zero_time + timedelta(hours=time_all[i*phi_num])
       shell_time_str.append(real_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
       shell_datetime.append(real_time)
       shell_time_hr.append(time_all[i*phi_num])

phi_min = cme_center - np.floor(phi_num/2.)*5
phi_max = cme_center + np.floor(phi_num/2.)*5


xdims = 500
x1min = 0.05
x1max = 2.0
max_n = 20.0
max_v = 25



x1a = [0.0]*xdims

for i in range(0, xdims):
       x1a[i] = x1min+ i * (x1max-x1min)/(xdims-1)


x3a = []

for i in range(0, 360):
       x3a.append(float(i)*361./360.)
azimuths = np.radians(x3a)

r, theta = np.meshgrid(x1a, azimuths)
#print (r.shape, theta.shape)


# for field lines:
num = 8  # number of field lines
theta_space = 360./num
dx1a = x1a[2] - x1a[1]
dt = 0.001/2
maxt = 20000
pi = 3.14159265359


# read file 0
hdf_in = SD(root_dir+"../zhto030JH", SDC.READ)
prev_v1 = hdf_in.select('Data-Set-2')
prev_dens = hdf_in.select('Data-Set-8')


for ii in range(0, shell_num):
       ifile = 31 + ii
       file_no = root_dir + "../zhto{:03d}JH".format(ifile)
       # read the solar wind values from HDF files
       hdf_in = SD(file_no, SDC.READ)
       print('file name:'+file_no)
       print('done reading')

       # print(hdf_in.datasets())
       
       v1 = hdf_in.select('Data-Set-2')
       b1 = hdf_in.select('Data-Set-5')
       b3 = hdf_in.select('Data-Set-7')
       dens = hdf_in.select('Data-Set-8')
       inter_energy = hdf_in.select('Data-Set-9')


       
       dens_norm = np.ndarray((360, xdims))
       diff_v = np.ndarray((360, xdims))
       diff_n = np.ndarray((360, xdims))
       


       for i in range(0, 360):
              for j in range(0,xdims):
                     dens_norm[i,j] = dens[i,0,j]*x1a[j]**2.
                     diff_v[i,j] = v1[i,0,j] - prev_v1[i,0,j]
                     diff_n[i,j] = dens[i,0,j]*x1a[j]**2. - prev_dens[i,0,j]*x1a[j]**2.

                     # Gx[i,j] = 0.0
                     # Gy[i,j] = 0.0
                     # G[i,j] = 0.0


       shk_begin = np.zeros(phi_num)
       shk_end = np.zeros(phi_num)
       comp_ratio = np.zeros(phi_num)
       comp_ratio_d = np.zeros(phi_num)
       comp_ratio_s = np.zeros(phi_num)
       comp_ratio_v = np.zeros(phi_num)
       shock_v = np.zeros(phi_num)
       shock_loc = np.zeros(phi_num)
       shock_back = np.zeros(phi_num)
       shock_v_1 = np.zeros(phi_num)
       shock_v_2 = np.zeros(phi_num)

       sound_speed = np.zeros(phi_num)
       mach_no = np.zeros(phi_num)

       # The sobel operator method
       # note that python is row-major while fortran is column-major
       kx = [[1., 0., -1.], [2., 0., -2.], [1., 0., -1.]]
       ky = [[1., 2., 1.], [0., 0., 0.], [-1., -2., -1.]]

       Gx = np.zeros((xdims, 360))
       Gy = np.zeros((xdims, 360))
       G = np.zeros((xdims, 360))
       entropy = np.ndarray((xdims, 360))

       for i in range(0, 360):
              for j in range(0,xdims):
                     entropy[j,i] = diff_n[i,j]

       for i in range(1, xdims-1):
              for k in range(1,359):
                     for iii in range(0,3):
                            for jjj in range(0,3):
                                   Gx[i][k] = Gx[i][k] + kx[iii][jjj]*entropy[i+1-iii][k+1-jjj]
                                   Gy[i][k] = Gy[i][k] + ky[iii][jjj]*entropy[i+1-iii][k+1-jjj]

       G[:,:] = np.sqrt(Gx[:,:]**2. + Gy[:,:]**2)                          


       # if glv_shock >= 800.
       #        if ii <= 2:
       #               ent_gauge = np.max(G)/150
       #        else:
       #               ent_gauge = np.max(G)/100
       # else:
       #        ent_gauge = np.max(G)/200

       # if glv_shock >= 800.:
       #        ent_gauge = np.max(G)/500
       # else:
       #        ent_gauge = np.max(G)/700

       if ii <= 3:
              ent_gauge = np.max(G) / 1000.
       else:
              ent_gauge = np.max(G) / 500.    

       # skipped


       for jj in range(0, phi_num):
              phi_cme = phi_0[jj] - 1
              
              # if ii <= 3:
              #        ent_gauge = np.max(diff_v[phi_cme,:]) / 100.
              # else:
              #        ent_gauge = np.max(diff_v[phi_cme,:]) / 80.


              # for j in range(0,xdims):
              #        # if diff_n[phi_cme, j-1] < ent_gauge and diff_n[phi_cme, j] >= ent_gauge:
              #        #        shk_begin[jj] = j
              #        #        b_i = j

              #        if diff_v[phi_cme, j] >= ent_gauge and diff_v[phi_cme, j+1] < ent_gauge:
              #               shk_end[jj] = j+1
              #               e_i = j+1

              for j in range(1, xdims-1):
                     if G[j,phi_cme] >= ent_gauge and G[j+1,phi_cme] < ent_gauge:
                            shk_end[jj] = j+1
                            e_i = j+1

              # if shk_begin[jj] < shk_end[jj]-2*shd:
              shk_begin[jj] = shk_end[jj]-4*shd
              b_i = e_i - 4*shd

              shock_back[jj] = x1a[int(b_i)]
              shock_loc[jj] = x1a[int(e_i)]

              # calculate shock properties:
              # if shk_begin[jj] == 0:
              #        print('warning, shock begin = 0')
              #        shk_begin[jj] = 

              #print(type(shk_begin[jj]))
              #d_dn = dens[phi_cme, 0, e_i-3*shd]
              #v_dn = v1[phi_cme, 0, e_i-3*shd]*52.483

              #d_up = dens[phi_cme, 0, e_i+shd]
              v_up = v1[phi_cme, 0, e_i+shd]*52.483

              if ii == 0:
                     comp_ratio_d[jj] = dens[phi_cme, 0, int(b_i+1)] / dens[phi_cme, 0, int(shk_end[jj]+shd)]
                     v_dn = v1[phi_cme, 0, b_i+1]*52.483

              if ii <=3 and ii >0 :
                     comp_ratio_d[jj] = dens[phi_cme, 0, int(b_i)] / dens[phi_cme, 0, int(shk_end[jj]+shd)]
                     v_dn = v1[phi_cme, 0, b_i]*52.483

              else:
                     comp_ratio_d[jj] = dens[phi_cme, 0, int(b_i-shd)] / dens[phi_cme, 0, int(shk_end[jj]+shd)]
                     v_dn = v1[phi_cme, 0, b_i-shd]*52.483

              if comp_ratio_d[jj] >3.9:
                     comp_ratio_d[jj] = 3.9

              if comp_ratio_d[jj] < 1.05:
                     comp_ratio_d[jj] = 1.05

              if ii == 0:
                     shock_v_1[jj] = glv + np.exp(-(phi_0[jj]-cme_center)**2. / (2*cme_var)) * (glv_shock - glv)
              else:
                     shock_v_1[jj] = (comp_ratio_d[jj] * v_dn - v_up) / (comp_ratio_d[jj] - 1)

              # =========================
              # method 2, shock speed based:
              if ii == 0:
                     shock_v_2[jj] = glv + np.exp(-(phi_0[jj]-cme_center)**2. / (2*cme_var)) * (glv_shock - glv)
              else:
                     shock_v_2[jj] = (shock_loc[jj] - prev_shock_posn[jj])*AU/1000./(shell_time_hr[ii] - shell_time_hr[ii-1])/3600

              # comp_ratio_s[jj] = (shock_v_2[jj] - v_up) / (shock_v_2[jj] - v_dn) ! this is similar to dens compression ratio

              sound_speed[jj] = np.sqrt(gamma*inter_energy[phi_cme, 0, e_i+shd] * (gamma -1) / dens[phi_cme, 0, e_i+shd])*52.483

              print ('sound_speed is', sound_speed[jj])

              # =========================

              shock_v[jj] = (shock_v_1[jj] + shock_v_2[jj])/2.

              mach_no[jj] = (shock_v[jj] - v_up)/sound_speed[jj]
              print ('Mach number is', mach_no[jj])

              comp_ratio_s[jj] = 4.* mach_no[jj]**2.0 /(mach_no[jj]**2.0 + 3.)
              comp_ratio_v[jj] = (shock_v[jj] - v_up) / (shock_v[jj] - v_dn) # this is similar to dens compression ratio
              if comp_ratio_v[jj] >3.9:
                     comp_ratio_v[jj] = 3.9

              if comp_ratio_v[jj] < 1.05:
                     comp_ratio_v[jj] = 1.05

              comp_ratio[jj] = (comp_ratio_d[jj] + comp_ratio_v[jj])/2.




       # test:
       # print('phi_num:', phi_num)

       # fig = plt.figure(0, figsize=(18,11))
     
       # plt.plot(v1[99,0,:], 'r', v1[100,0,:], 'g', v1[101,0,:], 'b' )
       # plt.xlim([0,50])
       # plt.show()


       all_fl_r =[]
       all_fl_th =[]


       ## plot field lines that go through certain points
       # find vantage point locations: (assumes Earth at 1 AU and doesn't move during the time)
       current_time = shell_datetime[ii]
       root_dir1 = root_dir+'../../../'

       earth_r, earth_lat, earth_lon = find_earth(current_time, root_dir1)
       STA_r, STA_lat, STA_lon = find_STA(current_time, root_dir1)
       mars_r, mars_lat, mars_lon = find_mars(current_time, root_dir1)

       phi_STA = phi_e + STA_lon - earth_lon
       phi_mars = phi_e + mars_lon - earth_lon
       
       if phi_STA >= 360.:
              phi_STA -= 360.
       if phi_STA < 0:
              phi_STA += 360.

       if phi_mars >= 360.:
              phi_mars -= 360.
       if phi_mars < 0:
              phi_mars += 360.

       if current_time > datetime.strptime('2018-249', "%Y-%j"):
              psp_r, psp_lat, psp_lon = find_psp(current_time, root_dir1)
              phi_psp = phi_e + psp_lon - earth_lon
              if phi_psp >= 360.:
                     phi_psp -= 360.
              if phi_psp < 0:
                     phi_psp += 360.

              mid_pos = [[1.0, phi_e], [mars_r, phi_mars],[STA_r, phi_STA],[psp_r, phi_psp]]
       else:
              mid_pos = [[1.0, phi_e], [mars_r, phi_mars],[STA_r, phi_STA]]

       target = []
       for i in range(0,len(mid_pos)):
              mfl_r = []
              mfl_th = []

              temp_r = mid_pos[i][0]
              temp_th = mid_pos[i][1]
              target.append([temp_th/180.*pi, temp_r])
              
              while temp_r >= x1min:
                     mfl_r.append(temp_r)
                     mfl_th.append(temp_th/180.*pi)

                     r_index = (temp_r-x1min)/dx1a

                     dr  = b1[int(round(temp_th))-1, 0, int(r_index)] * dt
                     dth = b3[int(round(temp_th))-1, 0, int(r_index)] * dt / temp_r *180./pi

                     temp_r = temp_r - dr
                     temp_th = temp_th - dth

                     if temp_th < 0:
                            temp_th += 360.
                     if temp_th >= 360:
                            temp_th -= 360.

              mfl_r.reverse()
              mfl_th.reverse()

              temp_r = mid_pos[i][0]
              temp_th = mid_pos[i][1]

              while temp_r <= x1max:

                     r_index = (temp_r-x1min)/dx1a

                     dr  = b1[int(round(temp_th))-1, 0, int(r_index)] * dt
                     dth = b3[int(round(temp_th))-1, 0, int(r_index)] * dt / temp_r *180./pi

                     temp_r = temp_r + dr
                     temp_th = temp_th + dth
                     
                     if temp_th < 0:
                            temp_th += 360.
                     if temp_th >= 360:
                            temp_th -= 360.

                     mfl_r.append(temp_r)
                     mfl_th.append(temp_th/180.*pi)

              all_fl_r.append(mfl_r)
              all_fl_th.append(mfl_th)                     

       ticks = []
       ticks_v = []
       
       for i in range(0,7):
              ticks.append(i*max_n/6.)

              ticks_v.append(-max_v+ 2*i*max_v/6.)

       print('done calculating')
       prev_v1 = v1
       prev_dens = dens
       prev_shock_posn = shock_loc


       fig=plt.figure

       fig = plt.figure(0, figsize=(18,11))
       grid = plt.GridSpec(2,4, left = 0.06, right=0.96, bottom =0.08, wspace=0.28, hspace =0.25  )


       ax0 = plt.subplot(grid[0,0])
       ax0.plot(phi_0, comp_ratio_d, 'b')
       ax0.plot(phi_0, comp_ratio_s, 'b--', phi_0, comp_ratio_v, 'r')
       ax0.plot(phi_0, comp_ratio, 'k')
       ax0.set_ylabel('s', fontsize=15)
       ax0.set_title('Compression ratio', fontsize=20)
       ax0.set_xlim([phi_min, phi_max])
       ax0.set_ylim([1,4])
       ax0.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
       ax0.tick_params(axis='both', which='major', labelsize=14)


       ax1 = plt.subplot(grid[0,1])
       ax1.plot(phi_0, shock_v_1,'r')
       ax1.plot(phi_0, shock_v_2,'r--')
       ax1.plot(phi_0, shock_v,'k')
       ax1.set_ylabel('$V_{shk} (km/s)$', fontsize=15)
       ax1.set_title('shock speed', fontsize=20)
       ax1.set_xlim([phi_min, phi_max])
       ax1.set_ylim([200,2500])
       ax1.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
       ax1.tick_params(axis='both', which='major', labelsize=14)


       #---- rotate plot so earth is at 0 ------------------------
       dens_norm_new = np.ndarray((360, xdims))
       diff_v_new = np.ndarray((360, xdims))
       diff_n_new = np.ndarray((360, xdims))

       for i in range(0, 360):
              old_i = i+phi_e
              if old_i < 0:
                     old_i += 360
              if old_i >= 360:
                     old_i -= 360
              for j in range(0,xdims):
                     dens_norm_new[i,j] = dens_norm[old_i,j]
                     diff_v_new[i,j] = diff_v[old_i,j]*52.483
                     diff_n_new[i,j] = diff_n[old_i,j]

       for i in range(0,len(mid_pos)):
              for j in range(0, len(all_fl_th[i])):
                     new_th =  all_fl_th[i][j] - phi_e*pi/180
                     if new_th < 0:
                            new_th += 2*pi
                     if new_th >= 2*pi:
                            new_th -= 2*pi
                     all_fl_th[i][j] = new_th
              target[i][0] = target[i][0] - phi_e*pi/180

       #-----------------------------------------------------------

       ax2 = plt.subplot(grid[:, 2:], projection='polar')
       colors1 = plt.cm.gist_ncar(np.linspace(0.02, 1, 512))
       colors2 = plt.cm.Greys(np.linspace(0, 1, 512))
       colors_combined = np.vstack((colors1, colors2))
       cmap_combined = ListedColormap(colors_combined, name='gist_ncar_greys')
       

       pcm = ax2.contourf(theta, r, dens_norm_new,  extend='max',\
          levels = np.linspace(0,max_n,1024), cmap =cmap_combined, vmin=0.0, vmax=max_n, yunits ='AU')
    
       ax2.plot(phi_rad, shock_loc, 'k--', linewidth=2.0)
       
       

       ax2.tick_params(axis='both', labelsize=20)
       ax2.set_rlabel_position(10)
       ax2.set_rlim([0, 0.6])
       #ax2.set_rticks([0.5, 1, 1.5, 2])

       # 1AU circle
       ax2.plot(np.linspace(0,2*pi,360), [1.0]*360, 'k', linewidth=2.5)
       

       for i in range(0,len(mid_pos)):
              ax2.plot(all_fl_th[i], all_fl_r[i], 'w--', linewidth=2.0)

       ax2.plot(target[0][0], target[0][1], 'o', linewidth=1.5, ms=12, mec='k', mfc = '#FFFF00', label = 'Earth')
       ax2.plot(target[1][0], target[1][1], 'o', linewidth=1.5, ms=12, mec='k', mfc = 'r', label = 'Mars')
       ax2.plot(target[2][0], target[2][1], 's', linewidth=1.5, ms=12, mec='k', mfc = 'g', label = 'STEREO-A')

       if current_time > datetime.strptime('2018-249', "%Y-%j"):
              ax2.plot(target[3][0], target[3][1], 'D', linewidth=1.5, ms=12, mec='k', mfc = 'y', label = 'PSP')

       ax2.legend(fontsize=15, loc='lower right', bbox_to_anchor=(1.1, -0.05))

       # for i in range(0,3):
       #        ax2.plot(target[i][0], target[i][1], 'wo',linewidth=2.0)
       
       cbaxes = fig.add_axes([0.55, 0.9, 0.38, 0.03]) 
       cb = plt.colorbar(pcm, cax = cbaxes,orientation='horizontal', ticks= ticks)
       cbaxes.tick_params(labelsize=18)
       cbaxes.set_title('$R^2 N(AU^2cm^{-3})$', fontsize=25)

       # ax2.set_theta_offset(-phi_e/180*pi)
       
       ax3 = plt.subplot(grid[1,0])
       ax3.plot(phi_0, shock_loc,'g')
       ax3.set_ylabel('r', fontsize=15)
       ax3.set_title('shock location', fontsize=20)
       ax3.set_xlim([phi_min, phi_max])
       ax3.set_ylim([0,1])
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

       # adding text
       plt.figtext(0.58,0.07, 'Trigger:'+trigger, fontsize=20)
       plt.figtext(0.58,0.03, 'dt ='+shell_time[ii]+'    t='+shell_time_str[ii], fontsize=20)

#       plt.show()

       plt.savefig(root_dir+'Diagnostic_CME{:03d}.png'.format(ii))
       plt.clf()

       #====================================================================
       #====================================================================
       # with running difference of n

       fig = plt.figure(1, figsize=(18,11))
       grid = plt.GridSpec(2,4, left = 0.06, right=0.96, bottom =0.08, wspace=0.28, hspace =0.25  )




       ax2 = plt.subplot(grid[:, 2:], projection='polar')
       # colors1 = plt.cm.gist_ncar(np.linspace(0.02, 1, 512))
       # colors2 = plt.cm.Greys(np.linspace(0, 1, 512))
       # colors_combined = np.vstack((colors1, colors2))
       # cmap_combined = ListedColormap(colors_combined, name='gist_ncar_greys')
       

       pcm = ax2.contourf(theta, r, diff_n_new,  extend='max',\
          levels = np.linspace(-max_n, max_n, 1024), cmap ='coolwarm', vmin=-max_n, vmax=max_n, yunits ='AU')
    
       ax2.plot(phi_rad, shock_loc, 'k--', linewidth=2.0)
       ax2.plot(phi_rad, shock_back, 'r--', linewidth=2.0)       
       

       ax2.tick_params(axis='both', labelsize=20)
       ax2.set_rlabel_position(10)
       ax2.set_rlim([0, 0.6])
       #ax2.set_rticks([0.5, 1, 1.5, 2])

       # 1AU circle
       ax2.plot(np.linspace(0,2*pi,360), [1.0]*360, 'k', linewidth=2.5)
       

       for i in range(0,len(mid_pos)):
              ax2.plot(all_fl_th[i], all_fl_r[i], 'w--', linewidth=2.0)

       ax2.plot(target[0][0], target[0][1], 'o', linewidth=1.5, ms=12, mec='k', mfc = '#FFFF00', label = 'Earth')
       ax2.plot(target[1][0], target[1][1], 'o', linewidth=1.5, ms=12, mec='k', mfc = 'r', label = 'Mars')
       ax2.plot(target[2][0], target[2][1], 's', linewidth=1.5, ms=12, mec='k', mfc = 'g', label = 'STEREO-A')

       if current_time > datetime.strptime('2018-249', "%Y-%j"):
              ax2.plot(target[3][0], target[3][1], 'D', linewidth=1.5, ms=12, mec='k', mfc = 'y', label = 'PSP')

       ax2.legend(fontsize=15, loc='lower right', bbox_to_anchor=(1.1, -0.05))

       # for i in range(0,3):
       #        ax2.plot(target[i][0], target[i][1], 'wo',linewidth=2.0)
       
       cbaxes = fig.add_axes([0.55, 0.9, 0.38, 0.03]) 
       cb = plt.colorbar(pcm, cax = cbaxes,orientation='horizontal', ticks= ticks_v)
       cbaxes.tick_params(labelsize=18)
       cbaxes.set_title('$R^2 N(AU^2cm^{-3})$', fontsize=25)

       # ax2.set_theta_offset(-phi_e/180*pi)
       
       ax3 = plt.subplot(grid[1,0])
       ax3.plot(phi_0, shock_loc,'g')
       ax3.set_ylabel('r', fontsize=15)
       ax3.set_title('shock location', fontsize=20)
       ax3.set_xlim([phi_min, phi_max])
       ax3.set_ylim([0,1])
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

       # adding text
       plt.figtext(0.58,0.07, 'Trigger:'+trigger, fontsize=20)
       plt.figtext(0.58,0.03, 'dt ='+shell_time[ii]+'    t='+shell_time_str[ii], fontsize=20)

#       plt.show()

       plt.savefig(root_dir+'Diagnostic_diif_v{:03d}.png'.format(ii))
       plt.clf()


       fig = plt.figure(2, figsize=(8,11))
       grid = plt.GridSpec(3,1, left = 0.06, right=0.96, bottom =0.08, wspace=0.28, hspace =0.35  )
       plt.title("t="+shell_time[ii])

       ax0 = plt.subplot(grid[0,0])
       ax0.plot(x1a[0:150], dens[100,0,0:150],'b.-')
       ax0.set_ylabel('density', fontsize=15)
       ax0.set_title('density vs r', fontsize=20)
       ax0.axvline(x=shock_loc[int((phi_num+1)/2)], color = 'k')
       #ax0.set_xlim([phi_min, phi_max])
       #ax0.set_ylim([0,4])
       ax0.set_xlabel('r(AU)', fontsize=15)
       ax0.tick_params(axis='both', which='major', labelsize=10)


       ax1 = plt.subplot(grid[1,0])
       ax1.plot(x1a[0:150], dens_norm[100,0:150],'b.-')
       ax1.set_ylabel('normalized density', fontsize=15)
       ax1.set_title('normalized density vs r', fontsize=20)
       ax1.axvline(x=shock_loc[int((phi_num+1)/2)], color = 'k')
       #ax1.set_xlim([phi_min, phi_max])
       #ax0.set_ylim([0,4])
       ax1.set_xlabel('r(AU)', fontsize=15)
       ax1.tick_params(axis='both', which='major', labelsize=10)

       ax2 = plt.subplot(grid[2,0])
       ax2.plot(x1a[0:150], v1[100,0,0:150]*52.483,'b.-')
       ax2.set_ylabel('speed', fontsize=15)
       ax2.set_title('speed vs r', fontsize=20)
       ax2.axvline(x=shock_loc[int((phi_num+1)/2)], color = 'k')
       #ax1.set_xlim([phi_min, phi_max])
       #ax0.set_ylim([0,4])
       ax2.set_xlabel('r(AU)', fontsize=15)
       ax2.tick_params(axis='both', which='major', labelsize=10)

       plt.figtext(0.15,0.93, 'Trigger:'+trigger+'\ndt ='+shell_time[ii]+'   t='+shell_time_str[ii], fontsize=20)

       plt.savefig(root_dir+'radial_{:03d}.png'.format(ii))
#       debug only. comment out when not using
       plt.clf()

'''       
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
       ax1.set_ylim([200,2500])
       ax1.set_xlabel('longitude $\phi (^\circ)$', fontsize=15)
       ax1.tick_params(axis='both', which='major', labelsize=14)


       #---- rotate plot so earth is at 0 ------------------------
       dens_norm_new = np.ndarray((360, xdims))

       for i in range(0, 360):
              old_i = i+phi_e
              if old_i < 0:
                     old_i += 360
              if old_i >= 360:
                     old_i -= 360
              for j in range(0,xdims):
                     dens_norm_new[i,j] = dens_norm[old_i,j]


       for i in range(0,len(mid_pos)):
              for j in range(0, len(all_fl_th[i])):
                     new_th =  all_fl_th[i][j] - phi_e*pi/180
                     if new_th < 0:
                            new_th += 2*pi
                     if new_th >= 2*pi:
                            new_th -= 2*pi
                     all_fl_th[i][j] = new_th
              target[i][0] = target[i][0] - phi_e*pi/180

       #-----------------------------------------------------------

       ax2 = plt.subplot(grid[:, 2:], projection='polar')
       colors1 = plt.cm.gist_ncar(np.linspace(0.02, 1, 512))
       colors2 = plt.cm.Greys(np.linspace(0, 1, 512))
       colors_combined = np.vstack((colors1, colors2))
       cmap_combined = ListedColormap(colors_combined, name='gist_ncar_greys')

       pcm = ax2.contourf(theta, r, dens_norm_new,  extend='max',\
          levels = np.linspace(0,max_n,1024), cmap =cmap_combined, vmin=0.0, vmax=max_n, yunits ='AU')
    
       #ax2.plot(phi_rad, x1a[shock_end[ii*phi_num:(ii+1)*phi_num]-3], 'k--', linewidth=2.0)
       
       ax2.set_rlim([0, 2.0])

       ax2.tick_params(axis='both', labelsize=20)
       ax2.set_rlabel_position(10)
       ax2.set_rticks([0.5, 1, 1.5, 2])

       # 1AU circle
       ax2.plot(np.linspace(0,2*pi,360), [1.0]*360, 'k', linewidth=2.5)
       
       for i in range(0,num):
              ax2.plot(fl0_th[i], fl0_r[i], 'k')

       for i in range(0,len(mid_pos)):
              ax2.plot(all_fl_th[i], all_fl_r[i], 'w--', linewidth=2.0)

       ax2.plot(target[0][0], target[0][1], 'o', linewidth=1.5, ms=12, mec='k', mfc = '#FFFF00', label = 'Earth')
       ax2.plot(target[1][0], target[1][1], 'o', linewidth=1.5, ms=12, mec='k', mfc = 'r', label = 'Mars')
       ax2.plot(target[2][0], target[2][1], 's', linewidth=1.5, ms=12, mec='k', mfc = 'g', label = 'STEREO-A')

       if current_time > datetime.strptime('2018-249', "%Y-%j"):
              ax2.plot(target[3][0], target[3][1], 'D', linewidth=1.5, ms=12, mec='k', mfc = 'y', label = 'PSP')

       ax2.legend(fontsize=15, loc='lower right', bbox_to_anchor=(1.1, -0.05))

       # for i in range(0,3):
       #        ax2.plot(target[i][0], target[i][1], 'wo',linewidth=2.0)
       
       cbaxes = fig.add_axes([0.55, 0.9, 0.38, 0.03]) 
       cb = plt.colorbar(pcm, cax = cbaxes,orientation='horizontal', ticks= ticks)
       cbaxes.tick_params(labelsize=18)
       cbaxes.set_title('$R^2 N(AU^2cm^{-3})$', fontsize=25)

       # ax2.set_theta_offset(-phi_e/180*pi)
       
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

       # adding text
       plt.figtext(0.58,0.07, 'Trigger:'+trigger, fontsize=20)
       plt.figtext(0.58,0.03, 'dt ='+shell_time[ii]+'    t='+shell_time_str[ii], fontsize=20)

       # plt.show()
       # pause
       plt.savefig(root_dir+'CME{:03d}.png'.format(ii))
       plt.clf()

       fig = plt.figure(1, figsize=(8,11))
       grid = plt.GridSpec(3,1, left = 0.06, right=0.96, bottom =0.08, wspace=0.28, hspace =0.35  )
       plt.title("t="+shell_time[ii])

       ax0 = plt.subplot(grid[0,0])
       ax0.plot(x1a[0:150], dens[100,0,0:150],'b.-')
       ax0.set_ylabel('density', fontsize=15)
       ax0.set_title('density vs r', fontsize=20)
       ax0.axvline(x=shock_loc[ii*phi_num+int((phi_num+1)/2)], color = 'k')
       #ax0.set_xlim([phi_min, phi_max])
       #ax0.set_ylim([0,4])
       ax0.set_xlabel('r(AU)', fontsize=15)
       ax0.tick_params(axis='both', which='major', labelsize=10)


       ax1 = plt.subplot(grid[1,0])
       ax1.plot(x1a[0:150], dens_norm[100,0:150],'b.-')
       ax1.set_ylabel('normalized density', fontsize=15)
       ax1.set_title('normalized density vs r', fontsize=20)
       ax1.axvline(x=shock_loc[ii*phi_num+int((phi_num+1)/2)], color = 'k')
       #ax1.set_xlim([phi_min, phi_max])
       #ax0.set_ylim([0,4])
       ax1.set_xlabel('r(AU)', fontsize=15)
       ax1.tick_params(axis='both', which='major', labelsize=10)

       ax2 = plt.subplot(grid[2,0])
       ax2.plot(x1a[0:150], v1[100,0,0:150]*52.483,'b.-')
       ax2.set_ylabel('speed', fontsize=15)
       ax2.set_title('speed vs r', fontsize=20)
       ax2.axvline(x=shock_loc[ii*phi_num+int((phi_num+1)/2)], color = 'k')
       #ax1.set_xlim([phi_min, phi_max])
       #ax0.set_ylim([0,4])
       ax2.set_xlabel('r(AU)', fontsize=15)
       ax2.tick_params(axis='both', which='major', labelsize=10)

       plt.figtext(0.15,0.93, 'Trigger:'+trigger+'\ndt ='+shell_time[ii]+'   t='+shell_time_str[ii], fontsize=20)

       plt.savefig(root_dir+'radial_{:03d}.png'.format(ii))
#       debug only. comment out when not using
       plt.clf()

'''



