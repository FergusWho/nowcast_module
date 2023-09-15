#!/bin/bash

DataDir=/data/iPATH/nowcast_module_v1

usage() {
   echo "$0 usage:" && grep "[[:space:]].)\ #" $0 \
   | sed 's/#//' \
   | sed -r 's/([a-z])\)/-\1/'
   exit 0
}

Types=Background,CME,Flare
while getopts ':hrf:t:s:' flag; do
   case $flag in
      r) # Force processing all simulations. Default: skip already processed simulations
         (( Recreate = 1 ));;
      f) # <from>: select only simulations with start date after <from>. Same format as date -d<from>. Default: 2023/01/01
         From=${OPTARG};;
      t) # <to>: select only simulations with start date till <to>. Same format as date -d<to>. Default: now
         To=${OPTARG};;
      s) # <types>: comma-separated list of simulation types, any of Background, CME, and Flare. Default: all of them
         Types=${OPTARG};;
      h) # Show help
         usage;;
   esac
done

MinStartDate=$(date -ud"${From:-20230101}" +%s)
MaxStartDate=$(date -ud"${To:-now}" +%s)

# build modification time tests for find command
[[ ! -z $From ]] && from_test="-newermt $From"
[[ ! -z $To ]] && to_test="! -newermt $To"

echo "Simulations with problems between $(date -ud@$MinStartDate +'%F %T') and $(date -ud@$MaxStartDate +'%F %T')"

cd $DataDir
for type in ${Types//,/ }; do
   printf "\nAnalyzing $type runs "

   (( Recreate )) && rm -rf $type/status
   touch $type/status

   # remove running simulations from DB, so they are not duplicated when
   # analyzed again below
   sed -Ei '/RUNNING/d' $type/status

   logs=($(find cron/$type -name '*.log' $from_test $to_test | sort -V | paste -sd' '))

   ntot=${#logs[@]}
   len=${#ntot}
   (( del = 2*len + 3 ))

   printf '[%*d/%*d]' $len 0 $len $ntot

   (( n = 0 ))
   for cron_log in ${logs[@]}; do
      (( ++n ))
      printf '\033[%dD[%*d/%*d]' $del $len $n $len $ntot

      run_time=$(basename -s .log $cron_log)

      grep -qF $run_time $type/status && continue

      # parse cron log
      [[ -s $cron_log ]] && {
         cron_status=$(awk -vtype=$type '
            /exit/ {
               if ($0 ~ /There is no (CME|flare)/) OK = 1
               else exited = 1
            }

            (/error/ && !/error\.[of]/) || /Error/ {
               error = 1
            }

            /Switching to/ {
               OK = 1
            }

            END {
               if (exited) status = "Exit"
               else if (OK) status = "OK"
               if (error) status = (status ? status "," : "") "Error"
               print status
            }
         ' $cron_log)
      } || {
         cron_status=''
      }

      dir=$(sed -En "/Switching/s|.*($type/.*)/log\.txt|\1|p" $cron_log)
      [[ -z $dir && $type == Background ]] && dir=$type/$run_time
      [[ ! -z $dir && ! -d $dir ]] && dir=''
      if [[ -z $dir ]]; then
         echo "$run_time $type cron:$cron_status" >>$type/status
         continue
      fi

      # parse simulation log
      log=$dir/log.txt
      if [[ ! -s $log ]]; then
         log_status='MissingLog'
      else
         log_status=$(awk -vtype=$type '
            /exit/ {
               exited = 1
            }

            (/error/ && !/error\.[of]/) || /Error/ {
               error = 1
            }

            /No such file/ {
               missing_file = 1
            }

            type == "Background" && /Cleaning up/ {
               last = 1
            }
            type != "Background" && /Copying output files to the staging area/ {
               last = 1
            }
            last && /Done/ {
               OK = 1
            }

            END {
               if (exited) status = "Exit"
               else if (OK) status = "OK"
               if (error) status = (status ? status "," : "") "Error"
               if (missing_file) status = (status ? status "," : "") "MissingFile"
               print status
            }
         ' $log)

         # simulation is still running, skip it
         [[ $log_status != OK* && $log_status != Exit* ]] && {
            echo $run_time $dir RUNNING >>$type/status
            continue
         }
      fi

      # parse SLURM logs
      slurm_status=''
      while read slurm_log; do
         [[ $slurm_log == *transport* ]] && job=$(echo $slurm_log | sed -E 's|.*/transport_([^/]+)/.*|\1|') || job=ZEUS
         if zcat $slurm_log | grep -qE '[Ee]rror'; then
            [[ -z $slurm_status ]] && slurm_status='Job'
            slurm_status="$slurm_status:$job"
         fi
      done < <(find $dir -name slurm*)

      [[ $cron_status == OK ]] && status='' || status="${cron_status:+cron:$cron_status}"
      [[ ! -z $status ]] && status="$status,"
      if [[ ! -z $slurm_status ]]; then
         [[ $log_status == OK ]] && status="$status$slurm_status" || status="$status$log_status,$slurm_status"
      else
         status="$status$log_status"
      fi
      echo $run_time $dir $status >>$type/status
   done

   printf "\n"

   TZ=UTC awk -vMinStartDate=$MinStartDate -vMaxStartDate=$MaxStartDate '
      !/OK$/ {
         y = substr($1, 1, 4)
         m = substr($1, 5, 2)
         d = substr($1, 7, 2)
         H = substr($1, 10, 2)
         M = substr($1, 12, 2)
         ut = mktime(y" "m" "d" "H" "M" 00")
         if (MinStartDate <= ut && ut < MaxStartDate) print
      }
   ' $type/status | sort -V
done
