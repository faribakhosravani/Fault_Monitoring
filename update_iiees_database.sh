#!/bin/bash

#echo "The following steps are taken before: "
#echo ""
#echo " 1- wget http://irsc.ut.ac.ir/bulletin.php "
#echo " 2- formfind < bulletin.php "
#echo ""

#--- FORM report. Uses POST to URL "../recentevents"
#Input: NAME="txtDate1" (TEXT)
#Input: NAME="txtDate2" (TEXT)
#Input: NAME="txtHour1" (TEXT)
#Input: NAME="txtHour2" (TEXT)
#Input: NAME="txtDepth1" (TEXT)
#Input: NAME="txtDepth2" (TEXT)
#Input: NAME="txtM1" (TEXT)
#Input: NAME="txtM2" (TEXT)
#Input: NAME="txtReference" (TEXT)
dbsrc="http://www.iiees.ac.ir/en/eqcatalog/"

txtDate1="2015/01/01"
txtDate2="2015/02/01"
txtDate1="01"
txtDate2="10"

    curl -s --data \
        "txtDate1=$txtDate1&txtDate2=$txtDate2&txtHour1=$txtHour1&txtHour2=$txtHour2&btnSubmit='Submit'" \
        $dbsrc > tmpout

#<a href="http://www.iiees.ac.ir/en/?iieesop=ascii&quid=qysYRc03&asciiformat=list" class="linkbutton" >List </a>
#<a href="http://www.iiees.ac.ir/en/?iieesop=ascii&quid=qysYRc03&asciiformat=seisan" class="linkbutton">Seisan</a>
#<a href="http://www.iiees.ac.ir/en/?iieesop=ascii&quid=qysYRc03&asciiformat=gse" class="linkbutton">GSE2.0</a>
 
echo 11111111111111111111111111111111111111



wget -O hhh  http://www.iiees.ac.ir/en/recentevents
exit

wget -O eqf "http://www.iiees.ac.ir/en/?iieesop=ascii&quid=qysYRc03&asciiformat=list" class="linkbutton"

#btnSubmit" VALUE="Submit

exit

#--- FORM report. Uses POST to URL "bulletin.php"
#Input: NAME="start_Y" VALUE="2006" (TEXT)
#Input: NAME="start_M" VALUE="01" (TEXT)
#Input: NAME="start_D" VALUE="01" (TEXT)
#Input: NAME="start_H" VALUE="00" (TEXT)
#Input: NAME="end_Y" (TEXT)
#Input: NAME="end_M" (TEXT)
#Input: NAME="end_D" (TEXT)
#Input: NAME="end_H" (TEXT)
#Input: NAME="min_lat" (TEXT)
#Input: NAME="max_lat" (TEXT)
#Input: NAME="min_lon" (TEXT)
#Input: NAME="max_lon" (TEXT)
#Input: NAME="min_dep" (TEXT)
#Input: NAME="max_dep" (TEXT)
#Input: NAME="min_mag" (TEXT)
#Input: NAME="max_mag" (TEXT)
#Input: NAME=" " (TEXT)
#Input: NAME=" " (TEXT)
#Input: NAME="action" VALUE="Search" (SUBMIT)
#--- end of FORM




dbsrc="http://irsc.ut.ac.ir/bulletin.php"

irscdb=$HOME/GMTdata/IRSN/IRSN_TEH_IRN.txt


cds=` date -u +%s `
n=0
nev=100


while (( $nev > 0 )) ; 
do
    ((n+=1))
    
    if [ ! -f $irscdb  ] ; then
        leqdate="2006-01-01T00:00:00.0"
        serial=0
    else
        last_irsc_line=` tail -10 $irscdb | gawk '{if (NF>5)print $0}' | tail -1 `
        serial=`echo $last_irsc_line | gawk '{print $2}'  `
        leqdate=`echo $last_irsc_line | gawk '{print $3"T"$4}' | sed 's/\//-/g' `
    fi
    
    by=`date -u -d"$leqdate" +%Y`
    bm=`date -u -d"$leqdate" +%m`
    bd=`date -u -d"$leqdate" +%d`
    bh=`date -u -d"$leqdate" +%H`
    
    if (( $by <= 2005 )) ; then
        nday=$((180*1))
    elif (( $by <= 2008 )) ; then
        nday=$((60*1))
    elif (( $by <= 2010 )) ; then
        nday=$((45*1))
    elif (( $by <= 2015 )) ; then
        nday=$((30*1))
    elif (( $by <= 2019 )) ; then
        nday=$((15*1))
    else
        nday=$((5*1))
    fi
    
    leqs=`date +%s -u -d"$leqdate"`
    nlds=$(($leqs + $nday * 86400))
    
    starttime=`date -u -d @$leqs +"%FT%X"`
    endtime=`  date -u -d @$nlds +"%FT%X"`
    
    ey=`date -u -d"$endtime" +%Y`
    em=`date -u -d"$endtime" +%m`
    ed=`date -u -d"$endtime" +%d`
    eh=`date -u -d"$endtime" +%H`
    
    curl -s --data \
        "start_Y=$by&start_M=$bm&start_D=$bd&start_H=$bh& end_Y=$ey&end_M=$em&end_D=$ed&end_H=$eh&action=Search" \
        $dbsrc > tmpout
    
    file_name=`grep 'Printable Version'  tmpout  | gawk '{print $7}' | gawk -F\> '{print $1}'`

    wget -q http://irsc.ut.ac.ir/$file_name

    bulfile=`echo $file_name |  gawk -F/ '{print $2}' `
    
    bline=`gawk -v var=$serial '{if(NR==1)bn=17;if( $2==var)bn=NR+1};END{print bn}' $bulfile `
    eline=`gawk '{if(NF>10)en=NR};END{print en}' $bulfile`
    


    sed -n "$bline,$eline"p $bulfile > trimed_data
   

    nev=`wc -l trimed_data | gawk '{print $1}'`

    echo " ==> Num of events: $nev $starttime $endtime $file_name "
    rm -f $bulfile
    
    if (( $nev > 0 )) ; then
        if [ ! -f $irscdb  ] ; then
            cp trimed_data $irscdb
        else
            cat trimed_data >> $irscdb 
        fi
        echo " The file $irscdb is updated."
    else
        echo " The file $irscdb is uptodate."
    fi

done

