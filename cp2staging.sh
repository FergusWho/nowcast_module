#!/bin/bash

CodeDir=/shared/iPATH/nowcast_module_v1
StagingDir=/data/iPATH/nowcast_module_v1/staging

# -t Type: simulation type, CME or Flare
# -s StartDate: prediction window start date, yyyyMMDD_HHMMSS
while getopts 's:t' flag; do
   case "${flag}" in
      t) Type=${OPTARG};;
      s) StartDate=${OPTARG};;
   esac
done

if [[ -z $Type ]]; then
   [[ $(pwd) == */CME/* ]] && Type=CME
   [[ $(pwd) == */Flare/* ]] && Type=Flare
   [[ -z $Type ]] && {
      echo " !!! Simulation type not found"
      exit 1
   }

   echo "Simulation type automatically deduced: $Type"
fi

if [[ -z $StartDate ]]; then
   [[ ! -d transport_earth ]] && {
      echo " !!! transport_earth folder is missing: cannot extract simulation start date"
      exit 1
   }

   cd transport_earth
   if [[ ! -s fp_total ]]; then
      [[ ! -s fp.tar.gz ]] && {
         echo " !!! Missing fp_total and fp.tar.gz: cannot extract simulate start date"
         exit 1
      }
      tar -xf fp.tar.gz fp_total
   fi
   StartDate=$(python3 $CodeDir/get_simulation_start_time.py)
   rm fp_total
   cd ..

   echo "Simulation start date automatically extracted: $StartDate"
fi

pfx=ZEUS+iPATH_${Type}_$StartDate

{
   echo "Claudio Corti"
   echo $HOSTNAME
   echo $PWD
   echo $0
} >staging.info

# SEP files for iSWA and SEP scoreboard
find -type d -name 'transport_*' -printf '%P\n' \
| while read dir; do
   cd $dir

   IFS=_ read skip obs <<<$dir

   # SEP scoreboard
   if [[ $obs == earth ]]; then
      cp -p ZEUS+iPATH_* $StagingDir/sep_scoreboard/
   fi

   # iSWA
   IssueDate=$(date -ud@$(stat -c %Y *_differential_flux.csv) '+%Y%m%d_%H%M%S')
   declare -A alias=(
      [differential_flux]=differential-flux
      [event_integrated_fluence]=event-integrated-fluence
      [plot]=quicklook-plot
      [input]=input
   )
   ls *_differential_flux.csv *_event_integrated_fluence.txt *_plot.png input.json \
   | while read f; do
      name=${f%.*}
      name=${name#*_} # remove startdate, if present
      ext=${f##*.}
      cp -p $f $StagingDir/iswa/${pfx}_${IssueDate}_${obs}_${alias[$name]}.$ext
   done

   cd ..
done

# CME & shock files for iSWA
cp -p staging.info $StagingDir/iswa/info
IssueDate=$(date -ud@$(stat -c %Y shock_momenta.dat) '+%Y%m%d_%H%M%S')
declare -A alias=(
   [CME]=CME-shock-parameters
   [shock_momenta]=shock-momenta
   [shock_posn_comp]=shock-posn-comp
)
for f in CME.gif shock_momenta.dat shock_posn_comp.dat; do
   name=${f%.*}
   ext=${f##*.}
   cp -p $f $StagingDir/iswa/${pfx}_${IssueDate}_${alias[$name]}.$ext
done
