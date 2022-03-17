#!/bin/bash
iPATH_dir='/home/junxiang/iPATH2.0'
root_dir='/home/junxiang/nowcast_module'

#run_time=$(date +'%Y-%m-%d_%H:%M' -u)

# testing for specific event:
run_time='2022-01-20_08:30'


/usr/bin/python3 $root_dir/grepSW.py --root_dir $root_dir --run_time $run_time

run_dir=`cat temp.txt`
rm temp.txt


mkdir $root_dir/$run_dir
cp -r $iPATH_dir/Acceleration/zeus3.6/* $root_dir/$run_dir
cp $root_dir/${run_dir}_input.json $root_dir/$run_dir/input.json


/usr/bin/python3 $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$run_dir --run_mode 1 --input $root_dir/${run_dir}_input.json

cd $root_dir/$run_dir
csh -v ./iPATH_zeus.s
./xdzeus36
cd ..


