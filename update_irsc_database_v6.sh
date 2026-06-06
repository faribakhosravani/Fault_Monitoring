#!/bin/bash

#echo "The following steps are taken before: "
#echo ""
#echo " 1- wget http://irsc.ut.ac.ir/bulletin.php "
#echo " 2- formfind < bulletin.php "
#echo ""
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

irscdir="$HOME/GMTdata/IRSN"

if test -d $irscdir; then
	echo "$irscdir Directory exists."
else
	mkdir -p $irscdir
	echo "$irscdir directory was created."
fi

dbsrc="http://irsc.ut.ac.ir/bulletin.php"

irscdb=$HOME/GMTdata/IRSN/IRSN_TEH_IRN.txt


cds=` date -u +%s `
n=0
nev=100


while (( $nev > 0 )) ; 
do
    sleep 60
    echo `date`
    ((n+=1))
    
    if [ ! -f $irscdb  ] ; then
        leqdate="2006-01-01T00:00:00.0"
        serial=0
        sn=0
    else
        last_irsc_line=` tail -10 $irscdb | gawk '{if (NF>5)print $0}' | tail -1 `
        serial=`echo $last_irsc_line | gawk '{print $1}'  `
        sn=`echo $last_irsc_line | gawk '{print $2}'  `
        leqdate=`echo $last_irsc_line | gawk '{print $3"T"$4}' | sed 's/\//-/g' `
    fi
    

echo $last_irsc_line
#echo $leqdate


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
    echo 1-leqs $leqs
    leqs=$(($leqs + 1 ))
    nlds=$(($leqs + $nday * 86400))

    #echo leqdate $leqdate
    #echo 2-leqs $leqs
    #echo nlds $nlds

    starttime=`date -u -d @$leqs +"%FT%H:%M:%S"`
    endtime=`  date -u -d @$nlds +"%FT%H:%M:%S"`
    
    ey=`date -u -d"$endtime" +%Y`
    em=`date -u -d"$endtime" +%m`
    ed=`date -u -d"$endtime" +%d`
    eh=`date -u -d"$endtime" +%H`
   
    echo "starttime: $starttime endtime: $endtime"
#exit

echo    curl --data "start_Y=$by&start_M=$bm&start_D=$bd&start_H=$bh& end_Y=$ey&end_M=$em&end_D=$ed&end_H=$eh&action=Search" $dbsrc 

    curl --data \
        "start_Y=$by&start_M=$bm&start_D=$bd&start_H=$bh& end_Y=$ey&end_M=$em&end_D=$ed&end_H=$eh&action=Search" \
        $dbsrc > tmpout


# exit


    ################################################################
    # This is to prevent hanging due to file absence        
    file_exist=` grep 'Printable Version'  tmpout | wc -l | gawk '{print $1}' `

    if (( $file_exist > 0 )) ; then
        file_name=`grep 'Printable Version'  tmpout | \
            gawk '{print $7}' | gawk -F\> '{print $1}'`
    else
        echo "No IRSC file name is available ....! "
        break
    fi
    ################################################################


    wget -q http://irsc.ut.ac.ir/$file_name

    bulfile=`echo $file_name |  gawk -F/ '{print $2}' `


    
    bline=`gawk -v var=$serial '{if(NR==1)bn=17;if( $2==var)bn=NR+1};END{print bn}' $bulfile `
    eline=`gawk '{if(NF>10)en=NR};END{print en}' $bulfile`
    


    sed -n "$bline,$eline"p $bulfile > trimed_data
   

    nev=`wc -l trimed_data | gawk '{print $1}'`

    #echo " ==> Num of events: $nev $starttime $endtime $file_name "
    rm -f $bulfile
    
    if (( $nev > 0 )) ; then

         # To add epoch at the begining 
        rm -f new_events
        touch  new_events
        
        while IFS= read -r line; do
            ceqdt=`echo $line | gawk '{print $3"-"$4}' | \
                gawk -F. '{print $1}' | sed 's/\//./g'  `
            t2=$( busybox date -u -d $ceqdt +"%s")
#######################################
            csn=`echo $line | gawk '{print $2}'`

            # if we use the commented case, the later postponed 
            #earthquakes during analysis at IRSC will be ignored 
            #and theis is not desirable.
            #if ((  $csn > $sn )) ; then
            
            if ((  $t2 > $leqs )) ; then
                echo $line | gawk -v v0=$t2 '{$1=v0; print $0}'  >> new_events
            fi
        done < trimed_data



        if [ ! -f $irscdb  ] ; then
            cp new_events $irscdb
        else
            cat new_events >> $irscdb 
        fi
        echo " -----> The file $irscdb is updated."
    else
        echo " ==> The file $irscdb is uptodate."
    fi

done

