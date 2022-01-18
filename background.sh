#!/bin/bash
iPATH_dir='/home/junxiang/iPATH2.0'
root_dir='/home/junxiang/nowcast_module'

run_dir=$(date +'%Y-%m-%d_%H:%M' -u)

## testing for specific event:
#run_dir='2022-01-14_16:00'


/usr/bin/python3 $root_dir/grepSW.py --root_dir $root_dir --run_name $run_dir

mkdir $root_dir/$run_dir
cp -r $iPATH_dir/Acceleration/zeus3.6/* $root_dir/$run_dir
cp $root_dir/${run_dir}_input.json $root_dir/$run_dir/input.json


/usr/bin/python3 $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$run_dir --run_mode 1

cd $root_dir/$run_dir
csh -v ./iPATH_zeus.s
./xdzeus36
cd ..


