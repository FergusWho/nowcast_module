#!/bin/bash

CodeDir=$(dirname "$(realpath "$0")")
DataDir=${CodeDir/shared/data}

MinStartDate=$(date -udyesterday +%s)
MaxStartDate=$(date -udtoday +%s)

# redirect output to both stdout and mailx
{
   $CodeDir/FindSimulationProblems.sh -f yesterday -t today -p no

   for type in CME Flare; do
      echo
      echo "Successful $type simulations:"

      # find good simulations in the last 24 hours
      TZ=UTC awk -vMinStartDate=$MinStartDate -vMaxStartDate=$MaxStartDate '
         /.*\/.*OK$/ {
            y = substr($1, 1, 4)
            m = substr($1, 5, 2)
            d = substr($1, 7, 2)
            H = substr($1, 10, 2)
            M = substr($1, 12, 2)
            ut = mktime(y" "m" "d" "H" "M" 00")
            if (MinStartDate <= ut && ut < MaxStartDate) print
         }
      ' $DataDir/$type/status | sort -V \
      | while read run_dt dir status; do
         # get date-time prefix for iSWA files
         sim_dt=$(awk '/Simulation start date automatically extracted/{ print $6 }' $DataDir/$dir/log.txt)

         # count number of iSWA files for each file type
         files=$(ls $DataDir/staging/iswa \
         | awk -F'[_-]' -vdt=$sim_dt -vtype=$type '
            $0 ~ dt && $0 ~ type {
               ftype[$7]++
            }
            END {
               PROCINFO["sorted_in"] = "@ind_str_asc"
               for (t in ftype) print t":"ftype[t]
            }' \
         | paste -sd' ')

         # count number of related SEP scoreboard files
         nseps=0
         while read f; do
            f=$(basename $f .json)
            n=$(ls $DataDir/staging/sep_scoreboard/${f/_differential/}.* 2>/dev/null | wc -l)
            (( nseps += n ))
         done < <(find $DataDir/$dir -name 'ZEUS+iPATH*.json')

         echo "$run_dt $dir $status $files SEPSB:$nseps"
      done
   done
} \
|& tee >(mailx -s "iPATH rt-hpc-prod summary" -r m_ipath corti@hawaii.edu)
