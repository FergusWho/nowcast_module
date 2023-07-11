#!/bin/bash

# default for CCMC AWS on rt-hpc-prod
iPATH_dir='/shared/iPATH/ipath_v2'
code_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'

echo "----------- Background Module -----------"

# default values for command-line arguments
run_time=$(date +'%Y%m%d_%H%M' -u)
if_local=0

# testing for specific event:
# example: bash background.sh -t '20220120_0830'
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
else
    source $code_dir/set_environment.sh
fi
echo "-----------------------------------------"
echo

# download solar wind quantities from iSWA
# write the run folder name in temp.txt
# create the file ${run_dir}_input.json with simulation input parameters
echo "[$(date -u +'%F %T')] Downloading solar wind data ..."
python3 $code_dir/grepSW.py --root_dir $data_dir --run_time $run_time
echo "[$(date -u +'%F %T')] Done"
echo

run_dir=$(cat $data_dir/temp.txt)
rm $data_dir/temp.txt

echo "[$(date -u +'%F %T')] Background simulation: $run_dir"

[[ ! -s $data_dir/${run_dir}_input.json ]] && {
   echo "[$(date -u +'%F %T')] Missing input.json: exit"
   exit 1
}

bkg_dir=$data_dir/Background/$run_dir
logfile=$bkg_dir/log.txt

echo "[$(date -u +'%F %T')] Copying files to $bkg_dir ..."
mkdir $bkg_dir
# copy ZEUS source code
cp -r $iPATH_dir/Acceleration/zeus3.6/* $bkg_dir/

# use the modified dzeus36 version for nowcasting
cp $code_dir/dzeus36_alt $bkg_dir/dzeus36

mv $data_dir/${run_dir}_input.json $bkg_dir/input.json
echo "[$(date -u +'%F %T')] Done"
echo
echo "[$(date -u +'%F %T')] Switching to $logfile"

cd $bkg_dir

# modify ZEUS source code according to the input json file
echo "[$(date -u +'%F %T')] Setting up background module ..." >>$logfile
python3 $iPATH_dir/prepare_PATH.py --root_dir $bkg_dir --path_dir $iPATH_dir --run_mode 1 --input $bkg_dir/input.json >>$logfile 2>&1
echo "[$(date -u +'%F %T')] Done" >>$logfile
echo >>$logfile

echo "[$(date -u +'%F %T')] Compiling ZEUS ..." >>$logfile
csh -v ./iPATH_zeus.s >>$logfile 2>&1
echo "[$(date -u +'%F %T')] Done" >>$logfile
echo >>$logfile

echo "[$(date -u +'%F %T')] Running background module ..." >>$logfile
if [ $if_local -eq 1 ]
then
    ./xdzeus36 >>$logfile 2>&1
else
    sbatch -W $code_dir/run_zeus.sh -r $bkg_dir >>$logfile 2>&1

    # compress Slurm logfile
    for f in slurm*.out; do
        gzip $f
    done
fi
echo "[$(date -u +'%F %T')] Done" >>$logfile
echo >>$logfile

echo "[$(date -u +'%F %T')] Cleaning up ..." >>$logfile
# ZEUS restart files before steady-state solution
rm zr001JH
rm zr002JH
rm zr003JH
rm zr004JH

# ZEUS dump files before steady-state solution
rm zhto00*JH
rm zhto01*JH
rm zhto02*JH

# unused ZEUS source files
rm -r releases

# unused iPATH output files
rm -r path_output
echo "[$(date -u +'%F %T')] Done" >>$logfile
