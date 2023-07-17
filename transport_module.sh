#!/bin/bash
root_dir='/data/iPATH/test'
opsep_dir='/data/iPATH/operational-sep'
python_bin='/data/spack/opt/spack/linux-centos7-skylake_avx512/gcc-10.2.0/python-3.8.9-dtvwd3qomfzkcimvlwvw5ilvr4eb5dvg/bin/python3'
# default for CCMC AWS

MPI_comp='mpif90'
FCOMP='gfortran'
if_local=0
trspt_dir='transport'
thread_count=10

while getopts 'r:i:s:e:p:L' flag
do
    case "${flag}" in
        r) root_dir=${OPTARG};;
        i) CME_id=${OPTARG};;
        s) startdate=${OPTARG};;
        e) enddate=${OPTARG};;
        p) location=${OPTARG};;
        L) if_local=1;;
    esac
done

if [ $location == "earth" ]
then
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


else

    if [ $if_local -eq 1 ]
    then
        cd $root_dir/CME/$CME_id/path_output/$trspt_dir
        mpirun -np $thread_count trspt.out
    else
        /opt/slurm/bin/sbatch -W run_transport.sh -r $root_dir/CME/$CME_id/path_output/${trspt_dir}_$location      
        wait
    fi
    wait

    echo "Tranpsort for "$location" done. Time: "$(date +'%Y-%m-%d_%H:%M' -u) >>$root_dir/CME/$CME_id/log.txt

    cd $root_dir/CME/$CME_id/path_output/${trspt_dir}_$location
    ./combine.out
    rm RawData*
    $python_bin $root_dir/CME/$CME_id/path_output/${trspt_dir}_$location/plot_iPATH_nowcast.py

fi

