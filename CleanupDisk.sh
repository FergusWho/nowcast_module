#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1

usage() {
   echo "$0 usage:" && grep "[[:space:]].)\ #" $0 \
   | sed 's/#//' \
   | sed -r 's/([a-z])\)/-\1/'
   exit 0
}

Types=Background,CME,Flare
while getopts ':hrf:t:s:p:' flag; do
   case $flag in
      f) # <from>: select only simulations with start date after <from>. Same format as date -d<from>. Default: 2023/01/01
         From=${OPTARG};;
      t) # <to>: select only simulations with start date till <to>. Same format as date -d<to>. Default: now
         To=${OPTARG};;
      s) # <types>: comma-separated list of simulation types, any of Background, CME, and Flare. Default: all of them
         Types=${OPTARG};;
      p) # <progress>: show (or not) a progress bar: yes or no (case insensitive). Default: yes
         Progress=${OPTARG,,};;
      h) # Show help
         usage;;
   esac
done

MinStartDate=$(date -ud"${From:-20230101}" +%s)
MaxStartDate=$(date -ud"${To:-now}" +%s)

[[ $Progress == no ]] && Progress=0 || Progress=1

# build modification time tests for find command
[[ ! -z $From ]] && from_test="-newermt $From"
[[ ! -z $To ]] && to_test="! -newermt $To"

echo "Cleaning up disk space for simulations between $(date -ud@$MinStartDate +'%F %T') and $(date -ud@$MaxStartDate +'%F %T')"

echo
echo "Disk usage before:"
df -h /data

cd $DataDir
for type in ${Types//,/ }; do
   echo
   du -hs $type | awk '{ printf "%s size before cleaning: %s ", $2, $1 }'

   dirs=($(find $type -name dzeus36 $from_test $to_test -printf '%h\n'))

   ntot=${#dirs[@]}
   len=${#ntot}
   (( del = 2*len + 3 ))

   (( Progress )) && printf '[%*d/%*d]' $len 0 $len $ntot

   (( n = 0 ))
   for dir in ${dirs[@]}; do
      (( ++n ))
      (( Progress )) && printf '\033[%dD[%*d/%*d]' $del $len $n $len $ntot

      [[ $type == Background ]] && {
         files=($(find $dir -type f ! \( -name '*.json' -o -name 'z*JH' -o -name '*.gz' -o -name log.txt \) -printf '%P\n'))
         tar -C $dir --remove-files -czf $dir/files.tar.gz ${files[@]}
         rm -rf $dir/dzeus3.6
      } || {
         find $dir -type f ! \( -path '*/path_output/*' -o -name '*.json' -o -name '*.gz' -o -name log.txt \) -delete
      }
   done

   echo
   du -hs $type | awk '{ printf "%s size after cleaning: %s\n", $2, $1 }'
done

echo
echo "Disk usage after:"
df -h /data
