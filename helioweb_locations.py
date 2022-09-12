import numpy as np
import datetime
from datetime import timedelta
from datetime import datetime

def find_mars(date_time):
    f1 = open('./helioweb/planets/mars.lst', 'r')
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

def find_earth(date_time):
    f1 = open('./helioweb/planets/earth.lst', 'r')
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

def find_psp(date_time):
    f1 = open('./helioweb/spacecraft/psp.lst', 'r')
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

if __name__ =='__main__':
    now = datetime.now()

    r, lat, lon = find_mars(now)
    earth_r, earth_lat, earth_lon = find_earth(now)

    print("mars location: r:", r, "latitude:", lat, "longitude:", lon)
    print("earth location: r:", earth_r, "latitude:", earth_lat, "longitude:", earth_lon)