#!/bin/bash
iPATH_dir='/shared/iPATH/ipath_v2'
root_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'
opsep_dir='/shared/iPATH/operational-sep'
# default for CCMC AWS on rt-hpc-prod

MPI_comp='mpif90'
FCOMP='gfortran'

run_time=$(date +'%Y-%m-%d_%H:%M' -u)
if_local=0

echo "-----------------------------------------"
echo $run_time

# testing for specific event:
# example: bash CME.sh -t 2022-01-20_08:30
while getopts 't:L' flag
do
    case "${flag}" in
        t) run_time=${OPTARG};;
        L) if_local=1;;
    esac
done

if [ $if_local -eq 1 ]
then
    # change these accordingly if you want to run locally
    iPATH_dir=$HOME'/iPATH2.0'
    root_dir=$HOME'/nowcast_module'
    thread_count=12
else
    source ~/setup_pkgs
    thread_count=64
fi

mkdir -p $data_dir/CME
[[ ! -d $data_dir/helioweb ]] && cp -r $root_dir/helioweb $data_dir/

CME_dir=$run_time

trspt_dir='transport'

# create already processed CME list, if not existent
[[ ! -f $data_dir/pastCME.json ]] && echo "[]" >$data_dir/pastCME.json

# read last line of output from check_CME.py
last_line=`python3 $root_dir/check_CME.py --root_dir $data_dir --run_time $run_time | tail -n 1`
IFS=' '
read -a strarr <<<$last_line
bgsw_folder_name=${strarr[0]}
CME_id=${strarr[1]}

# get the start and end date for Opsep
startdate=(${bgsw_folder_name//_/ })
enddate=$(date -d "$startdate + 2 days" +'%Y-%m-%d')

echo $bgsw_folder_name

if [ -z "$bgsw_folder_name" ]
then
    echo "There is no CME"

else
    #-----------------------------------------------
    # CME setup and acceleration:
    cp -r $data_dir/Background/$bgsw_folder_name $data_dir/CME/$CME_id
    echo "CME found! Checking Time: "$run_time >>$data_dir/CME/$CME_id/log.txt
    echo "CME id: "$CME_id >>$data_dir/CME/$CME_id/log.txt
    echo "current time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$data_dir/CME/$CME_id/log.txt

    # use the modified dzeus36 version for nowcasting
    cp $root_dir/dzeus36_alt $data_dir/CME/$CME_id/dzeus36

   python3 $iPATH_dir/prepare_PATH.py --root_dir $data_dir/CME/$CME_id --path_dir $iPATH_dir --run_mode 0 --input $data_dir/CME/$CME_id/${CME_dir}_input.json >>$data_dir/CME/$CME_id/log.txt 2>&1
    
    cp $data_dir/CME/$CME_id/${CME_dir}_input.json $data_dir/CME/$CME_id/CME_input.json
    
    cd $data_dir/CME/$CME_id
    csh -v ./iPATH_zeus.s
    if [ $if_local -eq 1 ]
    then
        ./xdzeus36 <input
    else
        cd $data_dir/CME/$CME_id
        sbatch -W $root_dir/run_zeus2.sh -r $data_dir/CME/$CME_id
    fi
    wait
    echo "CME setup and acceleration done. Time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$data_dir/CME/$CME_id/log.txt 
    cd $root_dir

    #-----------------------------------------------------------------------------------------
    # setup and compile for the transport module

    python3 $iPATH_dir/prepare_PATH.py --root_dir $data_dir/CME/$CME_id --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input $data_dir/CME/$CME_id/${CME_dir}_input.json >>$data_dir/CME/$CME_id/log.txt 2>&1
    
    mkdir $data_dir/CME/$CME_id/path_output/$trspt_dir
    
    $MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o $data_dir/CME/$CME_id/path_output/$trspt_dir/trspt.out
    $FCOMP $iPATH_dir/Transport/combine.f -o $data_dir/CME/$CME_id/path_output/$trspt_dir/combine.out

    cp $root_dir/plot_CME_info.py $data_dir/CME/$CME_id/path_output
    cp $iPATH_dir/Transport/trspt_input $data_dir/CME/$CME_id/path_output/$trspt_dir
    cp $root_dir/plot_iPATH_nowcast.py $data_dir/CME/$CME_id/path_output/$trspt_dir
    cp $data_dir/CME/$CME_id/${CME_dir}_input.json $data_dir/CME/$CME_id/path_output/$trspt_dir
    mv $data_dir/CME/$CME_id/${CME_dir}_output.json $data_dir/CME/$CME_id/path_output/$trspt_dir/output.json
   
 
    mkdir $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    python3 $iPATH_dir/prepare_PATH.py --root_dir $data_dir/CME/$CME_id --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input $data_dir/CME/$CME_id/${CME_dir}_mars_input.json >>$data_dir/CME/$CME_id/log.txt 2>&1
    
    cp $iPATH_dir/Transport/trspt_input $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $root_dir/plot_iPATH_nowcast.py $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $data_dir/CME/$CME_id/${CME_dir}_mars_input.json $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $data_dir/CME/$CME_id/path_output/$trspt_dir/combine.out $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $data_dir/CME/$CME_id/path_output/$trspt_dir/trspt.out $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars 
    cp $data_dir/CME/$CME_id/path_output/$trspt_dir/output.json $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars 
 
    #-----------------------------------------------------------------------------------------
    # Now run the transport module for Earth:
    if [ $if_local -eq 1 ]
    then
        cd $data_dir/CME/$CME_id/path_output/$trspt_dir
        mpirun -np $thread_count trspt.out
    else
        cd $data_dir/CME/$CME_id
        sbatch -W $root_dir/run_transport.sh -r $data_dir/CME/$CME_id/path_output/$trspt_dir
        wait
    fi
    wait

    echo "Transport for Earth done. Time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$data_dir/CME/$CME_id/log.txt

    cd $data_dir/CME/$CME_id/path_output/$trspt_dir
    ./combine.out
    # clean up some unused output
    rm RawData*
    rm $data_dir/CME/$CME_id/path_output/dist_all_shl.dat
    
    # Plot result:
    python3 $data_dir/CME/$CME_id/path_output/$trspt_dir/plot_iPATH_nowcast.py
    cd $data_dir/CME/$CME_id/path_output
    python3 $data_dir/CME/$CME_id/path_output/plot_CME_info.py
    wait

    # Use OpSep to produce output for SEP scoreboard
    echo "Now using OpSEP to generate output:" >>$data_dir/CME/$CME_id/log.txt
    cd $trspt_dir
    mkdir -p json/{library,data,output}
    cp output.json json/library/model_template.json
    cp ${startdate}_differential_flux.csv json/data/
    cd json
    python3 $opsep_dir/operational_sep_quantities.py --StartDate $startdate --EndDate $enddate --Experiment user --ModelName ZEUS+iPATH_CME --FluxType differential --UserFile ${startdate}_differential_flux.csv --spase spase://CCMC/SimulationModel/iPATH/2 >>$root_dir/CME/$CME_id/log.txt
    find -type d -empty -delete # remove empty folders created by opsep

    cd $root_dir

    # make CME movie
    convert -delay 5 $data_dir/CME/$CME_id/path_output/CME*.png $data_dir/CME/$CME_id/path_output/CME.gif
    wait

    #-----------------------------------------------------------------------------------------
    # Now run the transport for Mars:
    # Currently we prioritize the transport calculation at Earth.
    # Ideally we want to sbatch this run together with the Earth run. (can't use -W across two jobs atm)
    
    if [ $if_local -eq 1 ]
    then
        cd $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
        mpirun -np $thread_count trspt.out
    else
        cd $data_dir/CME/$CME_id
        sbatch -W $root_dir/run_transport.sh -r $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
        wait
    fi
    wait
   
    echo "Transport for Mars done. Time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$data_dir/CME/$CME_id/log.txt

    cd $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    ./combine.out
    rm RawData*
    python3 $data_dir/CME/$CME_id/path_output/${trspt_dir}_mars/plot_iPATH_nowcast.py
fi

