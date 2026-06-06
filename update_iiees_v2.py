import subprocess
import re
import requests
import io
import os
import sys
import shutil
from obspy import UTCDateTime

#####################################################################

def make_keystroke(last_event_datetime=None):
    global keyf

    byear="{0:04d}".format(last_event_datetime.year)
    bmonth="{0:02d}".format(last_event_datetime.month)
    bday="{0:02d}".format(last_event_datetime.day)
    
    tenYears = 3600*24*365*10
    t2=last_event_datetime+tenYears
    #t2=UTCDateTime.now()
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

def download_file(url):
    local_filename = url.split('=')[-1]+".txt"
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)
    return local_filename

#####################################################################
def get_last_iiees_event():

    try:
        with open(iiees_file,'r') as f:
            contents = f.readlines()

        last_line = contents[-1].split()

        if len(last_line) > 5:
            last_event_datetime=UTCDateTime(last_line[0]+"T"+last_line[1])
            return last_event_datetime
        else:
            sys.exit("\t ... IIEES catalog is not properly set.")
    except:
        os.makedirs(iiees_dir, exist_ok=True)
        #create empty file
        with open(iiees_file, 'w') as fp:
            pass
        #last_event_datetime=UTCDateTime(last_line[0]+"T"+last_line[1])
        last_event_datetime=UTCDateTime("1900-01-01")
        return last_event_datetime

#####################################################################

def add2iiees(downloaded_file=None, last_event_datetime=None):

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
        with open (iiees_file,'a') as f:
            for line in  add_list:
                f.write(line)
    else:
        print(f"\t ... No new event was found at {UTCDateTime.now()}")



#####################################################################

def update_iiees_catalog():
    global new_text

    url="http://www.iiees.ac.ir/en/eqcatalog/"

    pre_last_event_datetime=UTCDateTime.now()
    last_event_datetime = get_last_iiees_event()

    while pre_last_event_datetime != last_event_datetime:

        pre_last_event_datetime = last_event_datetime

        print(last_event_datetime)


        make_keystroke( last_event_datetime=last_event_datetime)


        cmd=f"lynx -crawl  -cmd_script=keystrokes {url} ".split() 

        print(cmd)

        #sys.exit()

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
            local_filename = download_file(urlFile)
            add2iiees(downloaded_file=local_filename, 
                         last_event_datetime=last_event_datetime 
                        )
        else:
            print(f"\t ... No link for file was found at {UTCDateTime.now()}")

        last_event_datetime = get_last_iiees_event()
            
#####################################################################

if __name__ == "__main__":

    home= os.path.expanduser("~")
    iiees_dir=os.path.join(home,"GMTdata","IIEES")

    print(iiees_dir)
    
    iiees_file=os.path.join(home,"GMTdata","IIEES",
                                "IIEES_catalog.txt")
 
    update_iiees_catalog()
