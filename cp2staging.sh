#!/bin/bash

CodeDir=/shared/iPATH/nowcast_module_v1
StagingDir=/data/iPATH/nowcast_module_v1/staging

# -t simulation type: CME or Flare
# -s start date: yyyymmdd_HHMMSS
# -d where to copy files, comma-separated list: any of iSWA or SEPSB
while getopts 's:t:d:' flag; do
   case "${flag}" in
      t) Type=${OPTARG};;
      s) StartDate=${OPTARG};;
      d) Destination=${OPTARG};;
   esac
done

# default value: copy to both iSWA and SEP scoreboard
Destination=${Destination:-iSWA,SEPSB}

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
   [[ ! -f transport_earth/output.json ]] && {
      echo " !!! transport_earth/output.json is missing: cannot extract simulation start date"
      exit 1
   }

   # use the CME start time or flare peak time from DONKI, converting it from yyyy-mm-ddTHH:MM:SSZ to yyyymmdd_HHMMSS
   CME_start_time=$(jq -r '.sep_forecast_submission.triggers[0].cme.start_time // .sep_forecast_submission.triggers[0].flare.peak_time' transport_earth/output.json)
   StartDate=${CME_start_time//[-:Z]}
   StartDate=${StartDate/T/_}

   # add seconds if missing
   (( ${#StartDate} == 13 )) && StartDate=${StartDate}00

   echo "Simulation start date automatically extracted: $StartDate"
fi

pfx=ZEUS+iPATH_${Type}_$StartDate

if [[ $Destination == *iSWA* ]]; then
   {
      echo "Claudio Corti"
      echo "rt-hpc-prod"
      echo $PWD
      echo $0
   } >staging.info
fi

# SEP files for iSWA and SEP scoreboard
while read dir; do
   cd $dir

   IFS=_ read skip obs <<<$dir

   # SEP scoreboard
   if [[ $obs == earth ]]; then
      while read f; do
         if [[ $Destination == *SEPSB* ]]; then
            # strip '_differential' from file names, including files pointed to inside the json file.
            # 'differential' is added by Katie's OpSEP code to differentiate the source files used to create the output files.
            # Since we use the option --FluxType differential when invoking opsep_dir/operational_sep_quantities.py,
            # this is carried over to the output files.
            # However, the time profiles (.txt files) correspond to integral fluxes, so '_differential' is removed to avoid confusion.
            dest=$StagingDir/sep_scoreboard/${f/_differential/}
            cp -p $f $dest
            [[ $f == *.json ]] && {
               # remove also the extra field sep_forecast_submission.model_type.flux_type,
               # including the leading comma, since the previous field will become
               # the last field in the model object (JSON spec does not allow a
               # comma after the last item of an object/list)
               sed -Ei -e's/, +"flux_type": +"[^"]+"//' -e's/_differential//g' $dest
               touch -r $f $dest # restore original modification time
            }
         fi

         # save issue date, to be used for all Earth and CME files
         [[ $f == *.json ]] && SEPSB_issue_date=$(sed -E -e's/.*\.([^.]+)Z\.json/\1/' -e's/-//g' -e's/T/_/' <<<$f)
      done < <(find -type f -name 'ZEUS+iPATH_*')
   fi

   # iSWA
   if [[ $Destination == *iSWA* ]]; then
      f=$(find -type f -name '*_differential_flux.csv')
      if [[ -z $f ]]; then
         echo " !!! No differential flux in $dir: skippping"
      else
         [[ $obs == earth && ! -z $SEPSB_issue_date ]] && IssueDate=$SEPSB_issue_date || IssueDate=$(date -ud@$(stat -c %Y $f) '+%Y%m%d_%H%M%S')
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
      fi
   fi

   cd ..
done < <(find -type d -name 'transport_*' -printf '%P\n')

[[ $Destination != *iSWA* ]] && exit

# CME & shock files for iSWA
cp -p staging.info $StagingDir/iswa/info
[[ ! -z $SEPSB_issue_date ]] && IssueDate=$SEPSB_issue_date || IssueDate=$(date -ud@$(stat -c %Y shock_momenta.dat) '+%Y%m%d_%H%M%S')
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
