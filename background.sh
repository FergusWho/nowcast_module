#!/bin/bash

# default for CCMC AWS on rt-hpc-prod
iPATH_dir='/shared/iPATH/ipath_v2'
code_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'

echo "----------- Background Module -----------"

# default values for command-line arguments
run_time=$(date -u +'%Y%m%d_%H%M')
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
# create the file ${run_dir}_input.json with simulation input parameters
echo "[$(date -u +'%F %T')] Downloading solar wind data ..."
run_dir=$(python3 $code_dir/grepSW.py --root_dir $data_dir --run_time $run_time | tail -1)
echo "[$(date -u +'%F %T')] Done"
echo

[[ -z $run_dir ]] && {
   echo "[$(date -u +'%F %T')] Empty background folder name: exit"
   exit 1
}

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

# redirect everything to the logfile
{
   cd $bkg_dir

   # modify ZEUS source code according to the input json file
   echo "[$(date -u +'%F %T')] Setting up background module ..."
   python3 $code_dir/prepare_PATH.py --root_dir $bkg_dir --path_dir $iPATH_dir --run_mode 1 --input $bkg_dir/input.json
   echo "[$(date -u +'%F %T')] Done"
   echo

   echo "[$(date -u +'%F %T')] Compiling ZEUS ..."
   csh -v ./iPATH_zeus.s
   echo "[$(date -u +'%F %T')] Done"
   echo

   echo "[$(date -u +'%F %T')] Running background module ..."
   if [ $if_local -eq 1 ]
   then
      ./xdzeus36
   else
      # wait for job to finish before returning
      sbatch -W $code_dir/run_zeus.sh -r $bkg_dir

      # compress Slurm logfile
      for f in slurm*.out; do
         gzip $f
      done
   fi
   echo "[$(date -u +'%F %T')] Done"
   echo

   echo "[$(date -u +'%F %T')] Cleaning up ..."
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
   echo "[$(date -u +'%F %T')] Done"

   echo "[$(date -u +'%F %T')] SLURM jobs summary:"
   jobs=$(find -name 'slurm*' \
   | sed -E 's/.*-([0-9]+).*/\1/' \
   | sort -n \
   | paste -sd',')
   sacct -j $jobs -P -X -ojobid,submit,planned,start,end,elapsedraw,partition,ncpus,nnodes,cputimeraw,state,exitcode,workdir \
   | column -s'|' -t
   echo "[$(date -u +'%F %T')] Done"

} >>$logfile 2>&1
