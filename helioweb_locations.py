import numpy as np
import datetime
from datetime import timedelta
from datetime import datetime

#root_dir1 = '/data/iPATH/nowcast_module'
def find_mars(date_time, root_dir1):
    f1 = open(root_dir1+'/helioweb/planets/mars.lst', 'r')
    line_no = 0
    year    = []
    day     = []
    rad     = []
    lat     = []
    lon     = []

    for line in f1:
        line = line.strip()
        columns = line.split()

        if line_no >=1 :
            year.append(columns[0])
            day.append(columns[1])
            rad.append(float(columns[2]))
            lat.append(float(columns[3]))
            lon.append(float(columns[4]))

        line_no = line_no+1

    f1.close()

    for i in range(1, line_no-1):
        time = datetime.strptime(year[i]+"-"+day[i],"%Y-%j")

        if time >= date_time and prev_time < date_time:
            x1 = time - date_time
            x2 = date_time - prev_time
            h  = time-prev_time

            mars_r = rad[i]*x2/h + rad[i-1]*x1/h 
            mars_lat = lat[i]*x2/h + lat[i-1]*x1/h 
            mars_lon = lon[i]*x2/h + lon[i-1]*x1/h 

        prev_time = time

    return mars_r, mars_lat, mars_lon

def find_earth(date_time, root_dir1):
    f1 = open(root_dir1+'/helioweb/planets/earth.lst', 'r')
    line_no = 0
    year    = []
    day     = []
    rad     = []
    lat     = []
    lon     = []
        
    for line in f1:
        line = line.strip()
        columns = line.split()

        if line_no >=1 :
            year.append(columns[0])
            day.append(columns[1])
            rad.append(float(columns[2]))
            lat.append(float(columns[3]))
            lon.append(float(columns[4]))

        line_no = line_no+1

    f1.close()

    for i in range(1, line_no-1):
        time = datetime.strptime(year[i]+"-"+day[i],"%Y-%j")

        if time >= date_time and prev_time < date_time:
            x1 = time - date_time
            x2 = date_time - prev_time
            h  = time-prev_time

            earth_r = rad[i]*x2/h + rad[i-1]*x1/h 
            earth_lat = lat[i]*x2/h + lat[i-1]*x1/h 
            earth_lon = lon[i]*x2/h + lon[i-1]*x1/h 

        prev_time = time

    return earth_r, earth_lat, earth_lon

def find_psp(date_time, root_dir1):
    f1 = open(root_dir1+'/helioweb/spacecraft/psp.lst', 'r')
    line_no = 0
    year    = []
    day     = []
    rad     = []
    lat     = []
    lon     = []
        
    for line in f1:
        line = line.strip()
        columns = line.split()

        if line_no >=1 :
            year.append(columns[0])
            day.append(columns[1])
            rad.append(float(columns[2]))
            lat.append(float(columns[3]))
            lon.append(float(columns[4]))

        line_no = line_no+1

    f1.close()

    for i in range(1, line_no-1):
        time = datetime.strptime(year[i]+"-"+day[i],"%Y-%j")

        if time >= date_time and prev_time < date_time:
            x1 = time - date_time
            x2 = date_time - prev_time
            h  = time-prev_time

            psp_r = rad[i]*x2/h + rad[i-1]*x1/h 
            psp_lat = lat[i]*x2/h + lat[i-1]*x1/h 
            psp_lon = lon[i]*x2/h + lon[i-1]*x1/h 

        prev_time = time

    return psp_r, psp_lat, psp_lon

def find_venus(date_time, root_dir1):
    f1 = open(root_dir1+'/helioweb/planets/venus.lst', 'r')
    line_no = 0
    year    = []
    day     = []
    rad     = []
    lat     = []
    lon     = []
        
    for line in f1:
        line = line.strip()
        columns = line.split()

        if line_no >=1 :
            year.append(columns[0])
            day.append(columns[1])
            rad.append(float(columns[2]))
            lat.append(float(columns[3]))
            lon.append(float(columns[4]))

        line_no = line_no+1

    f1.close()

    for i in range(1, line_no-1):
        time = datetime.strptime(year[i]+"-"+day[i],"%Y-%j")

        if time >= date_time and prev_time < date_time:
            x1 = time - date_time
            x2 = date_time - prev_time
            h  = time-prev_time

            venus_r = rad[i]*x2/h + rad[i-1]*x1/h 
            venus_lat = lat[i]*x2/h + lat[i-1]*x1/h 
            venus_lon = lon[i]*x2/h + lon[i-1]*x1/h 

        prev_time = time

    return venus_r, venus_lat, venus_lon


def find_STA(date_time, root_dir1):
    f1 = open(root_dir1+'/helioweb/spacecraft/stereoa.lst', 'r')
    line_no = 0
    year    = []
    day     = []
    rad     = []
    lat     = []
    lon     = []
        
    for line in f1:
        line = line.strip()
        columns = line.split()

        if line_no >=1 :
            year.append(columns[0])
            day.append(columns[1])
            rad.append(float(columns[2]))
            lat.append(float(columns[3]))
            lon.append(float(columns[4]))

        line_no = line_no+1

    f1.close()

    for i in range(1, line_no-1):
        time = datetime.strptime(year[i]+"-"+day[i],"%Y-%j")

        if time >= date_time and prev_time < date_time:
            x1 = time - date_time
            x2 = date_time - prev_time
            h  = time-prev_time

            STA_r = rad[i]*x2/h + rad[i-1]*x1/h 
            STA_lat = lat[i]*x2/h + lat[i-1]*x1/h 
            STA_lon = lon[i]*x2/h + lon[i-1]*x1/h 

        prev_time = time

    return STA_r, STA_lat, STA_lon


if __name__ =='__main__':
    now = datetime.now()
    
    root_dir1 = '/data/iPATH/nowcast_module'
    root_dir1 = './'
    
    r, lat, lon = find_mars(now,root_dir1)
    earth_r, earth_lat, earth_lon = find_earth(now,root_dir1)
    r3, lat3, lon3 = find_STA(now,root_dir1)
    r4, lat4, lon4 = find_venus(now,root_dir1)

    print("mars location: r:", r, "latitude:", lat, "longitude:", lon)
    print("earth location: r:", earth_r, "latitude:", earth_lat, "longitude:", earth_lon)
    print("STA location: r:", r3, "latitude:", lat3, "longitude:", lon3)
    print("Venus location: r:", r4, "latitude:", lat4, "longitude:", lon4)
