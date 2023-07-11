#!/bin/bash

# default values for CCMC AWS on rt-hpc-prod
iPATH_dir='/shared/iPATH/ipath_v2'
code_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'
opsep_dir='/shared/iPATH/operational_sep_v3'

MPI_comp='mpif90'
FCOMP='gfortran'

echo "-------------- CME Module --------------"

# default values for command-line arguments
run_time=$(date +'%Y%m%d_%H%M' -u)
if_local=0

# testing for specific event:
# example: bash CME.sh -t 20220120_0830
while getopts 't:L' flag
do
    case "${flag}" in
        t) run_time=${OPTARG};;
        L) if_local=1;;
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

# look for new CMEs from DONKI
# create the input parameters files for Earth and Mars: $bgsw_folder_name/${run_time}_CME_earth_input.json and $bgsw_folder_name/${run_time}_CME_mars_input.json
# last line is: bgsw_folder_name CME_id
# read last line of output from check_CME.py
echo "[$(date -u +'%F %T')] Checking for new CMEs ..."
last_line=$(python3 $code_dir/check_CME.py --root_dir $data_dir --run_time $run_time --model_mode nowcast | tail -n 1)
echo "[$(date -u +'%F %T')] Done"
echo

IFS=' '
read -a strarr <<<$last_line
bgsw_folder_name=${strarr[0]}
CME_id=${strarr[1]}

# get the start and end date for Opsep
startdate=(${bgsw_folder_name//_/ })
startdate_opsep=${startdate:0:4}-${startdate:4:2}-${startdate:6:2}
enddate=$(date -d "$startdate + 2 days" +'%Y-%m-%d')

echo "[$(date -u +'%F %T')] Background simulation: $bgsw_folder_name"

if [ -z "$bgsw_folder_name" ]
then
    echo "[$(date -u +'%F %T')] There is no CME: exit"
else
    # abort if no background simulation exists
    [[ ! -f $data_dir/Background/$bgsw_folder_name/zr005JH ]] && {
      echo "[$(date -u +'%F %T')] Background simulation not found: exit"
      exit 1
    }

    #-----------------------------------------------
    # CME setup and acceleration:
    CME_dir=$data_dir/CME/$CME_id
    logfile=$CME_dir/log.txt

    echo "[$(date -u +'%F %T')] Copying background simulation to $CME_dir ..."
    cp -r $data_dir/Background/$bgsw_folder_name $CME_dir

    # use the modified dzeus36 version for nowcasting
    cp $code_dir/dzeus36_alt $CME_dir/dzeus36

    # remove backgroun simulation log
    rm $CME_dir/log.txt
    echo "[$(date -u +'%F %T')] Done"
    echo
    echo "[$(date -u +'%F %T')] Switching to $logfile"

    cd $CME_dir

    echo "[$(date -u +'%F %T')] CME found! Checking Time: $run_time" >>$logfile
    echo "[$(date -u +'%F %T')] CME id: $CME_id" >>$logfile

    # delete residual files created by other CME/Flare simulations in the copied Background folder
    echo "[$(date -u +'%F %T')] Deleting residual files ..." >>$logfile
    rm -f slurm* # Slurm logfiles from Background simulation
    find -type f -name '*.json' | grep -v ${run_time}_CME | xargs rm -f # json files from CME/Flare simulations
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    # modify ZEUS source code according to the input json file
    echo "[$(date -u +'%F %T')] Setting up acceleration module ..." >>$logfile
    python3 $iPATH_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 0 --input ${run_time}_CME_earth_input.json >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    # CME_input.json used by plot_CME_info.py
    cp ${run_time}_CME_earth_input.json CME_input.json

    echo "[$(date -u +'%F %T')] Compiling ZEUS ..." >>$logfile
    csh -v ./iPATH_zeus.s >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Compilation done" >>$logfile
    echo >>$logfile

    echo "[$(date -u +'%F %T')] Running acceleration module" >>$logfile
    if [ $if_local -eq 1 ]
    then
        ./xdzeus36 <input >>$logfile 2>&1
    else
        sbatch -W $code_dir/run_zeus2.sh -r $CME_dir >>$logfile 2>&1

        # compress Slurm logfile
        for f in slurm*.out; do
           gzip $f >>$logfile 2>&1
        done
    fi
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    #-----------------------------------------------------------------------------------------
    # setup and compile for the transport module

    # modify iPATH source code according to the input json file
    echo "[$(date -u +'%F %T')] Setting up transport module for Earth ..." >>$logfile
    python3 $iPATH_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input ${run_time}_CME_earth_input.json >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    trspt_dir=$CME_dir/path_output/transport_earth
    mkdir $trspt_dir
    cd $trspt_dir

    echo "[$(date -u +'%F %T')] Compiling iPATH ..." >>$logfile
    $MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o trspt.out >>$logfile 2>&1
    $FCOMP $iPATH_dir/Transport/combine.f -o combine.out >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    cd $CME_dir

    echo "[$(date -u +'%F %T')] Copying files to $trspt_dir ..." >>$logfile
    cp $iPATH_dir/Transport/trspt_input $trspt_dir
    mv ${run_time}_CME_earth_input.json $trspt_dir/input.json
    mv ${run_time}_CME_earth_output.json $trspt_dir/output.json
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    echo "[$(date -u +'%F %T')] Setting up transport module for Mars ..." >>$logfile
    python3 $iPATH_dir/prepare_PATH.py --root_dir $CME_dir --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input ${run_time}_CME_mars_input.json >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    trspt_dir_mars=${trspt_dir/earth/mars}
    mkdir $trspt_dir_mars

    echo "[$(date -u +'%F %T')] Copying files to $trspt_dir_mars ..." >>$logfile
    cp $iPATH_dir/Transport/trspt_input $trspt_dir_mars
    mv ${run_time}_CME_mars_input.json $trspt_dir_mars/input.json
    cp $trspt_dir/combine.out $trspt_dir_mars
    cp $trspt_dir/trspt.out $trspt_dir_mars
    cp $trspt_dir/output.json $trspt_dir_mars
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    #-----------------------------------------------------------------------------------------
    echo "[$(date -u +'%F %T')] Running transport module for Earth ..." >>$logfile
    cd $trspt_dir
    if [ $if_local -eq 1 ]
    then
        mpirun -np $thread_count trspt.out >>$logfile 2>&1
    else
        sbatch -W $code_dir/run_transport.sh -r $trspt_dir >>$logfile 2>&1

        # compress Slurm logfile
        for f in slurm*.out; do
           gzip $f >>$logfile 2>&1
        done
    fi
    ./combine.out >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    echo "[$(date -u +'%F %T')] Plotting transport results ..." >>$logfile
    python3 $code_dir/plot_iPATH_nowcast.py >>$logfile 2>&1
    echo "[$(date -u +'%F %T')]  Done" >>$logfile
    echo >>$logfile

    # Use OpSep to produce output for SEP scoreboard
    echo "[$(date -u +'%F %T')] Using OpSEP to generate output ..." >>$logfile
    mkdir -p json/{library,data,output}
    cp output.json json/library/model_template.json
    cp ${startdate}_differential_flux.csv json/data/
    cd json
    python3 $opsep_dir/operational_sep_quantities.py --StartDate $startdate_opsep --EndDate $enddate --Experiment user --ModelName ZEUS+iPATH_CME --FluxType differential --UserFile ${startdate}_differential_flux.csv --spase spase://CCMC/SimulationModel/iPATH/2 >>$logfile 2>&1

    # move opsep output to transport dir and cleanup
    cd $trspt_dir
    mv json/output/* .
    rm -r json
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile
    #-----------------------------------------------------------------------------------------

    echo "[$(date -u +'%F %T')] Making CME movie ..." >>$logfile
    cd $CME_dir/path_output
    python3 $code_dir/plot_CME_info.py >>$logfile 2>&1
    convert -delay 5 CME*.png CME.gif >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    echo "[$(date -u +'%F %T')] Cleaning up ..." >>$logfile
    # remove source pngs if the animation exists and contains the right number of frames
    if [[ -f CME.gif ]]; then
      npngs=$(ls CME*.png | wc -l)
      nframes=$(identify CME.gif | wc -l)
      (( npngs == nframes )) && rm CME*.png
    fi

    cd $trspt_dir

    # clean up some unused output
    rm RawData*

    # compress transport files
    tar --remove-files -zcf fp.tar.gz fp_* >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    #-----------------------------------------------------------------------------------------
    # Now run the transport for Mars:
    # Currently we prioritize the transport calculation at Earth.
    # Ideally we want to sbatch this run together with the Earth run. (can't use -W across two jobs atm)

    echo "[$(date -u +'%F %T')] Running transport module for Mars ..." >>$logfile
    cd $trspt_dir_mars
    if [ $if_local -eq 1 ]
    then
        mpirun -np $thread_count trspt.out >>$logfile 2>&1
    else
        sbatch -W $code_dir/run_transport.sh -r $trspt_dir_mars >>$logfile 2>&1

        # compress Slurm logfile
        for f in slurm*.out; do
           gzip $f >>$logfile 2>&1
        done
    fi
    ./combine.out >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    echo "[$(date -u +'%F %T')] Plotting transport results ..." >>$logfile
    python3 $code_dir/plot_iPATH_nowcast.py >>$logfile 2>&1
    echo "[$(date -u +'%F %T')]  Done" >>$logfile
    echo >>$logfile

    echo "[$(date -u +'%F %T')] Cleaning up ..." >>$logfile
    # clean up some unused output
    rm RawData*

    # compress transport files
    tar --remove-files -zcf fp.tar.gz fp_* >>$logfile 2>&1

    cd $CME_dir/path_output

    # compress intermediate acceleration files
    for f in observer_pov.dat kappa-par-perp.dat all_shell_bndy.dat dist_at_shock.dat esc_distr* momenta-hi.dat solar_wind_profile.dat; do
      gzip $f >>$logfile 2>&1
    done

    # clean up unneeded intermediate acceleration files
    rm dist_all_shl.dat
    echo "[$(date -u +'%F %T')] Done" >>$logfile
    echo >>$logfile

    echo "[$(date -u +'%F %T')] Copying output files to the staging area" >>$logfile
    $code_dir/cp2staging.sh >>$logfile 2>&1
    echo "[$(date -u +'%F %T')] Done" >>$logfile
fi
