#!/bin/bash

cleanup_acceleration_files() {
   echo "[$(date -u +'%F %T')] Cleaning up acceleration files ..."

   cd $CME_dir/path_output

   # compress intermediate acceleration files
   for f in observer_pov.dat kappa-par-perp.dat all_shell_bndy.dat dist_at_shock.dat esc_distr*.dat momenta-hi.dat solar_wind_profile.dat; do
      [[ -s $f ]] && gzip $f
   done

   # remove unneeded intermediate acceleration files
   rm -f dist_all_shl.dat

    echo "[$(date -u +'%F %T')] Done"
}

# default values for CCMC AWS on rt-hpc-prod
iPATH_dir='/shared/iPATH/ipath_v2'
code_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'
opsep_dir='/shared/iPATH/operational_sep_v3'

MPI_comp='mpif90'
FCOMP='gfortran'

echo "-------------- Flare Module --------------"

# default values for command-line arguments
run_time=$(date -u +'%Y%m%d_%H%M')
if_local=0
Observers=(earth)

# testing for specific event:
# example: bash flare.sh -t 20220120_0830
# rerun already processed event:
# example: bash flare.sh -t 20230819_1715 -i 20230818T220000-FLR-001
# rerun already processed event, but skip all jobs:
# example: bash flare.sh -t 20230819_1715 -i 20230818T220000-FLR-001 -S
while getopts 't:i:LS' flag
do
    case "${flag}" in
        t) run_time=${OPTARG};;
        L) if_local=1;;
        i) CME_id=${OPTARG};;
        S) skip_jobs=1;;
    esac
done
echo "[$(date -u +'%F %T')] Run time: $run_time"

if [ $if_local -eq 1 ]
then
    # change these accordingly if you want to run locally
    iPATH_dir=$HOME'/iPATH2.0'
    code_dir=$HOME'/nowcast_module'
    thread_count=12
else
    source $code_dir/set_environment.sh
    thread_count=128
fi
echo "-----------------------------------------"
echo

if [[ -z $CME_id ]]; then
   # look for new flares from DONKI
   # create the input parameters files for Earth: $bgsw_folder_name/${run_time}_flare_earth_input.json
   # last line is: bgsw_folder_name flare_id
   # read last line of output from check_flare.py
   echo "[$(date -u +'%F %T')] Checking for new flares ..."
   last_line=$(python3 $code_dir/check_flare.py --root_dir $data_dir --run_time $run_time --model_mode forecast | tail -n 1)
   echo "[$(date -u +'%F %T')] Done"
   echo

   IFS=' '
   read -a strarr <<<$last_line
   bgsw_folder_name=${strarr[0]}
   bkg_dir=$data_dir/Background/${bgsw_folder_name:0:4}/$bgsw_folder_name
   CME_id=${strarr[1]}     # this is actually flare_id
   only_time_changed=${strarr[2]}

   [[ $only_time_changed == True ]] && skip_jobs=2

   echo "[$(date -u +'%F %T')] Background simulation: $bgsw_folder_name"

   # exit if no flare or if no background simulation exists
   if [[ -z $bgsw_folder_name ]]; then
      echo "[$(date -u +'%F %T')] There is no flare: exit"
      exit 1
   elif [[ $bgsw_folder_name == MISSING_BKG* ]]; then
      # check_flare.py could not find the background folder
      # this happens when:
      # - a simulation is triggered within 10 seconds of the background cron job
      # start time (00, 08, 16); in this case, since the flare has not been added
      # to past.json, it will be retried in the next cron
      # - grepSW.py failed to download any of the needed data; in this case,
      # since check_flare.py tried to find the previous background folder, it means
      # the last 2 background simualations failed: most likely there are issues
      # with the AWS instance or with iSWA servers
      echo "[$(date -u +'%F %T')] Background simulation not found: exit"
      exit 1
   elif [[ ! -f $bkg_dir/zr006JH ]]; then
      # the background simulation is not done yet or it failed

      # retrieve job id, eventually waiting up to 2 minutes for its submission
      # jobs are always submitted within 2 minutes from the background cron job start time
      jobid=$(awk '/Submitted batch job/{ print $4 }' $bkg_dir/log.txt)
      (( n = 1, MAX_WAIT = 12 ))
      while (( jobid == 0 && n <= MAX_WAIT )); do
         echo "[$(date -u +'%F %T')] Waiting for ZEUS job to be submitted [$n/$MAX_WAIT] ..."
         sleep 10s
         jobid=$(awk '/Submitted batch job/{ print $4 }' $bkg_dir/log.txt)
         (( ++n ))
      done

      (( jobid == 0 )) && {
         # NB: the CME has already been added to past.json, so it won't be
         # rerun in the next cron; if the background simulation is still running
         # or it has been manually fixed, then this CME needs to be manually
         # rerun
         echo "[$(date -u +'%F %T')] Background simulation failed or taking longer than expected: exit"
         exit 1
      }

      # retrieve job status, eventually waiting up to 70 minutes for its completion
      # 95% of the background simulations are completed within 70 minutes
      job_status=$(sacct -j $jobid -P -X -n -ostate 2>/dev/null)
      (( n = 1, MAX_WAIT = 70 ))
      while [[ $job_status != COMPLETED && $n -le $MAX_WAIT ]]; do
         echo "[$(date -u +'%F %T')] Waiting for ZEUS job $jobid to finish (status = $job_status) [$n/$MAX_WAIT] ..."
         sleep 1m
         job_status=$(sacct -j $jobid -P -X -n -ostate 2>/dev/null)
         (( ++n ))
      done

      [[ $job_status != COMPLETED || ! -f $bkg_dir/zr006JH ]] && {
         # NB: the flare has already been added to past.json, so it won't be
         # rerun in the next cron; if the background simulation is still running
         # or it has been manually fixed, then this flare needs to be manually
         # rerun
         echo "[$(date -u +'%F %T')] Background simulation failed or taking longer than expected: exit"
         exit 1
      }
   fi
else
   echo "[$(date -u +'%F %T')] Requested flare id: $CME_id"

   hour=${CME_id:9:2}

   # remove leading zero, otherwise Bash interprets it as hex number
   [[ ${hour:0:1} == 0 ]] && hour=${hour:1}

   if (( hour < 8 )); then
      hour=00
   elif (( hour < 16 )); then
      hour=08
   else
      hour=16
   fi
   bgsw_folder_name=${CME_id%%T*}_${hour}00
   bkg_dir=$data_dir/Background/${bgsw_folder_name:0:4}/$bgsw_folder_name

   echo "[$(date -u +'%F %T')] Background simulation: $bgsw_folder_name"
fi

#-----------------------------------------------
# CME setup and acceleration:
CME_dir=$data_dir/Flare/${CME_id:0:4}/$CME_id
logfile=$CME_dir/log.txt

# make sure correct folder hierarchy exists
mkdir -p $data_dir/CME/${CME_id:0:4}

(( skip_jobs == 1 )) && [[ ! -d $CME_dir ]] && {
   echo "[$(date -u +'%F %T')] Simulation folder $CME_dir does not exists; disabling skipping jobs"
   skip_jobs=0
}

# use the most recent previous flare version folder as starting point, if available
# this can only happen if check_flare.py detects that only start and/or peak time changed
if (( skip_jobs == 2 )); then
   version=${CME_id#*_}
   for (( v = version-1; v > 0; --v )); do
      previous_dir=${CME_dir/_$version/_$v}
      [[ -d $previous_dir ]] && break || previous_dir=
   done

   if [[ ! -z $previous_dir ]]; then
      # retrieve previous simulation status, eventually waiting up to 96 minutes for its completion
      # 95% of the background simulations are completed within 96 minutes
      prev_status=$(awk '/Cleanup and exit/{ print "ERROR" } /SLURM jobs summary/{ print "OK" }' $previous_dir/log.txt 2>/dev/null)
      (( n = 0, MAX_WAIT = 96 ))
      while [[ -z $prev_status && $n -lt $MAX_WAIT ]]; do
         echo "[$(date -u +'%F %T')] Waiting for previous flare version simulation to finish ..."
         sleep 1m
         prev_status=$(awk '/Cleanup and exit/{ print "ERROR" } /SLURM jobs summary/{ print "OK" }' $previous_dir/log.txt 2>/dev/null)
         (( ++n ))
      done

      [[ $prev_status == OK && -f $previous_dir/path_output/transport_earth/fp.tar.gz ]] && {
         echo "[$(date -u +'%F %T')] Copying previous flare version simulation $previous_dir to $CME_dir ..."
         cp -r $previous_dir $CME_dir
         echo "[$(date -u +'%F %T')] Done"
      } || {
         echo "[$(date -u +'%F %T')] Previous flare version simulation $previous_dir not completed yet or exited with error: skipping jobs disabled"
         skip_jobs=0
      }
   else
      echo "[$(date -u +'%F %T')] No previous flare version folder found: skipping jobs disabled"
      skip_jobs=0
   fi
fi

if (( skip_jobs )); then
   echo "[$(date -u +'%F %T')] Skipping jobs enabled"

   [[ -d $CME_dir && $skip_jobs -eq 1 ]] && {
      echo "[$(date -u +'%F %T')] Copying already existent simulation folder to $CME_dir.bak"
      cp -r $CME_dir $CME_dir.bak
   }

   echo "[$(date -u +'%F %T')] Setting up necessary files for skipping jobs ..."
   cp $bkg_dir/${run_time}_*.json $CME_dir/
   rm -f $CME_dir/log.txt
   rm -f $CME_dir/path_output/{CME.gif,staging.info}
   rm -f $CME_dir/path_output/transport_*/{ZEUS+iPATH*,*.csv,*.txt,*.png,*.pkl}
   for dir in $CME_dir/path_output/transport_*; do
      tar -xzf $dir/fp.tar.gz -C $dir fp_total
   done
   echo "[$(date -u +'%F %T')] Done"
else
   [[ -d $CME_dir ]] && {
      echo "[$(date -u +'%F %T')] Renaming already existent simulation folder to $CME_dir.bak"
      mv $CME_dir $CME_dir.bak
   }

   echo "[$(date -u +'%F %T')] Copying background simulation to $CME_dir ..."
   cp -r $bkg_dir $CME_dir

   # use the modified dzeus36 version for nowcasting
   cp $code_dir/dzeus36_alt $CME_dir/dzeus36

   # remove background simulation log
   rm $CME_dir/log.txt
   echo "[$(date -u +'%F %T')] Done"
fi

echo
echo "[$(date -u +'%F %T')] Switching to $logfile"

# redirect everything to the logfile
{
    cd $CME_dir

    echo "[$(date -u +'%F %T')] Flare found! Checking Time: $run_time"
    echo "[$(date -u +'%F %T')] Flare id: $CME_id"

    trspt_dir=$CME_dir/path_output/transport_earth

    if (( !skip_jobs )); then
      # delete residual files created by other CME/Flare simulations in the copied Background folder
      echo "[$(date -u +'%F %T')] Deleting residual files ..."
      rm -f slurm* # Slurm logfiles from Background simulation
      find -type f -name '*.json' | grep -v ${run_time}_flare | xargs rm -f # json files from CME/Flare simulations
      echo "[$(date -u +'%F %T')] Done"
      echo

      # modify ZEUS source code according to the input json file
      echo "[$(date -u +'%F %T')] Setting up acceleration module ..."
      python3 $code_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 0 --input ${run_time}_flare_earth_input.json
      echo "[$(date -u +'%F %T')] Done"
      echo

      # CME_input.json used by plot_CME_info.py
      cp ${run_time}_flare_earth_input.json CME_input.json

      echo "[$(date -u +'%F %T')] Compiling ZEUS ..."
      csh -v ./iPATH_zeus.s
      echo "[$(date -u +'%F %T')] Compilation done"
      echo

      echo "[$(date -u +'%F %T')] Running acceleration module"
      if [ $if_local -eq 1 ]
      then
         ./xdzeus36 <input
      else
         # wait for job to finish before returning
         sbatch -W $code_dir/run_zeus2.sh -r $CME_dir

         # compress Slurm logfile
         for f in slurm*.out; do
            [[ -s $f ]] && gzip $f
         done
      fi
      echo "[$(date -u +'%F %T')] Done"
      echo

      # check if CME ZEUS simulation was successful
      [[ ! -s $CME_dir/zl002JH ]] && {
         echo "[$(date -u +'%F %T')] ZEUS log file missing: simulation job probably terminated before completion"
         echo "[$(date -u +'%F %T')] Cleanup and exit"
         cleanup_acceleration_files
         exit 1
      }

      shock_files=(all_shell_bndy dist_all_shl dist_at_shock
         esc_distr_dn esc_distr-hi esc_distr_up
         kappa-par-perp momenta-hi shock_momenta shock_posn_comp)
      bad_shock_files=()
      for f in ${shock_files[@]}; do
         [[ ! -s $CME_dir/path_output/$f.dat ]] && bad_shock_files+=($f)
      done
      (( ${#bad_shock_files[@]} )) && {
         echo "[$(date -u +'%F %T')] One or more shock-related files missing or empty: shock detection failed"
         printf "%s " ${bad_shock_files[@]}
         printf "\n"
         echo "[$(date -u +'%F %T')] Cleanup and exit"
         cleanup_acceleration_files
         exit 1
      }

      #-----------------------------------------------------------------------------------------
      # setup and compile for the transport module

      # modify iPATH source code according to the input json file
      echo "[$(date -u +'%F %T')] Setting up transport module for Earth ..."
      python3 $code_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input ${run_time}_flare_earth_input.json
      echo "[$(date -u +'%F %T')] Done"
      echo

      mkdir $trspt_dir

      echo "[$(date -u +'%F %T')] Compiling iPATH ..."
      $MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o $trspt_dir/trspt.out
      $FCOMP $iPATH_dir/Transport/combine.f -o $trspt_dir/combine.out
      echo "[$(date -u +'%F %T')] Done"
      echo
    fi

    echo "[$(date -u +'%F %T')] Copying files to $trspt_dir ..."
    (( !skip_jobs )) && cp $iPATH_dir/Transport/trspt_input $trspt_dir
    mv ${run_time}_flare_earth_input.json $trspt_dir/input.json
    mv ${run_time}_flare_earth_output.json $trspt_dir/output.json
    echo "[$(date -u +'%F %T')] Done"
    echo

    CME_start_time=$(jq -r '.sep_forecast_submission.triggers[0].flare.peak_time' $trspt_dir/output.json)
    cur_date=${CME_start_time%T*}

    first_PSP_date=$(date -d 2018-09-06 +'%Y-%m-%d') # not the actual first date
    # loop on all observers, except Earth
    for obs in ${Observers[@]//earth}; do
        [[ $obs == PSP && $cur_date < $first_PSP_date ]] && continue

        if (( !skip_jobs )); then
            echo "[$(date -u +'%F %T')] Setting up transport module for ${obs^} ..."
            python3 $code_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input ${run_time}_flare_${obs}_input.json
            echo "[$(date -u +'%F %T')] Done"
            echo
        fi

        trspt_dir_obs=${trspt_dir/earth/$obs}
        (( !skip_jobs )) && mkdir $trspt_dir_obs

        echo "[$(date -u +'%F %T')] Copying files to $trspt_dir_obs ..."
        (( !skip_jobs )) && cp $iPATH_dir/Transport/trspt_input $trspt_dir_obs
        mv ${run_time}_flare_${obs}_input.json $trspt_dir_obs/input.json
        (( !skip_jobs )) && cp $trspt_dir/combine.out $trspt_dir_obs
        (( !skip_jobs )) && cp $trspt_dir/trspt.out $trspt_dir_obs
        cp $trspt_dir/output.json $trspt_dir_obs
        echo "[$(date -u +'%F %T')] Done"
        echo
    done

    #-----------------------------------------------------------------------------------------
    # Now run the transport modules:
    # NB: logs are saved separately, so they don't mix up
    (( if_local )) && opts='-L' || opts=
    (( skip_jobs )) && opts="$opts -S"
    for obs in ${Observers[@]}; do
        [[ $obs == PSP && $cur_date < $first_PSP_date ]] && continue

        $code_dir/transport_module.sh -r $code_dir -i $CME_id -s $CME_start_time -p $obs $opts &>$CME_dir/path_output/transport_$obs/log.txt &
    done
    wait

    # print logs in order and then remove them
    for obs in ${Observers[@]}; do
        log=$CME_dir/path_output/transport_$obs/log.txt
        [[ -f $log ]] && {
            cat $log
            rm $log
        }
    done

    cleanup_acceleration_files

    echo
    echo "[$(date -u +'%F %T')] Copying output files to the iSWA staging area"
    cd $CME_dir/path_output
    $code_dir/cp2staging.sh -d iSWA
    echo "[$(date -u +'%F %T')] Done"

    echo "[$(date -u +'%F %T')] SLURM jobs summary:"
    if (( !skip_jobs )); then
         cd $CME_dir
         jobs=$(find -name 'slurm*' \
            | sed -E 's/.*-([0-9]+).*/\1/' \
            | sort -n \
            | paste -sd',')
         sacct -j $jobs -P -X -ojobid,submit,planned,start,end,elapsedraw,partition,ncpus,nnodes,cputimeraw,state,exitcode,workdir \
         | column -s'|' -t
    fi
    echo "[$(date -u +'%F %T')] Done"

} >>$logfile 2>&1
