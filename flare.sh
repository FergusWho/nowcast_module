#!/bin/bash

cleanup_acceleration_files() {
   cd $CME_dir/path_output

   # compress intermediate acceleration files
   for f in observer_pov.dat kappa-par-perp.dat all_shell_bndy.dat dist_at_shock.dat esc_distr* momenta-hi.dat solar_wind_profile.dat; do
      [[ -s $f ]] && gzip $f
   done

   # remove unneeded intermediate acceleration files
   rm -f dist_all_shl.dat
}

# default values for CCMC AWS on rt-hpc-prod
iPATH_dir='/shared/iPATH/ipath_v2'
code_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'
opsep_dir='/shared/iPATH/operational_sep_v3'

MPI_comp='mpif90'
FCOMP='gfortran'

echo "------------- Flare Module -------------"

# default values for command-line arguments
run_time=$(date +'%Y%m%d_%H%M' -u)
if_local=0

# testing for specific event:
# example: bash CME.sh -t 20220120_0830
# rerun already processed event:
# example: bash CME.sh -t 20230819_1715 -i 20230818T220000-CME-001
while getopts 't:i:L' flag
do
    case "${flag}" in
        t) run_time=${OPTARG};;
        L) if_local=1;;
        i) CME_id=${OPTARG};;
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
CME_id=${strarr[1]}     # this is actually flare_id

echo "[$(date -u +'%F %T')] Background simulation: $bgsw_folder_name"

# abort if no flare or if no background simulation exists
if [[ -z $bgsw_folder_name ]]; then
   echo "[$(date -u +'%F %T')] There is no flare: exit"
   exit 1
elif [[ ! -f $data_dir/Background/$bgsw_folder_name/zr005JH ]]; then
   echo "[$(date -u +'%F %T')] Background simulation not found: exit"
   exit 1
fi
else
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
fi

# get the start and end date for Opsep
startdate=(${bgsw_folder_name//_/ })
startdate_opsep=${startdate:0:4}-${startdate:4:2}-${startdate:6:2}
enddate=$(date -d "$startdate + 2 days" +'%Y-%m-%d')

    #-----------------------------------------------
    # CME setup and acceleration:
    CME_dir=$data_dir/Flare/$CME_id
    logfile=$CME_dir/log.txt

    echo "[$(date -u +'%F %T')] Copying background simulation to $CME_dir ..."
    [[ -d $CME_dir ]] && mv $CME_dir $CME_dir.bak # rename already existing simulation folder, just in case
    cp -r $data_dir/Background/$bgsw_folder_name $CME_dir

    # use the modified dzeus36 version for nowcasting
    cp $code_dir/dzeus36_alt $CME_dir/dzeus36

    # remove background simulation log
    rm $CME_dir/log.txt
    echo "[$(date -u +'%F %T')] Done"
    echo
    echo "[$(date -u +'%F %T')] Switching to $logfile"

    # redirect everything to the logfile
    {

    cd $CME_dir

    echo "[$(date -u +'%F %T')] Flare found! Checking Time: $run_time"
    echo "[$(date -u +'%F %T')] Flare id: $CME_id"

    # delete residual files created by other CME/Flare simulations in the copied Background folder
    echo "[$(date -u +'%F %T')] Deleting residual files ..."
    rm -f slurm* # Slurm logfiles from Background simulation
    find -type f -name '*.json' | grep -v ${run_time}_flare | xargs rm -f # json files from CME/Flare simulations
    echo "[$(date -u +'%F %T')] Done"
    echo

    # modify ZEUS source code according to the input json file
    echo "[$(date -u +'%F %T')] Setting up acceleration module ..."
    python3 $iPATH_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 0 --input ${run_time}_flare_earth_input.json
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
    python3 $iPATH_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input ${run_time}_flare_earth_input.json
    echo "[$(date -u +'%F %T')] Done"
    echo

    trspt_dir=$CME_dir/path_output/transport_earth
    mkdir $trspt_dir
    cd $trspt_dir

    echo "[$(date -u +'%F %T')] Compiling iPATH ..."
    $MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o trspt.out
    $FCOMP $iPATH_dir/Transport/combine.f -o combine.out
    echo "[$(date -u +'%F %T')] Done"
    echo

    cd $CME_dir

    echo "[$(date -u +'%F %T')] Copying files to $trspt_dir ..."
    cp $iPATH_dir/Transport/trspt_input $trspt_dir
    mv ${run_time}_flare_earth_input.json $trspt_dir/input.json
    mv ${run_time}_flare_earth_output.json $trspt_dir/output.json
    echo "[$(date -u +'%F %T')] Done"
    echo

    #-----------------------------------------------------------------------------------------
    echo "[$(date -u +'%F %T')] Running transport module for Earth ..."
    cd $trspt_dir
    if [ $if_local -eq 1 ]
    then
        mpirun -np $thread_count trspt.out
    else
        # wait for job to finish before returning
        sbatch -W $code_dir/run_transport.sh -r $trspt_dir

        # compress Slurm logfile
        for f in slurm*.out; do
           [[ -s $f ]] && gzip $f
        done
    fi
    ./combine.out
    echo "[$(date -u +'%F %T')] Done"
    echo

    echo "[$(date -u +'%F %T')] Plotting transport results ..."
    python3 $code_dir/plot_iPATH_nowcast.py
    echo "[$(date -u +'%F %T')]  Done"
    echo

    # Use OpSep to produce output for SEP scoreboard
    echo "[$(date -u +'%F %T')] Using OpSEP to generate output ..."
    mkdir -p json/{library,data,output}
    cp output.json json/library/model_template.json
    cp ${startdate}_differential_flux.csv json/data/
    cd json
    python3 $opsep_dir/operational_sep_quantities.py --StartDate $startdate_opsep --EndDate $enddate --Experiment user --ModelName ZEUS+iPATH_Flare --FluxType differential --UserFile ${startdate}_differential_flux.csv --spase spase://CCMC/SimulationModel/iPATH/2

    # move opsep output to transport dir and cleanup
    cd $trspt_dir
    mv json/output/* .
    rm -r json
    echo "[$(date -u +'%F %T')] Done"
    echo
    #-----------------------------------------------------------------------------------------

    echo "[$(date -u +'%F %T')] Making CME movie ..."
    cd $CME_dir/path_output
    python3 $code_dir/plot_CME_info.py
    convert -delay 5 CME*.png CME.gif
    echo "[$(date -u +'%F %T')] Done"
    echo

    echo "[$(date -u +'%F %T')] Cleaning up ..."
    # remove source pngs if the animation exists and contains the right number of frames
    if [[ -s CME.gif ]]; then
      npngs=$(ls CME*.png | wc -l)
      nframes=$(identify CME.gif | wc -l)
      (( npngs == nframes )) && rm CME*.png
    fi

    cleanup_acceleration_files

    cd $trspt_dir

    # clean up some unused output
    rm -f RawData*

    # compress transport files
    tar --remove-files -zcf fp.tar.gz fp_*
    echo "[$(date -u +'%F %T')] Done"
    echo

    echo "[$(date -u +'%F %T')] Copying output files to the staging area"
    cd $CME_dir/path_output
    $code_dir/cp2staging.sh
    echo "[$(date -u +'%F %T')] Done"

    } >>$logfile 2>&1
