#!/bin/bash

root_dir='/home/junxiang/Workspace/cron_test/iPATH2.0'

run_dir=$(date +'%Y-%m-%d_%H:%M' -u)

/usr/bin/python3 $root_dir/grepSW.py

mkdir $root_dir/$run_dir
cp -r $root_dir/Acceleration/zeus3.6/* $root_dir/$run_dir
cp $root_dir/input.json $root_dir/$run_dir

cat > temp.txt << EOF
$root_dir/$run_dir
1
EOF

/usr/bin/python3 $root_dir/prepare_PATH.py
rm temp.txt

cd $root_dir/$run_dir
csh -v ./iPATH_zeus.s
./xdzeus36
cd ..


