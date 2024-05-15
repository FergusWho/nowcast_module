#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1
cd $DataDir

w=$(tput cols)

echo "  --- Simulation jobs ---"
squeue --me -h -o "%.18i %.10M %.6D %R %Z" \
| column -t
echo

n=$(( w/38 ))
echo "  --- Simulation logs (most recent 10/type) ---"
find Background CME Flare -mindepth 3 -maxdepth 3 -type f -name log.txt -printf '%T@ %p\n' \
| sort -k1rg,1 \
| awk '(/Background/ && ++nbkg <= 10) || (/CME/ && ++ncme <= 10) || (/Flare/ && ++nflr <= 10){ print $2 }' \
| sort -s -k1.1,1.3 \
| xargs awk 'ENDFILE{ n = split(FILENAME, p, "/"); printf "%4d %s\n", FNR, p[1]"/"p[n-1] }' \
| pr -${n}T -W$w
echo

n=$(( w/32 ))
echo "  --- cron logs (most recent 10/type) ---"
find cron -type f -printf '%T@ %p\n' \
| sort -k1rg,1 \
| awk '(/Background/ && ++nbkg <= 10) || (/CME/ && ++ncme <= 10) || (/Flare/ && ++nflr <= 10){ print $2 }' \
| sort -s -k1.7,1.9 \
| xargs awk 'ENDFILE{ n = split(FILENAME, p, /[/.]/); print FNR, p[2]"/"p[n-1] }' \
| pr -${n}T -W$w
echo

n=$(( w/42 ))
echo " --- staging area: iSWA (most recent 10/type) ---"
find staging/iswa -type f -printf '%P\n' \
| sort -t'_' -k5,6rV \
| cut -d'_' -f2-6 \
| uniq -c \
| awk '(/CME/ && ++ncme <= 10) || (/Flare/ && ++nflr <= 10){ print $1, $2 }' \
| sort -s -k2.1,2.3 \
| pr -${n}T -W$w
echo

n=$(( w/48 ))
echo " --- staging area: SEP scoreboard (most recent 10/type) ---"
find staging/sep_scoreboard -type f -printf '%P\n' \
| sort -t'.' -k3rV \
| cut -d'.' -f1-3 \
| uniq -c \
| awk '(/CME/ && ++ncme <= 10) || (/Flare/ && ++nflr <= 10){ gsub(/ZEUS\+iPATH_|_differential/, ""); print $1, $2 }' \
| sort -s -k2.1,2.3 \
| pr -${n}T -W$w
