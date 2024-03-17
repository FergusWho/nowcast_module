#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1

usage() {
   echo "$0 usage:" && grep "[[:space:]].)\ #" $0 \
   | sed 's/#//' \
   | sed -r 's/([a-z])\)/-\1/'
   exit 0
}

Types=Background,CME,Flare
while getopts ':hs:' flag; do
   case $flag in
      s) # <types>: comma-separated list of simulation types, any of Background, CME, and Flare. Default: all of them
         Types=${OPTARG};;
      h) # Show help
         usage;;
   esac
done

today=$(date -u +%Y%m%d)

cd $DataDir

declare -A ExtractDateTimeRegEx=(
   [CME]='s/.*:([0-9]+)-([0-9]+)-([0-9]+) ([0-9]+):([0-9]+):.*/\1\2\3_\4\5/'
   [Flare]='s/.*:([0-9]+)-([0-9]+)-([0-9]+) ([0-9]+):([0-9]+):.*/\1\2\3_\4\5/'
   [Background]='s/^([0-9]+)-([0-9]+)-([0-9]+) ([0-9]+):([0-9]+):.*/\1\2\3_\4\5/'
)
declare -A ExpectedCronJobs=(
   [CME]=96
   [Flare]=96
   [Background]=3
)

for type in ${Types//,/ }; do
   printf '=%.0s' $(seq $(( ${#type}+8 )))
   printf '\n'
   printf "=== $type ===\n"
   printf '=%.0s' $(seq $(( ${#type}+8 )))
   printf '\n'

   mkdir -p $type/lists

   echo "### Looking for missing cron jobs ..."
   touch $type/lists/missing-cron.list
   find cron/$type -type f -name '*.log' -printf '%f\n' \
   | cut -d'_' -f1 | sort -V | uniq -c \
   | awk -vn=${ExpectedCronJobs[$type]} '$1 != n{ printf "%s %d\n", $2, $1 }' \
   >$type/lists/missing-cron.new.list
   comm -3 \
      <(cut -d' ' -f1,2 $type/lists/missing-cron.new.list) \
      <(cut -d' ' -f1,2 $type/lists/missing-cron.list) \
   | grep -v $today
   echo

   echo "### Looking for mismatches between cron and status ..."
   comm -3 \
      <(find cron/$type -type f -name '*.log' -printf '%f\n' | cut -d'.' -f1 | sort -V) \
      <(cut -d' ' -f1 $type/status | sort -V) \
   | grep -v $today
   echo

   echo "### Looking for mismatches between status and log.txt ..."
   touch $type/lists/missing-log.list $type/lists/missing-status.list

   echo "    Missing from log.txt:"
   comm -2 -3 \
      <(cut -d' ' -f1 $type/status | sort -V) \
      <(sed -E "${ExtractDateTimeRegEx[$type]}" $type/log.txt | sort -Vu) \
   | grep -v $today \
   >$type/lists/missing-log.new.list
   comm -3 \
      <(cut -d' ' -f1 $type/lists/missing-log.new.list) \
      <(cut -d' ' -f1 $type/lists/missing-log.list)
   echo

   echo "    Missing from status:"
   comm -1 -3 \
      <(cut -d' ' -f1 $type/status | sort -V) \
      <(sed -E "${ExtractDateTimeRegEx[$type]}" $type/log.txt | sort -Vu) \
   | grep -v $today \
   >$type/lists/missing-status.new.list
   comm -3 \
      <(cut -d' ' -f1 $type/lists/missing-status.new.list) \
      <(cut -d' ' -f1 $type/lists/missing-status.list)
   echo

   echo "### Looking for mismatches between status and simulation folders ..."
   comm -3 \
      <(sed -En "/$type\//s|.* $type/(.*) .*|\1|p" $type/status | sort -V) \
      <(find $type -mindepth 1 -maxdepth 1 -type d ! -newermt $today -printf '%P\n' | grep -v lists | sort -V) \
   | grep -v $today
   echo

   [[ $type == Background ]] && {
      printf '\n\n\n'
      continue
   }

   echo "### Looking for mismatches between simulation folders and past.json ..."
   touch $type/lists/missing-simulations.list
   comm -3 \
      <(find $type -mindepth 1 -maxdepth 1 -type d -printf '%P\n' | grep -v lists | sort -V) \
      <(jq -r '.[] | ((.flrID // .associatedCMEID) | "\(.[:19] | gsub("[-:]"; ""))\(.[19:])") + (if .link == null then "" else .link | gsub(".*/(?<id>[0-9]+)/-1"; "_\(.id)") end)' $type/past.json | sort -V) \
   | tr '\t' ',' \
   | awk -F, 'NF==1{ print $1, "MissingLog" } NF==2{ print $2, "MissingSim" }' \
   > $type/lists/missing-simulations.new.list
   comm -3 \
      <(cut -d' ' -f1 $type/lists/missing-simulations.new.list) \
      <(cut -d' ' -f1 $type/lists/missing-simulations.list)
   echo

   printf '\n\n\n'
done

echo "After merging new issues, type:"
echo "rm $DataDir/*/lists/*.new.list"
