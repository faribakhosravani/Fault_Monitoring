#!/bin/bash


koeridir="$HOME/GMTdata/KOERI"

if test -d $koeridir; then
	echo "$koeridir Directory exists."
else
	mkdir -p $koeridir
	echo "$koeridir directory was created."
fi


# 1570482396 2019.10.07 21:06:36 38.8227 26.9590 4.8 -.- 1.1 -.- ALIAGA

stfile=$HOME/GMTdata/KOERI/KOERI_Turkey_Quick
tmpf=scratch_Koeri

rm -f $tmpf 
touch $tmpf

#leqdt=`head $stfile | gawk '{if(NF>7)print $0}' | head -1 | gawk '{print $1}' `
t1=`head $stfile | gawk '{if(NF>7)print $0}' | head -1 | gawk '{print $1}' `

#t1=$( busybox date -u -d $leqdt +"%s")

rm -f lasteq.asp

wget -q http://www.koeri.boun.edu.tr/scripts/lasteq.asp

# 2019.09.30 16:59:24  34.9638   33.5147        7.1      -.-  2.2  -.-   KIBRIS-LEFKOSA                                    Quick
# 2019.08.01 01:43:04	 39.8090	 27.2202	      5.4 	        2.5       	KALKIM-YENICE (CANAKKALE)                         	
 

begl=`grep -n '<pre>' lasteq.asp  | gawk -F: '{print $1 +7 }' `
endl=`grep -n '</pre>' lasteq.asp | gawk -F: '{print $1 -2 }' `

sed -n "$begl,$endl"p lasteq.asp > tmplines


while IFS= read -r line; do

    ceqdt=`echo $line | gawk '{print $1"-"$2}' `
    t2=$( busybox date -u -d $ceqdt +"%s")
    
    if [[ $t2 -gt $t1 ]];
    then
        echo $t2 $line | gawk '{printf "%10i %10s  %10s %7s  %7s  %5s  %3s  %4s %3s %25s \n",$1,$2,$3,$4,$5,$6,$7,$8,$9,$10 }'     >> $tmpf
    fi

done < tmplines

nnewl=`wc -l $tmpf | gawk '{print $1}' `

if [[ $nnewl -gt 0 ]];
then
    cat $tmpf $stfile > tmp_scrtch
    cp -f $stfile  .
    mv -f tmp_scrtch $stfile
    echo " ==> The file $stfile is updated."
else
    echo " ==> The file $stfile is uptodate."
fi


rm $tmpf tmplines lasteq.asp*
