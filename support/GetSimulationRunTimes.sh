#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1

print_stats() {
   local file=$1
   local col=$2
   local type=$3

   awk -vcol=$col -vtype=$type -vMinStartDate=$MinStartDate -vMaxStartDate=$MaxStartDate \
      -vOnlyGood=$OnlyGood -vSkipShort=$SkipShort '
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
         # skip short (i.e., failed) runs
         if (colname) {
            for (c = 4; c <= NF; ++c) {
               if ($c == colname) col = c+1
            }
         }
         if (!col || (SkipShort && $col < 10)) next

         t = $col/60
         avg += t
         std += t*t
         rt[++n] = t
      }

      END {
         if (!n) exit

         asort(rt)

         if (n % 2) t_med = rt[int(n/2)+1]
         else t_med = 0.5*(rt[n/2] + rt[n/2+1])

         n5 = sprintf("%.0f", 0.05*n) + 0
         if (n5 == 0) n5 = 1
         t_5 = rt[n5]
         t_95 = rt[n-n5+1]

         t_m = rt[1]
         t_M = rt[n]

         avg /= n
         std = n > 1 ? sqrt(n/(n-1)*(std/n - avg*avg)) : 0

         printf "%11s | %5d | %3.0fm %3.0fm %3.0fm | %3.0fm %3.0fm | %3.0fm %3.0fm\n",
            type, n, t_5, t_med, t_95, avg, std, t_m, t_M
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
      l) # Skip short simulations (<10 s): this usually means failed simulation. Default: use all simulations
         (( SkipShort = 1 ));;
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
(( SkipShort )) && sim_selection="${sim_selection}${sim_selection:+, }not short"
[[ -z $sim_selection ]] && sim_selection='all'

MinStartDate=$(date -ud"${From:-20230101}" +%s)
MaxStartDate=$(date -ud"${To:-now}" +%s)

[[ $Progress == no ]] && Progress=0 || Progress=1

# make sure SLURM programs are in PATH
which sacct &>/dev/null || {
   source /etc/profile.d/slurm.sh
}

echo "Run times for simulations ($sim_selection) between $(date -ud@$MinStartDate +'%F %T') and $(date -ud@$MaxStartDate +'%F %T')"

cd $DataDir
for type in ${Types//,/ }; do
   printf "\nAnalyzing $type runs "

   (( Recreate )) && rm -rf $type/runtimes
   touch $type/runtimes

   ntot=$(find $type -mindepth 2 -maxdepth 2 -type d | wc -l)
   len=${#ntot}
   (( del = 2*len + 3 ))

   (( Progress )) && printf '[%*d/%*d]' $len 0 $len $ntot || printf $ntot

   (( n = 0 ))
   while read dir; do
      (( ++n ))
      (( Progress )) && printf '\033[%dD[%*d/%*d]' $del $len $n $len $ntot

      grep -q $dir $type/runtimes && continue

      log=$dir/log.txt
      [[ ! -f $log ]] && continue

      # read status from status DB
      status=$(awk -vdir=$dir '$2 ~ dir { print $3 }' $type/status)
      [[ -z $status || $status == RUNNING* ]] && continue

      end_date=$(TZ=UTC awk 'END{ print mktime(gensub("[:-]+", " ", "g", substr($0, 2, 19))) }' $log)

      log=$(grep -lRF $dir cron/$type)
      [[ -z $log ]] && continue
      start_date=$(TZ=UTC awk 'NR==2{ print mktime(gensub("[:-]+", " ", "g", substr($0, 2, 19))) }' $log)

      {
         echo -n $dir $status $start_date 'Total' $(( end_date-start_date ))

         find $dir -name 'slurm-*' \
         | sort -V \
         | while read f; do
            [[ $f == *transport* ]] && loc=$(echo $f | sed -E 's|.*/transport_([^/]+)/.*|\1|') || loc=ZEUS
            jid=$(echo $f | sed -E 's/.*-([0-9]+)\..*/\1/')
            slurm_runtime=$(sacct -j $jid -nPX -oelapsedraw)
            echo -n " $loc" $slurm_runtime
         done

         echo
      } >>$type/runtimes
   done < <(
      find $type -mindepth 2 -maxdepth 2 -type d
   )

   sort -V $type/runtimes >$type/runtimes.sort
   mv $type/runtimes.sort $type/runtimes

   printf "\n"
   printf -- '--------------------------------------------------------------------\n'
   printf '%11s | %5s | %4s %4s %4s | %4s %4s | %4s %4s\n' "Job type" Runs 5% 50% 95% Avg Std Min Max
   printf -- '--------------------------------------------------------------------\n'

   print_stats $type/runtimes ZEUS

   awk '{
      for (c = 6; c <= NF; c += 2) if ($c != "ZEUS") print $c
   }' $type/runtimes \
   | sort -Vu \
   | while read obs; do
      print_stats $type/runtimes $obs
   done

   print_stats $type/runtimes Total

   printf -- '--------------------------------------------------------------------\n'
done