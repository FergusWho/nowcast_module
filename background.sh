#!/bin/bash
iPATH_dir='/shared/iPATH/ipath_v2'
root_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'
# default for CCMC AWS on rt-hpc-prod

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
else
    source ~/setup_pkgs
fi

mkdir -p $data_dir

cd $root_dir

python3 $root_dir/grepSW.py --root_dir $data_dir --run_time $run_time

run_dir=`cat $data_dir/temp.txt`
rm $data_dir/temp.txt


mkdir -p $data_dir/Background/$run_dir
cp -r $iPATH_dir/Acceleration/zeus3.6/* $data_dir/Background/$run_dir
# use the modified dzeus36 version for nowcasting
cp $root_dir/dzeus36_alt $data_dir/Background/$run_dir/dzeus36

mv $data_dir/${run_dir}_input.json $data_dir/Background/$run_dir/input.json


python3 $iPATH_dir/prepare_PATH.py --root_dir $data_dir/Background/$run_dir --path_dir $iPATH_dir --run_mode 1 --input $data_dir/Background/$run_dir/input.json

cd $data_dir/Background/$run_dir
csh -v ./iPATH_zeus.s

if [ $if_local -eq 1 ]
then
    ./xdzeus36
    cd ..
else
    cd $data_dir/Background/$run_dir
    sbatch -W $root_dir/run_zeus.sh -r $data_dir/Background/$run_dir
fi

wait
#clean up some files
rm $data_dir/Background/$run_dir/zr001JH
rm $data_dir/Background/$run_dir/zr002JH
rm $data_dir/Background/$run_dir/zr003JH
rm $data_dir/Background/$run_dir/zr004JH
