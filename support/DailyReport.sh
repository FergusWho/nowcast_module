#!/bin/bash

CodeDir=$(dirname "$(realpath "$0")")
DataDir=${CodeDir/shared/data}

MinStartDate=$(date -udyesterday +%s)
MaxStartDate=$(date -udtoday +%s)

# redirect output to both stdout and mailx
{
   $CodeDir/FindSimulationProblems.sh -f yesterday -t today -p no

   # silently update data size and run time DBs
   $CodeDir/GetSimulationDataSize.sh -f yesterday -t today -p no &>/dev/null
   $CodeDir/GetSimulationRunTimes.sh -f yesterday -t today -p no &>/dev/null

   for type in CME Flare; do
      echo
      echo "Successful $type simulations:"

      # find good simulations in the last 24 hours
      # select also good simulations in the last 48 hours, to include possible RUNNING simulations from previous day
      TZ=UTC awk -vMinStartDate=$MinStartDate -vMaxStartDate=$MaxStartDate '
         /.*\/.*OK$/ {
            y = substr($1, 1, 4)
            m = substr($1, 5, 2)
            d = substr($1, 7, 2)
            H = substr($1, 10, 2)
            M = substr($1, 12, 2)
            ut = mktime(y" "m" "d" "H" "M" 00")
            if (MinStartDate-86400 <= ut && ut < MaxStartDate) print
         }
      ' $DataDir/$type/status | sort -V \
      | while read run_dt dir status; do
         # check if simulation finished to run in the last 24 hours
         ut=$(stat -c %Y $DataDir/$dir/log.txt)
         (( ut < MinStartDate )) && continue

         # get date-time prefix for iSWA files
         sim_dt=$(awk '/Simulation start date automatically extracted/{ print $6; exit }' $DataDir/$dir/log.txt)

         # count number of iSWA files for each file type
         files=$(find $DataDir/staging/iswa -name "*_${type}_${sim_dt}_*" -printf '%P\n' \
         | awk -F'[_-]' '
            {
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

   echo
   df -h /data
} \
|& tee >(mailx -s "iPATH rt-hpc-prod summary" -r m_ipath corti@hawaii.edu)
