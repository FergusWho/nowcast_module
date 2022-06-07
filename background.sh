#!/bin/bash

iPATH_dir='/data/iPATH/iPATH2.0'
root_dir='/data/iPATH/nowcast_module'
python_bin='/data/spack/opt/spack/linux-centos7-skylake_avx512/gcc-10.2.0/python-3.8.9-dtvwd3qomfzkcimvlwvw5ilvr4eb5dvg/bin/python3'

module load gcc-4.8.5
module load python-3.8.9-gcc-10.2.0-dtvwd3q 
cd $root_dir
run_time=$(date +'%Y-%m-%d_%H:%M' -u)


# testing for specific event:
# example: bash background.sh -t '2022-01-20_08:30'
while getopts 't:L' flag
do
    case "${flag}" in
        t) run_time=${OPTARG};;
        L) if_local=1;;
    esac
done



$python_bin $root_dir/grepSW.py --root_dir $root_dir --run_time $run_time

run_dir=`cat $root_dir/temp.txt`
#run_dir=$run_time
rm $root_dir/temp.txt


mkdir $root_dir/$run_dir
cp -r $iPATH_dir/Acceleration/zeus3.6/* $root_dir/$run_dir
cp $root_dir/${run_dir}_input.json $root_dir/$run_dir/input.json


$python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$run_dir --path_dir $iPATH_dir --run_mode 1 --input $root_dir/${run_dir}_input.json

cd $root_dir/$run_dir
csh -v ./iPATH_zeus.s
cd $root_dir
/opt/slurm/bin/sbatch $root_dir/run_zeus.sh -r $root_dir/$run_dir

