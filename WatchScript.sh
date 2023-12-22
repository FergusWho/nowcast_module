#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1
cd $DataDir

w=$(tput cols)
n=$(( w/38 ))

echo "  --- Simulation jobs ---"
squeue --me -h -o "%.18i %.10M %.6D %R %Z" \
| column -t
echo

echo "  --- Simulation logs (most recent 10/type) ---"
find -mindepth 3 -maxdepth 3 -type f -name log.txt -printf "%P\n" \
| sort -rV \
| awk '
   $0 ~ /Background/ && nbkg < 10 { ++nbkg; print $0 }
   $0 ~ /CME/ && ncme < 10 { ++ncme; print $0 }
   $0 ~ /Flare/ && nflr < 10 { ++nflr; print $0 }' \
| sort -rV \
| xargs wc -l \
| sed -E -e'$d' -e"s|[^ /]+/||" -e"s|/log.txt||" \
| pr -${n}T -W$w
echo

n=$(( w/32 ))
echo "  --- cron logs (most recent 10/type) ---"
find cron -type f \
| sort -rV \
| awk '
   $0 ~ /Background/ && nbkg < 10 { ++nbkg; print $0 }
   $0 ~ /CME/ && ncme < 10 { ++ncme; print $0 }
   $0 ~ /Flare/ && nflr < 10 { ++nflr; print $0 }' \
| sort -rV \
| xargs wc -l \
| sed -E -e'$d' -e"s|cron/||" -e"s/.log//" \
| pr -${n}T -W$w
echo

n=$(( w/42 ))
echo " --- staging area: iSWA (most recent 10/type) ---"
find staging/iswa -type f -printf '%P\n' \
| sort -rV \
| cut -d'_' -f1-6 \
| uniq -c \
| awk '
   $0 ~ /iPATH_CME/ && ncme < 10 { ++ncme; print $0 }
   $0 ~ /iPATH_Flare/ && nflr < 10 { ++nflr; print $0 }' \
| sort -k2rV \
| sed -E -e's/ZEUS\+iPATH_//' \
| pr -${n}T -W$w
echo

n=$(( w/51 ))
echo " --- staging area: SEP scoreboard (most recent 10/type) ---"
find staging/sep_scoreboard -type f -printf '%P\n' \
| sort -rV \
| cut -d'.' -f1-3 \
| uniq -c \
| awk '
   $0 ~ /iPATH_CME/ && ncme < 10 { ++ncme; print $0 }
   $0 ~ /iPATH_Flare/ && nflr < 10 { ++nflr; print $0 }' \
| sort -k2rV \
| sed -E -e's/ZEUS\+iPATH_//' -e's/_differential//' \
| pr -${n}T -W$w
