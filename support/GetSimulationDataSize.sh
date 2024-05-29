#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1

print_stats() {
   local file=$1
   local col=$2
   local type=$3

   awk -vcol=$col -vtype=$type -vMinStartDate=$MinStartDate -vMaxStartDate=$MaxStartDate \
      -vOnlyGood=$OnlyGood -vSkipSmall=$SkipSmall '
      BEGIN {
         if (!type && col !~ /^[0-9]+$/) {
            type = colname = col
            col = 0
         }
      }

      ($3 >= MinStartDate && $3 < MaxStartDate) {
         # skip failed simulations, if requested
         if (OnlyGood && $2 != "OK") next

         # check that we have a valid column (in case col was originally a text)
         # skip small (i.e., failed) runs
         if (colname) {
            for (c = 4; c <= NF; ++c) {
               if ($c == colname) col = c+1
            }
         }
         if (!col || (SkipSmall && $col < 200)) next

         s = $col/1024
         avg += s
         std += s*s
         ds[++n] = s
      }

      END {
         if (!n) exit

         asort(ds)

         if (n % 2) s_med = ds[int(n/2)+1]
         else s_med = 0.5*(ds[n/2] + ds[n/2+1])

         n5 = sprintf("%.0f", 0.05*n) + 0
         if (n5 == 0) n5 = 1
         s_5 = ds[n5]
         s_95 = ds[n-n5+1]

         s_m = ds[1]
         s_M = ds[n]

         avg /= n
         std = n > 1 ? sqrt(n/(n-1)*(std/n - avg*avg)) : 0

         printf "%11s | %5d | %3.0fMB %3.0fMB %3.0fMB | %3.0fMB %3.0fMB | %3.0fMB %3.0fMB\n",
            type, n, s_5, s_med, s_95, avg, std, s_m, s_M
      }
   ' $file
}

usage() {
   echo "$0 usage:" && grep "[[:space:]].)\ #" $0 \
   | sed 's/#//' \
   | sed -r 's/([a-z])\)/-\1/'
   exit 0
}

Types=Background,CME,Flare
while getopts ':hrglf:t:s:' flag; do
   case $flag in
      r) # Force processing all simulations. Default: skip already processed simulations
         (( Recreate = 1 ));;
      g) # Display statistics only for successful simulations. Default: use all simulations
         (( OnlyGood = 1 ));;
      l) # Skip small size simulations (<200 kB): this usually means failed simulation. Default: use all simulations
         (( SkipSmall = 1 ));;
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

(( OnlyGood )) && sim_selection='successful'
(( SkipSmall )) && sim_selection="${sim_selection}${sim_selection:+, }not small"
[[ -z $sim_selection ]] && sim_selection='all'

MinStartDate=$(date -ud"${From:-20230101}" +%s)
MaxStartDate=$(date -ud"${To:-now}" +%s)

[[ $Progress == no ]] && Progress=0 || Progress=1

echo "Data size for simulations ($sim_selection) between $(date -ud@$MinStartDate +'%F %T') and $(date -ud@$MaxStartDate +'%F %T')"

cd $DataDir
for type in ${Types//,/ }; do
   printf "\nAnalyzing $type runs "

   (( Recreate )) && rm -rf $type/datasize
   touch $type/datasize

   ntot=$(find $type -mindepth 2 -maxdepth 2 -type d | wc -l)
   len=${#ntot}
   (( del = 2*len + 3 ))

   (( Progress )) && printf '[%*d/%*d]' $len 0 $len $ntot || printf $ntot

   (( n = 0 ))
   while read dir; do
      (( ++n ))
      (( Progress )) && printf '\033[%dD[%*d/%*d]' $del $len $n $len $ntot

      grep -q $dir $type/datasize && continue

      log=$dir/log.txt
      [[ ! -f $log ]] && continue

      # read status from status DB
      status=$(awk -vdir=$dir '$2 ~ dir { print $3 }' $type/status)
      [[ -z $status || $status == RUNNING* ]] && continue

      log=$(grep -lRF $dir cron/$type)
      [[ -z $log ]] && continue
      start_date=$(TZ=UTC awk 'NR==2{ print mktime(gensub("[:-]+", " ", "g", substr($0, 2, 19))) }' $log)

      {
         tot=$(du -s $dir | awk '{ print $1 }')
         echo -n $dir $status $start_date Total $tot

         while read loc; do
            obs=$(du -s $dir/$loc | awk '{ print $1 }')
            echo -n " ${loc/path_output\/transport_} $obs"
            (( tot -= obs ))
         done < <(
            find $dir -name 'transport_*' -printf '%P\n' \
            | sort -V
         )
         echo " ZEUS $tot"
      } >>$type/datasize
   done < <(
      find $type -mindepth 2 -maxdepth 2 -type d
   )

   sort -V $type/datasize >$type/datasize.sort
   mv $type/datasize.sort $type/datasize

   printf "\n"
   printf -- '--------------------------------------------------------------------\n'
   printf '%11s | %5s | %5s %5s %5s | %5s %5s | %5s %5s\n' "Job type" Runs 5% 50% 95% Avg Std Min Max
   printf -- '--------------------------------------------------------------------\n'

   print_stats $type/datasize ZEUS

   awk '{
      for (c = 6; c <= NF; c += 2) if ($c != "ZEUS") print $c
   }' $type/datasize \
   | sort -Vu \
   | while read obs; do
      print_stats $type/datasize $obs
   done

   print_stats $type/datasize Total

   printf -- '--------------------------------------------------------------------\n'
done
