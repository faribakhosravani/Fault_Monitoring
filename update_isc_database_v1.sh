#!/bin/bash

rm -f isc.csv
cy=0

iscdb=$HOME/GMTdata/ISC/ISC_1600_open.isc 
cds=` date -u +%s `
n=0
nev=100


while (( $nev > 2 )) ; 
do
    echo "----------------------------- FROM ISC -----------------------------"
    if [  $nev == 2 ] ; then
        nsec=60
        echo " ... sleeping $nsec seconds"
        sleep $nsec 
    fi
    

    ((n+=1))
    if [ ! -f $iscdb  ] ; then
        leqdate="1900-01-01T00:00:00.0"
    else
        last_isc_line=` tail -10 $iscdb | gawk -F, '{if (NF>5)print $0}' | tail -1 `
        #echo $last_isc_line
        leqdate=`echo $last_isc_line | gawk -F, '{print $4"T"$5}' `
    fi



    cy=`date -u -d"$leqdate" +%Y`






if (( $cy < 1900 )) ; then
    nday=$((365*100))
elif (( $cy <= 1920 )) ; then
    nday=$((365*10))
elif (( $cy <= 1940 )) ; then
    nday=$((365*5))
elif (( $cy <= 1950 )) ; then
    nday=$((365*2))
elif (( $cy <= 1970 )) ; then
    nday=$((365*1))
    #nday=$((90*1))
elif (( $cy <= 1980 )) ; then
    nday=$((45*1))
elif (( $cy <= 1990 )) ; then
    nday=$((30*1))
elif (( $cy <= 2000 )) ; then
    nday=$((30*1))
elif (( $cy <= 2010 )) ; then
    nday=$((15*1))
elif (( $cy <= 2030 )) ; then
    nday=$((15*1))
else
    nday=$((5*1))
fi



leqs=`date +%s -u -d"$leqdate"`
nlds=$(($leqs + $nday * 86400))

starttime=`date -u -d @$leqs +"%FT%H:%M:%S"`
endtime=`date -u -d @$nlds +"%FT%H:%M:%S"`

echo " $n From $starttime to $endtime"

by=`date -u -d"$starttime" +"%Y" `
bm=`date -u -d"$starttime" +"%m" `
bd=`date -u -d"$starttime" +"%d" `
bH=`date -u -d"$starttime" +"%H" `
bM=`date -u -d"$starttime" +"%M" `
bS=`date -u -d"$starttime" +"%S" `

ey=`date -u -d"$endtime" +"%Y" `
em=`date -u -d"$endtime" +"%m" `
ed=`date -u -d"$endtime" +"%d" `
eH=`date -u -d"$endtime" +"%H" `
eM=`date -u -d"$endtime" +"%M" `
eS=`date -u -d"$endtime" +"%S" `

bot_lat=15
top_lat=55
left_lon=35
right_lon=70

isccmd="http://www.isc.ac.uk/cgi-bin/web-db-v4?request=COMPREHENSIVE&out_format=CATCSV&searchshape=RECT&bot_lat=$bot_lat&top_lat=$top_lat&left_lon=$left_lon&right_lon=$right_lon&ctr_lat=&ctr_lon=&radius=&max_dist_units=deg&srn=&grn=&start_year=$by&start_month=$bm&start_day=$bd&start_time=$bH%3A$bM%3A$bS&end_year=$ey&end_month=$em&end_day=$ed&end_time=$eH%3A$eM%3A$eS&min_dep=&max_dep=&min_mag=&max_mag=&req_mag_type=&req_mag_agcy=&include_links=on" 

# get the output and replace HTML to pure ASCII
wget -qO- $isccmd | sed -e 's/<[^>]*>//g;s/^ //g' > downloaded_stripped_isc_file


bline=`grep -n  '\-\-EVENT\-\-' downloaded_stripped_isc_file  | gawk -F: '{print $1+1}'`
eline=`grep -n  'STOP' downloaded_stripped_isc_file  | gawk -F: '{print $1-2}'`

# Check if the file is empty of events
if [ ! -n "$bline" ] ||  [ ! -n "$eline" ]
then
    nev=0
else
    nev=$((eline-bline+1))
fi

echo " ==> Number of events: $nev "

if (( $nev > 2 )) ; then
    
    sed -n "$bline,$eline p" downloaded_stripped_isc_file >  isc.csv 
    
    #########################################
    # new
    rm -f isc_epoch
    touch  isc_epoch
    m=0
    
    while IFS= read -r line; do
        ((m+=1))
        if (( m == 1 )) ; then
            echo $line >> isc_epoch
        else
            ceqdt=`echo $line | gawk -F, '{print $4"T"$5}' | gawk -F. \
                '{print $1}' | sed 's/-/./g' | sed 's/T/-/g' `

            t2=$( busybox date -u -d $ceqdt +"%s")


            echo $line | gawk -F, -v v0=$t2 '{OFS=",";$1=v0; print $0 }'  >> isc_epoch
        fi
    done < isc.csv
         

    
    
    #########################################
    
    
    if [ ! -f $iscdb  ] ; then
        cp isc_epoch $iscdb
    else
        sed '1d' isc_epoch >> $iscdb 
    fi
    
    echo " --> The file $iscdb was updated."
else
    echo " ==> The file $iscdb is uptodate."
fi

done
