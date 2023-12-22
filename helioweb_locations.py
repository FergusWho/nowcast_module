import datetime
from datetime import timedelta
from datetime import datetime

def find_location(location, date_time, root_dir1):
    f1 = open(root_dir1 + '/helioweb/' + location + '.lst', 'r')
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

        # find first point for which time[i-1] < t <= time[i]
        if time >= date_time and prev_time < date_time:
            x1 = time - date_time
            x2 = date_time - prev_time
            h  = time-prev_time

            # linear interpolation of coordinates: s*rad[i] + (1-s)*rad[i-1], s = (t - t[i-1])/(t[i] - t[i-1])
            r = rad[i]*x2/h + rad[i-1]*x1/h
            lat = lat[i]*x2/h + lat[i-1]*x1/h
            lon = lon[i]*x2/h + lon[i-1]*x1/h

        prev_time = time

    return r, lat, lon

if __name__ =='__main__':
    now = datetime.now()

    root_dir1 = '.'

    mars_r, mars_lat, mars_lon = find_location('planets/mars', now, root_dir1)
    earth_r, earth_lat, earth_lon = find_location('planets/earth', now, root_dir1)
    venus_r, venus_lat, venus_lon = find_location('planets/venus', now, root_dir1)
    STA_r, STA_lat, STA_lon = find_location('spacecraft/stereoa', now, root_dir1)

    PSP_start_date = datetime.strptime('2018-09-06', '%Y-%m-%d')
    if now > PSP_start_date:
        PSP_r, PSP_lat, PSP_lon = find_location('spacecraft/psp', now, root_dir1)

    print("Mars location: r:", mars_r, "latitude:", mars_lat, "longitude:", mars_lon)
    print("Earth location: r:", earth_r, "latitude:", earth_lat, "longitude:", earth_lon)
    print("Venus location: r:", venus_r, "latitude:", venus_lat, "longitude:", venus_lon)
    print("STA location: r:", STA_r, "latitude:", STA_lat, "longitude:", STA_lon)
    if now > PSP_start_date:
        print("PSP location: r:", PSP_r, "latitude:", PSP_lat, "longitude:", PSP_lon)
