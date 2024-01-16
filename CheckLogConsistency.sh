#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1

usage() {
   echo "$0 usage:" && grep "[[:space:]].)\ #" $0 \
   | sed 's/#//' \
   | sed -r 's/([a-z])\)/-\1/'
   exit 0
}

while getopts ':h' flag; do
   case $flag in
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

for type in CME Flare Background; do
   printf '=%.0s' $(seq $(( ${#type}+8 )))
   printf '\n'
   printf "=== $type ===\n"
   printf '=%.0s' $(seq $(( ${#type}+8 )))
   printf '\n'

   echo "### Looking for missing cron jobs ..."
   touch $type/missing-cron.list
   ls cron/$type | cut -d'_' -f1 | sort -V | uniq -c \
   | awk -vn=${ExpectedCronJobs[$type]} '$1 != n{ printf "%s %2d\n", $2, $1 }' \
   >$type/missing-cron.new.list
   comm -3 \
      <(cut -d' ' -f1,2 $type/missing-cron.new.list) \
      <(cut -d' ' -f1,2 $type/missing-cron.list) \
   | grep -v $today
   echo

   echo "### Looking for mismatches between cron and status ..."
   comm -3 \
      <(ls cron/$type | cut -d'.' -f1 | sort -V) \
      <(cut -d' ' -f1 $type/status | sort -V) \
   | grep -v $today
   echo

   echo "### Looking for mismatches between status and log.txt ..."
   touch $type/missing-log.list
   grep -Ff <(
         comm -2 -3 \
            <(cut -d' ' -f1 $type/status | sort -V) \
            <(sed -E "${ExtractDateTimeRegEx[$type]}" $type/log.txt | sort -Vu)
      ) $type/status \
      >$type/missing-log.new.list
   comm -3 \
      <(cut -d' ' -f1 $type/missing-log.new.list) \
      <(cut -d' ' -f1 $type/missing-log.list)
   echo

   echo "### Looking for mismatches between status and simulation folders ..."
   comm -3 \
      <(sed -En "/$type\//s|.* $type/(.*) .*|\1|p" $type/status | sort -V) \
      <(find $type -mindepth 1 -maxdepth 1 -type d -printf '%P\n' | sort -V) \
   | grep -v $today
   echo

   printf '\n\n\n'
done
