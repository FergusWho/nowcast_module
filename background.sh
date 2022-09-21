#!/bin/bash
iPATH_dir='/data/iPATH/iPATH2.0'
root_dir='/data/iPATH/nowcast_module'
python_bin='/data/spack/opt/spack/linux-centos7-skylake_avx512/gcc-10.2.0/python-3.8.9-dtvwd3qomfzkcimvlwvw5ilvr4eb5dvg/bin/python3'
# default for CCMC AWS

run_time=$(date +'%Y-%m-%d_%H:%M' -u)
if_local=0

# testing for specific event:
# example: bash background.sh -t '2022-01-20_08:30'
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
else
    module load gcc-4.8.5
    module load python-3.8.9-gcc-10.2.0-dtvwd3q 
fi

cd $root_dir

$python_bin $root_dir/grepSW.py --root_dir $root_dir --run_time $run_time

run_dir=`cat $root_dir/temp.txt`
rm $root_dir/temp.txt


mkdir $root_dir/$run_dir
cp -r $iPATH_dir/Acceleration/zeus3.6/* $root_dir/$run_dir
# use the modified dzeus36 version for nowcasting
cp $root_dir/dzeus36_alt $root_dir/$run_dir/dzeus36

cp $root_dir/${run_dir}_input.json $root_dir/$run_dir/input.json


$python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$run_dir --path_dir $iPATH_dir --run_mode 1 --input $root_dir/${run_dir}_input.json

cd $root_dir/$run_dir
csh -v ./iPATH_zeus.s

if [ $if_local -eq 1 ]
then
    ./xdzeus36
    cd ..
else
    cd $root_dir
    /opt/slurm/bin/sbatch $root_dir/run_zeus.sh -r $root_dir/$run_dir
fi

#clean up some files
rm $root_dir/zr001JH
rm $root_dir/zr002JH
rm $root_dir/zr003JH
rm $root_dir/zr004JH
