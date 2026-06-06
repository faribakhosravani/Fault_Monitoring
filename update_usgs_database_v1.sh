#!/bin/bash

rm -f query.csv
cy=0

usgsdb=$HOME/GMTdata/USGS/query_1600_open.usgs 
cds=` date -u +%s `
n=0
nev=100


while (( $nev > 1 )) ; 
do
    ((n+=1))
if [ ! -f $usgsdb  ] ; then
    leqdate="1600-01-01T00:00:00.0"
else
    last_usgs_line=` tail -10 $usgsdb | gawk -F, '{if (NF>5)print $0}' | tail -1 `
    leqdate=`echo $last_usgs_line | gawk -F, '{print $1}' `
fi
cy=`date -u -d"$leqdate" +%Y`


if (( $cy <= 1900 )) ; then
    nday=$((365*400))
elif (( $cy <= 1920 )) ; then
    nday=$((365*10))
elif (( $cy <= 1940 )) ; then
    nday=$((365*5))
elif (( $cy <= 1950 )) ; then
    nday=$((365*3))
elif (( $cy <= 1970 )) ; then
    nday=$((90*1))
elif (( $cy <= 1980 )) ; then
    nday=$((45*1))
elif (( $cy <= 1990 )) ; then
    nday=$((30*1))
elif (( $cy <= 2000 )) ; then
    nday=$((30*1))
elif (( $cy <= 2030 )) ; then
    nday=$((30*1))
else
    nday=$((5*1))
fi



leqs=`date +%s -u -d"$leqdate"`
nlds=$(($leqs + $nday * 86400))



#starttime=`date -u -d @$leqs +"%F+%H%%3A%M%%3A%S"`
#endtime=`date -u -d @$nlds +"%F+%H%%3A%M%%3A%S"`

starttime=`date -u -d @$leqs +"%FT%H:%M:%S"`
endtime=`date -u -d @$nlds +"%FT%H:%M:%S"`

echo  " --> starttime: $starttime endtime: $endtime"

minlatitude=15
maxlatitude=55
minlongitude=35
maxlongitude=70



usgscmd="https://earthquake.usgs.gov/fdsnws/event/1/query?minmagnitude=1&maxmagnitude=&starttime=$starttime&endtime=$endtime&maxlatitude=$maxlatitude&minlongitude=$minlongitude&maxlongitude=$maxlongitude&minlatitude=$minlatitude&latitude=&longitude=&maxradiuskm=&mindepth=&maxdepth=&mingap=&maxgap=&reviewstatus=&eventtype=&minsig=&maxsig=&alertlevel=&minmmi=&maxmmi=&mincdi=&maxcdi=&minfelt=&catalog=&contributor=&producttype=&format=csv&kmlcolorby=age&callback=&orderby=time-asc&limit=&offset="

wget -q -O query.csv  $usgscmd

nev=`wc -l query.csv | gawk '{print $1-1}'`

if (( $nev > 1 )) ; then

    #########################################
    # new
    rm -f usgs_epoch
    touch  usgs_epoch
    m=0
    
    while IFS= read -r line; do
        ((m+=1))
        
        if (( m == 1 )) ; then
            echo $line >> usgs_epoch
        else
            ceqdt=`echo $line | gawk -F, '{print $1}' | gawk -F. \
                '{print $1}' | sed 's/-/./g' | sed 's/T/-/g' `

            t2=$( busybox date -u -d $ceqdt +"%s")
            
            echo $line , $t2  >> usgs_epoch
        fi
    done < query.csv
        

    
    
    #########################################
    
    
    if [ ! -f $usgsdb  ] ; then
        cp usgs_epoch $usgsdb
    else
        sed '1d' usgs_epoch >> $usgsdb 
    fi
    
    echo " --> The file $usgsdb was updated."
else
    echo " ==> The file $usgsdb is uptodate."
fi

done
