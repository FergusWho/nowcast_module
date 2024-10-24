#!/bin/bash
iPATH_dir='/data/iPATH/iPATH2.0'
root_dir='/data/iPATH/nowcast_module'
opsep_dir='/data/iPATH/operational-sep'
python_bin='/data/spack/opt/spack/linux-centos7-skylake_avx512/gcc-10.2.0/python-3.8.9-dtvwd3qomfzkcimvlwvw5ilvr4eb5dvg/bin/python3'
# default for CCMC AWS

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
    python_bin='/usr/bin/python3'
    thread_count=12
else
    source /etc/profile.d/modules.sh
    module load gcc-4.8.5
    module load python-3.8.9-gcc-10.2.0-dtvwd3q
    MPI_comp='/opt/amazon/openmpi/bin/mpif90'
    thread_count=64
fi

CME_dir=$run_time

trspt_dir='transport'


# read last line of output from check_CME.py
last_line=`$python_bin $root_dir/check_CME.py --root_dir $root_dir --run_time $run_time | tail -n 1`
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
    cp -r $root_dir/Background/$bgsw_folder_name $root_dir/CME/$CME_id
    echo "CME found! Checking Time: "$run_time >>$root_dir/CME/$CME_id/log.txt
    echo "CME id: "$CME_id >>$root_dir/CME/$CME_id/log.txt
    echo "current time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$root_dir/CME/$CME_id/log.txt

    # use the modified dzeus36 version for nowcasting
    cp $root_dir/dzeus36_alt $root_dir/CME/$CME_id/dzeus36

    $python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/CME/$CME_id --path_dir $iPATH_dir --run_mode 0 --input $root_dir/CME/$CME_id/${CME_dir}_input.json >>$root_dir/CME/$CME_id/log.txt 2>&1
    
    cp $root_dir/CME/$CME_id/${CME_dir}_input.json $root_dir/CME/$CME_id/CME_input.json
    
    cd $root_dir/CME/$CME_id
    csh -v ./iPATH_zeus.s
    if [ $if_local -eq 1 ]
    then
        ./xdzeus36 <input
    else
        cd $root_dir
        /opt/slurm/bin/sbatch -W run_zeus2.sh -r $root_dir/CME/$CME_id
    fi
    wait
    echo "CME setup and acceleration done. Time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$root_dir/CME/$CME_id/log.txt 
    cd $root_dir

    #-----------------------------------------------------------------------------------------
    # setup and compile for the transport module

    $python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/CME/$CME_id --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input $root_dir/CME/$CME_id/${CME_dir}_input.json >>$root_dir/CME/$CME_id/log.txt 2>&1
    
    mkdir $root_dir/CME/$CME_id/path_output/$trspt_dir
    
    $MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o $root_dir/CME/$CME_id/path_output/$trspt_dir/trspt.out
    $FCOMP $iPATH_dir/Transport/combine.f -o $root_dir/CME/$CME_id/path_output/$trspt_dir/combine.out

    cp $root_dir/plot_CME_info.py $root_dir/CME/$CME_id/path_output
    cp $iPATH_dir/Transport/trspt_input $root_dir/CME/$CME_id/path_output/$trspt_dir
    cp $root_dir/plot_iPATH_nowcast.py $root_dir/CME/$CME_id/path_output/$trspt_dir
    cp $root_dir/CME/$CME_id/${CME_dir}_input.json $root_dir/CME/$CME_id/path_output/$trspt_dir
    mv $root_dir/CME/$CME_id/${CME_dir}_output.json $root_dir/CME/$CME_id/path_output/$trspt_dir/output.json
   
 
    mkdir $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    $python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/CME/$CME_id --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input $root_dir/CME/$CME_id/${CME_dir}_mars_input.json >>$root_dir/CME/$CME_id/log.txt 2>&1
    
    cp $iPATH_dir/Transport/trspt_input $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $root_dir/plot_iPATH_nowcast.py $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $root_dir/CME/$CME_id/${CME_dir}_mars_input.json $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $root_dir/CME/$CME_id/path_output/$trspt_dir/combine.out $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    cp $root_dir/CME/$CME_id/path_output/$trspt_dir/trspt.out $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars 
    cp $root_dir/CME/$CME_id/path_output/$trspt_dir/output.json $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars 
 
    #-----------------------------------------------------------------------------------------
    # Now run the transport module for Earth:
    if [ $if_local -eq 1 ]
    then
        cd $root_dir/CME/$CME_id/path_output/$trspt_dir
        mpirun -np $thread_count trspt.out
    else
        /opt/slurm/bin/sbatch -W run_transport.sh -r $root_dir/CME/$CME_id/path_output/$trspt_dir    
        wait
    fi
    wait

    echo "Transport for Earth done. Time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$root_dir/CME/$CME_id/log.txt

    cd $root_dir/CME/$CME_id/path_output/$trspt_dir
    ./combine.out
    # clean up some unused output
    rm RawData*
    rm $root_dir/CME/$CME_id/path_output/dist_all_shl.dat
    
    # Plot result:
    $python_bin $root_dir/CME/$CME_id/path_output/$trspt_dir/plot_iPATH_nowcast.py
    cd $root_dir/CME/$CME_id/path_output
    $python_bin $root_dir/CME/$CME_id/path_output/plot_CME_info.py
    wait



    # Use OpSep to produce output for SEP scoreboard
    echo "Now using OpSEP to generate output:" >>$root_dir/CME/$CME_id/log.txt
    cp $root_dir/CME/$CME_id/path_output/$trspt_dir/${startdate}_differential_flux.csv $opsep_dir/data
    # copy output json that contains trigger info to OpSEP
    cp $root_dir/CME/$CME_id/path_output/$trspt_dir/output.json $opsep_dir/library/model_template.json
    cd $opsep_dir
    python3 operational_sep_quantities.py --StartDate $startdate --EndDate $enddate --Experiment user --ModelName ZEUS+iPATH_CME --FluxType differential --UserFile ${startdate}_differential_flux.csv --spase spase://CCMC/SimulationModel/iPATH/2 >>$root_dir/CME/$CME_id/log.txt
    wait
    # return model template back to default
    cp $opsep_dir/library/model_template.json.bk $opsep_dir/library/model_template.json
    
    cd $root_dir

    # make CME movie
    /usr/bin/convert -delay 5 $root_dir/CME/$CME_id/path_output/CME*.png $root_dir/CME/$CME_id/path_output/CME.gif
    wait

    #-----------------------------------------------------------------------------------------
    # Now run the transport for Mars:
    # Currently we prioritize the transport calculation at Earth.
    # Ideally we want to sbatch this run together with the Earth run. (can't use -W across two jobs atm)
    
    if [ $if_local -eq 1 ]
    then
        cd $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
        mpirun -np $thread_count trspt.out
    else
        /opt/slurm/bin/sbatch -W run_transport.sh -r $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
        wait
    fi
    wait
   
    echo "Transport for Mars done. Time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$root_dir/CME/$CME_id/log.txt

    cd $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars
    ./combine.out
    rm RawData*
    $python_bin $root_dir/CME/$CME_id/path_output/${trspt_dir}_mars/plot_iPATH_nowcast.py
fi

