#!/bin/bash

# default values for CCMC AWS on rt-hpc-prod
code_dir='/shared/iPATH/nowcast_module_v1'
data_dir='/data/iPATH/nowcast_module_v1'
opsep_dir='/shared/iPATH/operational_sep_v3'

# default values for command-line arguments
if_local=0
thread_count=12

while getopts 'r:i:s:p:L' flag
do
    case "${flag}" in
        r) code_dir=${OPTARG};;
        i) CME_id=${OPTARG};;
        s) starttime=${OPTARG};;
        p) location=${OPTARG};;
        L) if_local=1;;
    esac
done

# validate input arguments
[[ -z $CME_id ]] && {
   echo "[$(date -u +'%F %T')] No CME or flare id given: exit"
   exit 1
}
[[ -z $starttime ]] && {
   echo "[$(date -u +'%F %T')] No start time given: exit"
   exit 1
}
[[ -z $location ]] && {
   echo "[$(date -u +'%F %T')] No location given: exit"
   exit 1
}

[[ $CME_id == *CME* ]] && type=CME || type=Flare
CME_dir=$data_dir/$type/$CME_id
trspt_dir=$CME_dir/path_output/transport_$location
cd $trspt_dir

# convert the start date from yyyy-mm-ddTHH:MM:SSZ to yyyymmdd
startdate=${starttime%T*}
startdate=${startdate//-}

echo "[$(date -u +'%F %T')] Running transport module for ${location^} ..."
if (( if_local )); then
   mpirun -np $thread_count trspt.out
else
   [[ $location == earth ]] && run_script=run_transport.sh || run_script=run_transport2.sh

   # wait for job to finish before returning
   sbatch -W $code_dir/$run_script -r $trspt_dir

   # compress Slurm logfile
   for f in slurm*.out; do
      [[ -s $f ]] && gzip $f
   done
fi
./combine.out
echo "[$(date -u +'%F %T')] ${location^}: Done"
echo

if [[ ! -s fp_total ]]; then
   echo "[$(date -u +'%F %T')] ${location^}: iPATH fp_total missing: transport job or combine step probably failed"
   echo "[$(date -u +'%F %T')] ${location^}: Skipping plotting and OpSEP"
   exit 1
fi

echo "[$(date -u +'%F %T')] ${location^}: Plotting transport results ..."
python3 $code_dir/plot_iPATH_nowcast.py
echo "[$(date -u +'%F %T')] ${location^}: Done"
echo

if [[ $location == earth ]]; then
   # convert from yyyy-mm-ddTHH:MM:SSZ to yyyy-mm-dd HH:MM:SS, optionally adding the seconds part if it's missing
   starttime=${starttime/T/ }
   starttime=${starttime/Z}
   (( $(awk -F':' '{ print NF }' <<<$starttime) < 3 )) && starttime="$starttime:00"

   # read end time from differential flux output
   endtime=$(awk -F',' 'END{ print $1 }' ${startdate}_differential_flux.csv)
   echo "[$(date -u +'%F %T')] ${location^}: Prediction window start and end time: $starttime, $endtime"

   # Use OpSep to produce output for SEP scoreboard
   echo "[$(date -u +'%F %T')] ${location^}: Using OpSEP to generate output ..."
   mkdir -p json/{library,data,output}
   cp output.json json/library/model_template.json
   cp ${startdate}_differential_flux.csv json/data/
   cd json
   python3 $opsep_dir/operational_sep_quantities.py --StartDate "$starttime" --EndDate "$endtime" --Experiment user --ModelName ZEUS+iPATH_$type --FluxType differential --UserFile ${startdate}_differential_flux.csv --spase spase://CCMC/SimulationModel/iPATH/2 --Threshold '30,1;50,1'

   # move opsep output to transport dir and cleanup
   cd $trspt_dir
   mv json/output/* .
   rm -r json
   echo "[$(date -u +'%F %T')] ${location^}: Done"
   echo

   echo "[$(date -u +'%F %T')] Copying output files to the SEP scoreboard staging area"
   cd $CME_dir/path_output
   $code_dir/cp2staging.sh -d SEPSB
   echo "[$(date -u +'%F %T')] Done"

   echo "[$(date -u +'%F %T')] ${location^}: Making CME movie ..."
   python3 $code_dir/plot_CME_info.py
   convert -delay 5 CME*.png CME.gif
   echo "[$(date -u +'%F %T')] ${location^}: Done"
   echo
fi

echo "[$(date -u +'%F %T')] ${location^}: Cleaning up ..."

# clean up some unused output
cd $trspt_dir
rm -f RawData*

# compress transport files
tar --remove-files -zcf fp.tar.gz fp_*

# remove source pngs if the animation exists and contains the right number of frames
cd $CME_dir/path_output
if [[ $location == "earth" && -s CME.gif ]]; then
   npngs=$(ls CME*.png | wc -l)
   nframes=$(identify CME.gif | wc -l)
   (( npngs == nframes )) && rm CME*.png
fi

echo "[$(date -u +'%F %T')] ${location^}: Done"
echo
