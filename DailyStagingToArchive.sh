#!/bin/bash

nDays=${1:-30}
StagingDir=/data/iPATH/nowcast_module_v1/staging

date -u +'%F %T'
echo "Moving files older than $nDays days from staging to archive area:"

find $StagingDir -type f -mtime +$nDays \
| sort -V \
| while read path; do
   echo $path
   cp -p $path ${path/staging/archive} && rm $path
done

echo
echo "Creating iSWA tar.gz archives:"
cd ${StagingDir/staging/archive}/iswa
ls | grep -v tar.gz | cut -d'_' -f1-4 | sort -V | uniq -c \
| while read n f; do
   # if there's already an archive with the same prefix from previous runs,
   # first extract files from it, so all files are added to the same archive
   [[ -f $f.tar.gz ]] && {
      tar -zxf $f.tar.gz
      rm $f.tar.gz
      n="$n UPDATE"
   }
   echo $f $n
   tar --remove-files -zcf $f.tar.gz ${f}_*
done

echo
echo "Creating SEP Scoreboard tar.gz archives:"
cd ${StagingDir/staging/archive}/sep_scoreboard
ls | grep -v tar.gz | cut -d'.' -f1-2 | sort -V | uniq -c \
| while read n f; do
   # if there's already an archive with the same prefix from previous runs,
   # first extract files from it, so all files are added to the same archive
   [[ -f $f.tar.gz ]] && {
      tar -zxf $f.tar.gz
      rm $f.tar.gz
      n="$n UPDATE"
   }
   echo $f $n
   tar --remove-files -zcf $f.tar.gz ${f}.*-*
done
