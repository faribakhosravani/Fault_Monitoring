import os
import io
import re
import sys
import time
import glob
import pygmt
import pyproj
import shutil
import shapely
import requests
import datetime
import subprocess
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from obspy import UTCDateTime
from bs4 import BeautifulSoup as Soup
import numpy as np
from pyproj import Geod

#####################################################################
class historical_earthquake:
    def __init__ (self, name, year, mag, mean_lon, mean_lat, df):
        self.name=name
        self.year=year
        self.mag = mag                           
        self.mean_lon = mean_lon
        self.mean_lat = mean_lat
        self.df= df
#####################################################################
class surface_rupture:
    def __init__ (self, name, datetime, 
                  evlon, evlat, evdep, evmag):

        self.name=name
        self.datetime=datetime
        self.evlon = evlon
        self.evlat = evlat
        self.evdep = evdep
        self.evmag = evmag
        self.mean_lon = None
        self.mean_lat = None
        self.df=[]
#####################################################################
class barrier:
    def __init__ (self,name):
        self.name=name
        self.df=[]
        
#####################################################################
class base_fault:
    def __init__ (self,name,lon,lat,pos_width,neg_width,base_az, inset_region, country):
        self.name=name
        self.lon=lon
        self.lat=lat
        self.pos_width=pos_width 
        self.neg_width=neg_width 
        self.base_az=base_az
        self.catalog_df=pd.DataFrame()
        self.last_event_datetime=None
        self.last_updated_plot=datetime.datetime(2000,1,1)
        self.total_length=None
        self.seg_length=[]
        self.beg_str=None
        self.end_str=None
        self.barriers=[]
        self.surface_ruptures=[]
        self.inset_region=inset_region
        self.country = country

#####################################################################
class region:
    def __init__(self, west,east,south,north):
        self.west = west
        self.east = east
        self.south = south
        self.north = north
#####################################################################
class node:
    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude  = latitude

#####################################################################
class catalog:
    usgs_start=None
    usgs_end=None
    irsc_start=None
    irsc_end=None 
    iiees_start=None
    iiees_end=None
   
#####################################################################
def extract_kml_coordinates(kml_file=None):

    Latitude =[]
    Longitude=[]

    with open(kml_file) as data:
        kml_soup = Soup(data, 'lxml-xml') 

    coordinates = kml_soup.find_all('coordinates')
    
    for coord in coordinates:
        coord=coord.text.strip().split()
        lat=[]
        lon=[]
        for xyz in coord:
            xyz=xyz.split(",")
            if len(xyz)>1:
                lon.append(float(xyz[0]))
                lat.append(float(xyz[1]))
        
        Latitude.append(lat)
        Longitude.append(lon)

    return Longitude, Latitude
 
#####################################################################

def make_keystroke(last_event_datetime=None):
    global keyf

    byear="{0:04d}".format(last_event_datetime.year)
    bmonth="{0:02d}".format(last_event_datetime.month)
    bday="{0:02d}".format(last_event_datetime.day)
    t2=UTCDateTime.now()
    if t2.date == last_event_datetime.date:
        t2+=3600*24

    eyear="{0:04d}".format(t2.year)
    emonth="{0:02d}".format(t2.month)
    eday="{0:02d}".format(t2.day)

    y11=byear[0]
    y12=byear[1]
    y13=byear[2]
    y14=byear[3]
    m11=bmonth[0]
    m12=bmonth[1]
    d11=bday[0]
    d12=bday[1]

    y21=eyear[0]
    y22=eyear[1]
    y23=eyear[2]
    y24=eyear[3]
    m21=emonth[0]
    m22=emonth[1]
    d21=eday[0]
    d22=eday[1]

    keyf = io.StringIO(
    f"""key <space>\nkey <space>\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow
    key {y11}\nkey {y12}\nkey {y13}\nkey {y14}\nkey /
    key {m11}\nkey {m12}\nkey /\nkey {d11}\nkey {d12}
    key Down Arrow\n
    key {y21}\nkey {y22}\nkey {y23}\nkey {y24}\nkey /
    key {m21}\nkey {m22}\nkey /\nkey {d21}\nkey {d22}
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey ^J\nkey <space>\nkey <space>
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey Down Arrow\nkey Down Arrow\nkey Down Arrow
    key Down Arrow\nkey ^J\nkey <space>\nkey <space>\nkey <space>
    key <space>\nkey <space>\nkey <space>\nkey <space>\nkey <space>
    key <space>\nkey <space>\nkey <space>\nkey q\nkey ^J
    """)

    with open('keystrokes', 'w') as fd:
      keyf.seek(0)
      shutil.copyfileobj(keyf, fd)


#####################################################################

def download_file(url=None, local_filename=None):
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)

    return r.status_code

#####################################################################
def get_last_iiees_event(iiees_db_file=None):


    with open(iiees_db_file,'r') as f:
        contents = f.readlines()

    last_line = contents[-1].split()

    if len(last_line) > 5:
        last_event_datetime=UTCDateTime(last_line[0]+"T"+last_line[1])
        return last_event_datetime
    else:
        print(f"\t ... Improper IIEES catalog at {UTCDateTime.now()}.")

#####################################################################
def get_last_irsc_event(irsc_db_file=None):


    with open(irsc_db_file,'r') as f:
        contents = f.readlines()

    last_line = contents[-1].split()

    #print(last_line)

    if len(last_line) > 5:
        last_event_datetime=UTCDateTime(last_line[2]+"T"+last_line[3])

        return last_event_datetime
    else:
        print(f"\t ... Improper IIEES catalog at {UTCDateTime.now()}.")

#####################################################################

def add2iiees(downloaded_file=None, 
              last_event_datetime=None,
              iiees_db_file=None ):

    add_list=[]
    with open (downloaded_file, 'r' ) as f:
        contents= f.readlines()

    for line in contents:
        if "yyyy" in line or "----------" in line:
            continue

        cline=line.strip().split()
        cdt=UTCDateTime(cline[0]+"T"+cline[1])

        if cdt > last_event_datetime:
            add_list.append(line)
        
    if len(add_list)> 0:
        found_new_iiees_event = True
        with open (iiees_db_file,'a') as f:
            for line in  add_list:
                f.write(line)
    else:
        print(f"\t ... No new IIEES event was found at {UTCDateTime.now()}")


#####################################################################

def add2irsc (downloaded_file=None, 
              last_event_datetime=None,
              irsc_db_file=None ):

    add_list=[]
    with open (downloaded_file, 'r' ) as f:
        contents= f.readlines()

    # %s – seconds since 1970-01-01 00:00:00 UTC
    for line in contents:
        if "/" not in line:
            continue
        cline=line.split()
        cdt=UTCDateTime(cline[2]+"T"+cline[3])
        sf1970=str(int(cdt.timestamp))

        if cdt > last_event_datetime:
            #add_list.append(" ".join(sf1970, cline[1:]))
            add_list.append(" ".join([sf1970]+ cline[1:]))

    if len(add_list)> 0:
        with open (irsc_db_file,'a') as f:
            for line in  add_list:
                f.write(line+"\n")
    else:
        print(f"\t ... No new IRSC event was found at {UTCDateTime.now()}")

#####################################################################

def update_irsc_catalog(irsc_db_file=None):

    t1 = get_last_irsc_event(irsc_db_file=irsc_db_file)
    t2=t1+10*24*3600
    now=UTCDateTime.now()
    t2=min(t2,now)


    url="http://irsc.ut.ac.ir/bulletin.php"

    data = {"start_Y":"{0:04d}".format(t1.year), 
            "start_M":"{0:02d}".format(t1.month), 
            "start_D":"{0:02d}".format(t1.day),
            "start_H":"{0:02d}".format(t1.hour), 
            "end_Y":"{0:04d}".format(t2.year), 
            "end_M":"{0:02d}".format(t2.month), 
            "end_D":"{0:02d}".format(t2.day),
            "end_H":"{0:02d}".format(t2.hour),
            "action":"Search"  
            }
    try:
        response = requests.post(url, data=data)
    except:
        print (f"\t ... Unsuccessful IRSC at {UTCDateTime.now()} ")
        return

    decoded_content=response.content.decode("utf-8")
            
    irsc_file_found=False
    for word in decoded_content.split():
        if "txt" in word and "bul" in word:
            irsc_file_found=True
            irsc_file=word.split(">")[0]

    if irsc_file_found:
        irsc_file_link="http://irsc.ut.ac.ir/"+irsc_file
        local_filename = irsc_file.split("/")[-1]
        status=download_file(url = irsc_file_link, 
                    local_filename = local_filename)

        if status == 200 :

            add2irsc(downloaded_file=local_filename, 
                      last_event_datetime=t1,
                      irsc_db_file=irsc_db_file)

            os.remove(local_filename) 
            print(f"\t ... IRSC database updated at {UTCDateTime.now()}")

        else:
            print(f"\t ... Unsuccessful {irsc_file_link} at {UTCDateTime.now()}")
    else:
        print (f"\t ... No IRSC file link was found at {UTCDateTime.now()} ")
        return


#####################################################################

def update_iiees_catalog(iiees_db_file=None):

    url="http://www.iiees.ac.ir/en/eqcatalog/"

    last_event_datetime = get_last_iiees_event(iiees_db_file=iiees_db_file)
    make_keystroke( last_event_datetime=last_event_datetime)
    cmd=f"lynx -crawl  -cmd_script=keystrokes {url} ".split() 
    reaesc = re.compile(r'\x1b[^m]*m')
    result = subprocess.run(cmd, capture_output=True)
    new_text = reaesc.sub('', result.stdout.decode("utf-8")) 
    new_text_splitted=new_text.split()

    urlFound=False
    for line in  new_text_splitted:
        if "quid" in line:
            burl=line.find("http")
            eurl=line.find("=list")+5
            urlFile=line[burl:eurl]
            urlFound=True

    if urlFound:
        local_filename = urlFile.split('=')[-1]+".txt"

        status=download_file(url=urlFile, local_filename=local_filename)
        if status == 200 :

            add2iiees(downloaded_file=local_filename, 
                      last_event_datetime=last_event_datetime,
                      iiees_db_file=iiees_db_file 
                     )

            os.remove(local_filename) 
            print(f"\t ... IIEES database updated at {UTCDateTime.now()}")

        else:
            print(f"\t ... Unsuccessful {urlFile} at {UTCDateTime.now()}")

    else:
        print(f"\t ... No link for file was found at {UTCDateTime.now()}")
#####################################################################
#####################################################################
def get_polygon(lons=None,
                lats=None, 
                pos_width=None,
                neg_width=None,
                azimuth  =None ):

    
    # check lat and lon for flipping.
    geodesic = pyproj.Geod(ellps='WGS84')
    long1=lons[0]
    lat1=lats[0]
    long2=lons[-1]
    lat2=lats[-1]
    fwd_azimuth,back_azimuth,distance = \
          geodesic.inv(long1, lat1, long2, lat2)

#####################################################################
def read_usgs (usgs_file=None):
    
    global usgs_df

    usgs_df=pd.read_csv(usgs_file,
                        sep=",",
                        usecols=[2,1,3,4,0], 
                        index_col=False)

    usgs_df=usgs_df[(usgs_df["longitude"] > seismicity_region.west)  & 
                    (usgs_df["longitude"] < seismicity_region.east)  & 
                    (usgs_df["latitude"]  > seismicity_region.south) & 
                    (usgs_df["latitude"]  < seismicity_region.north)
                    ]

    usgs_df = usgs_df [["longitude","latitude","depth","mag","time"]]    
    usgs_df['time'] = pd.to_datetime(usgs_df['time'])

#####################################################################
def read_irsc (irsc_db_file=None):
    
    global irsc_df

    names=["ts","sn","Date","Time","latitude","longitude","depth","mag"]
    irsc_df=pd.read_csv(irsc_db_file,
                        sep="\\s+",
                        usecols=[0,1,2,3,4,5,6,7],
                        names=names,
                        index_col=False)

    irsc_df["time"]=irsc_df["Date"]+"T"+irsc_df["Time"]
    irsc_df = irsc_df [["longitude","latitude","depth","mag","time"]]
    irsc_df['time'] = pd.to_datetime(irsc_df['time'])

#####################################################################
def read_iiees (iiees_db_file=None):

    global iiees_df

    with open(iiees_db_file,'r') as f:
        contents = f.readlines()

    Date=[]
    Time=[]
    latitude=[]
    longitude=[]
    depth=[]
    mag=[]

    names=["Date","Time","latitude","longitude","depth","mag"]

    try:
        for line in contents:
            if "yyyy" in line or "----------" in line:
                continue

            line=line.strip().split()
            Date.append(line[0])
            Time.append(line[1])
            latitude.append(float(line[3]))
            longitude.append(float(line[4]))
            depth.append(float(line[5]))
            trimag=re.sub("[^.0-9]","",line[6])
            if trimag.replace(".","").isdigit():
                mag.append(float(re.sub("[^.0-9]","",line[6])))
            else:
                mag.append(0.0)


    except:
        print ("\t ... No proper IIEES database!")

    iiees_df = pd.DataFrame({"Date":Date,
                             "Time":Time,
                             "latitude":latitude,
                             "longitude":longitude,
                             "depth":depth,
                             "mag":mag
                            })
                            
    if len(iiees_df) ==0:
        iiees_df["time"]=iiees_df["Date"]
    else:
        iiees_df["time"]=iiees_df["Date"]+"T"+iiees_df["Time"]

    iiees_df = iiees_df [["longitude","latitude","depth","mag","time"]]
    iiees_df['time'] = pd.to_datetime(iiees_df['time'])


#####################################################################
def file_paths():

    global home
    global seismicity_region
    global usgs_db_file
    global isc_db_file
    global irsc_db_file
    global iiees_db_file
    global mag_legend
    global eq_deep_limit
    global gsiFaultFile
    global treshold_historical_mag
    global zagrosRockslideFile
    global rockslidesZones
    global force_update_seconds
    global emergency_plot
    global topo_grid_file_15s

    emergency_plot=[]
    mag_legend = [4,5,6,7]
    eq_deep_limit = 60.0
    force_update_seconds = 10*3600

    treshold_historical_mag = 5.9

    seismicity_region = region(25,65,10,50)
    rockslidesZones=["SEIMARE", "ZAGROS" ]

    home= os.path.expanduser("~")

    gsiFaultFile = os.path.join(home,"GMTdata","Iran_GSI_Faults.xyz")
    zagrosRockslideFile = os.path.join(home,"GMTdata","Zagros_Rockslid_Polygones.gmt")

    usgs_db_file = os.path.join(home,"GMTdata","USGS",
                                "query_1600_open.usgs")

    isc_db_file = os.path.join(home,"GMTdata","ISC",
                                "ISC_1600_open.isc")

    irsc_db_file = os.path.join(home,"GMTdata","IRSN",
                                "IRSN_TEH_IRN.txt")

    iiees_db_file=os.path.join(home,"GMTdata","IIEES",
                                "IIEES_catalog.txt")

    topo_grid_file_15s=os.path.join(home,"GMTdata",
        "gebco_2024_n45.0_s20.0_w25.0_e80.0.nc")
    

#####################################################################
def concat_usgs_irsc():

    global usgs_irsc_df

    irsc_first_date = irsc_df.iloc[0].time.tz_localize('utc')

    catalog.usgs_start = usgs_df.iloc[0].time.tz_localize(None)
    catalog.usgs_end   = usgs_df.iloc[-1].time.tz_localize(None)

    catalog.irsc_start = irsc_df.iloc[0].time
    catalog.irsc_end   = irsc_df.iloc[-1].time

    usgs_pre2006 = usgs_df[usgs_df.time < irsc_first_date]
    dfs=[usgs_pre2006, irsc_df ]

    usgs_irsc_df= pd.concat(dfs,ignore_index=True,sort=False)

    del usgs_pre2006
    del globals()['irsc_df']
    ##del globals()['usgs_df']

#####################################################################
def concat_usgs_irsc_iiees():

    global usgs_irsc_iiees_df

    # difference between time stamp of IRSC and IIEES
    irsc_last_date  = usgs_irsc_df.iloc[-1].time
    catalog.iiees_start = iiees_df.iloc[0].time
    catalog.iiees_end   = iiees_df.iloc[-1].time

    iiees_post_irsc = iiees_df[iiees_df.time > irsc_last_date]
    dfs=[usgs_irsc_df, iiees_post_irsc ]

    usgs_irsc_iiees_df= pd.concat(dfs,ignore_index=True,sort=False)

    del iiees_post_irsc
    del globals()['iiees_df']


#####################################################################

def assign_base_fault_dfs():

    global tdf

    for cdb in [ref_eq_df]: 
        
        for cbase_fault in base_faults:
            clons=cbase_fault.lon
            clats=cbase_fault.lat

            width=[ cbase_fault.neg_width, 
                    cbase_fault.pos_width ]
            tdf=pd.DataFrame()

            cbase_fault.beg_str, cbase_fault.end_str = \
                get_be_str(lon1=clons[0],
                           lat1=clats[0], 
                           lon2=clons[-1],  
                           lat2=clats[-1])


            cumul_segs_length = 0.0     
         
            for i in range(len(clons)-1):
                
                try:
                    segdf = pygmt.project(
                            data=cdb,
                            center=[clons[i],clats[i]], 
                            endpoint=[clons[i+1],clats[i+1]],
                            width=width,
                            length=["w"],
                            unit=True 
                            )
                    segdf[5]=segdf[5]+cumul_segs_length
                    # fix for length
                    tdf = pd.concat([tdf,segdf], ignore_index=True)
                except:
                    pass
                    #print("\t ... No event in the profile segment!")

                # find segment length and assign
                az12,az21,dist_km = geo_distaz(lon1=clons[i],
                                               lat1=clats[i], 
                                               lon2=clons[i+1],  
                                               lat2=clats[i+1])
                 
                cumul_segs_length += dist_km 

            cbase_fault.total_length=cumul_segs_length
             
            tdf = tdf.drop_duplicates()
            if len(tdf.index) > 0:
                tdf=tdf.sort_values(4, ignore_index=True)
                cbase_fault.catalog_df = tdf
                cbase_fault.last_event_datetime = \
                    pd.to_datetime( tdf.iloc[-1][4])


#####################################################################
def get_be_str(lon1=None, lat1=None, lon2=None, lat2=None):

    g = Geod(ellps='clrk66') # Use Clarke 1866 ellipsoid.
    az12,az21,dist = g.inv(lon1, lat1, lon2, lat2)
    
    es =["N","NE","NE","NE","NE","E","E","SE",
         "SE","SE","SE","S","S","SW","SW","SW",
         "SW","W","W","NW","NW","NW","NW","N"]

    bs =["S","SW","SW","SW","SW","W","W","NW",
         "NW","NW","NW","N","N","NE","NE","NE",
         "NE","E","E","SE","SE","SE","SE","S"]

    az_index = int(np.floor(az12/15.))

    return bs[az_index],es[az_index] 

#####################################################################

def geo_distaz(lon1=None,lat1=None, lon2=None,  lat2=None):

    g = Geod(ellps='clrk66') # Use Clarke 1866 ellipsoid.
    az12,az21,dist = g.inv(lon1, lat1, lon2, lat2)

    return az12,az21,dist/1000.0

#####################################################################

def get_region(lons=None, lats=None): 

    aspect_ratio = 1.5

    del_lon=max(lons) - min(lons) 
    del_lat=max(lats) - min(lats) 
    
    max_dels = max ([del_lon, del_lat])
    if max_dels >= 4:
        jump=1.0
    elif max_dels >= 2 and max_dels <4:
        jump=0.5
    else:
        jump=0.25
    
    llon=np.floor(min(lons)/jump)*jump
    rlon=np.ceil(max(lons)/jump)*jump
    dlat=np.floor(min(lats)/jump)*jump
    ulat=np.ceil(max(lats)/jump)*jump

    del_lon=rlon-llon
    del_lat=ulat-dlat

        
    while  del_lat / del_lon  > aspect_ratio:
        llon-=jump
        rlon+=jump
        del_lon=rlon-llon

    while del_lon / del_lat > aspect_ratio:
        dlat-=jump
        ulat+=jump
        del_lat=ulat-dlat

    #Now check if the distances are more than 2 degrees 
    if rlon - max (lons) > 2:
        rlon= np.ceil(max (lons) +2)

    if  min (lons) - llon > 2:
        llon= np.floor(min (lons)-2)

    if ulat - max (lats) > 2:
        ulat= np.ceil(max (lats) +2)

    if  min (lats) - dlat > 2:
        dlat= np.floor(min (lats)-2)

    region = [llon, rlon, dlat, ulat]

    # location of scale 
    x_scale= (llon+ rlon)/2
    y_scale= dlat+ (ulat- dlat)/20
    xy_scale=[x_scale,y_scale ]

    # location of earthquake legend
    x_seis_legend = llon + (rlon - llon)/20
    y_seis_legend = ulat - (ulat - dlat)/20
    xy_seis_legend = [x_seis_legend,y_seis_legend]

    area_deg = (rlon-llon)*(ulat-dlat)

    return region, xy_scale, xy_seis_legend, area_deg

#####################################################################
def plot_monitor_maps ():
    
    print (f"\t ... Enter plot_monitor_maps: {UTCDateTime.now()}")
    projection="M15c"

    if len(emergency_plot) > 0:
        caseplots = [ emergency_plot ]
    else:
        caseplots = [ base_fault_toplot, base_fault_toupdate_plot ]

    for castplot in caseplots:
        for cbase_fault in base_faults:
            if cbase_fault.name in castplot:
                if len(cbase_fault.catalog_df.index) >0:
                    plot_plan_maps(cbase_fault = cbase_fault,
                                    projection = projection)

                    plot_time_profile(cbase_fault=cbase_fault)

                    cbase_fault.last_updated_plot = common_now
                    
                else:
                    print (f"\t ... Empty event df for {cbase_fault.name}")

            else:
                print (f"\t ... No new event for {cbase_fault.name}")

    print (f"\t ... Exit plot_monitor_maps: {UTCDateTime.now()}")

#####################################################################
def get_db_times (xtime=None):

    #print("I- min(xtime): ", min(xtime) )
    #print("II- : catalog.irsc_end: ", catalog.irsc_end )
    #print("III- : catalog.irsc_start: ", catalog.irsc_start  )
    #print("IV- : catalog.usgs_start: ", catalog.usgs_start )

    if min(xtime) >= catalog.irsc_end:
        t_iiees= min(xtime)
        t_irsc = catalog.irsc_start
        t_usgs = catalog.usgs_start
    elif min(xtime) >= catalog.irsc_start:
        t_irsc= min(xtime)
        t_iiees = catalog.irsc_end
        t_usgs = catalog.usgs_start
    elif min(xtime) >= catalog.usgs_start:
        t_usgs= min(xtime)
        t_iiees = catalog.irsc_end
        t_irsc = catalog.irsc_start
    elif min(xtime) < catalog.usgs_start:
        t_usgs= min(xtime)
        t_iiees = catalog.irsc_end
        t_irsc = catalog.irsc_start

    
    return t_usgs, t_irsc, t_iiees
#####################################################################

def get_time_wondows():
    
    legend_coef=.95
    tw_start=[]
    tw_title=[]
    tw_start_TS= []
    tw_legend  = []
    tw_legend_TS = []

    deldays=[1,10,30]
    for days in deldays:
        dd = datetime.timedelta(days=days)
        dd_leg = datetime.timedelta(days=days*legend_coef)
        tw_start.append(common_now -dd )
        tw_legend.append(common_now - dd_leg )
        if days == 1:
            tw_title.append(f"{days}-day")
        else:
            tw_title.append(f"{days}-days")

    delyears=[1,10,30,60]
    for years in delyears:
        dd = datetime.timedelta(days=years*365)
        dd_leg = datetime.timedelta(days=years*365*legend_coef)
        tw_start.append(common_now -dd )
        tw_legend.append(common_now - dd_leg )
        if years == 1:
            tw_title.append(f"{years}-year")
        else:
            tw_title.append(f"{years}-years")

    d1900=datetime.datetime(1900,1,1)
    dyears=round((common_now-d1900).days /365)

    dd_leg = datetime.timedelta(days=(common_now-d1900).days*legend_coef)
    tw_start.append(d1900)
    tw_title.append(f"{dyears}-years")
    tw_legend.append(common_now - dd_leg )

    for i in range(len(tw_start)):
        tw_start_TS.append(pd.Timestamp(tw_start[i]))
        tw_legend_TS.append(pd.Timestamp(tw_legend[i]))
        
    return tw_start_TS, tw_legend_TS, tw_start, tw_title

#####################################################################

def plot_time_profile(cbase_fault=None):

    global cdata, tw_start_TS

    data = cbase_fault.catalog_df
    data.iloc[:,4]=[pd.Timestamp(v) for v in data[4]]
    kink_list = cbase_fault.seg_length[:-1]

    #cbarriers=[]
    #for i in range(len(cbase_fault.barriers)):
    #    cbarriers.append(cbase_fault.barriers[i].name)

    xt=data[4]
    t_usgs, t_irsc, t_iiees = get_db_times (xtime=xt)

    tw_start_TS, tw_legend_TS, tw_start, tw_title = get_time_wondows()

    y_legend = cbase_fault.total_length * .95
    lat_legend = [y_legend for n in range(len(mag_legend))]

    for k in range(len(tw_start)):


        cdata=data[data[4]>tw_start_TS[k]]

        for j in range(2):

            if j == 0:
                plot_time_section=True
                region=[tw_start[k], common_now, 0,cbase_fault.total_length]
                x=cdata[4]
                y=cdata[5]
                figName=f"{cbase_fault.name}_TS_{k}.png"
                lon_legend = [tw_legend_TS[k] for n in range(len(mag_legend))]
                cxvar="Date"
            else:
                plot_time_section=False
                region=[0, eq_deep_limit, 0,cbase_fault.total_length]
                x=cdata[2]
                y=cdata[5]
                figName=f"{cbase_fault.name}_DS_{k}.png"
                lon_legend = [ (1-0.95)*eq_deep_limit for n in range(len(mag_legend))]
                cxvar="Depth"

            magdf=pd.DataFrame({"lon_legend":lon_legend,
                                "lat_legend":lat_legend,
                                "mag_legend":mag_legend})

            fig = pygmt.Figure()
            pygmt.makecpt(cmap="jet", series=[0, eq_deep_limit])
    
            fsystem = cbase_fault.name.upper().replace("_","-")
            ts=tw_start_TS[k].isoformat().split('.')[0]
            te=common_now.isoformat().split('.')[0]
            title=f"Figure {k+1}. {tw_title[k]} seismicity, {ts} to {te} (UTC)"
            frame=[f"xaf+l{cxvar}",f"yaf+lDistance along the {fsystem} system (km)", f"WSne+t{title}"]
            fig.basemap( projection="X15c/10c",
                         region=region,
                         frame=frame)
            
            # mark kink lines
            for cykink in kink_list:
                xseg=region[0:2]
                yseg=[cykink for x in xseg ]
                fig.plot(x=xseg, 
                         y=yseg, 
                         pen=".1p,yellow"
                        )


            # write section names along the left axis
            fig.text(x=region[0], 
                     y=0, 
                     text= cbase_fault.beg_str, 
                     font="11p,NewCenturySchlbk-Bold,blue",
                     justify="ML", 
                     angle=90,
                     fill="white",
                     clearance="+tO",
                     pen="0.25p,black,solid",
                     no_clip=True,
                     offset="-0.70c/0c")

            fig.text(x=region[0], 
                     y=cbase_fault.total_length, 
                     text= cbase_fault.end_str, 
                     font="11p,NewCenturySchlbk-Bold,blue",
                     justify="MR", 
                     angle=90,
                     fill="white",
                     clearance="+tO",
                     pen="0.25p,black,solid",
                     no_clip=True,
                     offset="-0.70c/0.0c")

            if plot_time_section:

                fig.text(x=t_irsc, 
                         y=0, 
                         text= "IRSC", 
                         justify="BL", 
                         angle=90,
                         no_clip=False,
                         font="8p,Helvetica,red",
                         offset="0.15c/0.0c")

                fig.text(x=t_iiees, 
                         y=0, 
                         text= "IIEES", 
                         justify="BL", 
                         angle=90,
                         no_clip=False,
                         font="8p,Helvetica,red",
                         offset="0.15c/0.0c")

                # 
                fig.text(x=t_usgs, 
                         y=0, 
                         text= "ISC", 
                         justify="BL", 
                         angle=90,
                         no_clip=False,
                         font="8p,Helvetica,red",
                         offset="0.15c/0.0c")


            # plot earthquakes
            if len(x) > 0:
                fig.plot(x=x, 
                         y=y, 
                         style="cc", 
                         size=0.005 * 2**cdata[3],
                         pen=".25p", 
                         fill=cdata[2],
                         cmap=True
                        )

            # plot legend
            fig.plot(
                     x=magdf.lon_legend,
                     y=magdf.lat_legend,
                     size=0.005 * 2**magdf.mag_legend,
                     style="cc",
                     pen="black",
                    )

            # write legend text
            fig.text(x=lon_legend[0], 
                     y=lat_legend[0], 
                     text= "M "+str(mag_legend[0])+":"+str(mag_legend[-1]),
                     justify="ML", 
                     #fill="white",
                     clearance="+tO",
                     pen="0.35p,black,solid",
                     no_clip=True,
                     offset="0.50c/0c")


            # plot barriers
            for i in range(len(cbase_fault.barriers)):

                if len(cbase_fault.barriers[i].df.index) ==0:
                    continue

                yb= cbase_fault.barriers[i].df[2]
            
                if plot_time_section:
                    xb =[common_now] * len(yb)
                else:
                    xb =[eq_deep_limit] * len(yb)


                yt=np.average(yb)
                ctext= cbase_fault.barriers[i].name[0]

                fig.plot(x=xb,
                         y=yb,
                         pen="4p,red", 
                         no_clip = True,
                         offset = ".2c/0c"
                        )

                fig.text(x=xb[0], 
                         y=yt, 
                         text=ctext, 
                         justify="MC", 
                         fill="yellow",
                         clearance="+tO",
                         pen="0.25p,black,solid",
                         angle=90,
                         no_clip=True,
                         offset="0.4c/0c")


            # plot surface surface ruptures
            for i in range(len(cbase_fault.surface_ruptures)):

                if len(cbase_fault.surface_ruptures[i].df.index) ==0:
                    continue

                yb= cbase_fault.surface_ruptures[i].df[2]
            
                if plot_time_section:
                    
                    cdatetime= max(tw_start[k],cbase_fault.surface_ruptures[i].datetime)
                    if type(cdatetime) == UTCDateTime:
                        cdatetime = cdatetime.datetime
                        #print("======cdatetime========:",cdatetime)
                    xb = [cdatetime] * len(yb)
                else:
                    xb =[cbase_fault.surface_ruptures[i].evdep] * len(yb)


                yt=np.average(yb)
                ctext= cbase_fault.surface_ruptures[i].name[0]

                fig.plot(x=xb,
                         y=yb,
                         pen="4p,magenta", 
                         no_clip = True,
                         offset = "0c/0c"
                        )


            if j == 0:
                fig.colorbar(frame="af+lDepth (km)")

            fig.savefig(fname=figName)

#####################################################################

def plot_plan_maps(cbase_fault=None, 
                    projection=None):

    global data, region 

    cbarriers=[]
    scale_length=np.floor(cbase_fault.total_length /300)*100
    scale_length=max(100,scale_length)
    inset_region = cbase_fault.inset_region
    country = cbase_fault.country


    csurface_ruptures=[]
    for i in range(len(cbase_fault.surface_ruptures)):
        csurface_ruptures.append(cbase_fault.surface_ruptures[i].name)
    
    for i in range(len(cbase_fault.barriers)):
        cbarriers.append(cbase_fault.barriers[i].name)
    
    region, xy_scale, xy_seis_legend, area_deg = \
        get_region(lons=cbase_fault.lon, lats=cbase_fault.lat) 

    tw_start_TS, tw_legend_TS, tw_start, tw_title = get_time_wondows()

    if use_local_grid:
        tmp_local_grid = pygmt.grdcut(
                grid=topo_grid_file_15s, 
                region=region
                )
        
        # Resample based on area_deg
        if 20 < area_deg <= 64:
            image_resolution ="30s"
            print("\t ... Change in grid resolution to 30s.")
            tmp_local_grid = pygmt.grdsample(grid=tmp_local_grid, 
                                             spacing=["30+s","30+s"])
        elif 64 < area_deg :
            print("\t ... Change in grid resolution to 1m.")
            tmp_local_grid = pygmt.grdsample(grid=tmp_local_grid, 
                                             spacing=["1+m","1+m"])


    # find surface ruptures that fall in the region            
    allSurfaceRutureNames=sorted(set(surface_rupture_gdf.surface_rupture.array))

    region_surface_ruptur_names=[]
    for sr_name in allSurfaceRutureNames:
        lonary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lon
        latary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lat
        mean_lon = np.mean(lonary)
        mean_lat = np.mean(latary)
        if region[0] <= mean_lon <= region[1] and \
           region[2] <= mean_lat <= region[3]:
            region_surface_ruptur_names.append(sr_name)

    #print(region_surface_ruptur_names)

    # find historical events that fall in the area
    region_historical_events=[]
    for i, historical_earthquake in enumerate(historical_earthquakes):
        if historical_earthquake.mag > treshold_historical_mag:
            mean_lon=historical_earthquake.mean_lon
            mean_lat=historical_earthquake.mean_lat
            if region[0] <= mean_lon <= region[1] and \
               region[2] <= mean_lat <= region[3]:
                region_historical_events.append(i)
    #print("region_historical_events: ",region_historical_events)

    for j in range(3):
        #print("\t  1:",j,datetime.datetime.now().isoformat() )
        if j==0:
            ctitle= "Depth (km)"
            data = cbase_fault.catalog_df[[0,1,2,3,4]]
            data.iloc[:,4]=[pd.Timestamp(v) for v in data[4]]
            num_iter=len(tw_start)
        elif j==1:
            ctitle= "Depth (km)"
            subreg=ref_eq_df[(ref_eq_df.longitude >= region[0]) & 
                             (ref_eq_df.longitude <= region[1]) &
                             (ref_eq_df.latitude  >= region[2]) &
                             (ref_eq_df.latitude  <= region[3])
                            ]

            data =  subreg[["longitude","latitude","depth","mag","time"]].\
            rename(columns={"longitude":0,"latitude":1,"depth":2, "mag":3,"time":4} )
            data.iloc[:,4]=[pd.Timestamp(v) for v in data[4]]
            num_iter=len(tw_start)
        else:
            ctitle= "Elevation (m)"
            num_iter=1
        #print("\t  2:",j,datetime.datetime.now().isoformat() )


        # here the fixation should be made over j
        for k in range(num_iter):
            if j==0:
                figName=f"{cbase_fault.name}_stripe_{k}.png"
            elif j==1:
                figName=f"{cbase_fault.name}_seis_{k}.png"
            else:
                figName=f"{cbase_fault.name}_legend.png"

            fig = pygmt.Figure()

            if plot_background:
                if area_deg <= 20:
                    image_resolution ="15s"
                elif 20 < area_deg <= 64:
                    image_resolution ="30s"
                elif 64 < area_deg <= 144:
                    image_resolution ="01m"
                else:
                    image_resolution ="01m"

                try:
                    if use_local_grid:
                        grid = tmp_local_grid
                    else:
                        grid = pygmt.datasets.load_earth_relief(
                                resolution=image_resolution, 
                                region=region
                                )
                except:
                    grid = "@earth_relief_01m_g"

            #print("\t  3:",j,k,datetime.datetime.now().isoformat() )
        
            azi="0/45"
            nor="t1"
            if j==2:
                if plot_background:
                    shade = pygmt.grdgradient(grid=grid, 
                                              azimuth=azi, 
                                              normalize=nor)
                else:
                    shade = None 
            else:
                shade = None 


            #print("\t  4:",j,k,datetime.datetime.now().isoformat() )
            if plot_background:           
                fig.grdimage( region=region,
                              grid=grid,
                              shading=shade,
                              cmap="terra",
                              projection=projection,
                              frame=True,
                            )
                        
            map_scale=f"jBC+w{scale_length}k+o0c/.75c+f"

            fsystem = cbase_fault.name.upper().replace("_","-")
            ts=tw_start_TS[k].isoformat().split('.')[0]
            te=common_now.isoformat().split('.')[0]
            title=f"Figure {k+1}. {tw_title[k]} seismicity, {ts} to {te} (UTC)"
            if j==2:
                title=""
            frame=[f"af", f"WSne+t{title}"]

            fig.basemap(region=region, 
                        projection=projection, 
                        map_scale=map_scale,
                        frame=frame)
        
            fig.coast(shorelines="0.5p,black", 
                      resolution="f",
                      borders="a",
                      rivers=2)

            #print("\t  5:",j,k,datetime.datetime.now().isoformat() )

            # plot section
            fig.plot(
                region=region,
                projection=projection,
                x=cbase_fault.lon,
                y=cbase_fault.lat,
                pen="2p,yellow",
            )

            #print("\t  6:",j,k,datetime.datetime.now().isoformat() )
            # plot barriers
            for brr_name in cbarriers:
                lonary=barrier_gdf[barrier_gdf["barrier"]==brr_name].lon
                latary=barrier_gdf[barrier_gdf["barrier"]==brr_name].lat

                fig.plot(
                    region=region,
                    projection=projection,
                    x=lonary,
                    y=latary,
                    pen="2p,red",
                )

                fig.text(x=np.average(lonary), 
                         y=np.average(latary), 
                         text=brr_name[0], 
                         justify="MC", 
                         fill="yellow",
                         clearance="+tO",
                         pen="0.25p,black,solid",
                         no_clip=True,
                         offset="-0.50c/0c")

            #print("\t  7:",j,k,datetime.datetime.now().isoformat() )

            # plot GSI faults on header map
            if j==2:
                fig.plot(data=gsiFaultFile,
                         region=region,
                         projection=projection,
                         pen="0.75p,white"
                        )

            # plot rockslides
            if j>0:
                if cbase_fault.name in rockslidesZones:
                    fig.plot(data=zagrosRockslideFile,
                             region=region,
                             projection=projection,
                             pen="1p,red",
                             fill="red"
                            )




            # plot surface ruptures
            if j==0:
                # plot stripe surface ruptures
                for sr_name in csurface_ruptures:
                    lonary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lon
                    latary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lat

                    fig.plot(
                        region=region,
                        projection=projection,
                        x=lonary,
                        y=latary,
                        pen="2p,magenta",
                    )
            else:
                #print("\t  8:",j,k,datetime.datetime.now().isoformat() )
                # plot only those that fall in the region
                for sr_name in region_surface_ruptur_names:
                    lonary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lon
                    latary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lat

                    fig.plot(
                        region=region,
                        projection=projection,
                        x=lonary,
                        y=latary,
                        pen="2p,magenta",
                    )
                #print("\t  9:",j,k,datetime.datetime.now().isoformat() )
 
                # plot historical events
                for sn in region_historical_events:
                    lonary=historical_earthquakes[sn].df.lon
                    latary=historical_earthquakes[sn].df.lat
                    txtlon=historical_earthquakes[sn].mean_lon
                    txtlat=historical_earthquakes[sn].mean_lat
                    #ctext =historical_earthquakes[sn].name
                    ctext =" ".join(historical_earthquakes[sn].name.split()[:2])
                    
                    #print("\t 10:",j,k,datetime.datetime.now().isoformat() )

                    fig.plot(region=region,
                             projection=projection,
                             x=lonary,
                             y=latary,
                             pen="1.5p,219/0/91"
                            )

                    #print("\t 11:",j,k,datetime.datetime.now().isoformat() )

                    # write historical earthquake text
                    fig.text(x=txtlon, 
                             y=txtlat, 
                             font="10p,Helvetica,219/0/91",
                             text= ctext, 
                             justify="MC" 
                            )

                    #print("\t 12:",j,k,datetime.datetime.now().isoformat() )


            # write section text
            fig.text(x=cbase_fault.lon[0], 
                     y=cbase_fault.lat[0], 
                     font="12p,NewCenturySchlbk-Bold,blue",
                     text= cbase_fault.beg_str, 
                     justify="ML", 
                     fill="white",
                     clearance="+tO",
                     pen="0.35p,black,solid",
                     no_clip=True,
                     offset="-0.50c/0c")

            # write section text
            #print("\t 13:",j,k,datetime.datetime.now().isoformat() )

            fig.text(x=cbase_fault.lon[-1], 
                     y=cbase_fault.lat[-1], 
                     text= cbase_fault.end_str, 
                     font="12p,NewCenturySchlbk-Bold,blue",
                     justify="MR", 
                     fill="white",
                     clearance="+tO",
                     pen="0.35p,black,solid",
                     no_clip=True,
                     offset="0.50c/0c")
            #print("\t 14:",j,k,datetime.datetime.now().isoformat() )
            # dont plot events on the legend map
            if j != 2:
            
                # plot earthquakes
                cdata=data[data[4]>tw_start_TS[k]]
                pygmt.makecpt(cmap="jet", series=[0, eq_deep_limit])

                if len(cdata.index) > 0:
                    fig.plot(
                        x=cdata[0],
                        y=cdata[1],
                        size=0.005 * 2**cdata[3],
                        fill=cdata[2],
                        cmap=True,
                        style="cc",
                        pen="black",
                    )

                lon_legend = [xy_seis_legend[0] for n in range(len(mag_legend))]
                lat_legend = [xy_seis_legend[1] for n in range(len(mag_legend))]

                magdf=pd.DataFrame({"lon_legend":lon_legend,
                                    "lat_legend":lat_legend,
                                    "mag_legend":mag_legend})

                fig.plot(
                         x=magdf.lon_legend,
                         y=magdf.lat_legend,
                         size=0.005 * 2**magdf.mag_legend,
                         style="cc",
                         pen="black",
                        )

                # write legend text
                fig.text(x=lon_legend[0], 
                         y=lat_legend[0], 
                         text= "M "+str(mag_legend[0])+":"+str(mag_legend[-1]),
                         justify="ML", 
                         #fill="white",
                         clearance="+tO",
                         pen="0.35p,black,solid",
                         no_clip=True,
                         offset="0.50c/0c")

            #plot inset
            with fig.inset( position="jBL+o0.1c",
                            box="+gwhite+p1p",
                            region = inset_region,
                            projection="M2.5c",):

                fig.coast( dcw=country+"+g255/218/179+p0.2p",
                           area_thresh=10000,
                         )
                rectangle = [[region[0], region[2], region[1], region[3]]]
                fig.plot(data=rectangle, style="r+s", pen="1p,blue")

            #xy_seis_legend
            if plot_background and j == 2:
                fig.colorbar(frame="af+l"+ctitle)
            elif j != 2:
                fig.colorbar(frame="af+l"+ctitle)
                
            
            fig.savefig(fname=figName)

#####################################################################

def assign_base_fault_barriers():

    global barrier_gdf
    #global bf_names, gls

    barrier_files=glob.glob(os.path.join(home,"GMTdata","*.brr"))

    tbr_lon=[]
    tbr_lat=[]
    tbr_name=[]

    for bf in barrier_files:
        print(10*"==",bf )
        with open(bf, "r") as f:
            contents = f.readlines()
            for line in contents:
                line=line.strip().split()
                if len(line) == 3:
                    clon=float(line[0])
                    clat=float(line[1])
                    cname=line[2]
                    tbr_lon.append(clon)
                    tbr_lat.append(clat)
                    tbr_name.append(cname)

    brr_df=pd.DataFrame({"barrier":tbr_name,"lon":tbr_lon,"lat":tbr_lat})

    barrier_gdf = gpd.GeoDataFrame(brr_df, 
          geometry=gpd.points_from_xy(brr_df.lon, brr_df.lat), 
          crs="EPSG:4326")

    tbrn=[]
    tbr_lon=[]
    tbr_lat=[]

    tbf=[]
    tflon=[]
    tflat=[]

    for cbase_fault in base_faults:
        tflon+=cbase_fault.lon
        tflat+=cbase_fault.lat
        tbf+=[cbase_fault.name] * len(cbase_fault.lon)

    common_crs = 'ESRI:102022'
        
    tdf=pd.DataFrame({"profile":tbf,"lon":tflon, "lat":tflat })    

    gdf = gpd.GeoDataFrame(tdf, 
          geometry=gpd.points_from_xy(tdf.lon, tdf.lat), crs="EPSG:4326")
    gdf = gdf.to_crs(common_crs)

    gls = gpd.GeoSeries(
          gdf.groupby("profile").apply(
          lambda d: shapely.geometry.LineString(d["geometry"].values)))

    barrier_gdf = barrier_gdf.to_crs(common_crs)

    bf_names=gls.axes[0]
 
    for i in range(len(gls)):
        cgls=gls[i]
        barrier_gdf['distance_km'] = barrier_gdf.distance(cgls) / 1000
        brr_name_list = sorted(set(barrier_gdf[barrier_gdf["distance_km"]<1].barrier))
        #print (brr_name_list)
        brr_list=[]
        for tb in brr_name_list:
            brr_list.append(barrier(tb) )
            #print(brr_list)
        #print ("==> ", i,base_faults[i].name, bf_names[i])
        for j in range(len(base_faults)):
            if base_faults[j].name == bf_names[i]:
                base_faults[j].barriers = brr_list



#####################################################################

def assign_surface_ruptures():

    global surface_rupture_gdf

    surface_rupture_files=glob.glob(os.path.join(home,"GMTdata","*.lln"))

    tsr_lon=[]
    tsr_lat=[]
    tsr_name=[]
    tsr_ev_datetime =[]
    tsr_ev_lon =[]
    tsr_ev_lat =[]
    tsr_ev_dep =[]
    tsr_ev_mag =[]

    for sf in surface_rupture_files:
        print(10*"==",sf )
        with open(sf, "r") as f:
            contents = f.readlines()
            cntr=0
            #eqname=""
            #cname=eqname+"s"+str(cntr)
            for line in contents:
                get_specifications=False
                if "#" in line and "Source" not in line :
                    get_specifications=True

                if ">" in line:
                    cntr+=1
                    cname=eqname+"s"+str(cntr)
                    continue

                line=line.strip().split()
                if get_specifications and len(line) >5:
                    ev_datetime = UTCDateTime(line[1])
                    ev_lon=float(line[2])
                    ev_lat=float(line[3])
                    ev_dep=float(line[4])
                    ev_mag=float(line[5])
                    eqname=line[1].replace(":","").replace(".","").replace("-","")

                if len(line) == 2:
                    clon=float(line[0])
                    clat=float(line[1])
                    tsr_lon.append(clon)
                    tsr_lat.append(clat)
                    tsr_name.append(cname)
                    tsr_ev_datetime.append(ev_datetime)
                    tsr_ev_lon.append(ev_lon)
                    tsr_ev_lat.append(ev_lat)
                    tsr_ev_dep.append(ev_dep)
                    tsr_ev_mag.append(ev_mag)

    srr_df=pd.DataFrame({"surface_rupture":tsr_name,
                         "lon":tsr_lon,
                         "lat":tsr_lat,
                         "ev_datetime":tsr_ev_datetime,
                         "ev_lon":tsr_ev_lon,
                         "ev_lat":tsr_ev_lat,
                         "ev_dep":tsr_ev_dep,
                         "ev_mag":tsr_ev_mag
                        })

    surface_rupture_gdf = gpd.GeoDataFrame(srr_df, 
          geometry=gpd.points_from_xy(srr_df.lon, srr_df.lat), 
          crs="EPSG:4326")

    tsrn=[]
    tsr_lon=[]
    tsr_lat=[]

    tsf=[]
    tflon=[]
    tflat=[]

    for cbase_fault in base_faults:
        tflon+=cbase_fault.lon
        tflat+=cbase_fault.lat
        tsf+=[cbase_fault.name] * len(cbase_fault.lon)

    common_crs = 'ESRI:102022'
        
    tdf=pd.DataFrame({"event":tsf,"lon":tflon, "lat":tflat })    

    gdf = gpd.GeoDataFrame(tdf, 
          geometry=gpd.points_from_xy(tdf.lon, tdf.lat), crs="EPSG:4326")
    gdf = gdf.to_crs(common_crs)

    gls = gpd.GeoSeries(
          gdf.groupby("event").apply(
          lambda d: shapely.geometry.LineString(d["geometry"].values)))

    surface_rupture_gdf = surface_rupture_gdf.to_crs(common_crs)

    sf_names=gls.axes[0]
 
    for i in range(len(gls)):
        cgls=gls[i]
        surface_rupture_gdf['distance_km'] = surface_rupture_gdf.distance(cgls) / 1000
        srr_name_list = sorted(set(surface_rupture_gdf[surface_rupture_gdf["distance_km"]<1].surface_rupture))
        srr_list=[]
        for tb in srr_name_list:
            fldf = surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==tb].iloc[0]
            evdatetime  = fldf.ev_datetime
            evlon= fldf.ev_lon 
            evlat= fldf.ev_lat 
            evdep= fldf.ev_dep 
            evmag= fldf.ev_mag 

            srr_list.append(surface_rupture(tb, evdatetime,evlon,evlat,evdep,evmag))

        #print (srr_name_list)

        for j in range(len(base_faults)):
            if base_faults[j].name == sf_names[i]:
                base_faults[j].surface_ruptures = srr_list

#####################################################################

def along_profile_barrier_length ():

    global tdf

    width=[-1,1]

    for cbase_fault in base_faults:
        #print(10*"*",cbase_fault.name )
        print(f"\t---> Fault System: {cbase_fault.name}" )
        clons=cbase_fault.lon
        clats=cbase_fault.lat
        cbarriers=[]
            
        cumul_segs_length = 0.0     
        for i in range(len(clons)-1):     
            az12,az21,dist_km = geo_distaz(lon1=clons[i],
                                           lat1=clats[i], 
                                           lon2=clons[i+1],  
                                           lat2=clats[i+1])
         
            cumul_segs_length += dist_km 

        for i in range(len(cbase_fault.barriers)):
            cbarriers.append(cbase_fault.barriers[i].name)

        for k, brr_name in enumerate(cbarriers):
            #print(brr_name)
            blonary=barrier_gdf[barrier_gdf["barrier"]==brr_name].lon
            blatary=barrier_gdf[barrier_gdf["barrier"]==brr_name].lat

            cdb=pd.DataFrame({"lon":blonary,"lat":blatary})
            # it is enough the first and last points of the barrier
            tmp_cumul_length = 0.0     
            tdf=pd.DataFrame()
         
            for i in range(len(clons)-1):     
                try:
                    segdf = pygmt.project(
                            data=cdb,
                            center=[clons[i],clats[i]], 
                            endpoint=[clons[i+1],clats[i+1]],
                            width=width,
                            length=["w"],
                            unit=True 
                            )
                    segdf[2]=segdf[2]+tmp_cumul_length
                    # fix for length
                    tdf = pd.concat([tdf,segdf], ignore_index=True)
                except:
                    pass
                    #print("\t ... No match in the profile segment!")
            
                # find segment length and assign
                az12,az21,dist_km = geo_distaz(lon1=clons[i],
                                               lat1=clats[i], 
                                               lon2=clons[i+1],  
                                               lat2=clats[i+1])
             
                tmp_cumul_length += dist_km 

            tdf = tdf.drop_duplicates()
            cbase_fault.barriers[k].df = tdf

        cbase_fault.total_length=cumul_segs_length
         
        print(f"\t==> System length: {round(cumul_segs_length,3)} km" )


#####################################################################

def along_profile_surface_rupture_length ():

    global tsrdf

    width=[-5,5]

    for cbase_fault in base_faults:
        #print(10*"*",cbase_fault.name )
        print(f"\t---> Fault System: {cbase_fault.name}" )
        
        clons=cbase_fault.lon
        clats=cbase_fault.lat
        csurface_ruptures=[]
            
        cumul_segs_length = 0.0
        seg_length=[]     
        for i in range(len(clons)-1):     
            az12,az21,dist_km = geo_distaz(lon1=clons[i],
                                           lat1=clats[i], 
                                           lon2=clons[i+1],  
                                           lat2=clats[i+1])
         
            cumul_segs_length += dist_km 
            seg_length.append(cumul_segs_length)

        for i in range(len(cbase_fault.surface_ruptures)):
            csurface_ruptures.append(cbase_fault.surface_ruptures[i].name)

        for k, sr_name in enumerate(csurface_ruptures):
            #print(sr_name)
            slonary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lon
            slatary=surface_rupture_gdf[surface_rupture_gdf["surface_rupture"]==sr_name].lat

            cdb=pd.DataFrame({"lon":slonary,"lat":slatary})
            # it is enough the first and last points of the barrier
            tmp_cumul_length = 0.0     
            tsrdf=pd.DataFrame()
         
            for i in range(len(clons)-1):     
                try:
                    segdf = pygmt.project(
                            data=cdb,
                            center=[clons[i],clats[i]], 
                            endpoint=[clons[i+1],clats[i+1]],
                            width=width,
                            length=["w"],
                            unit=True 
                            )
                    segdf[2]=segdf[2]+tmp_cumul_length
                    # fix for length
                    tsrdf = pd.concat([tsrdf,segdf], ignore_index=True)
                except:
                    pass
                    #print("\t ... No match in the profile segment!")
            
                # find segment length and assign
                az12,az21,dist_km = geo_distaz(lon1=clons[i],
                                               lat1=clats[i], 
                                               lon2=clons[i+1],  
                                               lat2=clats[i+1])
             
                tmp_cumul_length += dist_km 

            tsrdf = tsrdf.drop_duplicates()
            cbase_fault.surface_ruptures[k].df = tsrdf

        cbase_fault.total_length=cumul_segs_length
        cbase_fault.seg_length=seg_length
         
        print(f"\t==> System length: {round(cumul_segs_length,3)} km" )

#####################################################################
def gen_final_eq_df():
        
    global last_datetime_iiees
    global last_datetime_irsc
    global ref_eq_df

    if len(iiees_df) > 0:
        last_datetime_iiees = iiees_df.iloc[-1].time
    else:
        last_datetime_iiees = UTCDateTime("1900/01/01")
        
    if len(irsc_df) > 0:
        last_datetime_irsc  = irsc_df.iloc[-1].time
    else:
        last_datetime_irsc  = UTCDateTime("1900/01/01")


    concat_usgs_irsc()

    if last_datetime_iiees > last_datetime_irsc:
        concat_usgs_irsc_iiees()
        ref_eq_df = usgs_irsc_iiees_df
        del globals()['usgs_irsc_iiees_df']
    else:
        ref_eq_df = usgs_irsc_df
        


    ref_eq_df["time"]=[datetime.datetime.fromisoformat(
              str(v).split("+")[0]) for v in  ref_eq_df["time"]]

    del globals()['usgs_irsc_df']

#####################################################################
 
def read_historical_events():

    global historical_earthquakes
    historical_earthquakes = []

    heq_ptrn = os.path.join(home,"GMTdata","KML","Ambraseys",
                           "GMT","*.gmt") 
    historical_events=glob.glob(heq_ptrn)

    for i,heq in enumerate(historical_events):
        #print(heq)
        with open(heq, "r") as f:
            contents=f.readlines()
        hplon=[]
        hplat=[]
        for line in contents:
            headline=False
            if ">" in line:
                headline=True
            cline=line.strip().split()
            if headline and len(cline) > 1:
                #print(cline)
                eq_title=line.split('"')[1]
                titleSplit=eq_title.split()
                heq_year=int(titleSplit[0].split("/")[0])
                #heq_date=UTCDateTime(titleSplit[0])
                heq_mag = float(titleSplit[1].
                                replace("(","").
                                replace(")","").
                                replace("?",""))

                #heq_region = titleSplit[2]
                
                #print(eq_title)
                #print(heq_mag, heq_region  )
                continue
            
            if len(cline)>1:
                #print("====>> ",cline[0], cline[1])
                hplon.append(float(cline[0]) )
                hplat.append(float(cline[1]) )


 
        mean_lon = np.mean(hplon)
        mean_lat = np.mean(hplat)
        df=pd.DataFrame({"lon":hplon,"lat":hplat})
        historical_earthquakes.append(
            historical_earthquake ( eq_title, 
                                    heq_year, 
                                    heq_mag,
                                    mean_lon,
                                    mean_lat, 
                                    df))

#####################################################################
def record_last_events(firstTry=None):

    global bf_last_event

    bfname=[]
    bfdatetime=[]
    trial_datetime=UTCDateTime( 1975,1,1)
    for cbf in base_faults:
        bfname.append(cbf.name)
        if firstTry:
            bfdatetime.append(trial_datetime)
        else:
            bfdatetime.append(cbf.last_event_datetime)

    bf_last_event = pd.DataFrame({"name":bfname,
                                 "last_event_datetime":bfdatetime}
                                )

#####################################################################

def monitor_plotting_order():

    global base_fault_toplot
    global base_fault_toupdate_plot

    base_fault_toplot =[]
    base_fault_toupdate_plot =[]

    for cbf in base_faults:
        cbf_name=cbf.name
        cbf_datetime =cbf.last_event_datetime
        #print ("I: ", cbf_name,cbf_datetime )
        cbf_last_datetime = \
         bf_last_event[bf_last_event.name == cbf_name].iloc[0].last_event_datetime
        #print ("II: ", cbf_last_datetime )
        #print ("III: common_now: ", common_now )
        #print ("IV: cbf.last_updated_plot: ", cbf.last_updated_plot )
        #print ("V: typt common_now: ", type(common_now))
        #print ("VI: typt cbf.last_updated_plot: ", type(cbf.last_updated_plot))

        dt = (common_now - cbf.last_updated_plot).seconds

        #print("VII: cbf_datetime, cbf_last_datetime: ",cbf_datetime, cbf_last_datetime)            

        if cbf_datetime > cbf_last_datetime:
            base_fault_toplot.append(cbf_name)

        if dt > force_update_seconds:
            if cbf_name not in base_fault_toplot:
                base_fault_toupdate_plot.append(cbf_name)

    print (f"\t ... The base faults to plot: \n\t {base_fault_toplot}")
    print (f"\t ... The base faults to update plot: \n\t {base_fault_toupdate_plot}")

#####################################################################
def get_base_faults():

    global base_faults, cbase_params
    base_faults=[]
    
    ir_inset_region = [40, 65, 24, 42]
    tr_inset_region = [24, 45, 34, 43]
    af_inset_region = [40, 65, 24, 42]

    kml_path= os.path.join(home,"GMTdata","KML","Time_Section")
    # name, pos_width, neg_width, base_az
    base_params=[['Avaj.kml',            20,20, 330, ir_inset_region,'IR'],
                ['Bam-Ravar.kml',       20,20, 320, ir_inset_region,'IR'],
                ['Damavand.kml',        20,20,  85, ir_inset_region,'IR'],
                ['Dehshir.kml',         20,20, 320, ir_inset_region,'IR'],
                #['East_Africa_Rift.kml',50,50,0.75, ir_inset_region,'IR'],
                ['Ipak.kml',            20,20, 275, ir_inset_region,'IR'],
                ['Kazeroon.kml',        20,20, 320, ir_inset_region,'IR'],
                ['Kerman.kml',          20,20, 320, ir_inset_region,'IR'],
                ['Kopedagh.kml',        40,40, 320, ir_inset_region,'IR'],
                ['Kuhbanan.kml',        20,20, 320, ir_inset_region,'IR'],
                #['Marmare.kml',         20,20,90.75, tr_inset_region,'TR'],
                ['NE_Lut.kml',          20,20,  10, ir_inset_region,'IR'],
                ['Neyshabur.kml',       20,20,  10, ir_inset_region,'IR'],
                ['Qom.kml',             20,20,  10, ir_inset_region,'IR'],
                ['Semnan.kml',          20,20,  10, ir_inset_region,'IR'],
                ['Seimare.kml',         50,50, 320, ir_inset_region,'IR'],
                ['Shahrud.kml',         20,20,  75, ir_inset_region,'IR'],
                ['Sabzvar.kml',         20,20, 275, ir_inset_region,'IR'],
                ['Tehran.kml',          20,20, 320, ir_inset_region,'IR'],
                ['Turkmanchay.kml',     20,20,  32, ir_inset_region,'IR'],
                ['Van_Tabriz.kml',      20,20, 320, ir_inset_region,'IR'],
                ['West_Lut.kml',        20,20,  10, ir_inset_region,'IR'],
                ['Zagros.kml',         50,50, 285, ir_inset_region,'IR']
                ]

    if small_set:
        base_params=[
                ['Ipak.kml',            20,20, 275, ir_inset_region,'IR'],
                ['Shahrud.kml',         20,20,  75, ir_inset_region,'IR'],
                ['Tehran.kml',          20,20, 320, ir_inset_region,'IR'],
                    ]


    for cbase_params in base_params:
        kml_file=os.path.join(kml_path,cbase_params[0] )

        lonlist, latlist = extract_kml_coordinates(kml_file=kml_file)

        name=cbase_params[0].upper().replace(".KML","").replace("_","-")
        pos_width = float(cbase_params[1]) 
        neg_width = float(cbase_params[2])*-1
        base_az   = float(cbase_params[3])
        inset_region    = cbase_params[4]
        country   = cbase_params[5]


        cbase_fault=base_fault (name,
                                lonlist[0],
                                latlist[0],
                                pos_width, 
                                neg_width, 
                                base_az, 
                                inset_region, 
                                country
                                )

        base_faults.append(cbase_fault)


#####################################################################
#####################################################################

if __name__ == "__main__":

    
    sleep_seconds = 60
    pygmt.config(FONT_TITLE ="12p,Helvetica,black")
    small_set = False
    plot_background = True
    use_local_grid = True

    file_paths()
    read_historical_events()
    get_base_faults()
    assign_base_fault_barriers()
    along_profile_barrier_length()
    assign_surface_ruptures()
    along_profile_surface_rupture_length()
    read_usgs (usgs_file = usgs_db_file)
    record_last_events(firstTry=True)

    while True:
        time.sleep(sleep_seconds)
        common_now = datetime.datetime.now()

        if False:
            update_iiees_catalog(iiees_db_file=iiees_db_file)
            
        update_irsc_catalog(irsc_db_file=irsc_db_file)

        read_irsc (irsc_db_file = irsc_db_file)
        read_iiees (iiees_db_file=iiees_db_file)
        gen_final_eq_df()    

        assign_base_fault_dfs()

        monitor_plotting_order()
        
        plot_monitor_maps ()
            
        record_last_events(firstTry=False)
        print(40*"=", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
